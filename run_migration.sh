#!/bin/bash
# Script para ejecutar la migración de base de datos

echo "🗄️  Ejecutando migración: Agregar campos retry_count y last_error_stage"
echo "========================================================================"
echo ""

# Verificar que existe .env
if [ ! -f .env ]; then
    echo "⚠️  Error: No existe archivo .env"
    echo "📝 Copia .env.example a .env y configura las variables necesarias"
    exit 1
fi

# Verificar que existe el virtualenv (para psycopg2 si es necesario)
if [ ! -d "venv" ]; then
    echo "⚠️  Advertencia: No existe virtualenv, usando psql del sistema"
fi

# Cargar variables de .env
source .env

# Verificar variables requeridas
if [ -z "$DB_HOST" ] || [ -z "$DB_NAME" ] || [ -z "$DB_USER" ]; then
    echo "⚠️  Error: Variables DB_HOST, DB_NAME, DB_USER no están configuradas en .env"
    exit 1
fi

echo "📋 Configuración:"
echo "   Host: $DB_HOST"
echo "   Base de datos: $DB_NAME"
echo "   Usuario: $DB_USER"
echo ""

# Ejecutar migración
echo "⚙️  Ejecutando SQL..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f migrations/001_add_retry_fields.sql

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Migración completada exitosamente"
    echo ""
    echo "📋 Columnas agregadas:"
    echo "   - retry_count (INTEGER, default 0)"
    echo "   - last_error_stage (VARCHAR(50))"
    echo ""
    echo "🔍 Índices creados:"
    echo "   - idx_control_error_recovery"
    echo "   - idx_control_error_stage"
    echo ""
else
    echo ""
    echo "❌ Error ejecutando migración"
    echo "   Verifica las credenciales en .env"
    exit 1
fi
