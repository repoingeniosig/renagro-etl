# Instalación de Servicios Systemd para Producción

## Arquitectura

- **renagro-api.service** - FastAPI con uvicorn (4 workers)
- **renagro-worker-json-save.service** - Worker para guardar JSON
- **renagro-worker-etl-transform.service** - Worker para transformar datos
- **renagro-worker-db-insert.service** - Worker para insertar en BD

## Instalación

### 1. Preparar el entorno

```bash
# Crear usuario del sistema
sudo useradd -r -s /bin/false renagro

# Copiar aplicación
sudo mkdir -p /opt/renagro-etl-process
sudo cp -r . /opt/renagro-etl-process/
sudo chown -R renagro:renagro /opt/renagro-etl-process

# Crear virtualenv
cd /opt/renagro-etl-process
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

```bash
# Copiar .env
sudo cp .env.example /opt/renagro-etl-process/.env
sudo nano /opt/renagro-etl-process/.env

# Asegurar permisos (archivo tiene credenciales)
sudo chmod 600 /opt/renagro-etl-process/.env
sudo chown renagro:renagro /opt/renagro-etl-process/.env
```

### 3. Instalar servicios systemd

```bash
# Copiar archivos de servicio
sudo cp systemd/*.service /etc/systemd/system/

# Recargar systemd
sudo systemctl daemon-reload

# Habilitar servicios (auto-start en boot)
sudo systemctl enable renagro-api.service
sudo systemctl enable renagro-worker-json-save.service
sudo systemctl enable renagro-worker-etl-transform.service
sudo systemctl enable renagro-worker-db-insert.service
```

### 4. Iniciar servicios

```bash
# Iniciar API primero (carga mapeos + recovery)
sudo systemctl start renagro-api.service

# Esperar 10 segundos para que API cargue mapeos
sleep 10

# Iniciar workers
sudo systemctl start renagro-worker-json-save.service
sudo systemctl start renagro-worker-etl-transform.service
sudo systemctl start renagro-worker-db-insert.service
```

## Gestión de Servicios

### Ver estado

```bash
# Estado de todos los servicios
sudo systemctl status renagro-*

# Estado individual
sudo systemctl status renagro-api.service
sudo systemctl status renagro-worker-json-save.service
```

### Logs

**systemd journal centraliza todos los logs:**

```bash
# Logs en tiempo real de API
sudo journalctl -u renagro-api.service -f

# Logs de worker específico
sudo journalctl -u renagro-worker-json-save.service -f

# Logs de todos los workers
sudo journalctl -u 'renagro-worker-*' -f

# Logs con prioridad ERROR
sudo journalctl -u renagro-api.service -p err

# Logs de las últimas 24 horas
sudo journalctl -u renagro-api.service --since "24 hours ago"

# Exportar logs a archivo
sudo journalctl -u renagro-api.service -S today > api-logs.txt
```

### Reiniciar servicios

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

### Detener servicios

```bash
# Detener todo
sudo systemctl stop renagro-*

# Detener solo workers (API sigue corriendo)
sudo systemctl stop renagro-worker-*
```

## Configuración Nginx

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

Activar:

```bash
sudo ln -s /etc/nginx/sites-available/renagro-etl /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Logs de la Aplicación

### Estrategia Dual: systemd journal + archivos

**systemd journal** (RECOMENDADO para producción):
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

### Configuración logrotate

```bash
# /etc/logrotate.d/renagro-etl

/opt/renagro-etl-process/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 renagro renagro
    sharedscripts
    postrotate
        # Señal para que Python reabra logs
        systemctl reload renagro-api.service
        systemctl reload renagro-worker-*.service
    endscript
}
```

## Monitoreo

### Healthcheck endpoint

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

### Alertas con systemd

```bash
# /etc/systemd/system/renagro-alert@.service

[Unit]
Description=Alerta de falla en %i

[Service]
Type=oneshot
ExecStart=/usr/local/bin/renagro-alert.sh %i
```

Script de alerta:

```bash
#!/bin/bash
# /usr/local/bin/renagro-alert.sh

SERVICE=$1
echo "⚠️ ALERTA: Servicio $SERVICE ha fallado" | mail -s "RENAGRO ETL - Falla en $SERVICE" admin@renagro.gob.ec
```

## Escalamiento

### Múltiples workers por cola

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

## Ventajas sobre scripts .sh

✅ **Gestión profesional** - systemd es el estándar  
✅ **Auto-restart** - Si worker muere, systemd lo reinicia  
✅ **Logs centralizados** - journalctl para todo  
✅ **Dependencias** - Workers esperan a que API esté lista  
✅ **Límites de recursos** - CPU, memoria controlados  
✅ **Boot automático** - Se inician al arrancar servidor  
✅ **Monitoreo integrado** - Status, logs, alertas  
✅ **Sin PIDs manuales** - systemd los gestiona  

## Despliegue

```bash
# 1. Copiar código al servidor
rsync -avz --exclude='venv' --exclude='logs' \
    ./ servidor:/opt/renagro-etl-process/

# 2. SSH al servidor
ssh servidor

# 3. Ejecutar setup
cd /opt/renagro-etl-process
sudo bash systemd/install.sh

# 4. Verificar
sudo systemctl status renagro-*
```
