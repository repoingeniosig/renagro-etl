#!/bin/bash

# Script para ejecutar el flujo completo de envío a MAG
# 1. Construye JSONs desde BD (worker envio_mag)
# 2. Envía JSONs a API remota (worker envio_mag_sender)

set -e

echo "========================================"
echo "FLUJO DE ENVÍO A MAG"
echo "========================================"

# Paso 1: Construir JSONs desde BD
echo ""
echo "Paso 1: Construyendo JSONs desde BD..."
echo "----------------------------------------"
python -m src.workers envio_mag

# Verificar si hubo errores
if [ $? -ne 0 ]; then
    echo "❌ Error construyendo JSONs. Abortando."
    exit 1
fi

echo "✅ JSONs construidos exitosamente"

# Paso 2: Enviar JSONs a API remota
echo ""
echo "Paso 2: Enviando JSONs a API remota..."
echo "----------------------------------------"
python -m src.workers envio_mag_sender

if [ $? -ne 0 ]; then
    echo "❌ Error enviando JSONs."
    exit 1
fi

echo ""
echo "========================================"
echo "✅ FLUJO COMPLETO FINALIZADO"
echo "========================================"
