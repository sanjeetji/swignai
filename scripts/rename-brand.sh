#!/usr/bin/env bash
# rename-brand.sh — rename the platform across the whole repo in one command.
#
#   scripts/rename-brand.sh OLD NEW            # dry-run: show what would change
#   scripts/rename-brand.sh OLD NEW --apply    # actually apply the rename
#
# Example:
#   scripts/rename-brand.sh SwingAI SwingWise --apply
#
# Renames case-sensitively for the exact token AND a lowercase variant
# (SwingAI->SwingWise and swingai->swingwise). Skips .git, node_modules,
# build outputs. Portable to macOS bash 3.2 (no mapfile/arrays).
set -eu

OLD="${1:-}"; NEW="${2:-}"; MODE="${3:-}"
if [ -z "$OLD" ] || [ -z "$NEW" ]; then
  echo "usage: $0 OLD NEW [--apply]"; exit 1
fi
OLD_LC="$(printf '%s' "$OLD" | tr '[:upper:]' '[:lower:]')"
NEW_LC="$(printf '%s' "$NEW" | tr '[:upper:]' '[:lower:]')"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

LIST="$(mktemp)"
trap 'rm -f "$LIST"' EXIT
grep -RIl -e "$OLD" -e "$OLD_LC" . \
  --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.next \
  --exclude-dir=.venv --exclude-dir=dist --exclude-dir=build --exclude-dir=.turbo \
  > "$LIST" 2>/dev/null || true

COUNT="$(wc -l < "$LIST" | tr -d ' ')"
if [ "$COUNT" -eq 0 ]; then echo "No occurrences of '$OLD' found."; exit 0; fi

echo "Files containing '$OLD'/'$OLD_LC' ($COUNT):"
sed 's/^/  /' "$LIST"

if [ "$MODE" != "--apply" ]; then
  echo
  echo "DRY RUN — re-run with --apply to perform the rename."
  echo "After applying, also update brand/brand.config.json (name/domain/email) and .env"
  echo "(APP_DOMAIN, NEXT_PUBLIC_*) by hand."
  exit 0
fi

while IFS= read -r f; do
  [ -n "$f" ] || continue
  sed -i.bak -e "s/$OLD/$NEW/g" -e "s/$OLD_LC/$NEW_LC/g" "$f" && rm -f "$f.bak"
done < "$LIST"
echo "Applied: $OLD -> $NEW (and $OLD_LC -> $NEW_LC) across $COUNT files."
echo "Now: update brand/brand.config.json (name/domain/email) + .env, and verify the app boots."
