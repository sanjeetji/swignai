#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
#  SwingAI — Master Control
#  Usage: scripts/swingai.sh [start|stop|restart|status|fresh|create-admin|logs|test]
#    start         db + backend + frontend
#    stop          stop everything (data preserved)
#    fresh         WIPE the DB + start + create the first super admin (asks y/n first)
#    create-admin  create / promote a super admin (interactive, or pass --email/--name/--password)
#    status        show what's running
#    logs          tail backend + frontend
#    test          run backend test suite
# ════════════════════════════════════════════════════════════════
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

banner() {
  echo -e "${CYAN}${BOLD}"
  echo "  ╔══════════════════════════════════════════╗"
  echo "  ║            SwingAI  Platform             ║"
  echo "  ╚══════════════════════════════════════════╝"
  echo -e "${NC}"
}

start_all() {
  banner
  ensure_docker || exit 1
  bash "$SCRIPT_DIR/db.sh" start
  bash "$SCRIPT_DIR/backend.sh" start
  bash "$SCRIPT_DIR/frontend.sh" start
  echo
  ok "SwingAI is up:"
  echo -e "   Marketing   → ${BOLD}http://localhost:$MARKETING_PORT${NC}"
  echo -e "   Dashboard   → ${BOLD}http://localhost:$DASHBOARD_PORT${NC}"
  echo -e "   API docs    → ${BOLD}http://localhost:$BACKEND_PORT/docs${NC}"
  echo -e "   Logs        → ${BOLD}scripts/logs.sh all${NC}"
  if ! ( cd "$BACKEND_DIR" && DATABASE_URL="$DATABASE_URL" "$PY" -m app.admin_setup --check >/dev/null 2>&1 ); then
    warn "No super admin yet — run:  ${BOLD}scripts/swingai.sh create-admin${NC}"
  fi
}

# Create / promote the first super admin (interactive, or pass --email/--name/--password)
create_admin() {
  ensure_docker || exit 1
  bash "$SCRIPT_DIR/db.sh" start >/dev/null 2>&1 || true
  ( cd "$BACKEND_DIR" && DATABASE_URL="$DATABASE_URL" "$PY" -m app.admin_setup "$@" )
}

stop_all() {
  banner
  bash "$SCRIPT_DIR/frontend.sh" stop || true
  bash "$SCRIPT_DIR/backend.sh" stop || true
  bash "$SCRIPT_DIR/db.sh" stop || true
  ok "all stopped"
}

status_all() {
  banner
  echo -e "${BOLD}Containers${NC}"; bash "$SCRIPT_DIR/db.sh" status || true
  echo -e "\n${BOLD}Processes${NC}"
  bash "$SCRIPT_DIR/backend.sh" status
  bash "$SCRIPT_DIR/frontend.sh" status
  echo -e "\n${BOLD}Ports${NC}"
  for pl in "DB:$DB_PORT" "Redis:$REDIS_PORT" "API:$BACKEND_PORT" "Dashboard:$DASHBOARD_PORT" "Marketing:$MARKETING_PORT"; do
    name="${pl%%:*}"; port="${pl##*:}"
    if port_listening "$port"; then echo -e "  ${GREEN}●${NC} $name ($port)"; else echo -e "  ${RED}○${NC} $name ($port)"; fi
  done
}

case "${1:-help}" in
  start)   start_all ;;
  stop)    stop_all ;;
  restart) stop_all; start_all ;;
  status)  status_all ;;
  fresh)
    banner
    err "DESTRUCTIVE: this WIPES the database — all users, trades, plans, settings — and recreates it."
    printf "  Type 'y' to continue, anything else to abort: "
    read -r ans
    [ "$ans" = "y" ] || { echo "  aborted."; exit 0; }
    ensure_docker || exit 1
    dc down -v >/dev/null 2>&1 || true
    ok "database wiped"
    start_all
    echo; log "Database is fresh — now create your first super admin:"
    create_admin ;;
  create-admin) create_admin "${@:2}" ;;
  logs)    bash "$SCRIPT_DIR/logs.sh" all ;;
  test)    bash "$SCRIPT_DIR/backend.sh" test ;;
  *) sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//' ;;
esac
