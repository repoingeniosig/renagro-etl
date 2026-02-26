#!/bin/bash
#!/bin/bash
# ⚠️  SOLO PARA DESARROLLO LOCAL
# Para producción, usar servicios systemd en systemd/
# Ver: systemd/README.md

# Script para ejecutar un worker individual en modo desarrollo

# Obtener directorio raíz del proyecto
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_ROOT"

WORKER_TYPE=$1

if [ -z "$WORKER_TYPE" ]; then
    echo "Uso: ./scripts-dev/run_worker.sh <worker_type>"
    echo ""
    echo "Workers disponibles:"
    echo "  json_save      - Guarda JSON en base de datos"
    echo "  etl_transform  - Procesa transformaciones"
    echo "  db_insert      - Ejecuta transacciones SQL"
    echo "  envio_mag        - Construye JSONs para envío MAG"
    echo "  envio_mag_sender - Envía JSONs a API remota"
    echo "  envio_mag_geometria        - Construye JSONs de geometría (boleta + terreno)"
    echo "  envio_mag_geometria_boleta - Construye JSONs de geometría de boleta"
    echo "  envio_mag_geometria_terreno - Construye JSONs de geometría de terreno"
    echo "  envio_mag_geometria_sender  - Envía JSONs de geometría a API remota"
    echo "  envio_mag_adicional         - Construye JSONs adicionales (capacitacion + comunicacion + produccion)"
    echo "  envio_mag_adicional_capacitacion  - Construye JSONs de capacitacion"
    echo "  envio_mag_adicional_comunicacion  - Construye JSONs de comunicacion"
    echo "  envio_mag_adicional_produccion    - Construye JSONs de produccion"
    echo "  envio_mag_adicional_sender  - Envía JSONs adicionales a API remota"
    echo ""
    echo "Ejemplo:"
    echo "  ./scripts-dev/run_worker.sh json_save"
    exit 1
fi

# Verificar que existe el archivo .env
if [ ! -f .env ]; then
    echo "⚠️  Advertencia: No existe archivo .env"
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
source venv/bin/activate

echo "🚀 Iniciando worker: $WORKER_TYPE"
echo ""

# Ejecutar worker
if [[ "$WORKER_TYPE" == envio_mag_adicional* ]]; then
    ENVIO_MAG_LOGGER_NAME="worker_envio_mag_adicional" python3 -m src.workers $WORKER_TYPE
elif [[ "$WORKER_TYPE" == envio_mag_geometria* ]]; then
    ENVIO_MAG_LOGGER_NAME="worker_envio_mag_geometria" python3 -m src.workers $WORKER_TYPE
elif [[ "$WORKER_TYPE" == envio_mag* ]]; then
    ENVIO_MAG_LOGGER_NAME="worker_envio_mag" python3 -m src.workers $WORKER_TYPE
else
    python3 -m src.workers $WORKER_TYPE
fi
