#!/usr/bin/env bash
# Frontend (Turborepo: marketing + dashboard) control. Usage:
#   scripts/frontend.sh [start|stop|status|restart|install|logs]
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

PIDF="$RUN_DIR/frontend.pid"
LOGF="$LOG_DIR/frontend.log"

install_deps() {
  if [ ! -d "$ROOT_DIR/node_modules" ]; then
    log "Installing JS deps (first run)…"
    ( cd "$ROOT_DIR" && npm install )
    ok "node_modules ready"
  fi
}

start() {
  if pid_alive "$PIDF"; then warn "frontend already running (pid $(cat "$PIDF"))"; return 0; fi
  install_deps
  log "Starting marketing (:$MARKETING_PORT) + dashboard (:$DASHBOARD_PORT)…"
  ( cd "$ROOT_DIR" && NEXT_PUBLIC_API_BASE="http://localhost:$BACKEND_PORT" \
      nohup npm run dev >>"$LOGF" 2>&1 & echo $! >"$PIDF" )
  wait_for_port "$DASHBOARD_PORT" "dashboard :$DASHBOARD_PORT" 120 || true
  wait_for_port "$MARKETING_PORT" "marketing :$MARKETING_PORT" 60 || true
  ok "frontend up → http://localhost:$MARKETING_PORT (marketing) · :$DASHBOARD_PORT (dashboard)"
}

stop() {
  if pid_alive "$PIDF"; then
    # kill the npm/turbo process group
    pkill -P "$(cat "$PIDF")" 2>/dev/null || true
    kill "$(cat "$PIDF")" 2>/dev/null || true
  fi
  # also clear any stray next dev servers on our ports
  for p in "$DASHBOARD_PORT" "$MARKETING_PORT"; do
    lsof -ti ":$p" 2>/dev/null | xargs kill 2>/dev/null || true
  done
  rm -f "$PIDF"; ok "frontend stopped"
}

case "${1:-start}" in
  start) start ;;
  stop) stop ;;
  restart) stop; start ;;
  install) install_deps ;;
  status) if pid_alive "$PIDF"; then ok "frontend running (pid $(cat "$PIDF"))"; else warn "frontend not running"; fi ;;
  logs) tail -f "$LOGF" ;;
  *) echo "usage: frontend.sh [start|stop|status|restart|install|logs]"; exit 1 ;;
esac
