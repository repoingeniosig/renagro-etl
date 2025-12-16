# Protección Contra Duplicados - Sistema Envío MAG

## Problema Identificado

### Sin Protección (ANTES)

```
T=0min (Timer 1ra ejecución):
  Query: WHERE estado_etl='PROCESADO' AND envio_datos_procesados='PENDIENTE'
  → 100 registros
  
  └─ Lote 1 (10 registros):
       ├─ Construir JSONs
       ├─ Publicar a RabbitMQ
       └─ Estado: PENDIENTE (sin cambio) ❌
  
  └─ Total: 100 registros procesados, estado=PENDIENTE

T=5min (Timer 2da ejecución):
  Query: WHERE estado_etl='PROCESADO' AND envio_datos_procesados='PENDIENTE'
  → 150 registros (100 viejos + 50 nuevos) ❌
  
  └─ Duplica los 100 registros anteriores
```

**Problema:** Los registros procesados siguen con `PENDIENTE`, se reprosesan en cada ejecución del timer.

---

## Solución Implementada (DESPUÉS)

### Estado PROCESANDO como Barrera

```sql
-- migrations/004_add_procesando_estado.sql
ALTER TYPE sc_renagro_mag.estado_envio_enum ADD VALUE IF NOT EXISTS 'PROCESANDO';
```

### Flujo Corregido

```
T=0min (Timer 1ra ejecución):
  Query: WHERE estado_etl='PROCESADO' AND envio_datos_procesados='PENDIENTE'
  → 100 registros
  
  └─ Para cada registro:
       1. UPDATE SET envio_datos_procesados='PROCESANDO'  ✅
       2. Construir JSON
          ├─ Éxito → Publicar a RabbitMQ
          └─ Error → UPDATE SET envio_datos_procesados='ERROR'
  
  └─ Resultado:
       ├─ 95 registros exitosos → estado='PROCESANDO'
       └─ 5 registros con error → estado='ERROR'

T=5min (Timer 2da ejecución):
  Query: WHERE estado_etl='PROCESADO' AND envio_datos_procesados='PENDIENTE'
  → 50 registros nuevos ✅
  
  └─ Los 100 anteriores NO se procesan (están en PROCESANDO)
  └─ Solo procesa los 50 nuevos
```

---

## Estados y Transiciones

```
PENDIENTE
    │
    ▼ [Timer: consulta + marca PROCESANDO]
    │
PROCESANDO ──────────────────────┐
    │                            │
    ├─► [Construye JSON OK]      │
    │   └─► Publica RabbitMQ     │
    │       (estado: PROCESANDO) │
    │                            │
    └─► [Error construcción] ────┼──► ERROR
                                 │    (no reencola)
                                 │
                                 ▼
                        [Worker sender consume]
                                 │
                        ENTREGANDO
                                 │
                    ├────────────┼────────────┐
                    │            │            │
              HTTP 201      HTTP 4xx     HTTP 5xx
                    │            │            │
                    ▼            ▼            ▼
                ENVIADO       ERROR      [Reintentos]
                                              │
                                    ├─────────┴─────────┐
                                    │                   │
                                  Éxito             Agotados
                                    │                   │
                                    ▼                   ▼
                                ENVIADO              ERROR
```

---

## Casos de Error

### 1. Error Construcción JSON

**Ejemplo:** Datos faltantes en BD, mapeo incorrecto

```python
try:
    self._mark_as_processing(control_id)  # Estado: PROCESANDO
    json_data = self.build_json_for_record(...)
except Exception as e:
    # ❌ ERROR permanente (equivalente a 4xx)
    self._mark_as_error(control_id, f"Error construyendo JSON: {e}")
    # Estado: ERROR
    # NO se publica a RabbitMQ
    # NO se reencola
```

**Query siguiente ejecución:** NO lo encuentra (estado=ERROR)

---

### 2. Error HTTP 4xx

**Ejemplo:** Validación API, formato incorrecto

```python
response = await session.post(url, json=json_data)

if 400 <= response.status < 500:
    # ❌ ERROR permanente
    await self.update_control_status(
        control_id, 
        'ERROR',
        f"HTTP {response.status}: {await response.text()}"
    )
    # NO reencola
```

**Query siguiente ejecución:** NO lo encuentra (estado=ERROR)

---

### 3. Error HTTP 5xx

**Ejemplo:** API remota caída, timeout

```python
response = await session.post(url, json=json_data)

if 500 <= response.status < 600:
    # ⚠️ Reintenta con backoff exponencial
    for attempt in range(MAX_RETRY_ATTEMPTS):
        await asyncio.sleep(backoff_delay)
        retry_response = await session.post(url, json=json_data)
        
        if retry_response.status == 201:
            # ✅ Éxito en reintento
            await self.update_control_status(control_id, 'ENVIADO')
            break
    else:
        # ❌ Reintentos agotados
        await self.update_control_status(
            control_id,
            'ERROR',
            f"HTTP 5xx agotado después de {MAX_RETRY_ATTEMPTS} reintentos"
        )
```

**Query siguiente ejecución:** NO lo encuentra (estado=ENVIADO o ERROR)

---

## Garantías del Sistema

### ✅ No Duplicados

- **Timer cada 5 min:** Solo consulta registros con `PENDIENTE`
- **Marca PROCESANDO antes de construir:** Evita reprosesamientos
- **Actualiza a ENVIADO/ERROR después de HTTP:** Estados finales

### ✅ Reintentos Solo para 5xx

- **4xx:** Error cliente → ERROR inmediato (sin reintentos)
- **5xx:** Error servidor → Reintentos con backoff exponencial
- **Error JSON:** Error construcción → ERROR inmediato (sin publicar)

### ✅ Idempotencia

- **HTTP 201:** Marca ENVIADO (no vuelve a procesar)
- **HTTP 4xx:** Marca ERROR (no vuelve a procesar)
- **5xx agotado:** Marca ERROR (no vuelve a procesar)

---

## Consultas de Monitoreo

```sql
-- Registros pendientes de procesamiento
SELECT COUNT(*) 
FROM sc_renagro_mag.control_envios_boletas
WHERE estado_etl = 'PROCESADO' 
  AND envio_datos_procesados = 'PENDIENTE';

-- Registros en construcción de JSON (esperando envío)
SELECT COUNT(*) 
FROM sc_renagro_mag.control_envios_boletas
WHERE envio_datos_procesados = 'PROCESANDO';

-- Registros enviándose actualmente
SELECT COUNT(*) 
FROM sc_renagro_mag.control_envios_boletas
WHERE envio_datos_procesados = 'ENTREGANDO';

-- Registros completados exitosamente
SELECT COUNT(*) 
FROM sc_renagro_mag.control_envios_boletas
WHERE envio_datos_procesados = 'ENVIADO';

-- Errores permanentes (requieren intervención manual)
SELECT 
    _id,
    error_mensajes_envio,
    fecha_recepcion,
    updated_at
FROM sc_renagro_mag.control_envios_boletas
WHERE envio_datos_procesados = 'ERROR'
ORDER BY updated_at DESC
LIMIT 20;

-- Estadísticas generales
SELECT 
    envio_datos_procesados AS estado,
    COUNT(*) AS cantidad,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS porcentaje
FROM sc_renagro_mag.control_envios_boletas
WHERE estado_etl = 'PROCESADO'
GROUP BY envio_datos_procesados
ORDER BY cantidad DESC;
```

---

## Migración Necesaria

```bash
# Aplicar migración antes de desplegar
psql -h localhost -U postgres -d renagro_db \
  -f migrations/004_add_procesando_estado.sql
```

**Importante:** Los registros existentes con `PENDIENTE` se procesarán normalmente en la próxima ejecución del timer.
