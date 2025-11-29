#!/bin/bash
# Script para detener todos los workers

if [ ! -f .worker_pids ]; then
    echo "⚠️  No se encontró archivo .worker_pids"
    echo "Los workers no parecen estar ejecutándose"
    exit 1
fi

echo "🛑 Deteniendo workers..."

while read pid; do
    if ps -p $pid > /dev/null 2>&1; then
        echo "   Deteniendo PID $pid..."
        kill $pid
    fi
done < .worker_pids

rm .worker_pids

echo "✅ Workers detenidos"
