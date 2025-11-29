#!/bin/bash
# Script para ejecutar workers de RabbitMQ

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

echo "🚀 Iniciando worker: $WORKER_TYPE"
echo ""

# Ejecutar worker
python -m src.workers $WORKER_TYPE
