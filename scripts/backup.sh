#!/usr/bin/env bash
# Postgres backup/restore for the SwingAI dev DB (blueprint/19).
# Dumps the Dockerised Postgres to a gzipped file under backups/, prunes old ones,
# and restores on demand. For a real cron, schedule:  scripts/backup.sh backup
#   scripts/backup.sh [backup|restore <file>|list|prune]
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
source "$SCRIPT_DIR/_common.sh"

BACKUP_DIR="$ROOT_DIR/backups"
KEEP="${BACKUP_KEEP:-14}"          # how many dumps to retain
mkdir -p "$BACKUP_DIR"

prune() {
  local n; n=$(ls -1t "$BACKUP_DIR"/swingaidb-*.sql.gz 2>/dev/null | tail -n +"$((KEEP+1))" | wc -l | tr -d ' ')
  ls -1t "$BACKUP_DIR"/swingaidb-*.sql.gz 2>/dev/null | tail -n +"$((KEEP+1))" | xargs -r rm -f
  [ "$n" != "0" ] && log "pruned $n old backup(s), keeping $KEEP"
  return 0
}

case "${1:-backup}" in
  backup)
    ensure_docker || exit 1
    ts="$(date +%Y%m%d-%H%M%S)"
    out="$BACKUP_DIR/swingaidb-$ts.sql.gz"
    log "Dumping $POSTGRES_DB → $out"
    dc exec -T db pg_dump -U "$POSTGRES_USER" --clean --if-exists "$POSTGRES_DB" | gzip > "$out"
    if [ ! -s "$out" ]; then err "backup is empty — aborting"; rm -f "$out"; exit 1; fi
    ok "backup written ($(du -h "$out" | cut -f1))"
    prune ;;
  restore)
    ensure_docker || exit 1
    f="${2:-}"
    [ -z "$f" ] && { err "usage: backup.sh restore <file.sql.gz>"; exit 1; }
    [ -f "$f" ] || f="$BACKUP_DIR/$f"
    [ -f "$f" ] || { err "no such backup: $2"; exit 1; }
    warn "Restoring $f into $POSTGRES_DB (existing data is overwritten)…"
    gunzip -c "$f" | dc exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null
    ok "restore complete" ;;
  list)
    ls -1t "$BACKUP_DIR"/swingaidb-*.sql.gz 2>/dev/null | while read -r f; do
      echo "  $(basename "$f")  ($(du -h "$f" | cut -f1))"
    done || true
    [ -z "$(ls -A "$BACKUP_DIR" 2>/dev/null)" ] && echo "  (no backups yet)"; true ;;
  prune) prune ;;
  *) echo "usage: backup.sh [backup|restore <file>|list|prune]"; exit 1 ;;
esac
