

## Configuración Inicial de Base de Datos

### Conectar a la base de datos
```bash
docker exec -it renagro-etl-db psql -U postgres -d renagro
```

### Ejecutar Migraciones (en orden)

```bash
docker exec -i renagro-etl-db psql -U postgres -d renagro < ./migrations/001_sc_renagro_mag_estructura.sql

docker exec -i renagro-etl-db psql -U postgres -d renagro < ./migrations/002_create_control_tables.sql

docker exec -i renagro-etl-db psql -U postgres -d renagro < ./migrations/003_nuevos_campos_renagro_mag.sql

docker exec -i renagro-etl-db psql -U postgres -d renagro < ./migrations/004_update_estado_envio_enum.sql

docker exec -i renagro-etl-db psql -U postgres -d renagro < ./migrations/005_add_error_mensajes_envio_column.sql

docker exec -i renagro-etl-db psql -U postgres -d renagro < ./migrations/006_add_procesando_estado.sql

docker exec -i renagro-etl-db psql -U postgres -d renagro < ./migrations/007_add_reintentable_column.sql
```

## Utilidades de Base de Datos

### Backup de datos
```bash
docker exec -t renagro-etl-db sh -c "pg_dump -U postgres --data-only --column-inserts -d renagro" > datos.sql
```

## Procesamiento de Datos

### Cargar datos desde archivo JSON (volcado de Kobo Toolbox)
```bash
python3 -m src.batch_processor /somepath/data.json
```

## Redis Cache

### Limpiar caché de Redis
```bash
docker exec -it renagro-etl-redis redis-cli
FLUSHDB
```

## Ejecución del Sistema ETL

### Iniciar API REST
```bash
uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
```

### Iniciar todos los workers de RabbitMQ
```bash
sh run_all_workers.sh
```

### Detener todos los workers
```bash
sh stop_workers.sh
```
