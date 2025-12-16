# ⚠️  SOLO PARA DESARROLLO LOCAL
# Para producción, usar servicios de Windows o systemd en Linux
# Ver: systemd/README.md

# Script para detener todos los workers (DESARROLLO - Windows)

# Obtener directorio raíz del proyecto
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Set-Location $ProjectRoot

if (-not (Test-Path ".worker_pids")) {
    Write-Host '⚠️  No se encontró archivo .worker_pids' -ForegroundColor Yellow
    Write-Host 'Los workers no parecen estar ejecutándose'
    exit 1
}

Write-Host '🛑 Deteniendo workers...' -ForegroundColor Cyan

$pids = Get-Content ".worker_pids"

foreach ($pid in $pids) {
    $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
    if ($process) {
        Write-Host "   Deteniendo PID $pid..."
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    }
}

Remove-Item ".worker_pids" -ErrorAction SilentlyContinue

Write-Host '✅ Workers detenidos' -ForegroundColor Green
