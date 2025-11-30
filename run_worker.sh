#!/bin/bash
#!/bin/bash
# ⚠️  SOLO PARA DESARROLLO LOCAL
# Para producción, usar servicios systemd en systemd/
# Ver: systemd/README.md

# Script para ejecutar un worker individual en modo desarrollo

WORKER_TYPE=$1

if [ -z "$WORKER_TYPE" ]; then
    echo "Uso: ./run_worker.sh <worker_type>"
    echo ""
    echo "Workers disponibles:"
    echo "  json_save      - Guarda JSON en base de datos"
    echo "  etl_transform  - Procesa transformaciones"
    echo "  db_insert      - Ejecuta transacciones SQL"
    echo ""
    echo "Ejemplo:"
    echo "  ./run_worker.sh json_save"
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
python3 -m src.workers $WORKER_TYPE
