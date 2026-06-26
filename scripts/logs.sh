#!/usr/bin/env bash
# View logs. Usage: scripts/logs.sh [all|backend|frontend|db|redis] [N]
#   no N  → live follow (stays attached, streams new lines; Ctrl-C to stop)
#   N     → snapshot: print the last N lines and exit (prompt returns immediately)
# Examples:  logs.sh all          (follow both)
#            logs.sh backend 100  (last 100 backend lines, then exit)
#            logs.sh all 50       (last 50 lines of each, then exit)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

N="${2:-}"                      # if a line count is given, snapshot instead of follow
is_num() { [[ "$1" =~ ^[0-9]+$ ]]; }

# Follow files live, or print the last N lines and exit when a count was passed.
view() {  # $@ = files
  if is_num "$N"; then tail -n "$N" "$@"; else tail -f "$@"; fi
}

# Same idea for docker compose logs (db/redis).
view_dc() {  # $1 = service
  if is_num "$N"; then dc logs --tail "$N" "$1"; else dc logs -f "$1"; fi
}

case "${1:-all}" in
  backend)  touch "$LOG_DIR/backend.log";  view "$LOG_DIR/backend.log" ;;
  frontend) touch "$LOG_DIR/frontend.log"; view "$LOG_DIR/frontend.log" ;;
  db)       ensure_docker || exit 1; view_dc db ;;
  redis)    ensure_docker || exit 1; view_dc redis ;;
  all)
    touch "$LOG_DIR/backend.log" "$LOG_DIR/frontend.log"
    if is_num "$N"; then log "Last $N lines of backend + frontend:"
    else log "Tailing backend + frontend (Ctrl-C to stop). Snapshot instead: logs.sh all 50"; fi
    view "$LOG_DIR/backend.log" "$LOG_DIR/frontend.log" ;;
  *) echo "usage: logs.sh [all|backend|frontend|db|redis] [N]   (N = last N lines, no live follow)"; exit 1 ;;
esac
