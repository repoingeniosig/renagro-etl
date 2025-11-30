# Procesamiento por Lotes - Batch Processor

Script para procesar múltiples registros desde un archivo JSON y enviarlos a la cola ETL.

## 📋 Requisitos

1. **Servidor API y workers activos**:
   ```bash
   # Terminal 1: Iniciar API
   python run_server.py
   
   # Terminal 2: Iniciar workers
   ./run_all_workers.sh
   ```

2. **RabbitMQ ejecutándose**

3. **PostgreSQL con base de datos configurada**

## 📖 Uso

### Estructura del archivo JSON

El archivo debe tener esta estructura:

```json
{
    "count": 38,
    "next": null,
    "previous": null,
    "results": [
        {
            "_id": 12345,
            "_uuid": "abc-123",
            "datos_productor/nombre": "Juan Pérez",
            ...
        },
        {
            "_id": 12346,
            "_uuid": "def-456",
            "datos_productor/nombre": "María García",
            ...
        }
    ]
}
```

### Comandos

```bash
# Procesar lote (omite duplicados por defecto)
python3 -m src.batch_processor datos.json

# Procesar lote permitiendo duplicados (actualiza registros existentes)
python3 -m src.batch_processor --allow-duplicates datos.json
```

## 🔄 Flujo de Procesamiento

1. **Carga del archivo**: Lee el JSON y extrae los registros de `results`
2. **Validación**: Verifica que cada registro tenga campo `_id`
3. **Verificación de duplicados**: Consulta BD para detectar IDs existentes
4. **Publicación a cola**: Envía cada registro válido a `renagro.json.save`
5. **Procesamiento ETL**: Los workers procesan automáticamente:
   - `json_save`: Guarda en `control_envios_boletas`
   - `etl_transform`: Transforma según mapeos YAML
   - `db_insert`: Ejecuta transacción en BD

## 📊 Salida Esperada

```
================================================================================
RENAGRO ETL - PROCESAMIENTO POR LOTES
Envío de registros a cola de procesamiento
================================================================================

📂 Cargando archivo: datos.json
✅ Archivo cargado exitosamente
   Tamaño: 125,432 bytes (122.49 KB)
   Total de registros: 38

Procesando registros... ━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 38/38

================================================================================
RESUMEN DE PROCESAMIENTO
================================================================================
📊 Total de registros: 38
✅ Enviados a cola:    35
⏭️  Duplicados omitidos: 2
⚠️  Inválidos:          1
❌ Errores:            0
================================================================================

✅ 35 registros encolados para procesamiento ETL

💡 Los workers procesarán los registros automáticamente.
   Puedes consultar el estado en la tabla 'control_envios_boletas'
```

## 📌 Notas Importantes

1. **Duplicados**:
   - Por defecto (`--skip-duplicates` implícito): Omite registros con `_id` ya existente
   - Con `--allow-duplicates`: Actualiza el JSON en BD y resetea estado a PENDIENTE

2. **Registros inválidos**: Se omiten registros sin campo `_id` requerido

3. **Monitoreo**: 
   ```sql
   -- Ver estado de procesamiento
   SELECT _id, estado_etl, procesado_at, error_message
   FROM control_envios_boletas
   ORDER BY created_at DESC
   LIMIT 20;
   ```

4. **Logs**:
   - Script: Consola con Rich (barra de progreso)
   - ETL: `logs/etl.log`
   - Workers: `logs/worker_*.log`

## ⚠️ Diferencias con `process_json.py`

| Aspecto | `process_json.py` | `batch_processor.py` |
|---------|-------------------|----------------------|
| Entrada | 1 formulario completo | Lote con múltiples registros |
| Procesamiento | Síncrono (inmediato) | Asíncrono (vía colas) |
| Duplicados | Permite actualización | Configurable (omitir/actualizar) |
| Uso | Testing/Debug | Carga masiva desde API |
| Workers | NO requiere | SÍ requiere (deben estar activos) |

## 🚀 Casos de Uso

- **Importación inicial**: Cargar datos históricos desde API de KoboToolbox
- **Sincronización**: Procesar respuestas pendientes desde JSON exportado
- **Recuperación**: Reprocesar lotes que fallaron
- **Testing**: Probar ETL con múltiples registros reales

## 🔍 Ejemplo Completo

```bash
# 1. Iniciar servicios

# Alternativa
uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
python3 run_server.py

./run_all_workers.sh

# 2. Procesar lote
python -m src.batch_processor data/kobo_export_20250130.json

# 3. Monitorear procesamiento
tail -f logs/worker_json_save.log

# 4. Verificar resultados en BD
psql -d renagro_db -c "SELECT estado_etl, COUNT(*) FROM control_envios_boletas GROUP BY estado_etl;"
```

## ❓ Solución de Problemas

### Error: "No se pudo publicar a cola"
- Verificar que RabbitMQ esté ejecutándose: `systemctl status rabbitmq-server`
- Verificar credenciales en `.env`

### Registros quedan en PENDIENTE
- Verificar que workers estén activos: `ps aux | grep workers`
- Revisar logs de workers: `tail -f logs/worker_*.log`

### Duplicados no se omiten
- Usar flag `--allow-duplicates` si quieres actualizarlos
- Sin flag: duplicados se omiten automáticamente
