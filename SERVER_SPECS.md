# Especificaciones del Servidor de Producción

## Hardware

- **CPUs:** 4 cores
- **RAM:** 16 GB
- **Disco:** 250 GB SSD
- **Sistema Operativo:** Ubuntu Server 22.04 LTS
- **Usuario:** ubuntu

## Asignación de Recursos

### Total disponible: 4 CPUs, 16GB RAM

| Servicio | CPUs | RAM | Prioridad | Descripción |
|----------|------|-----|-----------|-------------|
| **renagro-api** | 1.5 (150%) | 4GB (soft: 3GB) | Alta | FastAPI con 2 workers uvicorn |
| **worker-json-save** | 0.75 (75%) | 2GB (soft: 1.5GB) | Media | Guardar JSON en BD |
| **worker-etl-transform** | 1.0 (100%) | 4GB (soft: 3GB) | Alta | Transformaciones (más pesado) |
| **worker-db-insert** | 0.75 (75%) | 2GB (soft: 1.5GB) | Alta | Inserción SQL |
| **PostgreSQL** | - | ~2GB | Crítica | Base de datos |
| **RabbitMQ** | - | ~512MB | Crítica | Message broker |
| **Redis** | - | ~256MB | Media | Cache |
| **Nginx** | - | ~128MB | Alta | Reverse proxy |
| **Sistema** | - | ~1GB | - | Ubuntu + overhead |

**Total asignado:**
- CPUs: 4.0 cores (100% utilización máxima)
- RAM: ~16GB

### Límites configurados en systemd

**API:**
- `CPUQuota=150%` → Máximo 1.5 CPUs
- `MemoryLimit=4G` → Hard limit 4GB
- `MemoryHigh=3G` → Soft limit 3GB (empieza a hacer throttling)
- `CPUWeight=100` → Prioridad normal

**Worker ETL Transform** (más pesado):
- `CPUQuota=100%` → Máximo 1 CPU
- `MemoryLimit=4G` → Hard limit 4GB
- `MemoryHigh=3G` → Soft limit 3GB
- `CPUWeight=100` → Prioridad normal

**Workers JSON Save y DB Insert**:
- `CPUQuota=75%` → Máximo 0.75 CPUs cada uno
- `MemoryLimit=2G` → Hard limit 2GB
- `MemoryHigh=1536M` → Soft limit 1.5GB
- `CPUWeight=80-90` → Prioridad media-alta

### API: 2 workers uvicorn (no 4)

Con 4 CPUs, usar 2 workers es óptimo porque:
- 1 worker = 1 proceso Python
- 2 workers permiten manejar 2 requests simultáneos
- Más workers = más overhead de memoria
- RabbitMQ maneja la carga asíncrona real

**Regla general:** workers = (CPUs / 2) + 1
- (4 / 2) + 1 = 3 workers
- Usamos 2 para dejar margen a workers ETL

## Espacio en Disco (250GB)

### Estimación de uso

| Componente | Uso estimado | Descripción |
|------------|--------------|-------------|
| Sistema operativo | 10 GB | Ubuntu Server + paquetes |
| Aplicación | 2 GB | Python + deps + código |
| PostgreSQL data | 50-100 GB | Datos de formularios (crece) |
| Logs (systemd journal) | 2-5 GB | journald con límite |
| Logs aplicación | 1-2 GB | etl_process.log + etl_errors.log |
| RabbitMQ data | 1-5 GB | Mensajes persistentes |
| Redis snapshots | 512 MB | Cache dumps |
| Backups | 50 GB | Backups de PostgreSQL |
| **Disponible** | **~100 GB** | Margen para crecimiento |

### Configuración de límites

**systemd journal:**
```bash
# /etc/systemd/journald.conf
[Journal]
SystemMaxUse=2G
SystemMaxFileSize=128M
MaxRetentionSec=2week
```

**Logs aplicación:**
- Rotación semanal automática (TimedRotatingFileHandler)
- Mantiene 12 semanas = ~3 meses
- Estimado: 1GB total

**PostgreSQL:**
```bash
# Configurar autovacuum para limpiar
# Monitorear con: SELECT pg_size_pretty(pg_database_size('renagro_db'));
```

## Monitoreo de Recursos

### Ver uso actual

```bash
# CPU y memoria
htop

# Disco
df -h
du -sh /opt/renagro-etl-process/*
du -sh /var/lib/postgresql/
du -sh /var/lib/rabbitmq/

# systemd resources
systemctl status renagro-api.service
systemctl show renagro-api.service -p MemoryCurrent -p CPUUsageNSec

# Logs de systemd journal
sudo journalctl --disk-usage
```

### Alertas recomendadas

**Disco:**
- Alerta al 70% uso
- Crítico al 85% uso

**RAM:**
- Alerta si swap usage > 1GB
- Crítico si OOM killer activo

**CPU:**
- Alerta si load average > 4.0 (número de CPUs)
- Crítico si load average > 6.0

## Escalamiento

### Cuándo escalar

**Escalar verticalmente** (más recursos al servidor):
- Load average constantemente > 4.0
- RAM usage constantemente > 90%
- Disco < 20% disponible

**Escalar horizontalmente** (múltiples workers):
- Colas de RabbitMQ crecen constantemente
- Throughput insuficiente
- Ver: systemd/README.md sección "Escalamiento"

### Múltiples workers por cola

```bash
# Si necesitas más throughput en transform
sudo systemctl start renagro-worker-etl-transform@1.service
sudo systemctl start renagro-worker-etl-transform@2.service

# Ajustar CPUQuota en cada servicio
CPUQuota=50%  # Para 2 workers en paralelo
```

## Optimizaciones

### PostgreSQL (para 16GB RAM)

```bash
# /etc/postgresql/14/main/postgresql.conf
shared_buffers = 4GB                 # 25% de RAM
effective_cache_size = 12GB          # 75% de RAM
maintenance_work_mem = 1GB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1               # SSD
effective_io_concurrency = 200       # SSD
work_mem = 64MB
max_connections = 100
```

### RabbitMQ

```bash
# /etc/rabbitmq/rabbitmq.conf
vm_memory_high_watermark.relative = 0.6
disk_free_limit.absolute = 10GB
```

### Redis

```bash
# /etc/redis/redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru
```

## Backup

### PostgreSQL

```bash
# Backup diario con cron
0 2 * * * /usr/bin/pg_dump -U postgres renagro_db | gzip > /backups/renagro_$(date +\%Y\%m\%d).sql.gz

# Limpiar backups > 30 días
find /backups -name "renagro_*.sql.gz" -mtime +30 -delete
```

### Aplicación

```bash
# Backup configuración
tar -czf renagro-config-$(date +%Y%m%d).tar.gz \
  /opt/renagro-etl-process/.env \
  /opt/renagro-etl-process/mapping/ \
  /etc/systemd/system/renagro-*.service
```
