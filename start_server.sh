#!/bin/bash

# Script para ejecutar el servidor FastAPI
# Asegúrate de tener activado tu entorno virtual antes de ejecutar

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
python -m run_server
