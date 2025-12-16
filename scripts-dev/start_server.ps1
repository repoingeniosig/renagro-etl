# Script para ejecutar el servidor FastAPI (DESARROLLO - Windows)
# Asegúrate de tener activado tu entorno virtual antes de ejecutar

# Obtener directorio raíz del proyecto
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Set-Location $ProjectRoot

Write-Host "🚀 Iniciando servidor RENAGRO ETL API..." -ForegroundColor Cyan
Write-Host ""

# Verificar que existe el archivo .env
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  Advertencia: No existe archivo .env" -ForegroundColor Yellow
    Write-Host "📝 Copia .env.example a .env y configura las variables necesarias"
    Write-Host ""
    Write-Host "Copy-Item .env.example .env"
    Write-Host ""
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

# Ejecutar el servidor
Write-Host ""
Write-Host "▶️  Ejecutando servidor en http://0.0.0.0:8000" -ForegroundColor Green
Write-Host ""
uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
