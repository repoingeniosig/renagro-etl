# Sistema de Envío a API Remota MAG

## Descripción General

Sistema de dos fases para enviar datos procesados a la API remota de RENAGRO:

1. **Fase 1**: Construcción de JSONs desde la base de datos
2. **Fase 2**: Envío paralelo con reintentos a API remota

## Arquitectura

```
┌──────────────────────────────────────────────────────────────┐
│ FASE 1: Construcción de JSONs                                │
└──────────────────────────────────────────────────────────────┘

PostgreSQL (control_envios_boletas)
    │ estado_etl='PROCESADO'
    │ envio_datos_procesados='PENDIENTE'
    │
    ▼
Worker: envio_mag
    │ - Consulta en lotes (BATCH_SIZE_SEND_MAG)
    │ - Construye JSON según mappings-envio-mag/
    │ - Guarda debug si DEBUG_JSON_OUTPUT=true
    │
    ▼
RabbitMQ: QUEUE_ENVIO_MAG_SEND
    │ Mensaje: {control_id, record_id, json_data, control_table}
    │
    ▼

┌──────────────────────────────────────────────────────────────┐
│ FASE 2: Envío a API Remota                                   │
└──────────────────────────────────────────────────────────────┘

Worker: envio_mag_sender
    │ - Consume cola con prefetch=PARALLEL_REQUESTS_SEND_MAG
    │ - Envío paralelo controlado por semáforo
    │ - Actualiza estado en BD
    │
    ▼
API Remota RENAGRO
    │ POST {RENAGRO_ENDPOINT}
    │ Authorization: {RENAGRO_TOKEN}
    │
    ▼
Respuesta HTTP
    │
    ├─► 201 Created
    │   └─► UPDATE control_envios SET envio_datos_procesados='ENVIADO'
    │
    ├─► 4xx Client Error
    │   └─► UPDATE control_envios SET envio_datos_procesados='ERROR'
    │       (NO reintenta)
    │
    └─► 5xx Server Error
        └─► Reintentos con backoff (5s, 10s, 20s)
            │
            ├─► Éxito → 'ENVIADO'
            └─► Agotados → 'ERROR' con mensaje
```

## Variables de Entorno

```bash
# API Remota
RENAGRO_ENDPOINT=https://api.renagro.gob.ec/v1/boletas
RENAGRO_TOKEN=Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Configuración de envío
PARALLEL_REQUESTS_SEND_MAG=10    # Solicitudes HTTP simultáneas
MAX_RETRY_ATTEMPTS=3              # Reintentos para errores 5xx
BATCH_SIZE_SEND_MAG=1000          # Registros consultados por lote
DEBUG_JSON_OUTPUT=false           # Guardar JSONs en temp_json_output/

# Colas RabbitMQ (auto-configuradas)
QUEUE_ENVIO_MAG_SEND=renagro.envio.mag.send
QUEUE_ENVIO_MAG_SEND_RETRY=renagro.envio.mag.send.retry
QUEUE_ENVIO_MAG_SEND_DLQ=renagro.envio.mag.send.dlq
```

## Uso

### Opción 1: Script automático

Ejecuta ambos workers en secuencia:

```bash
./run_envio_mag.sh
```

### Opción 2: Ejecución manual

```bash
# Paso 1: Construir JSONs desde BD
python -m src.workers envio_mag

# Esperar a que termine...

# Paso 2: Enviar JSONs a API remota
python -m src.workers envio_mag_sender
```

### Opción 3: Servicios systemd (producción)

```bash
# Ejecutar ambos workers como servicios
sudo systemctl start renagro-envio-mag.service
sudo systemctl start renagro-envio-mag-sender.service

# Ver logs en tiempo real
sudo journalctl -u renagro-envio-mag.service -f
sudo journalctl -u renagro-envio-mag-sender.service -f
```

## Estados de Control

### Tabla: control_envios_boletas

| Campo | Valores | Descripción |
|-------|---------|-------------|
| `estado_etl` | PENDIENTE, PROCESANDO, PROCESADO, ERROR | Estado del pipeline ETL |
| `envio_datos_procesados` | PENDIENTE, ENTREGANDO, ENVIADO, ERROR | Estado del envío a API |
| `error_envio_datos` | TEXT | Mensaje de error (solo si envio=ERROR) |

### Flujo de estados para envío

```
estado_etl='PROCESADO' + envio_datos_procesados='PENDIENTE'
    │
    ▼ (Worker envio_mag construye JSON)
    │
envio_datos_procesados='PENDIENTE'  (JSON en cola RabbitMQ)
    │
    ▼ (Worker envio_mag_sender consume)
    │
envio_datos_procesados='ENTREGANDO'  (Enviando a API)
    │
    ├─► HTTP 201 → envio_datos_procesados='ENVIADO'
    │
    └─► HTTP 4xx/5xx → envio_datos_procesados='ERROR'
                       error_envio_datos='HTTP 400: Bad Request...'
```

## Manejo de Errores

### Errores 4xx (Cliente)

**Causa**: Problema con el JSON enviado (validación, formato, etc.)

**Acción**:
- NO reintenta automáticamente
- Marca como ERROR inmediatamente
- Guarda mensaje de error en `error_envio_datos`

**Ejemplo**:
```
HTTP 400: {"error": "Campo 'provincia' es requerido"}
```

**Solución**:
1. Revisar error en BD
2. Corregir mapping YAML si es necesario
3. Reprocesar registro manualmente

### Errores 5xx (Servidor)

**Causa**: Problema temporal del servidor remoto (sobrecarga, mantenimiento)

**Acción**:
- Reintenta automáticamente hasta MAX_RETRY_ATTEMPTS
- Backoff exponencial: 5s → 10s → 20s
- Si agota reintentos, marca como ERROR

**Ejemplo**:
```
HTTP 503: Service Unavailable
```

**Solución**:
- Esperar a que servidor remoto se recupere
- Reprocesar registros con ERROR manualmente

### Errores de Red

**Causa**: Problemas de conectividad (timeout, DNS, etc.)

**Acción**:
- Reintenta automáticamente
- Marca como ERROR después de reintentos

**Ejemplo**:
```
Error de conexión: Connection timeout after 30s
```

## Consultas SQL Útiles

### Estadísticas generales

```sql
SELECT 
  envio_datos_procesados AS estado,
  COUNT(*) AS cantidad,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS porcentaje
FROM sc_renagro_mag.control_envios_boletas
WHERE estado_etl = 'PROCESADO'
GROUP BY envio_datos_procesados
ORDER BY cantidad DESC;
```

### Registros pendientes de envío

```sql
SELECT 
  _id,
  fecha_recepcion,
  fecha_etl_completo
FROM sc_renagro_mag.control_envios_boletas
WHERE estado_etl = 'PROCESADO' 
  AND envio_datos_procesados = 'PENDIENTE'
ORDER BY fecha_recepcion ASC
LIMIT 100;
```

### Errores de envío

```sql
SELECT 
  _id,
  fecha_recepcion,
  error_envio_datos,
  LENGTH(error_envio_datos) AS error_length
FROM sc_renagro_mag.control_envios_boletas
WHERE envio_datos_procesados = 'ERROR'
ORDER BY fecha_recepcion DESC
LIMIT 20;
```

### Tipos de errores más comunes

```sql
SELECT 
  SUBSTRING(error_envio_datos FROM 1 FOR 50) AS error_prefix,
  COUNT(*) AS cantidad
FROM sc_renagro_mag.control_envios_boletas
WHERE envio_datos_procesados = 'ERROR'
GROUP BY error_prefix
ORDER BY cantidad DESC
LIMIT 10;
```

### Registros en proceso de envío

```sql
SELECT 
  _id,
  fecha_recepcion
FROM sc_renagro_mag.control_envios_boletas
WHERE envio_datos_procesados = 'ENTREGANDO'
ORDER BY fecha_recepcion DESC;
```

### Performance: Tiempo promedio de envío

```sql
SELECT 
  AVG(EXTRACT(EPOCH FROM (fecha_envio_completo - fecha_etl_completo))) AS segundos_promedio,
  MIN(EXTRACT(EPOCH FROM (fecha_envio_completo - fecha_etl_completo))) AS segundos_minimo,
  MAX(EXTRACT(EPOCH FROM (fecha_envio_completo - fecha_etl_completo))) AS segundos_maximo
FROM sc_renagro_mag.control_envios_boletas
WHERE envio_datos_procesados = 'ENVIADO'
  AND fecha_envio_completo IS NOT NULL;
```

## Debug Mode

### Activar modo debug

```bash
# En .env
DEBUG_JSON_OUTPUT=true
```

### Ver JSONs generados

```bash
# Ejecutar worker
python -m src.workers envio_mag

# JSONs se guardan en temp_json_output/
ls -lh temp_json_output/

# Ver contenido
cat temp_json_output/boleta_237.json | jq .

# Contar JSONs
ls temp_json_output/ | wc -l

# Limpiar directorio
rm -rf temp_json_output/*.json
```

### Validar JSON manualmente

```bash
# Copiar JSON de debug
cp temp_json_output/boleta_237.json /tmp/test.json

# Probar envío con curl
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer tu_token" \
  -d @/tmp/test.json \
  https://api.renagro.gob.ec/v1/boletas
```

## Logs

### Ver logs de construcción de JSONs

```bash
# Logs del worker envio_mag
tail -f logs/worker_envio_mag.log

# Buscar errores
grep ERROR logs/worker_envio_mag.log

# Filtrar por fecha
grep "2025-12-08" logs/worker_envio_mag.log | grep ERROR
```

### Ver logs de envío

```bash
# Logs del worker envio_mag_sender
tail -f logs/worker_envio_mag.log

# Ver estadísticas finales
tail -20 logs/worker_envio_mag.log | grep "ESTADÍSTICAS"

# Buscar envíos exitosos
grep "✅ Enviado" logs/worker_envio_mag.log

# Buscar errores de envío
grep "❌ Error enviando" logs/worker_envio_mag.log
```

## Monitoreo en Producción

### Métricas clave

1. **Tasa de éxito**: % de envíos exitosos vs errores
2. **Latencia promedio**: Tiempo de respuesta de la API
3. **Errores 4xx vs 5xx**: Clasificación de errores
4. **Registros pendientes**: Acumulación en cola

### Alertas recomendadas

```bash
# Alerta: Más de 100 registros pendientes
SELECT COUNT(*) FROM control_envios_boletas 
WHERE estado_etl='PROCESADO' AND envio_datos_procesados='PENDIENTE';

# Alerta: Tasa de error > 10%
SELECT 
  ROUND(COUNT(*) FILTER (WHERE envio_datos_procesados='ERROR') * 100.0 / COUNT(*), 2) AS error_rate
FROM control_envios_boletas
WHERE estado_etl='PROCESADO';

# Alerta: Registros atascados en ENTREGANDO > 5 minutos
SELECT COUNT(*) FROM control_envios_boletas
WHERE envio_datos_procesados='ENTREGANDO'
  AND fecha_etl_completo < NOW() - INTERVAL '5 minutes';
```

## Reprocesamiento Manual

### Reprocesar registros con ERROR

```sql
-- Marcar como PENDIENTE para reprocesar
UPDATE sc_renagro_mag.control_envios_boletas
SET 
  envio_datos_procesados = 'PENDIENTE',
  error_envio_datos = NULL
WHERE envio_datos_procesados = 'ERROR'
  AND _id IN (237, 238, 240);  -- IDs específicos

-- Ejecutar worker nuevamente
python -m src.workers envio_mag
python -m src.workers envio_mag_sender
```

### Limpiar registros atascados

```sql
-- Si registros quedaron en ENTREGANDO por fallo del worker
UPDATE sc_renagro_mag.control_envios_boletas
SET envio_datos_procesados = 'PENDIENTE'
WHERE envio_datos_procesados = 'ENTREGANDO'
  AND fecha_etl_completo < NOW() - INTERVAL '10 minutes';
```

## Troubleshooting

### Worker no encuentra registros pendientes

**Síntoma**: "No hay registros pendientes"

**Causas**:
1. No hay registros con estado_etl='PROCESADO'
2. Todos ya fueron enviados (envio_datos_procesados='ENVIADO')

**Solución**:
```sql
-- Verificar registros disponibles
SELECT 
  estado_etl,
  envio_datos_procesados,
  COUNT(*)
FROM control_envios_boletas
GROUP BY estado_etl, envio_datos_procesados;
```

### Error: "API endpoint o token no configurados"

**Causa**: Variables de entorno faltantes

**Solución**:
```bash
# Verificar .env
cat .env | grep RENAGRO

# Agregar variables
echo "RENAGRO_ENDPOINT=https://api.example.com" >> .env
echo "RENAGRO_TOKEN=Bearer token_here" >> .env
```

### Error: "Connection timeout after 30s"

**Causa**: API remota lenta o inaccesible

**Solución**:
1. Verificar conectividad: `curl -I https://api.renagro.gob.ec`
2. Revisar firewall/proxy
3. Aumentar timeout en api_sender_envio_mag.py si es necesario

### JSONs no se guardan en debug mode

**Causa**: DEBUG_JSON_OUTPUT=false o directorio sin permisos

**Solución**:
```bash
# Activar debug
export DEBUG_JSON_OUTPUT=true

# Crear directorio manualmente
mkdir -p temp_json_output
chmod 755 temp_json_output

# Ejecutar worker
python -m src.workers envio_mag
```

## Performance Tuning

### Ajustar paralelismo

```bash
# Para servidores potentes
PARALLEL_REQUESTS_SEND_MAG=50

# Para servidores con recursos limitados
PARALLEL_REQUESTS_SEND_MAG=5

# Para testing local
PARALLEL_REQUESTS_SEND_MAG=2
```

### Ajustar tamaño de lote

```bash
# Lotes grandes (menos queries, más memoria)
BATCH_SIZE_SEND_MAG=5000

# Lotes pequeños (más queries, menos memoria)
BATCH_SIZE_SEND_MAG=100
```

### Monitorear uso de recursos

```bash
# CPU y memoria del worker
top -p $(pgrep -f "envio_mag_sender")

# Conexiones HTTP activas
netstat -an | grep ESTABLISHED | grep 443 | wc -l

# Mensajes en cola RabbitMQ
sudo rabbitmqctl list_queues name messages
```
