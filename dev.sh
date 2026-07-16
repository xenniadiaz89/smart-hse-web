#!/bin/bash
# Entorno LOCAL de Smart HSE. Nada de lo que hagas aquí toca Render ni Neon.
#
#   ./dev.sh            → levanta en http://localhost:5001 con recarga automática
#   ./dev.sh --reset    → borra la BD local y la recrea limpia
#   PORT=5002 ./dev.sh  → otro puerto
#
# Atajo de entrada: http://localhost:5001/prueba (login demo, sin clave).
# Puerto 5001 y no 5000: en macOS el 5000 lo ocupa AirPlay Receiver (devuelve 403).
set -e
cd "$(dirname "$0")"
PORT="${PORT:-5001}"
export PORT

# Blindaje: si DATABASE_URL está en el shell, la app escribiría en el Postgres de
# PRODUCCIÓN. En local siempre SQLite (smarthse.db, ya está en .gitignore).
unset DATABASE_URL

PY=venv/bin/python
[ -x "$PY" ] || { echo "✘ No existe venv/. Crea el entorno:  python3 -m venv venv && venv/bin/pip install -r requirements.txt"; exit 1; }

if [ "$1" = "--reset" ]; then
    rm -f smarthse.db
    echo "· BD local borrada; se recreará limpia al arrancar."
fi

echo "──────────────────────────────────────────────────────"
echo " Smart HSE · LOCAL   ·   http://localhost:$PORT"
echo " Entrar directo:         http://localhost:$PORT/prueba"
echo " Base de datos:          smarthse.db (SQLite, local)"
echo " Producción (Neon):      INTACTA — este proceso no la toca"
echo "──────────────────────────────────────────────────────"

exec "$PY" app.py
