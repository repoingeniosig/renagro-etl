# ⚠️  SOLO PARA DESARROLLO LOCAL
# Para producción, usar servicios de Windows o systemd en Linux
# Ver: systemd/README.md

# Script para ejecutar un worker individual en modo desarrollo (Windows)

param(
    [string]$WorkerType
)

# Obtener directorio raíz del proyecto
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Set-Location $ProjectRoot

if (-not $WorkerType) {
    Write-Host 'Uso: .\scripts-dev\run_worker.ps1 <worker_type>'
    Write-Host ''
    Write-Host 'Workers disponibles:'
    Write-Host '  json_save        - Guarda JSON en base de datos'
    Write-Host '  etl_transform    - Procesa transformaciones'
    Write-Host '  db_insert        - Ejecuta transacciones SQL'
    Write-Host '  envio_mag        - Construye JSONs para envío MAG'
    Write-Host '  envio_mag_sender - Envía JSONs a API remota'
    Write-Host '  envio_mag_geometria        - Construye JSONs de geometría (boleta + terreno)'
    Write-Host '  envio_mag_geometria_boleta - Construye JSONs de geometría de boleta'
    Write-Host '  envio_mag_geometria_terreno - Construye JSONs de geometría de terreno'
    Write-Host '  envio_mag_geometria_sender - Envía JSONs de geometría a API remota'
    Write-Host '  envio_mag_adicional        - Construye JSONs adicionales (capacitacion + comunicacion + produccion)'
    Write-Host '  envio_mag_adicional_capacitacion  - Construye JSONs de capacitacion'
    Write-Host '  envio_mag_adicional_comunicacion  - Construye JSONs de comunicacion'
    Write-Host '  envio_mag_adicional_produccion    - Construye JSONs de produccion'
    Write-Host '  envio_mag_adicional_sender  - Envía JSONs adicionales a API remota'
    Write-Host ''
    Write-Host 'Ejemplo:'
    Write-Host '  .\scripts-dev\run_worker.ps1 json_save'
    exit 1
}

# Verificar que existe el archivo .env
if (-not (Test-Path ".env")) {
    Write-Host '⚠️  Advertencia: No existe archivo .env' -ForegroundColor Yellow
    Write-Host '📝 Copia .env.example a .env y configura las variables necesarias'
    exit 1
}

# Verificar que existe el virtualenv
if (-not (Test-Path "venv")) {
    Write-Host '⚠️  Error: No existe el virtualenv en venv/' -ForegroundColor Yellow
    Write-Host '📝 Crea el virtualenv con: python -m venv venv'
    Write-Host '   Luego instala dependencias: .\venv\Scripts\Activate.ps1 && pip install -r requirements.txt'
    exit 1
}

# Activar virtualenv
Write-Host '🐍 Activando virtualenv...'
& ".\venv\Scripts\Activate.ps1"

Write-Host ''
Write-Host "🚀 Iniciando worker: $WorkerType" -ForegroundColor Cyan
Write-Host ''

# Ejecutar worker
if ($WorkerType -like 'envio_mag_adicional*') {
    $env:ENVIO_MAG_LOGGER_NAME = 'worker_envio_mag_adicional'
} elseif ($WorkerType -like 'envio_mag_geometria*') {
    $env:ENVIO_MAG_LOGGER_NAME = 'worker_envio_mag_geometria'
} elseif ($WorkerType -like 'envio_mag*') {
    $env:ENVIO_MAG_LOGGER_NAME = 'worker_envio_mag'
}

python -m src.workers $WorkerType
