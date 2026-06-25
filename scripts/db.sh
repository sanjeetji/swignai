#!/usr/bin/env bash
# Database + Redis control (Docker). Usage:
#   scripts/db.sh [start|stop|status|psql|redis-cli|reset|wait]
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

cmd="${1:-start}"
# actions that REQUIRE Docker running → ensure Colima/Docker is up first.
# (status/stop are read-only-ish and degrade gracefully, so they don't force-start)
case "$cmd" in
  start|wait|psql|redis-cli|reset) ensure_docker || exit 1 ;;
esac
case "$cmd" in
  start)
    log "Starting SwingAI Postgres (:$DB_PORT) + Redis (:$REDIS_PORT)…"
    dc up -d db redis
    wait_for_port "$DB_PORT" "postgres :$DB_PORT" 60
    wait_for_port "$REDIS_PORT" "redis :$REDIS_PORT" 30
    ok "database stack up"
    ;;
  stop)
    log "Stopping database stack (data preserved in volumes)…"
    dc stop db redis && ok "stopped"
    ;;
  status)
    dc ps db redis
    ;;
  wait)
    wait_for_port "$DB_PORT" "postgres :$DB_PORT" 60
    ;;
  psql)
    dc exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
    ;;
  redis-cli)
    dc exec redis redis-cli
    ;;
  reset)
    warn "This DESTROYS the SwingAI database volume."
    read -r -p "Type 'yes' to confirm: " a
    [ "$a" = "yes" ] || { log "aborted"; exit 0; }
    dc down -v && ok "volumes removed; run 'db.sh start' to recreate"
    ;;
  *)
    echo "usage: db.sh [start|stop|status|psql|redis-cli|reset|wait]"; exit 1 ;;
esac
