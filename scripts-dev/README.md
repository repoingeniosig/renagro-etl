# Scripts de Desarrollo

Scripts para ejecutar el sistema ETL en modo desarrollo (local).

⚠️ **SOLO PARA DESARROLLO LOCAL**  
Para producción, usar servicios systemd en Linux. Ver: `systemd/README.md`

## 📁 Contenido

### Scripts Linux/macOS (.sh)
- `run_all_workers.sh` - Iniciar todos los workers o grupos específicos
- `stop_workers.sh` - Detener todos los workers
- `start_server.sh` - Iniciar servidor FastAPI
- `run_worker.sh` - Iniciar un worker individual

### Scripts Windows (.ps1)
- `run_all_workers.ps1` - Iniciar todos los workers o grupos específicos
- `stop_workers.ps1` - Detener todos los workers
- `start_server.ps1` - Iniciar servidor FastAPI
- `run_worker.ps1` - Iniciar un worker individual

## 🐧 Uso en Linux/macOS

### Iniciar servidor API

```bash
cd /ruta/al/proyecto
./scripts-dev/start_server.sh
```

### Iniciar todos los workers

```bash
# Todos los workers (ETL + Envío MAG)
./scripts-dev/run_all_workers.sh

# Solo workers ETL (json_save, etl_transform, db_insert)
./scripts-dev/run_all_workers.sh etl

# Solo workers de Envío MAG (envio_mag, envio_mag_sender)
./scripts-dev/run_all_workers.sh envio

# Combinar grupos
./scripts-dev/run_all_workers.sh etl envio
```

### Iniciar worker individual

```bash
./scripts-dev/run_worker.sh json_save
./scripts-dev/run_worker.sh etl_transform
./scripts-dev/run_worker.sh db_insert
./scripts-dev/run_worker.sh envio_mag
./scripts-dev/run_worker.sh envio_mag_sender
```

### Detener workers

```bash
./scripts-dev/stop_workers.sh
```

## 🪟 Uso en Windows (PowerShell)

### Configuración inicial

1. Abrir PowerShell como Administrador
2. Habilitar ejecución de scripts (solo la primera vez):
   ```powershell
   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

### Iniciar servidor API

```powershell
cd C:\ruta\al\proyecto
.\scripts-dev\start_server.ps1
```

### Iniciar todos los workers

```powershell
# Todos los workers (ETL + Envío MAG)
.\scripts-dev\run_all_workers.ps1

# Solo workers ETL
.\scripts-dev\run_all_workers.ps1 etl

# Solo workers de Envío MAG
.\scripts-dev\run_all_workers.ps1 envio

# Combinar grupos
.\scripts-dev\run_all_workers.ps1 etl envio
```

### Iniciar worker individual

```powershell
.\scripts-dev\run_worker.ps1 json_save
.\scripts-dev\run_worker.ps1 etl_transform
.\scripts-dev\run_worker.ps1 db_insert
.\scripts-dev\run_worker.ps1 envio_mag
.\scripts-dev\run_worker.ps1 envio_mag_sender
```

### Detener workers

```powershell
.\scripts-dev\stop_workers.ps1
```

## 📊 Ver Logs

### Linux/macOS

```bash
# Ver log de un worker específico
tail -f logs/worker_json_save.log
tail -f logs/worker_etl_transform.log

# Ver todos los logs
tail -f logs/worker_*.log
```

### Windows

```powershell
# Ver log de un worker específico
Get-Content logs\worker_json_save.log -Wait
Get-Content logs\worker_etl_transform.log -Wait

# Ver logs en tiempo real (múltiples ventanas)
# Abrir una ventana PowerShell por cada worker
Get-Content logs\worker_json_save.log -Wait
```

## 🔧 Requisitos Previos

### Ambos sistemas (Linux/macOS/Windows)

1. **Python 3.8+** instalado
2. **Virtualenv creado**:
   ```bash
   # Linux/macOS
   python3 -m venv venv
   
   # Windows
   python -m venv venv
   ```

3. **Dependencias instaladas**:
   ```bash
   # Linux/macOS
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Windows
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

4. **Archivo `.env` configurado**:
   ```bash
   # Linux/macOS
   cp .env.example .env
   
   # Windows
   Copy-Item .env.example .env
   ```

5. **PostgreSQL** corriendo
6. **RabbitMQ** corriendo
7. **Redis** corriendo (opcional, para cache)

## 📋 Workers Disponibles

| Worker | Descripción |
|--------|-------------|
| `json_save` | Guarda JSONs de Kobo en base de datos |
| `etl_transform` | Transforma JSON a SQL según mappings YAML |
| `db_insert` | Ejecuta transacciones INSERT en PostgreSQL |
| `envio_mag` | Construye JSONs desde BD para envío a MAG |
| `envio_mag_sender` | Envía JSONs a API remota MAG |

## 🚀 Despliegue en Producción

**NO usar estos scripts en producción.**

Para producción en Linux, usar servicios systemd:
- Ver: `systemd/README.md`
- Instalación: `sudo bash systemd/install.sh`

Para producción en Windows, considerar:
- **NSSM** (Non-Sucking Service Manager) para crear servicios de Windows
- **Task Scheduler** con tareas programadas
- **Docker** con docker-compose (multiplataforma)

## ⚠️ Notas Importantes

### Linux/macOS
- Los scripts `.sh` requieren permisos de ejecución: `chmod +x scripts-dev/*.sh`
- Usa `Ctrl+C` para detener workers iniciados con `run_all_workers.sh`

### Windows
- Los scripts `.ps1` pueden requerir cambiar la política de ejecución
- Usa `Ctrl+C` para detener workers iniciados con `run_all_workers.ps1`
- Los logs incluyen archivos `*_error.log` adicionales para errores

### Ambos Sistemas
- Los PIDs de workers se guardan en `.worker_pids` (se limpia automáticamente)
- Los logs se guardan en el directorio `logs/` (se crean automáticamente)
- El servidor API corre en `http://0.0.0.0:8000` por defecto

## 🐛 Solución de Problemas

### Error: "No existe archivo .env"
```bash
# Copiar archivo de ejemplo y configurar
cp .env.example .env
# Editar .env con tus credenciales
```

### Error: "No existe el virtualenv"
```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Error: "Cannot run script" (Windows)
```powershell
# Ejecutar como Administrador
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Workers no se detienen
```bash
# Linux/macOS
pkill -f "python.*src.workers"

# Windows
Get-Process python | Where-Object {$_.CommandLine -like "*src.workers*"} | Stop-Process -Force
```

## 📚 Documentación Adicional

- **README principal**: `../README.md`
- **Documentación completa**: `../documentation/`
- **Configuración systemd**: `../systemd/README.md`
- **Ejemplos de API**: `../documentation/API_EXAMPLES.md`
- **Manejo de errores**: `../documentation/ERROR_HANDLING.md`
