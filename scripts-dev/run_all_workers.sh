#!/bin/bash
# ⚠️  SOLO PARA DESARROLLO LOCAL
# Para producción, usar servicios systemd en systemd/
# Ver: systemd/README.md

# Script para iniciar workers en paralelo (DESARROLLO)
# Uso:
#   ./run_all_workers.sh etl        - Solo workers ETL (json_save, etl_transform, db_insert)
#   ./run_all_workers.sh envio      - Solo workers Envío MAG actual (envio_mag + envio_mag_sender)
#   ./run_all_workers.sh envio geometria boleta   - Solo geometría boleta
#   ./run_all_workers.sh envio geometria terreno  - Solo geometría terreno
#   ./run_all_workers.sh envio adicional capacitacion  - Solo adicional capacitacion
#   ./run_all_workers.sh envio adicional comunicacion  - Solo adicional comunicacion
#   ./run_all_workers.sh envio adicional produccion    - Solo adicional produccion
#   ./run_all_workers.sh etl envio  - Todos los workers
#   ./run_all_workers.sh            - Todos los workers (sin argumentos)

# Parsear argumentos
START_ETL=false
START_ENVIO_NORMAL=false
START_ENVIO_GEOM_BOLETA=false
START_ENVIO_GEOM_TERRENO=false
START_ENVIO_GEOM_SENDER=false
START_ENVIO_ADDT_CAPACITACION=false
START_ENVIO_ADDT_COMUNICACION=false
START_ENVIO_ADDT_PRODUCCION=false
START_ENVIO_ADDT_SENDER=false

if [ $# -eq 0 ]; then
    # Sin argumentos: iniciar todos
    START_ETL=true
    START_ENVIO_NORMAL=true
    START_ENVIO_GEOM_BOLETA=true
    START_ENVIO_GEOM_TERRENO=true
    START_ENVIO_GEOM_SENDER=true
    START_ENVIO_ADDT_CAPACITACION=true
    START_ENVIO_ADDT_COMUNICACION=true
    START_ENVIO_ADDT_PRODUCCION=true
    START_ENVIO_ADDT_SENDER=true
else
    while [ $# -gt 0 ]; do
        case "$1" in
            etl)
                START_ETL=true
                shift
                ;;
            envio)
                START_ENVIO_NORMAL=true
                shift
                ;;
            geometria)
                if [ $# -lt 2 ]; then
                    echo "❌ Falta especificar target de geometría: boleta | terreno"
                    exit 1
                fi

                case "$2" in
                    boleta)
                        START_ENVIO_NORMAL=false
                        START_ENVIO_GEOM_BOLETA=true
                        START_ENVIO_GEOM_SENDER=true
                        ;;
                    terreno)
                        START_ENVIO_NORMAL=false
                        START_ENVIO_GEOM_TERRENO=true
                        START_ENVIO_GEOM_SENDER=true
                        ;;
                    *)
                        echo "❌ Target de geometría inválido: $2"
                        echo "Usa: boleta | terreno"
                        exit 1
                        ;;
                esac

                shift 2
                ;;
            adicional)
                if [ $# -lt 2 ]; then
                    echo "❌ Falta especificar target adicional: capacitacion | comunicacion | produccion"
                    exit 1
                fi

                case "$2" in
                    capacitacion)
                        START_ENVIO_NORMAL=false
                        START_ENVIO_ADDT_CAPACITACION=true
                        START_ENVIO_ADDT_SENDER=true
                        ;;
                    comunicacion)
                        START_ENVIO_NORMAL=false
                        START_ENVIO_ADDT_COMUNICACION=true
                        START_ENVIO_ADDT_SENDER=true
                        ;;
                    produccion)
                        START_ENVIO_NORMAL=false
                        START_ENVIO_ADDT_PRODUCCION=true
                        START_ENVIO_ADDT_SENDER=true
                        ;;
                    *)
                        echo "❌ Target adicional inválido: $2"
                        echo "Usa: capacitacion | comunicacion | produccion"
                        exit 1
                        ;;
                esac

                shift 2
                ;;
            *)
                echo "❌ Argumento inválido: $1"
                echo ""
                echo "Uso:"
                echo "  ./run_all_workers.sh etl                                - Solo workers ETL"
                echo "  ./run_all_workers.sh envio                              - Solo workers Envío MAG actual"
                echo "  ./run_all_workers.sh envio geometria boleta             - Solo geometría boleta"
                echo "  ./run_all_workers.sh envio geometria terreno            - Solo geometría terreno"
                echo "  ./run_all_workers.sh envio adicional capacitacion       - Solo adicional capacitacion"
                echo "  ./run_all_workers.sh envio adicional comunicacion       - Solo adicional comunicacion"
                echo "  ./run_all_workers.sh envio adicional produccion         - Solo adicional produccion"
                echo "  ./run_all_workers.sh etl envio                          - ETL + envío actual"
                echo "  ./run_all_workers.sh                                    - Todos los workers"
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
    echo "📝 Crea el virtualenv con: python3 -m venv venv"
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
    python3 -m src.workers json_save > logs/worker_json_save.log 2>&1 &
    PIDS+=($!)
    WORKER_NAMES+=("json_save")
    LOG_FILES+=("logs/worker_json_save.log")
    
    echo "🔄 Iniciando worker etl_transform..."
    python3 -m src.workers etl_transform > logs/worker_etl_transform.log 2>&1 &
    PIDS+=($!)
    WORKER_NAMES+=("etl_transform")
    LOG_FILES+=("logs/worker_etl_transform.log")
    
    echo "💾 Iniciando worker db_insert..."
    python3 -m src.workers db_insert > logs/worker_db_insert.log 2>&1 &
    PIDS+=($!)
    WORKER_NAMES+=("db_insert")
    LOG_FILES+=("logs/worker_db_insert.log")
fi

# Iniciar workers Envío MAG
if [ "$START_ENVIO_NORMAL" = true ]; then
    echo ""
    echo "📤 Iniciando Workers Envío MAG (actual)..."
    echo "------------------------------------------"
    
    echo "📤 Iniciando worker envio_mag..."
    ENVIO_MAG_LOGGER_NAME=worker_envio_mag python3 -m src.workers envio_mag > logs/worker_envio_mag.log 2>&1 &
    PIDS+=($!)
    WORKER_NAMES+=("envio_mag")
    LOG_FILES+=("logs/worker_envio_mag.log")
    
    echo "🚀 Iniciando worker envio_mag_sender..."
    ENVIO_MAG_LOGGER_NAME=worker_envio_mag_sender python3 -m src.workers envio_mag_sender > logs/worker_envio_mag_sender.log 2>&1 &
    PIDS+=($!)
    WORKER_NAMES+=("envio_mag_sender")
    LOG_FILES+=("logs/worker_envio_mag_sender.log")

fi

if [ "$START_ENVIO_GEOM_BOLETA" = true ] || [ "$START_ENVIO_GEOM_TERRENO" = true ] || [ "$START_ENVIO_GEOM_SENDER" = true ]; then
    echo ""
    echo "🗺️ Iniciando Workers Envío MAG Geometría..."
    echo "-------------------------------------------"

    if [ "$START_ENVIO_GEOM_BOLETA" = true ]; then
        echo "🗺️ Iniciando worker envio_mag_geometria_boleta..."
        ENVIO_MAG_LOGGER_NAME=worker_envio_mag_geometria python3 -m src.workers envio_mag_geometria_boleta >> logs/worker_envio_mag_geometria.log 2>&1 &
        PIDS+=($!)
        WORKER_NAMES+=("envio_mag_geometria_boleta")
        LOG_FILES+=("logs/worker_envio_mag_geometria.log")
    fi

    if [ "$START_ENVIO_GEOM_TERRENO" = true ]; then
        echo "🗺️ Iniciando worker envio_mag_geometria_terreno..."
        ENVIO_MAG_LOGGER_NAME=worker_envio_mag_geometria python3 -m src.workers envio_mag_geometria_terreno >> logs/worker_envio_mag_geometria.log 2>&1 &
        PIDS+=($!)
        WORKER_NAMES+=("envio_mag_geometria_terreno")
        LOG_FILES+=("logs/worker_envio_mag_geometria.log")
    fi

    if [ "$START_ENVIO_GEOM_SENDER" = true ] || [ "$START_ENVIO_GEOM_BOLETA" = true ] || [ "$START_ENVIO_GEOM_TERRENO" = true ]; then
        echo "🛰️ Iniciando worker envio_mag_geometria_sender..."
        ENVIO_MAG_LOGGER_NAME=worker_envio_mag_geometria python3 -m src.workers envio_mag_geometria_sender > logs/worker_envio_mag_geometria_sender.log 2>&1 &
        PIDS+=($!)
        WORKER_NAMES+=("envio_mag_geometria_sender")
        LOG_FILES+=("logs/worker_envio_mag_geometria_sender.log")
    fi

fi

if [ "$START_ENVIO_ADDT_CAPACITACION" = true ] || [ "$START_ENVIO_ADDT_COMUNICACION" = true ] || [ "$START_ENVIO_ADDT_PRODUCCION" = true ] || [ "$START_ENVIO_ADDT_SENDER" = true ]; then
    echo ""
    echo "📋 Iniciando Workers Envío MAG Adicional..."
    echo "--------------------------------------------"

    if [ "$START_ENVIO_ADDT_CAPACITACION" = true ]; then
        echo "📋 Iniciando worker envio_mag_adicional_capacitacion..."
        ENVIO_MAG_LOGGER_NAME=worker_envio_mag_adicional python3 -m src.workers envio_mag_adicional_capacitacion >> logs/worker_envio_mag_adicional.log 2>&1 &
        PIDS+=($!)
        WORKER_NAMES+=("envio_mag_adicional_capacitacion")
        LOG_FILES+=("logs/worker_envio_mag_adicional.log")
    fi

    if [ "$START_ENVIO_ADDT_COMUNICACION" = true ]; then
        echo "📋 Iniciando worker envio_mag_adicional_comunicacion..."
        ENVIO_MAG_LOGGER_NAME=worker_envio_mag_adicional python3 -m src.workers envio_mag_adicional_comunicacion >> logs/worker_envio_mag_adicional.log 2>&1 &
        PIDS+=($!)
        WORKER_NAMES+=("envio_mag_adicional_comunicacion")
        LOG_FILES+=("logs/worker_envio_mag_adicional.log")
    fi

    if [ "$START_ENVIO_ADDT_PRODUCCION" = true ]; then
        echo "📋 Iniciando worker envio_mag_adicional_produccion..."
        ENVIO_MAG_LOGGER_NAME=worker_envio_mag_adicional python3 -m src.workers envio_mag_adicional_produccion >> logs/worker_envio_mag_adicional.log 2>&1 &
        PIDS+=($!)
        WORKER_NAMES+=("envio_mag_adicional_produccion")
        LOG_FILES+=("logs/worker_envio_mag_adicional.log")
    fi

    if [ "$START_ENVIO_ADDT_SENDER" = true ] || [ "$START_ENVIO_ADDT_CAPACITACION" = true ] || [ "$START_ENVIO_ADDT_COMUNICACION" = true ] || [ "$START_ENVIO_ADDT_PRODUCCION" = true ]; then
        echo "🛰️ Iniciando worker envio_mag_adicional_sender..."
        ENVIO_MAG_LOGGER_NAME=worker_envio_mag_adicional python3 -m src.workers envio_mag_adicional_sender > logs/worker_envio_mag_adicional_sender.log 2>&1 &
        PIDS+=($!)
        WORKER_NAMES+=("envio_mag_adicional_sender")
        LOG_FILES+=("logs/worker_envio_mag_adicional_sender.log")
    fi

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
