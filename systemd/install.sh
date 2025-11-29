#!/bin/bash
# Script de instalación automatizada para producción

set -e  # Exit on error

echo "🚀 Instalando RENAGRO ETL Process en producción"
echo "================================================"
echo ""

# Verificar que se ejecuta como root
if [ "$EUID" -ne 0 ]; then 
   echo "⚠️  Este script debe ejecutarse como root (sudo)"
   exit 1
fi

# Variables
APP_DIR="/opt/renagro-etl-process"
APP_USER="renagro"
VENV_DIR="$APP_DIR/venv"

echo "📁 Configuración:"
echo "   Directorio: $APP_DIR"
echo "   Usuario: $APP_USER"
echo ""

# 1. Crear usuario del sistema
if id "$APP_USER" &>/dev/null; then
    echo "✓ Usuario $APP_USER ya existe"
else
    echo "👤 Creando usuario $APP_USER..."
    useradd -r -s /bin/false $APP_USER
fi

# 2. Crear directorio y copiar archivos
echo "📦 Preparando directorio de aplicación..."
mkdir -p $APP_DIR
mkdir -p $APP_DIR/logs

# Si se ejecuta desde el repo, copiar archivos
if [ -f "requirements.txt" ]; then
    echo "📋 Copiando archivos..."
    cp -r ./* $APP_DIR/
fi

# 3. Crear virtualenv e instalar dependencias
echo "🐍 Configurando Python virtualenv..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv $VENV_DIR
fi

source $VENV_DIR/bin/activate
pip install --upgrade pip
pip install -r $APP_DIR/requirements.txt
deactivate

# 4. Configurar .env
if [ ! -f "$APP_DIR/.env" ]; then
    echo "⚙️  Creando archivo .env..."
    cp $APP_DIR/.env.example $APP_DIR/.env
    echo ""
    echo "⚠️  IMPORTANTE: Edita $APP_DIR/.env con tus credenciales"
    echo "   sudo nano $APP_DIR/.env"
    echo ""
fi

# 5. Ajustar permisos
echo "🔒 Configurando permisos..."
chown -R $APP_USER:$APP_USER $APP_DIR
chmod 600 $APP_DIR/.env
chmod 755 $APP_DIR/logs

# 6. Instalar servicios systemd
echo "⚙️  Instalando servicios systemd..."
cp $APP_DIR/systemd/*.service /etc/systemd/system/

# 7. Recargar systemd
echo "🔄 Recargando systemd..."
systemctl daemon-reload

# 8. Habilitar servicios
echo "✅ Habilitando servicios..."
systemctl enable renagro-api.service
systemctl enable renagro-worker-json-save.service
systemctl enable renagro-worker-etl-transform.service
systemctl enable renagro-worker-db-insert.service

echo ""
echo "✅ Instalación completada"
echo ""
echo "📋 Próximos pasos:"
echo ""
echo "1. Configurar variables de entorno:"
echo "   sudo nano $APP_DIR/.env"
echo ""
echo "2. Ejecutar migración de base de datos:"
echo "   psql -h localhost -U postgres -d renagro_db -f $APP_DIR/migrations/001_add_retry_fields.sql"
echo ""
echo "3. Iniciar servicios:"
echo "   sudo systemctl start renagro-api.service"
echo "   sleep 10  # Esperar a que API cargue mapeos"
echo "   sudo systemctl start renagro-worker-json-save.service"
echo "   sudo systemctl start renagro-worker-etl-transform.service"
echo "   sudo systemctl start renagro-worker-db-insert.service"
echo ""
echo "4. Verificar estado:"
echo "   sudo systemctl status renagro-*"
echo ""
echo "5. Ver logs:"
echo "   sudo journalctl -u renagro-api.service -f"
echo ""
