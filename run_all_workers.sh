#!/bin/bash
# ⚠️  SOLO PARA DESARROLLO LOCAL
# Para producción, usar servicios systemd en systemd/
# Ver: systemd/README.md

# Script para iniciar todos los workers en paralelo (DESARROLLO)

echo "🚀 Iniciando todos los workers del pipeline ETL"
echo "==============================================="
echo ""

# Verificar que existe el archivo .env
if [ ! -f .env ]; then
    echo "⚠️  Error: No existe archivo .env"
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
echo "🐍 Activando virtualenv..."
source venv/bin/activate

# Iniciar workers en background
echo "📥 Iniciando worker json_save..."
python3 -m src.workers json_save > logs/worker_json_save.log 2>&1 &
JSON_SAVE_PID=$!

echo "🔄 Iniciando worker etl_transform..."
python3 -m src.workers etl_transform > logs/worker_etl_transform.log 2>&1 &
ETL_TRANSFORM_PID=$!

echo "💾 Iniciando worker db_insert..."
python3 -m src.workers db_insert > logs/worker_db_insert.log 2>&1 &
DB_INSERT_PID=$!

echo ""
echo "✅ Todos los workers iniciados:"
echo "   json_save      -> PID $JSON_SAVE_PID"
echo "   etl_transform  -> PID $ETL_TRANSFORM_PID"
echo "   db_insert      -> PID $DB_INSERT_PID"
echo ""
echo "📊 Para ver logs en tiempo real:"
echo "   tail -f logs/worker_json_save.log"
echo "   tail -f logs/worker_etl_transform.log"
echo "   tail -f logs/worker_db_insert.log"
echo ""
echo "🛑 Para detener todos los workers:"
echo "   kill $JSON_SAVE_PID $ETL_TRANSFORM_PID $DB_INSERT_PID"
echo ""

# Guardar PIDs en archivo
echo $JSON_SAVE_PID > .worker_pids
echo $ETL_TRANSFORM_PID >> .worker_pids
echo $DB_INSERT_PID >> .worker_pids

# Esperar a que el usuario presione Ctrl+C
wait
