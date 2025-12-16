#!/bin/bash

# Script para ejecutar el servidor FastAPI
# Asegúrate de tener activado tu entorno virtual antes de ejecutar

# Obtener directorio raíz del proyecto
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_ROOT"

echo "🚀 Iniciando servidor RENAGRO ETL API..."
echo ""

# Verificar que existe el archivo .env
if [ ! -f .env ]; then
    echo "⚠️  Advertencia: No existe archivo .env"
    echo "📝 Copia .env.example a .env y configura las variables necesarias"
    echo ""
    echo "cp .env.example .env"
    echo ""
    exit 1
fi

# Ejecutar el servidor
uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
