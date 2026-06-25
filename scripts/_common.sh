#!/usr/bin/env bash
# Shared config + helpers, sourced by every SwingAI control script.
# Keep this the single source of truth for ports, URLs, and paths.
set -euo pipefail

# --- paths --- (BASH_SOURCE guard so `source _common.sh` is safe under `set -u`)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
RUN_DIR="$ROOT_DIR/.run"        # pid files
LOG_DIR="$ROOT_DIR/logs"        # process logs
mkdir -p "$RUN_DIR" "$LOG_DIR"

# --- ports (separate from OmniMark) ---
export DB_PORT="${DB_PORT:-5434}"
export REDIS_PORT="${REDIS_PORT:-6380}"
# SwingAI uses the 9000 series (clear of OmniMark's 3000/8000). DB/Redis: 5434/6380.
export BACKEND_PORT="${BACKEND_PORT:-9000}"
export DASHBOARD_PORT="${DASHBOARD_PORT:-9001}"
export MARKETING_PORT="${MARKETING_PORT:-9002}"

# --- db / redis ---
export POSTGRES_USER="${POSTGRES_USER:-swingai}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-swingai}"
export POSTGRES_DB="${POSTGRES_DB:-swingaidb}"
export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:${DB_PORT}/${POSTGRES_DB}}"
export REDIS_URL="${REDIS_URL:-redis://localhost:${REDIS_PORT}/0}"

# python venv
VENV_DIR="$BACKEND_DIR/.venv"
PY="$VENV_DIR/bin/python"

# --- colors ---
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

log()  { echo -e "${CYAN}▸${NC} $*"; }
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}!${NC} $*"; }
err()  { echo -e "${RED}✗${NC} $*" >&2; }

# compose wrapper (uses root docker-compose.yml + env)
dc() { ( cd "$ROOT_DIR" && DB_PORT="$DB_PORT" REDIS_PORT="$REDIS_PORT" \
        POSTGRES_USER="$POSTGRES_USER" POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
        POSTGRES_DB="$POSTGRES_DB" docker compose "$@" ); }

# wait until a TCP port accepts connections
wait_for_port() {
  local port=$1 label=$2 max=${3:-60} waited=0
  printf "  %-22s" "${label}"
  while ! (lsof -i ":${port}" -sTCP:LISTEN -P -n &>/dev/null || nc -z localhost "$port" &>/dev/null); do
    if [ "$waited" -ge "$max" ]; then echo -e " ${RED}timed out${NC}"; return 1; fi
    printf "${CYAN}.${NC}"; sleep 2; waited=$((waited + 2))
  done
  echo -e " ${GREEN}ready${NC}"
}

port_listening() { lsof -i ":$1" -sTCP:LISTEN -P -n &>/dev/null; }

pid_alive() { [ -f "$1" ] && kill -0 "$(cat "$1")" 2>/dev/null; }

ensure_venv() {
  if [ ! -x "$PY" ]; then
    log "Creating Python venv + installing backend deps (first run)…"
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install -q --upgrade pip
    "$VENV_DIR/bin/pip" install -q -r "$BACKEND_DIR/requirements.txt"
    ok "venv ready"
  fi
}

# Ensure the Docker daemon is reachable; auto-start Colima if it's the runtime.
# Idempotent + fast: a no-op when Docker is already up. Returns non-zero if it
# can't get Docker running so callers stop instead of failing cryptically.
ensure_docker() {
  if docker info &>/dev/null; then return 0; fi
  warn "Docker daemon not reachable."
  if command -v colima &>/dev/null; then
    log "Starting Colima (Docker runtime)…"
    colima start || { err "colima start failed"; return 1; }
    printf "  %-22s" "waiting for docker"
    local waited=0
    until docker info &>/dev/null; do
      if [ "$waited" -ge 60 ]; then echo -e " ${RED}timed out${NC}"; err "Docker still not ready"; return 1; fi
      printf "${CYAN}.${NC}"; sleep 2; waited=$((waited + 2))
    done
    echo -e " ${GREEN}ready${NC}"
    ok "Colima + Docker ready"
  else
    err "Docker isn't running and Colima isn't installed. Start Docker manually, then retry."
    return 1
  fi
}
