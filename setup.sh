#!/bin/bash

# Script de setup rápido para RENAGRO ETL Process
# Ejecutar: bash setup.sh

set -e

echo "=========================================="
echo "RENAGRO ETL Process - Setup Rápido"
echo "=========================================="
echo ""

# Verificar Python
echo "1. Verificando Python 3..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 no está instalado"
    exit 1
fi
echo "✅ Python $(python3 --version) encontrado"
echo ""

# Crear ambiente virtual
echo "2. Creando ambiente virtual..."
if [ -d "venv" ]; then
    echo "⚠️  El directorio venv ya existe. Eliminando..."
    rm -rf venv
fi
python3 -m venv venv
echo "✅ Ambiente virtual creado"
echo ""

# Activar ambiente virtual
echo "3. Activando ambiente virtual..."
source venv/bin/activate
echo "✅ Ambiente virtual activado"
echo ""

# Actualizar pip
echo "4. Actualizando pip..."
pip install --upgrade pip --quiet
echo "✅ pip actualizado"
echo ""

# Instalar dependencias
echo "5. Instalando dependencias..."
pip install -r requirements.txt --quiet
echo "✅ Dependencias instaladas"
echo ""

# Crear archivo .env si no existe
echo "6. Configurando variables de entorno..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ Archivo .env creado desde .env.example"
    echo "⚠️  IMPORTANTE: Edita .env con tus configuraciones de base de datos"
else
    echo "ℹ️  El archivo .env ya existe, no se modificó"
fi
echo ""

# Crear directorio para datos de prueba
echo "7. Creando directorios adicionales..."
mkdir -p data
mkdir -p logs
mkdir -p temp
echo "✅ Directorios creados: data/, logs/, temp/"
echo ""

echo "=========================================="
echo "✅ Setup completado exitosamente"
echo "=========================================="
echo ""
echo "Próximos pasos:"
echo ""
echo "1. Editar el archivo .env con tus configuraciones:"
echo "   nano .env"
echo ""
echo "2. Crear la tabla de control en PostgreSQL:"
echo "   psql -U postgres -d renagro_db -f scripts/create_control_table.sql"
echo ""
echo "3. Procesar un archivo JSON de prueba:"
echo "   python -m src.process_json data/tu_archivo.json"
echo ""
echo "Para activar el ambiente virtual en el futuro:"
echo "   source venv/bin/activate"
echo ""
