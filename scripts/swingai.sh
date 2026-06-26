#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
#  SwingAI — Master Control
#  Usage: scripts/swingai.sh <command>
#    start [--logs] db + backend + frontend (services run in the background).
#                   --logs (or -w) keeps the terminal attached and streams logs after start,
#                   so you SEE crashes live (Ctrl-C stops watching; services keep running).
#    dev            alias for `start --logs` (start, then watch logs in the foreground).
#    stop           stop everything (data preserved).
#    restart        stop then start.
#    status         health check: ports + API /health + recent errors from the logs.
#    health         same as status (quick health probe; safe to run anytime).
#    fresh [--logs] WIPE the DB + start + create the first super admin (asks y/n first).
#    create-admin   create / promote a super admin (interactive, or --email/--name/--password).
#    pipeline       (re)run the daily screener now to refresh market data / picks.
#    logs [N]       tail backend + frontend (N = last N lines then exit; no N = live follow).
#    test           run the backend test suite.
# ════════════════════════════════════════════════════════════════
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

banner() {
  echo -e "${CYAN}${BOLD}"
  echo "  ╔══════════════════════════════════════════╗"
  echo "  ║            SwingAI  Platform             ║"
  echo "  ╚══════════════════════════════════════════╝"
  echo -e "${NC}"
}

# Ensure there's market data to show. Runs the daily pipeline only when the picks table is
# empty (first run / after `fresh`), so normal starts stay fast. `force` re-runs regardless.
ensure_market_data() {
  local force="${1:-}"
  ( cd "$BACKEND_DIR" && DATABASE_URL="$DATABASE_URL" REDIS_URL="$REDIS_URL" "$PY" - "$force" <<'PY'
import asyncio, sys
from sqlalchemy import select, func
from app.core.db import SessionLocal
from app.models.trading import AIPick
from app.jobs.daily_pipeline import run
force = (len(sys.argv) > 1 and sys.argv[1] == "force")
async def main():
    async with SessionLocal() as db:
        n = (await db.execute(select(func.count(AIPick.id)))).scalar()
    if n and not force:
        print(f"  market data present ({n} picks) — skipping pipeline")
        return
    print(("  refreshing" if n else "  no market data yet — populating") + " via the daily pipeline (real prices)…")
    try:
        r = await run()
        print(f"  pipeline done: regime={r.get('regime')}, {len(r.get('picks', []))} picks")
    except Exception as e:
        print(f"  pipeline failed ({e}) — picks will fill on the 3:30pm job / `swingai.sh pipeline`")
asyncio.run(main())
PY
  ) 2>&1 | grep -vE "smartConnect|INFO:|WARNING:" || true
}

# Real health probe: each port up/down, the API /health response, and a peek at recent
# error lines in the logs. Returns non-zero if anything core is down.
health_summary() {
  local down=0
  echo -e "${BOLD}Health${NC}"
  for pl in "Postgres:$DB_PORT" "Redis:$REDIS_PORT" "API:$BACKEND_PORT" "Dashboard:$DASHBOARD_PORT" "Marketing:$MARKETING_PORT"; do
    local name="${pl%%:*}" port="${pl##*:}"
    if port_listening "$port"; then echo -e "  ${GREEN}●${NC} $name (:$port)"
    else echo -e "  ${RED}○${NC} $name (:$port) — ${RED}DOWN${NC}"; down=1; fi
  done
  if http_ok "http://localhost:$BACKEND_PORT/api/health"; then
    echo -e "  ${GREEN}●${NC} API /api/health responding"
  else
    echo -e "  ${RED}○${NC} API /api/health not responding"; down=1
  fi
  local be fe
  be="$(recent_errors "$LOG_DIR/backend.log")"; fe="$(recent_errors "$LOG_DIR/frontend.log")"
  if [ -n "$be" ]; then echo -e "  ${YELLOW}recent backend errors:${NC}"; echo "$be" | sed 's/^/    /'; fi
  if [ -n "$fe" ]; then echo -e "  ${YELLOW}recent frontend errors:${NC}"; echo "$fe" | sed 's/^/    /'; fi
  [ "$down" = 0 ] && echo -e "  ${GREEN}all services healthy${NC}"
  return "$down"
}

# $1 = "watch" to attach + stream logs after a successful start.
start_all() {
  local watch="${1:-}"
  banner
  ensure_docker || exit 1
  bash "$SCRIPT_DIR/db.sh" start || { err "database failed to start — aborting."; exit 1; }
  local trouble=0
  bash "$SCRIPT_DIR/backend.sh" start  || { warn "backend reported a problem (see its log above)"; trouble=1; }
  bash "$SCRIPT_DIR/frontend.sh" start || { warn "frontend reported a problem (see its log above)"; trouble=1; }
  # Market data is populated on demand: the dashboard auto-fetches it (with a progress bar)
  # on first open when the DB is empty (e.g. after `fresh`). Refresh anytime: swingai.sh pipeline
  echo
  health_summary || trouble=1
  echo
  if [ "$trouble" = 0 ]; then ok "SwingAI is up:"; else warn "SwingAI started with issues — check the health report above + the logs:"; fi
  echo -e "   Marketing   → ${BOLD}http://localhost:$MARKETING_PORT${NC}"
  echo -e "   Dashboard   → ${BOLD}http://localhost:$DASHBOARD_PORT${NC}"
  echo -e "   API docs    → ${BOLD}http://localhost:$BACKEND_PORT/docs${NC}"
  echo -e "   Watch logs  → ${BOLD}scripts/swingai.sh logs${NC}   (or start with --logs)"
  if ! ( cd "$BACKEND_DIR" && DATABASE_URL="$DATABASE_URL" "$PY" -m app.admin_setup --check >/dev/null 2>&1 ); then
    warn "No super admin yet — run:  ${BOLD}scripts/swingai.sh create-admin${NC}"
  fi
  if [ "$watch" = "watch" ]; then
    echo; log "Attaching to logs (Ctrl-C to stop watching — services keep running)…"
    exec bash "$SCRIPT_DIR/logs.sh" all
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

# True if the 2nd CLI arg asks to attach to logs after starting.
wants_watch() { case "${1:-}" in --logs|-w|--watch) return 0 ;; *) return 1 ;; esac; }

case "${1:-help}" in
  start)   if wants_watch "${2:-}"; then start_all watch; else start_all; fi ;;
  dev)     start_all watch ;;                       # start + attach to logs (see crashes live)
  stop)    stop_all ;;
  restart) stop_all; if wants_watch "${2:-}"; then start_all watch; else start_all; fi ;;
  status|health) banner; health_summary || true ;;
  fresh)
    banner
    err "DESTRUCTIVE: this WIPES the database — all users, trades, plans, settings — and recreates it."
    printf "  Type 'y' to continue, anything else to abort: "
    read -r ans
    [ "$ans" = "y" ] || { echo "  aborted."; exit 0; }
    ensure_docker || exit 1
    dc down -v >/dev/null 2>&1 || true
    ok "database wiped"
    start_all                                   # starts + creates tables/seeds (no watch yet)
    echo; log "Database is fresh — now create your first super admin:"
    create_admin                                # needs the tables that start_all just created
    if wants_watch "${2:-}"; then
      echo; log "Attaching to logs (Ctrl-C to stop watching — services keep running)…"
      exec bash "$SCRIPT_DIR/logs.sh" all
    fi ;;
  create-admin) create_admin "${@:2}" ;;
  pipeline) ensure_docker || exit 1; bash "$SCRIPT_DIR/db.sh" start >/dev/null 2>&1 || true
            log "Refreshing market data (daily pipeline)…"; ensure_market_data force ;;
  logs)    bash "$SCRIPT_DIR/logs.sh" all "${2:-}" ;;
  test)    bash "$SCRIPT_DIR/backend.sh" test ;;
  *) sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//' ;;
esac
