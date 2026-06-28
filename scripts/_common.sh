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

# Free a port held by a STALE process before we (re)start a service — prevents a cryptic
# "address already in use" bind failure when a previous run was killed but left a zombie on
# the port. Safe: callers invoke this on `start` only AFTER confirming our own pidfile says
# we're NOT running, so it never kills a legitimately-running instance.
ensure_port_free() {  # $1=port  $2=label
  local pids; pids=$(lsof -ti ":$1" -sTCP:LISTEN 2>/dev/null) || true
  if [ -n "$pids" ]; then
    warn "port $1 (${2:-service}) held by a stale process — clearing it"
    echo "$pids" | xargs kill -9 2>/dev/null || true
    sleep 1
  fi
}

# HTTP check — 0 if the URL answers (2xx/3xx) within the timeout. Used for real health probes.
http_ok() { curl -sf -o /dev/null --max-time "${2:-4}" "$1" 2>/dev/null; }

# Print the last N lines of a log under a labelled header — used to SURFACE a crash reason
# right in the terminal when a service fails to come up (so you don't have to hunt the log).
tail_log() {  # $1=file  $2=lines(default 30)
  local f="$1" n="${2:-30}"
  [ -f "$f" ] || { warn "no log file at $f yet"; return 0; }
  echo -e "${YELLOW}┄┄ last $n lines · $(basename "$f") ┄┄${NC}" >&2
  tail -n "$n" "$f" >&2
  echo -e "${YELLOW}┄┄ (full log: $f) ┄┄${NC}" >&2
}

# Best-effort scan of a log's tail for error-ish lines (empty output = looks clean).
recent_errors() {  # $1=file  $2=lines-to-scan(default 250)
  local f="$1" scan="${2:-250}"
  [ -f "$f" ] || return 0
  tail -n "$scan" "$f" 2>/dev/null \
    | grep -iE "traceback|exception|error|✗|fatal|address already in use|cannot find module" \
    | grep -viE "0 errors|error_|errorMessage|GET /|POST /" | tail -n 4
}

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
    if ! colima start; then
      # Common failure: "attach disk in use by instance colima" — a previous session left an
      # orphaned colima daemon / limactl process holding the VM disk lock. Reap it and retry once.
      warn "colima start failed — clearing a stale VM lock and retrying once…"
      colima stop --force &>/dev/null || true
      pkill -f 'colima daemon' 2>/dev/null || true
      pkill -f 'limactl' 2>/dev/null || true
      sleep 2
      colima start || { err "colima start failed again. Try: colima stop -f && colima start (last resort: colima delete && colima start)"; return 1; }
    fi
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
