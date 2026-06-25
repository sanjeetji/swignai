#!/usr/bin/env bash
# Tail logs. Usage: scripts/logs.sh [all|backend|frontend|db|redis]
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

case "${1:-all}" in
  backend)  tail -f "$LOG_DIR/backend.log" ;;
  frontend) tail -f "$LOG_DIR/frontend.log" ;;
  db)       ensure_docker || exit 1; dc logs -f db ;;
  redis)    ensure_docker || exit 1; dc logs -f redis ;;
  all)
    log "Tailing backend + frontend (Ctrl-C to stop). For db/redis: logs.sh db|redis"
    touch "$LOG_DIR/backend.log" "$LOG_DIR/frontend.log"
    tail -f "$LOG_DIR/backend.log" "$LOG_DIR/frontend.log" ;;
  *) echo "usage: logs.sh [all|backend|frontend|db|redis]"; exit 1 ;;
esac
