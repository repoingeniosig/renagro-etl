# Despliegue en Producción - Sistema RENAGRO ETL

Este documento consolida la guía completa de instalación y configuración de todos los servicios del sistema ETL en producción.

## Tabla de Contenidos

1. [Arquitectura del Sistema](#arquitectura-del-sistema)
2. [Diferencias entre Desarrollo y Producción](#diferencias-entre-desarrollo-y-producción)
3. [Instalación en Producción](#instalación-en-producción)
4. [Configuración de Servicios Systemd](#configuración-de-servicios-systemd)
5. [Configuración Nginx](#configuración-nginx)
6. [Gestión de Logs](#gestión-de-logs)
7. [Monitoreo y Troubleshooting](#monitoreo-y-troubleshooting)
8. [Escalamiento](#escalamiento)

---

## Arquitectura del Sistema

### Servicios Principales

**API y Workers ETL:**
- `renagro-api.service` - FastAPI con uvicorn (4 workers)
- `renagro-worker-json-save.service` - Worker para guardar JSON
- `renagro-worker-etl-transform.service` - Worker para transformar datos
- `renagro-worker-db-insert.service` - Worker para insertar en BD

**Workers Envío MAG:**
- `renagro-worker-envio-mag.timer` + `.service` - Construcción de JSONs (timer cada 5 min)
- `renagro-worker-envio-mag-sender.service` - Envío HTTP a API remota (continuo)

### Flujo Completo

```
HTTP POST JSON
    │
    ▼
renagro-api (FastAPI)
    │ Valida
    │ Guarda archivo
    │ Publica a RabbitMQ
    ▼
QUEUE_JSON_SAVE
    │
    ▼
worker-json-save
    │ Guarda en MongoDB
    │ Publica QUEUE_ETL_TRANSFORM
    ▼
worker-etl-transform
    │ Transforma datos
    │ Publica QUEUE_DB_INSERT
    ▼
worker-db-insert
    │ Inserta en PostgreSQL
    │ Estado: PROCESADO
    ▼
[Timer cada 5 min]
    │
    ▼
worker-envio-mag (oneshot)
    │ Consulta registros PROCESADOS
    │ Construye JSONs
    │ Publica QUEUE_ENVIO_MAG_SEND
    ▼
worker-envio-mag-sender (continuo)
    │ Consume cola
    │ HTTP POST a API RENAGRO
    │ Actualiza estado: ENVIADO/ERROR
```

---

## Diferencias entre Desarrollo y Producción

### Desarrollo (ENVIRONMENT=development)

**Características:**
- ✅ Workers con **loop infinito**
- ✅ Revisan BD cada X segundos (configurable en `.env`)
- ✅ Se ejecutan continuamente hasta detenerlos manualmente
- ✅ Ideal para pruebas locales
- ✅ Logs en terminal y archivos

**Variables de entorno:**
```bash
ENVIRONMENT=development
ENVIO_MAG_CHECK_INTERVAL=300        # 5 minutos
ENVIO_MAG_SENDER_CHECK_INTERVAL=120 # 2 minutos (no usado)
```

**Ejecutar:**
```bash
# Terminal 1: API
python -m src.api

# Terminal 2-5: Workers ETL
python -m src.workers json_save
python -m src.workers etl_transform
python -m src.workers db_insert

# Terminal 6-7: Workers Envío MAG
python -m src.workers envio_mag         # Loop cada 5 min
python -m src.workers envio_mag_sender  # Consume cola continuamente

# O todos a la vez:
bash run_all_workers.sh
```

---

### Producción (ENVIRONMENT=production)

**Características:**
- ✅ Gestión profesional con **systemd**
- ✅ Worker `envio_mag`: **Ejecución única** controlada por **systemd timer**
- ✅ Resto de workers: **Servicios continuos** que consumen colas
- ✅ Auto-restart automático en fallos
- ✅ Logs centralizados en **journalctl**
- ✅ Inicio automático en boot del servidor
- ✅ Control de recursos (CPU, memoria)

**Arquitectura Timer:**
```
systemd timer (cada 5 min)
    │
    ▼
renagro-worker-envio-mag.service (oneshot)
    │ Consulta BD
    │ Construye JSONs
    │ Publica a RabbitMQ
    │ Termina
    ▼
RabbitMQ (QUEUE_ENVIO_MAG_SEND)
    │
    ▼
renagro-worker-envio-mag-sender.service (continuo)
    │ Consume cola
    │ Envía HTTP
    │ Actualiza estados
```

---

## Instalación en Producción

### 1. Preparar el Entorno

```bash
# El usuario 'ubuntu' ya existe en Ubuntu Server
# Verificar
id ubuntu

# Crear directorio de aplicación
sudo mkdir -p /opt/renagro-etl-process

# Copiar aplicación desde máquina local (excluir archivos innecesarios)
rsync -avz --exclude='venv' --exclude='logs' --exclude='__pycache__' \
  ./ usuario@servidor:/tmp/renagro-etl/

# En el servidor, mover a /opt
ssh servidor
sudo mv /tmp/renagro-etl/* /opt/renagro-etl-process/
sudo chown -R ubuntu:ubuntu /opt/renagro-etl-process

# Crear virtualenv
cd /opt/renagro-etl-process
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configurar Variables de Entorno

```bash
# Copiar plantilla .env
sudo cp .env.example /opt/renagro-etl-process/.env
sudo nano /opt/renagro-etl-process/.env

# Asegurar permisos (archivo contiene credenciales sensibles)
sudo chmod 600 /opt/renagro-etl-process/.env
sudo chown ubuntu:ubuntu /opt/renagro-etl-process/.env
```

**Importante:** Establecer `ENVIRONMENT=production`:

```bash
# Application Configuration
ENVIRONMENT=production  # ← CRÍTICO para producción

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=renagro_db
DB_USER=renagro_user
DB_PASSWORD=password_seguro

# MongoDB
MONGO_URI=mongodb://localhost:27017
MONGO_DB=renagro_json

# Redis Cache
REDIS_HOST=localhost
REDIS_PORT=6379

# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# API Remota RENAGRO
RENAGRO_ENDPOINT=https://api.renagro.gob.ec/v1/boletas
RENAGRO_TOKEN=Bearer tu_token_real_aqui
PARALLEL_REQUESTS_SEND_MAG=10
MAX_RETRY_ATTEMPTS=3
BATCH_SIZE_SEND_MAG=1000

# NO se usan intervalos en producción (systemd timer los controla)
# ENVIO_MAG_CHECK_INTERVAL=300  ← Se ignora en producción
```

### 3. Ejecutar Migraciones SQL

```bash
psql -h localhost -U postgres -d renagro_db \
  -f /opt/renagro-etl-process/migrations/001_update_estado_envio_enum.sql

psql -h localhost -U postgres -d renagro_db \
  -f /opt/renagro-etl-process/migrations/003_add_uuid_boleta_to_control_tables.sql
```

---

## Configuración de Servicios Systemd

### 1. Instalar Servicios

```bash
# Copiar archivos de servicio
sudo cp systemd/*.service /etc/systemd/system/
sudo cp systemd/*.timer /etc/systemd/system/

# Recargar systemd
sudo systemctl daemon-reload

# Habilitar servicios (auto-start en boot)
sudo systemctl enable renagro-api.service
sudo systemctl enable renagro-worker-json-save.service
sudo systemctl enable renagro-worker-etl-transform.service
sudo systemctl enable renagro-worker-db-insert.service
sudo systemctl enable renagro-worker-envio-mag.timer  # Timer, no service
sudo systemctl enable renagro-worker-envio-mag-sender.service
```

**O usar el script automatizado:**

```bash
cd /opt/renagro-etl-process
sudo bash systemd/install.sh
```

### 2. Iniciar Servicios

```bash
# API (debe iniciar primero para cargar mapeos)
sudo systemctl start renagro-api.service
sleep 10

# Workers ETL
sudo systemctl start renagro-worker-json-save.service
sudo systemctl start renagro-worker-etl-transform.service
sudo systemctl start renagro-worker-db-insert.service

# Workers Envío MAG
sudo systemctl start renagro-worker-envio-mag.timer  # Timer, no service
sudo systemctl start renagro-worker-envio-mag-sender.service
```

### 3. Verificar Estado

```bash
# Estado de todos los servicios
sudo systemctl status renagro-*

# Estado individual
sudo systemctl status renagro-api.service
sudo systemctl status renagro-worker-json-save.service

# Ver timers activos
sudo systemctl list-timers --all | grep renagro

# Debería mostrar:
# NEXT                         LEFT     LAST                         PASSED  UNIT
# Sun 2025-12-08 16:05:00 UTC  4min     Sun 2025-12-08 16:00:00 UTC  30s ago renagro-worker-envio-mag.timer
```

### 4. Gestión de Servicios

**Reiniciar servicios:**
```bash
# Reiniciar API
sudo systemctl restart renagro-api.service

# Reiniciar workers
sudo systemctl restart renagro-worker-json-save.service
sudo systemctl restart renagro-worker-etl-transform.service
sudo systemctl restart renagro-worker-db-insert.service

# Reiniciar todo
sudo systemctl restart renagro-*
```

**Detener servicios:**
```bash
# Detener todo
sudo systemctl stop renagro-*

# Detener solo workers (API sigue corriendo)
sudo systemctl stop renagro-worker-*
```

**Deshabilitar servicios (no inician en boot):**
```bash
sudo systemctl disable renagro-worker-envio-mag.timer
sudo systemctl disable renagro-worker-envio-mag-sender.service
```

---

## Configuración Nginx

### Proxy Reverso para API

```nginx
# /etc/nginx/sites-available/renagro-etl

upstream renagro_api {
    # uvicorn con 4 workers escucha en puerto 8000
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name etl.renagro.gob.ec;  # Cambiar por tu dominio
    
    # Redirigir HTTP a HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name etl.renagro.gob.ec;
    
    # SSL (usar certbot para Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/etl.renagro.gob.ec/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/etl.renagro.gob.ec/privkey.pem;
    
    # Headers de seguridad
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    
    # Proxy a FastAPI
    location / {
        proxy_pass http://renagro_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts para requests largos
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffer
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_busy_buffers_size 8k;
    }
    
    # Health check
    location /health {
        proxy_pass http://renagro_api/health;
        access_log off;
    }
    
    # Limitar tamaño de body (JSONs grandes)
    client_max_body_size 10M;
}
```

**Activar configuración:**

```bash
sudo ln -s /etc/nginx/sites-available/renagro-etl /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

**Instalar SSL con Certbot:**

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d etl.renagro.gob.ec
```

---

## Gestión de Logs

### Estrategia Dual: systemd journal + archivos

**systemd journal (RECOMENDADO para producción):**
- ✅ Centralizado para todos los servicios
- ✅ Rotación automática
- ✅ Búsqueda rápida con journalctl
- ✅ Integración con monitoreo (Prometheus, Grafana)
- ✅ No necesita configuración adicional

**Archivos logs/** (etl_process.log, etl_errors.log):
- ✅ Mantenerlos para debugging detallado
- ✅ Logs de aplicación controlados por logger.py
- ✅ Útiles para análisis histórico
- ⚠️ Configurar logrotate

### Ver Logs con journalctl

```bash
# Logs en tiempo real de API
sudo journalctl -u renagro-api.service -f

# Logs de worker específico
sudo journalctl -u renagro-worker-json-save.service -f

# Logs de todos los workers
sudo journalctl -u 'renagro-worker-*' -f

# Logs del timer
sudo journalctl -u renagro-worker-envio-mag.timer -f

# Logs de ejecuciones del worker
sudo journalctl -u renagro-worker-envio-mag.service -f

# Logs del sender (continuo)
sudo journalctl -u renagro-worker-envio-mag-sender.service -f

# Ver últimas 100 líneas
sudo journalctl -u renagro-worker-envio-mag.service -n 100

# Logs con prioridad ERROR
sudo journalctl -u renagro-api.service -p err

# Logs de las últimas 24 horas
sudo journalctl -u renagro-api.service --since "24 hours ago"

# Exportar logs a archivo
sudo journalctl -u renagro-api.service -S today > api-logs.txt
```

### Configuración logrotate para archivos logs/

```bash
# /etc/logrotate.d/renagro-etl

/opt/renagro-etl-process/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 ubuntu ubuntu
    sharedscripts
    postrotate
        # Señal para que Python reabra logs
        systemctl reload renagro-api.service
        systemctl reload renagro-worker-*.service
    endscript
}
```

---

## Monitoreo y Troubleshooting

### Configuración del Timer

El timer está configurado en: `systemd/renagro-worker-envio-mag.timer`

```ini
[Timer]
OnBootSec=2min         # Ejecuta 2 min después del boot
OnUnitActiveSec=5min   # Ejecuta cada 5 min después de última ejecución
```

**Ajustar intervalo:**

```bash
# Editar timer
sudo nano /etc/systemd/system/renagro-worker-envio-mag.timer

# Cambiar a cada 10 minutos:
OnUnitActiveSec=10min

# Recargar systemd
sudo systemctl daemon-reload

# Reiniciar timer
sudo systemctl restart renagro-worker-envio-mag.timer
```

### Ver Próximas Ejecuciones

```bash
sudo systemctl list-timers renagro-worker-envio-mag.timer

# Output:
# NEXT                         LEFT       LAST                         PASSED
# Sun 2025-12-08 16:10:00 UTC  2min 30s   Sun 2025-12-08 16:05:00 UTC  2min 30s ago
```

### Ver Historial de Ejecuciones

```bash
# Últimas 10 ejecuciones
sudo journalctl -u renagro-worker-envio-mag.service -n 10 --no-pager

# Filtrar por éxito
sudo journalctl -u renagro-worker-envio-mag.service | grep "FINALIZADO"

# Filtrar por errores
sudo journalctl -u renagro-worker-envio-mag.service -p err
```

### Health Check Endpoint

Agregar a `src/api.py`:

```python
@app.get("/health")
async def health_check():
    """Health check para systemd y nginx"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": "ok",  # Verificar conexión
            "redis": "ok",     # Verificar conexión
            "rabbitmq": "ok"   # Verificar conexión
        }
    }
```

### Consultas SQL de Monitoreo

```sql
-- Pendientes de construcción de JSON
SELECT COUNT(*) FROM sc_renagro_mag.control_envios_boletas
WHERE estado_etl = 'PROCESADO' 
  AND envio_datos_procesados = 'PENDIENTE';

-- Estadísticas de envío
SELECT 
  envio_datos_procesados,
  COUNT(*) AS cantidad
FROM sc_renagro_mag.control_envios_boletas
WHERE estado_etl = 'PROCESADO'
GROUP BY envio_datos_procesados;

-- Últimos errores de envío
SELECT _id, error_envio_datos, fecha_recepcion
FROM sc_renagro_mag.control_envios_boletas
WHERE envio_datos_procesados = 'ERROR'
ORDER BY fecha_recepcion DESC
LIMIT 10;
```

### Troubleshooting Común

#### Timer no ejecuta

```bash
# Verificar que timer está activo
sudo systemctl is-active renagro-worker-envio-mag.timer

# Si está inactivo, iniciar
sudo systemctl start renagro-worker-envio-mag.timer

# Ver logs del timer
sudo journalctl -u renagro-worker-envio-mag.timer -f
```

#### Worker falla inmediatamente

```bash
# Ver error específico
sudo journalctl -u renagro-worker-envio-mag.service -n 50

# Verificar .env
sudo cat /opt/renagro-etl-process/.env | grep ENVIRONMENT

# Debe ser:
ENVIRONMENT=production
```

#### Worker ejecuta loop en producción

**Causa:** `ENVIRONMENT` no está establecido a `production`

**Solución:**
```bash
sudo nano /opt/renagro-etl-process/.env
# Cambiar a: ENVIRONMENT=production

sudo systemctl restart renagro-worker-envio-mag.timer
```

#### Ejecutar manualmente para debug

```bash
# Ejecutar worker una vez (como lo haría el timer)
cd /opt/renagro-etl-process
source venv/bin/activate
ENVIRONMENT=production python -m src.workers envio_mag
```

---

## Escalamiento

### Múltiples Workers por Cola

Si necesitas más throughput:

```bash
# Copiar servicio
sudo cp /etc/systemd/system/renagro-worker-json-save.service \
       /etc/systemd/system/renagro-worker-json-save@.service

# Modificar para usar instancias
# [Unit]
# Description=RENAGRO ETL Worker - JSON Save %i

# Iniciar múltiples instancias
sudo systemctl start renagro-worker-json-save@1.service
sudo systemctl start renagro-worker-json-save@2.service
sudo systemctl start renagro-worker-json-save@3.service
```

### Configurar Límites de Recursos

Editar archivos `.service` y agregar:

```ini
[Service]
# Limitar CPU al 50%
CPUQuota=50%

# Limitar memoria a 2GB
MemoryLimit=2G

# Limitar operaciones de I/O
IOWeight=500
```

---

## Ventajas de Systemd sobre Scripts

✅ **Gestión profesional** - systemd es el estándar de Linux  
✅ **Auto-restart** - Si worker muere, systemd lo reinicia  
✅ **Logs centralizados** - journalctl para todo  
✅ **Dependencias** - Workers esperan a que API esté lista  
✅ **Límites de recursos** - CPU, memoria controlados  
✅ **Boot automático** - Se inician al arrancar servidor  
✅ **Monitoreo integrado** - Status, logs, alertas  
✅ **Sin PIDs manuales** - systemd los gestiona  

---

## Comparación Final

| Aspecto | Desarrollo | Producción |
|---------|-----------|------------|
| `ENVIRONMENT` | `development` | `production` |
| Worker envio_mag | Loop infinito (cada 5 min) | Ejecución única (timer) |
| Worker sender | Consume cola (continuo) | Consume cola (continuo) |
| Resto de workers | Consumen colas (continuo) | Consumen colas (continuo) |
| Control | Manual (Ctrl+C) | systemd timer/services |
| Logs | Terminal/archivos | journalctl + archivos |
| Auto-restart | No | Sí (systemd) |
| Inicio en boot | No | Sí |
| Límites recursos | No | Sí (configurable) |
| SSL/HTTPS | No | Sí (nginx + certbot) |

---

## Resumen de Comandos

### Instalación Rápida

```bash
# 1. Copiar código al servidor
rsync -avz --exclude='venv' --exclude='logs' ./ servidor:/opt/renagro-etl-process/

# 2. SSH al servidor
ssh servidor

# 3. Ejecutar setup
cd /opt/renagro-etl-process
sudo bash systemd/install.sh

# 4. Configurar .env
sudo nano /opt/renagro-etl-process/.env
# Establecer: ENVIRONMENT=production

# 5. Verificar
sudo systemctl status renagro-*
sudo systemctl list-timers --all | grep renagro
```

### Comandos Diarios

```bash
# Ver estado general
sudo systemctl status renagro-*

# Ver logs en vivo
sudo journalctl -u renagro-api.service -f

# Reiniciar todo
sudo systemctl restart renagro-*

# Ver próximas ejecuciones timer
sudo systemctl list-timers renagro-worker-envio-mag.timer
```

---

## Referencias

- **Systemd Timers:** https://www.freedesktop.org/software/systemd/man/systemd.timer.html
- **Journalctl:** https://www.freedesktop.org/software/systemd/man/journalctl.html
- **Nginx:** https://nginx.org/en/docs/
- **Certbot:** https://certbot.eff.org/
- **Documentación completa:** [ENVIO_MAG.md](../ENVIO_MAG.md)

