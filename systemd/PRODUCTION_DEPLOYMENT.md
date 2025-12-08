# Despliegue en Producción - Workers Envío MAG

## Diferencias entre Desarrollo y Producción

### Desarrollo (ENVIRONMENT=development)
- ✅ Workers con **loop infinito**
- ✅ Revisan BD cada X segundos (configurable en `.env`)
- ✅ Se ejecutan continuamente hasta detenerlos manualmente
- ✅ Ideal para pruebas locales

**Variables de entorno:**
```bash
ENVIRONMENT=development
ENVIO_MAG_CHECK_INTERVAL=300        # 5 minutos
ENVIO_MAG_SENDER_CHECK_INTERVAL=120 # 2 minutos (no usado, consume cola)
```

**Ejecutar:**
```bash
# Terminal 1: Construcción de JSONs (loop cada 5 min)
python -m src.workers envio_mag

# Terminal 2: Envío a API (consume cola continuamente)
python -m src.workers envio_mag_sender
```

---

### Producción (ENVIRONMENT=production)

- ✅ Worker `envio_mag`: **Ejecución única** controlada por **systemd timer**
- ✅ Worker `envio_mag_sender`: **Servicio continuo** que consume cola
- ✅ Gestión profesional con systemd
- ✅ Auto-restart en fallos
- ✅ Logs centralizados en journalctl

**Arquitectura:**
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

### 1. Ejecutar Script de Instalación

```bash
# Copiar código al servidor
rsync -avz ./ servidor:/opt/renagro-etl-process/

# Conectar al servidor
ssh servidor

# Ejecutar instalación
cd /opt/renagro-etl-process
sudo bash systemd/install.sh
```

### 2. Configurar Variables de Entorno

```bash
sudo nano /opt/renagro-etl-process/.env
```

**Importante:** Establecer `ENVIRONMENT=production`:

```bash
# Application Configuration
ENVIRONMENT=production  # ← CRÍTICO para producción

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

### 4. Iniciar Servicios

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

### 5. Verificar Estado

```bash
# Estado de servicios
sudo systemctl status renagro-*

# Ver timers activos
sudo systemctl list-timers --all | grep renagro

# Debería mostrar:
# NEXT                         LEFT     LAST                         PASSED  UNIT
# Sun 2025-12-08 16:05:00 UTC  4min     Sun 2025-12-08 16:00:00 UTC  30s ago renagro-worker-envio-mag.timer
```

### 6. Ver Logs

```bash
# Logs del timer
sudo journalctl -u renagro-worker-envio-mag.timer -f

# Logs de ejecuciones del worker
sudo journalctl -u renagro-worker-envio-mag.service -f

# Logs del sender (continuo)
sudo journalctl -u renagro-worker-envio-mag-sender.service -f

# Ver últimas 100 líneas
sudo journalctl -u renagro-worker-envio-mag.service -n 100
```

---

## Configuración del Timer

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

---

## Monitoreo

### Ver próximas ejecuciones

```bash
sudo systemctl list-timers renagro-worker-envio-mag.timer

# Output:
# NEXT                         LEFT       LAST                         PASSED
# Sun 2025-12-08 16:10:00 UTC  2min 30s   Sun 2025-12-08 16:05:00 UTC  2min 30s ago
```

### Ver historial de ejecuciones

```bash
# Últimas 10 ejecuciones
sudo journalctl -u renagro-worker-envio-mag.service -n 10 --no-pager

# Filtrar por éxito
sudo journalctl -u renagro-worker-envio-mag.service | grep "FINALIZADO"

# Filtrar por errores
sudo journalctl -u renagro-worker-envio-mag.service -p err
```

### Consultas SQL de monitoreo

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

---

## Troubleshooting

### Timer no ejecuta

```bash
# Verificar que timer está activo
sudo systemctl is-active renagro-worker-envio-mag.timer

# Si está inactivo, iniciar
sudo systemctl start renagro-worker-envio-mag.timer

# Ver logs del timer
sudo journalctl -u renagro-worker-envio-mag.timer -f
```

### Worker falla inmediatamente

```bash
# Ver error específico
sudo journalctl -u renagro-worker-envio-mag.service -n 50

# Verificar .env
sudo cat /opt/renagro-etl-process/.env | grep ENVIRONMENT

# Debe ser:
ENVIRONMENT=production
```

### Worker ejecuta loop en producción

**Causa:** `ENVIRONMENT` no está establecido a `production`

**Solución:**
```bash
sudo nano /opt/renagro-etl-process/.env
# Cambiar a: ENVIRONMENT=production

sudo systemctl restart renagro-worker-envio-mag.timer
```

### Ejecutar manualmente para debug

```bash
# Ejecutar worker una vez (como lo haría el timer)
cd /opt/renagro-etl-process
source venv/bin/activate
ENVIRONMENT=production python -m src.workers envio_mag
```

---

## Desactivar en Producción

```bash
# Detener timer y servicios
sudo systemctl stop renagro-worker-envio-mag.timer
sudo systemctl stop renagro-worker-envio-mag-sender.service

# Deshabilitar (no inician en boot)
sudo systemctl disable renagro-worker-envio-mag.timer
sudo systemctl disable renagro-worker-envio-mag-sender.service
```

---

## Comparación Final

| Aspecto | Desarrollo | Producción |
|---------|-----------|------------|
| `ENVIRONMENT` | `development` | `production` |
| Worker envio_mag | Loop infinito (cada 5 min) | Ejecución única (timer) |
| Worker sender | Consume cola (continuo) | Consume cola (continuo) |
| Control | Manual (Ctrl+C) | systemd timer |
| Logs | Terminal/archivos | journalctl |
| Auto-restart | No | Sí (systemd) |
| Inicio en boot | No | Sí |

---

## Referencias

- **Systemd Timers:** https://www.freedesktop.org/software/systemd/man/systemd.timer.html
- **Journalctl:** https://www.freedesktop.org/software/systemd/man/journalctl.html
- **Documentación completa:** [ENVIO_MAG.md](../ENVIO_MAG.md)
