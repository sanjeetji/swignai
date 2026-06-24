#!/usr/bin/env bash
# Backend (FastAPI) control. Usage:
#   scripts/backend.sh [start|stop|status|restart|seed|test|logs]
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

PIDF="$RUN_DIR/backend.pid"
LOGF="$LOG_DIR/backend.log"

start() {
  if pid_alive "$PIDF"; then warn "backend already running (pid $(cat "$PIDF"))"; return 0; fi
  ensure_venv
  log "Starting FastAPI on :$BACKEND_PORT (DB=$DATABASE_URL)…"
  ( cd "$BACKEND_DIR" && DATABASE_URL="$DATABASE_URL" REDIS_URL="$REDIS_URL" \
      nohup "$VENV_DIR/bin/uvicorn" app.main:app --host 0.0.0.0 --port "$BACKEND_PORT" \
      >>"$LOGF" 2>&1 & echo $! >"$PIDF" )
  wait_for_port "$BACKEND_PORT" "backend :$BACKEND_PORT" 40
  ok "backend up → http://localhost:$BACKEND_PORT/docs"
}

stop() {
  if pid_alive "$PIDF"; then kill "$(cat "$PIDF")" 2>/dev/null || true; fi
  rm -f "$PIDF"; ok "backend stopped"
}

case "${1:-start}" in
  start) start ;;
  stop) stop ;;
  restart) stop; start ;;
  status)
    if pid_alive "$PIDF"; then ok "backend running (pid $(cat "$PIDF"))"; else warn "backend not running"; fi ;;
  seed)
    ensure_venv
    ( cd "$BACKEND_DIR" && DATABASE_URL="$DATABASE_URL" "$PY" -c "import asyncio; from app.core.db import init_db; from app.seed import seed_if_empty; asyncio.run(init_db()); asyncio.run(seed_if_empty()); print('seeded')" ) ;;
  test)
    ensure_venv
    ( cd "$BACKEND_DIR" && "$VENV_DIR/bin/python" -m pytest -q ) ;;
  logs) tail -f "$LOGF" ;;
  *) echo "usage: backend.sh [start|stop|status|restart|seed|test|logs]"; exit 1 ;;
esac
