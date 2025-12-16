# ⚠️  SOLO PARA DESARROLLO LOCAL
# Para producción, usar servicios systemd en Linux o servicios de Windows
# Ver: systemd/README.md

# Script para iniciar workers en paralelo (DESARROLLO - Windows)
# Uso:
#   .\run_all_workers.ps1 etl        - Solo workers ETL (json_save, etl_transform, db_insert)
#   .\run_all_workers.ps1 envio      - Solo workers Envío MAG (envio_mag, envio_mag_sender)
#   .\run_all_workers.ps1 etl envio  - Todos los workers
#   .\run_all_workers.ps1            - Todos los workers (sin argumentos)

param(
    [string[]]$WorkerGroups
)

# Parsear argumentos
$START_ETL = $false
$START_ENVIO = $false

if ($WorkerGroups.Count -eq 0) {
    # Sin argumentos: iniciar todos
    $START_ETL = $true
    $START_ENVIO = $true
} else {
    foreach ($arg in $WorkerGroups) {
        switch ($arg.ToLower()) {
            "etl" {
                $START_ETL = $true
            }
            "envio" {
                $START_ENVIO = $true
            }
            default {
                Write-Host "❌ Argumento inválido: $arg" -ForegroundColor Red
                Write-Host ""
                Write-Host "Uso:"
                Write-Host "  .\run_all_workers.ps1 etl        - Solo workers ETL"
                Write-Host "  .\run_all_workers.ps1 envio      - Solo workers Envío MAG"
                Write-Host "  .\run_all_workers.ps1 etl envio  - Todos los workers"
                Write-Host "  .\run_all_workers.ps1            - Todos los workers"
                exit 1
            }
        }
    }
}

# Obtener directorio raíz del proyecto
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Set-Location $ProjectRoot

Write-Host "🚀 Iniciando workers del pipeline ETL" -ForegroundColor Cyan
Write-Host "======================================"
Write-Host ""

# Verificar que existe el archivo .env
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  Error: No existe archivo .env" -ForegroundColor Yellow
    Write-Host "📝 Copia .env.example a .env y configura las variables necesarias"
    exit 1
}

# Verificar que existe el virtualenv
if (-not (Test-Path "venv")) {
    Write-Host "⚠️  Error: No existe el virtualenv en venv/" -ForegroundColor Yellow
    Write-Host "📝 Crea el virtualenv con: python -m venv venv"
    Write-Host "   Luego instala dependencias: .\venv\Scripts\Activate.ps1 && pip install -r requirements.txt"
    exit 1
}

# Activar virtualenv
Write-Host "🐍 Activando virtualenv..."
& ".\venv\Scripts\Activate.ps1"

# Arrays para procesos
$Jobs = @()
$WorkerNames = @()
$LogFiles = @()

# Crear directorio de logs si no existe
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

# Iniciar workers ETL
if ($START_ETL) {
    Write-Host ""
    Write-Host "📦 Iniciando Workers ETL..." -ForegroundColor Green
    Write-Host "----------------------------"
    
    Write-Host "📥 Iniciando worker json_save..."
    $job = Start-Process python -ArgumentList "-m", "src.workers", "json_save" `
        -NoNewWindow -PassThru -RedirectStandardOutput "logs\worker_json_save.log" `
        -RedirectStandardError "logs\worker_json_save_error.log"
    $Jobs += $job
    $WorkerNames += "json_save"
    $LogFiles += "logs\worker_json_save.log"
    
    Write-Host "🔄 Iniciando worker etl_transform..."
    $job = Start-Process python -ArgumentList "-m", "src.workers", "etl_transform" `
        -NoNewWindow -PassThru -RedirectStandardOutput "logs\worker_etl_transform.log" `
        -RedirectStandardError "logs\worker_etl_transform_error.log"
    $Jobs += $job
    $WorkerNames += "etl_transform"
    $LogFiles += "logs\worker_etl_transform.log"
    
    Write-Host "💾 Iniciando worker db_insert..."
    $job = Start-Process python -ArgumentList "-m", "src.workers", "db_insert" `
        -NoNewWindow -PassThru -RedirectStandardOutput "logs\worker_db_insert.log" `
        -RedirectStandardError "logs\worker_db_insert_error.log"
    $Jobs += $job
    $WorkerNames += "db_insert"
    $LogFiles += "logs\worker_db_insert.log"
}

# Iniciar workers Envío MAG
if ($START_ENVIO) {
    Write-Host ""
    Write-Host "📤 Iniciando Workers Envío MAG..." -ForegroundColor Green
    Write-Host "---------------------------------"
    
    Write-Host "📤 Iniciando worker envio_mag..."
    $job = Start-Process python -ArgumentList "-m", "src.workers", "envio_mag" `
        -NoNewWindow -PassThru -RedirectStandardOutput "logs\worker_envio_mag.log" `
        -RedirectStandardError "logs\worker_envio_mag_error.log"
    $Jobs += $job
    $WorkerNames += "envio_mag"
    $LogFiles += "logs\worker_envio_mag.log"
    
    Write-Host "🚀 Iniciando worker envio_mag_sender..."
    $job = Start-Process python -ArgumentList "-m", "src.workers", "envio_mag_sender" `
        -NoNewWindow -PassThru -RedirectStandardOutput "logs\worker_envio_mag_sender.log" `
        -RedirectStandardError "logs\worker_envio_mag_sender_error.log"
    $Jobs += $job
    $WorkerNames += "envio_mag_sender"
    $LogFiles += "logs\worker_envio_mag_sender.log"
}

# Mostrar resumen
Write-Host ""
Write-Host "✅ Workers iniciados:" -ForegroundColor Green
Write-Host "--------------------"
for ($i = 0; $i -lt $Jobs.Count; $i++) {
    Write-Host ("   {0,-20} -> PID {1}" -f $WorkerNames[$i], $Jobs[$i].Id)
}

Write-Host ""
Write-Host "📊 Para ver logs en tiempo real:"
foreach ($log in $LogFiles) {
    Write-Host "   Get-Content $log -Wait"
}

Write-Host ""
Write-Host "🛑 Para detener todos los workers:"
Write-Host "   .\scripts-dev\stop_workers.ps1"
Write-Host ""

# Guardar PIDs en archivo
$Jobs | ForEach-Object { $_.Id } | Out-File -FilePath ".worker_pids" -Encoding UTF8

Write-Host "Presiona Ctrl+C para detener todos los workers..." -ForegroundColor Yellow
Write-Host ""

# Esperar a que el usuario presione Ctrl+C
try {
    while ($true) {
        Start-Sleep -Seconds 1
        # Verificar si algún proceso terminó
        foreach ($job in $Jobs) {
            if ($job.HasExited) {
                Write-Host "⚠️  Worker con PID $($job.Id) ha terminado" -ForegroundColor Yellow
            }
        }
    }
} finally {
    # Cleanup al presionar Ctrl+C
    Write-Host ""
    Write-Host "Deteniendo workers..." -ForegroundColor Yellow
    foreach ($job in $Jobs) {
        if (-not $job.HasExited) {
            Stop-Process -Id $job.Id -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Host "✅ Workers detenidos" -ForegroundColor Green
}
