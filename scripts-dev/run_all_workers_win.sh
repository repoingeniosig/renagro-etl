#!/bin/bash
# ⚠️  SOLO PARA DESARROLLO LOCAL
# Para producción, usar servicios systemd en systemd/
# Ver: systemd/README.md

# Script para iniciar workers en paralelo (DESARROLLO)
# Uso:
#   ./run_all_workers.sh etl        - Solo workers ETL (json_save, etl_transform, db_insert)
#   ./run_all_workers.sh envio      - Solo workers Envío MAG (envio_mag, envio_mag_sender)
#   ./run_all_workers.sh etl envio  - Todos los workers
#   ./run_all_workers.sh            - Todos los workers (sin argumentos)

# Parsear argumentos
START_ETL=false
START_ENVIO=false

if [ $# -eq 0 ]; then
    # Sin argumentos: iniciar todos
    START_ETL=true
    START_ENVIO=true
else
    # Con argumentos: iniciar según lo especificado
    for arg in "$@"; do
        case $arg in
            etl)
                START_ETL=true
                ;;
            envio)
                START_ENVIO=true
                ;;
            *)
                echo "❌ Argumento inválido: $arg"
                echo ""
                echo "Uso:"
                echo "  ./run_all_workers.sh etl        - Solo workers ETL"
                echo "  ./run_all_workers.sh envio      - Solo workers Envío MAG"
                echo "  ./run_all_workers.sh etl envio  - Todos los workers"
                echo "  ./run_all_workers.sh            - Todos los workers"
                exit 1
                ;;
        esac
    done
fi

echo "🚀 Iniciando workers del pipeline ETL"
echo "======================================"
echo ""

# Obtener directorio raíz del proyecto
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_ROOT"

# Verificar que existe el archivo .env
if [ ! -f .env ]; then
    echo "⚠️  Error: No existe archivo .env"
    echo "📝 Copia .env.example a .env y configura las variables necesarias"
    exit 1
fi

# Verificar que existe el virtualenv
if [ ! -d "venv" ]; then
    echo "⚠️  Error: No existe el virtualenv en venv/"
    echo "📝 Crea el virtualenv con: python -m venv venv"
    echo "   Luego instala dependencias: source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activar virtualenv
echo "🐍 Activando virtualenv..."
source venv/bin/activate

# Arrays para PIDs y logs
PIDS=()
WORKER_NAMES=()
LOG_FILES=()

# Iniciar workers ETL
if [ "$START_ETL" = true ]; then
    echo ""
    echo "📦 Iniciando Workers ETL..."
    echo "----------------------------"
    
    echo "📥 Iniciando worker json_save..."
    python -m src.workers json_save > logs/worker_json_save.log 2>&1 &
    PIDS+=($!)
    WORKER_NAMES+=("json_save")
    LOG_FILES+=("logs/worker_json_save.log")
    
    echo "🔄 Iniciando worker etl_transform..."
    python -m src.workers etl_transform > logs/worker_etl_transform.log 2>&1 &
    PIDS+=($!)
    WORKER_NAMES+=("etl_transform")
    LOG_FILES+=("logs/worker_etl_transform.log")
    
    echo "💾 Iniciando worker db_insert..."
    python -m src.workers db_insert > logs/worker_db_insert.log 2>&1 &
    PIDS+=($!)
    WORKER_NAMES+=("db_insert")
    LOG_FILES+=("logs/worker_db_insert.log")
fi

# Iniciar workers Envío MAG
if [ "$START_ENVIO" = true ]; then
    echo ""
    echo "📤 Iniciando Workers Envío MAG..."
    echo "---------------------------------"
    
    echo "📤 Iniciando worker envio_mag..."
    python -m src.workers envio_mag > logs/worker_envio_mag.log 2>&1 &
    PIDS+=($!)
    WORKER_NAMES+=("envio_mag")
    LOG_FILES+=("logs/worker_envio_mag.log")
    
    echo "🚀 Iniciando worker envio_mag_sender..."
    python -m src.workers envio_mag_sender > logs/worker_envio_mag_sender.log 2>&1 &
    PIDS+=($!)
    WORKER_NAMES+=("envio_mag_sender")
    LOG_FILES+=("logs/worker_envio_mag_sender.log")
fi

# Mostrar resumen
echo ""
echo "✅ Workers iniciados:"
echo "--------------------"
for i in "${!PIDS[@]}"; do
    printf "   %-20s -> PID %s\n" "${WORKER_NAMES[$i]}" "${PIDS[$i]}"
done

echo ""
echo "📊 Para ver logs en tiempo real:"
for log in "${LOG_FILES[@]}"; do
    echo "   tail -f $log"
done

echo ""
echo "🛑 Para detener todos los workers:"
echo "   ./scripts-dev/stop_workers.sh"
echo ""

# Guardar PIDs en archivo
rm -f .worker_pids
for pid in "${PIDS[@]}"; do
    echo $pid >> .worker_pids
done

# Esperar a que el usuario presione Ctrl+C
wait
