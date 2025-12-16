# Sistema de Manejo de Errores y Reintentos

## Arquitectura

El sistema implementa un patrón de **reintentos con backoff exponencial** y **Dead Letter Queues (DLQ)** para manejo robusto de errores.

### Componentes

#### 1. Colas RabbitMQ

**Colas Principales** (procesamiento normal):
- `renagro.json.save` - Guardar JSON en BD
- `renagro.etl.transform` - Transformar datos
- `renagro.db.insert` - Ejecutar transacción SQL

**Colas de Reintentos** (con TTL dinámico):
- `renagro.json.save.retry`
- `renagro.etl.transform.retry`
- `renagro.db.insert.retry`

**Dead Letter Queues** (errores permanentes):
- `renagro.json.save.dlq`
- `renagro.etl.transform.dlq`
- `renagro.db.insert.dlq`

#### 2. Campos en Base de Datos

Tabla `control_envios_boletas`:
- `retry_count` - Contador de reintentos (default: 0)
- `last_error_stage` - Última etapa donde falló ('json_save', 'etl_transform', 'db_insert')
- `error_message` - Mensaje del último error
- `estado_etl` - Estado del procesamiento (PENDIENTE, PROCESADO, ERROR)

## Flujo de Procesamiento

### Caso 1: Procesamiento Exitoso ✅

```
API → json_save → etl_transform → db_insert → BD (PROCESADO)
```

### Caso 2: Error con Reintentos ⚠️

```
1. Worker detecta error en procesamiento
2. Incrementa retry_count en BD
3. Actualiza last_error_stage
4. Verifica: retry_count < MAX_RETRIES (default: 3)
5. Publica a cola .retry con TTL = 2^retry_count segundos
   - Intento 1: delay 2 segundos
   - Intento 2: delay 4 segundos  
   - Intento 3: delay 8 segundos
6. Mensaje expira en cola .retry
7. RabbitMQ redirige automáticamente a cola principal
8. Worker reintenta procesamiento
```

### Caso 3: Error Permanente ❌

```
1. Worker detecta error
2. retry_count >= MAX_RETRIES
3. Marca estado_etl = ERROR en BD
4. Publica a DLQ con metadata reducida:
   {
     "_id": 12345,
     "error": "mensaje de error",
     "original_queue": "renagro.json.save",
     "retry_count": 3,
     "timestamp": 1234567890.123
   }
5. Requiere intervención manual
```

### Caso 4: Recuperación al Reiniciar 🔄

**Al iniciar el servidor API:**

```python
@app.on_event("startup")
async def startup_event():
    # 1. Cargar mapeos YAML a Redis
    mapping_loader.load_master()
    mapping_loader.load_all_mappings()
    
    # 2. Recuperar mensajes con ERROR
    await recover_failed_messages()
```

**Proceso de recuperación:**

1. Consulta BD: `SELECT * FROM control_envios_boletas WHERE estado_etl='ERROR' AND retry_count < MAX_RETRIES`
2. Para cada registro:
   - Obtiene `json_data` completo
   - Identifica `last_error_stage`
   - Publica a cola `.retry` correspondiente
   - Incrementa `retry_count`
   - Actualiza `estado_etl = PENDIENTE`
3. Pipeline continúa desde donde falló

## Configuración

### Variables de Entorno (.env)

```bash
# Número máximo de reintentos antes de enviar a DLQ
MAX_RETRIES=3

# Colas de reintentos
QUEUE_JSON_SAVE_RETRY=renagro.json.save.retry
QUEUE_ETL_TRANSFORM_RETRY=renagro.etl.transform.retry
QUEUE_DB_INSERT_RETRY=renagro.db.insert.retry

# Dead Letter Queues
QUEUE_JSON_SAVE_DLQ=renagro.json.save.dlq
QUEUE_ETL_TRANSFORM_DLQ=renagro.etl.transform.dlq
QUEUE_DB_INSERT_DLQ=renagro.db.insert.dlq
```

### Backoff Exponencial

El delay entre reintentos crece exponencialmente:

| Intento | Delay | Cálculo |
|---------|-------|---------|
| 1       | 2s    | 2^1     |
| 2       | 4s    | 2^2     |
| 3       | 8s    | 2^3     |

Esto previene sobrecarga del sistema y da tiempo para que errores transitorios se resuelvan.

## Monitoreo

### Consultar Mensajes con ERROR

```sql
-- Mensajes con errores permanentes (retry_count >= 3)
SELECT _id, retry_count, last_error_stage, error_message, fecha_recepcion
FROM sc_renagro_mag.control_envios_boletas
WHERE estado_etl = 'ERROR' AND retry_count >= 3
ORDER BY fecha_recepcion DESC;

-- Mensajes con errores recuperables (retry_count < 3)
SELECT _id, retry_count, last_error_stage, error_message, fecha_recepcion
FROM sc_renagro_mag.control_envios_boletas
WHERE estado_etl = 'ERROR' AND retry_count < 3
ORDER BY fecha_recepcion DESC;
```

### Consultar DLQs en RabbitMQ

```bash
# Ver mensajes en Dead Letter Queue
rabbitmqadmin get queue=renagro.json.save.dlq count=10

# Ver estadísticas de colas
rabbitmqadmin list queues name messages
```

### Logs

Buscar en logs por etapa:

```bash
# Errores en json_save
grep "[json_save].*ERROR" logs/etl_errors.log

# Errores en etl_transform
grep "[etl_transform].*ERROR" logs/etl_errors.log

# Errores en db_insert
grep "[db_insert].*ERROR" logs/etl_errors.log

# Mensajes enviados a DLQ
grep "enviado a DLQ" logs/etl_errors.log
```

## Reprocesar Mensajes con ERROR

### Opción 1: Reiniciar Servidor (automático)

```bash
# Al reiniciar, recovery.py procesa automáticamente mensajes ERROR
uvicorn src.api:app --host 0.0.0.0 --port 8000
```

### Opción 2: Script Manual de Recuperación

```bash
# Ejecutar recovery standalone
python -m src.recovery
```

### Opción 3: Corrección Manual + Reset

```sql
-- 1. Corregir YAML o código fuente
-- 2. Resetear contador de reintentos
UPDATE sc_renagro_mag.control_envios_boletas
SET retry_count = 0,
    estado_etl = 'PENDIENTE',
    last_error_stage = NULL
WHERE _id = 12345;

-- 3. Reiniciar servidor para que recovery lo procese
```

### Opción 4: Consumir DLQ

```python
# Script para consumir y reprocesar DLQ
async def reprocess_dlq():
    async for message in dlq_queue.iterator():
        dlq_data = json.loads(message.body)
        _id = dlq_data['_id']
        
        # Obtener JSON completo de BD
        with db.get_session() as session:
            record = session.query(ControlEnviosBoletas).filter_by(_id=_id).first()
            if record:
                # Resetear y republicar
                record.retry_count = 0
                record.estado_etl = EstadoETLEnum.PENDIENTE
                session.commit()
                
                # Publicar a cola principal
                await rabbitmq_client.publish_message(
                    queue_name=config.QUEUE_JSON_SAVE,
                    message=record.json_data
                )
```

## Ventajas del Sistema

✅ **Sin pérdida de datos** - Todos los mensajes se guardan en BD  
✅ **Reintentos inteligentes** - Backoff exponencial previene sobrecarga  
✅ **Trazabilidad completa** - Logs + BD + DLQ  
✅ **Recuperación automática** - Al reiniciar servidor  
✅ **Eficiencia de memoria** - DLQ solo guarda `_id`, no JSON completo  
✅ **Intervención manual** - Para errores permanentes que requieren corrección de código  
✅ **Identificación de etapa** - `last_error_stage` indica dónde falló  

## Limitaciones

⚠️ Después de 3 intentos (MAX_RETRIES), el mensaje va a DLQ y requiere:
- Corrección del código fuente o YAML
- Reinicio del servidor
- Reseteo manual del registro en BD

⚠️ Mensajes en DLQ no se reprocesarán automáticamente  
⚠️ Recovery al startup solo procesa mensajes con `retry_count < MAX_RETRIES`
