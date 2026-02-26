#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
VENV_DIR="$BACKEND_DIR/.venv"
VENV_PY="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-4200}"
ENABLE_TUNNEL="${ENABLE_TUNNEL:-1}"
TUNNEL_NAME="${TUNNEL_NAME:-driss-sisas}"
DB_NAME="${DB_NAME:-sisas_db}"
DB_USER="${DB_USER:-sisas_user}"
DB_PASS="${DB_PASS:-sisas_pass}"
DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-5432}"
USE_DOCKER_DB="${USE_DOCKER_DB:-1}"

cd "$ROOT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[error] python3 no está instalado."
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "[error] npm/node no está instalado."
  exit 1
fi

# Asegura pg_dump en macOS (Homebrew), útil para respaldo PostgreSQL local.
if [ -x "/opt/homebrew/opt/libpq/bin/pg_dump" ]; then
  export PATH="/opt/homebrew/opt/libpq/bin:$PATH"
elif [ -x "/usr/local/opt/libpq/bin/pg_dump" ]; then
  export PATH="/usr/local/opt/libpq/bin:$PATH"
fi

if [ "$USE_DOCKER_DB" = "1" ] && ! command -v docker >/dev/null 2>&1; then
  echo "[warn] docker no está instalado y USE_DOCKER_DB=1."
  echo "[warn] Se usará PostgreSQL externo/local (equivalente a USE_DOCKER_DB=0)."
  USE_DOCKER_DB="0"
fi

if [ "$ENABLE_TUNNEL" = "1" ] && ! command -v cloudflared >/dev/null 2>&1; then
  echo "[warn] cloudflared no está instalado; se iniciará solo frontend/backend."
  echo "[warn] Para acceso externo instala cloudflared o ejecuta ENABLE_TUNNEL=0 ./iniciar.sh"
fi

if [ ! -d "$VENV_DIR" ]; then
  echo "[init] Creando entorno virtual..."
  python3 -m venv "$VENV_DIR"
fi

if [ ! -x "$VENV_PY" ] || [ ! -x "$VENV_PIP" ]; then
  echo "[error] No se encontró Python dentro de $VENV_DIR"
  exit 1
fi

export DB_NAME DB_USER DB_PASS DB_HOST DB_PORT

if command -v pg_dump >/dev/null 2>&1; then
  echo "[init] pg_dump detectado: $(command -v pg_dump)"
else
  echo "[warn] pg_dump no detectado en PATH. El respaldo PostgreSQL puede fallar."
fi

if [ "$USE_DOCKER_DB" = "1" ]; then
  COMPOSE_CMD=""
  if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
  elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
  else
    echo "[error] No se encontró docker compose ni docker-compose."
    exit 1
  fi

  echo "[init] Iniciando PostgreSQL con Docker Compose..."
  $COMPOSE_CMD up -d db

  echo "[init] Esperando PostgreSQL en $DB_HOST:$DB_PORT..."
  ATTEMPTS=0
  until $COMPOSE_CMD exec -T db pg_isready -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; do
    ATTEMPTS=$((ATTEMPTS + 1))
    if [ "$ATTEMPTS" -ge 60 ]; then
      echo "[error] PostgreSQL no estuvo listo a tiempo."
      exit 1
    fi
    sleep 1
  done
fi

echo "[init] Instalando dependencias backend..."
"$VENV_PIP" install -r "$BACKEND_DIR/requirements.txt"

echo "[init] Aplicando migraciones..."
"$VENV_PY" "$BACKEND_DIR/manage.py" migrate

cd "$FRONTEND_DIR"

if [ ! -d "node_modules" ]; then
  echo "[init] Instalando dependencias frontend..."
  npm install
fi

# Preferencia local para trabajar sin Docker
PROXY_FILE="proxy.conf.local.json"
if [ ! -f "$PROXY_FILE" ] && [ -f "proxy.local.conf.json" ]; then
  PROXY_FILE="proxy.local.conf.json"
elif [ ! -f "$PROXY_FILE" ] && [ -f "proxy.conf.json" ]; then
  PROXY_FILE="proxy.conf.json"
fi

if [ ! -f "$PROXY_FILE" ]; then
  echo "[error] No se encontró archivo de proxy en $FRONTEND_DIR"
  exit 1
fi

if [ "$PROXY_FILE" = "proxy.local.conf.json" ] && grep -q "8001" "$PROXY_FILE"; then
  echo "[warn] $PROXY_FILE apunta a 8001. Se recomienda 8000 para local."
fi

if [ "$PROXY_FILE" = "proxy.conf.local.json" ] && ! grep -q "8000" "$PROXY_FILE"; then
  echo "[warn] $PROXY_FILE no apunta a 8000. Revisa target de /api."
fi

LAN_IP="$(ipconfig getifaddr en0 2>/dev/null || true)"
if [ -z "$LAN_IP" ]; then
  LAN_IP="$(ipconfig getifaddr en1 2>/dev/null || true)"
fi

cd "$ROOT_DIR"

echo "[run] Iniciando backend en http://localhost:$BACKEND_PORT"
"$VENV_PY" "$BACKEND_DIR/manage.py" runserver 0.0.0.0:"$BACKEND_PORT" &
BACKEND_PID=$!

echo "[run] Iniciando frontend en http://localhost:$FRONTEND_PORT (proxy: $PROXY_FILE)"
(
  cd "$FRONTEND_DIR"
  if [ "$PROXY_FILE" = "proxy.conf.local.json" ]; then
    npm run start:local -- --port "$FRONTEND_PORT"
  else
    npm run start -- --port "$FRONTEND_PORT" --proxy-config "$PROXY_FILE"
  fi
) &
FRONTEND_PID=$!

TUNNEL_PID=""
if [ "$ENABLE_TUNNEL" = "1" ] && command -v cloudflared >/dev/null 2>&1; then
  echo "[run] Iniciando túnel Cloudflare: $TUNNEL_NAME"
  cloudflared tunnel run "$TUNNEL_NAME" &
  TUNNEL_PID=$!
fi

echo "[ok] Servicios levantados:"
echo "     Frontend local: http://localhost:$FRONTEND_PORT"
echo "     Backend local:  http://localhost:$BACKEND_PORT"
if [ -n "$LAN_IP" ]; then
  echo "     Acceso LAN:     http://$LAN_IP:$FRONTEND_PORT"
fi
if [ -n "$TUNNEL_PID" ]; then
  echo "     Acceso externo: https://$TUNNEL_NAME (según hostnames del túnel)"
fi

cleanup() {
  echo ""
  echo "[stop] Cerrando servicios..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  if [ -n "$TUNNEL_PID" ]; then
    kill "$TUNNEL_PID" 2>/dev/null || true
  fi
}

trap cleanup INT TERM EXIT

if [ -n "$TUNNEL_PID" ]; then
  wait "$BACKEND_PID" "$FRONTEND_PID" "$TUNNEL_PID"
else
  wait "$BACKEND_PID" "$FRONTEND_PID"
fi
