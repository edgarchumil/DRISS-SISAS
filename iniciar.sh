#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PY="$ROOT_DIR/.venv/bin/python"
VENV_PIP="$ROOT_DIR/.venv/bin/pip"

cd "$ROOT_DIR"

if [ ! -d ".venv" ]; then
  echo "[init] Creando entorno virtual..."
  python3 -m venv .venv
fi

if [ ! -x "$VENV_PY" ] || [ ! -x "$VENV_PIP" ]; then
  echo "[error] No se encontró Python dentro de .venv"
  exit 1
fi

echo "[init] Instalando dependencias backend..."
"$VENV_PIP" install -r backend/requirements.txt >/dev/null

echo "[init] Aplicando migraciones..."
"$VENV_PY" backend/manage.py migrate

cd "$ROOT_DIR/frontend"

if [ ! -d "node_modules" ]; then
  echo "[init] Instalando dependencias frontend..."
  npm install
fi

PROXY_FILE="proxy.conf.json"
if [ -f "proxy.local.conf.json" ]; then
  PROXY_FILE="proxy.local.conf.json"
elif [ -f "proxy.conf.local.json" ]; then
  PROXY_FILE="proxy.conf.local.json"
fi

cd "$ROOT_DIR"

echo "[run] Iniciando backend en http://localhost:8001"
"$VENV_PY" backend/manage.py runserver 0.0.0.0:8001 &
BACKEND_PID=$!

echo "[run] Iniciando frontend en http://localhost:4200 (proxy: $PROXY_FILE)"
(
  cd "$ROOT_DIR/frontend"
  npm run start -- --proxy-config "$PROXY_FILE"
) &
FRONTEND_PID=$!

cleanup() {
  echo ""
  echo "[stop] Cerrando servicios..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}

trap cleanup INT TERM EXIT

wait "$BACKEND_PID" "$FRONTEND_PID"
