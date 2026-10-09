#!/bin/sh
# Rollback for the CLV fixed-voltage independent decode evidence set (2026-09-20).
# This task only created new files; it modified no existing artifact. Rollback therefore
# removes exactly the files listed below and prints the one manual memory step.
# Usage: ./ROLLBACK.sh           -> dry run (lists what would be removed)
#        ./ROLLBACK.sh --apply   -> removes the files
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../../.." && pwd)
TARGETS="$HERE
$ROOT/docs/research/2026-09-20-fixed-voltage-independent-decode.md
$ROOT/docs/action-logs/2026-09-20-fixed-voltage-independent-decode.md"
echo "rollback targets:"
printf '%s\n' "$TARGETS" | sed 's/^/  /'
echo "manual step (not automatic): remove the '## G7 correction: fixed-voltage byte-assertion labels'"
echo "  section appended to memory/project-state.md and the matching oc-recheck entry, keeping"
echo "  the superseded text as project history."
if [ "${1:-}" != "--apply" ]; then
  echo "dry run: nothing removed (pass --apply to remove)"
  exit 0
fi
printf '%s\n' "$TARGETS" | while IFS= read -r t; do
  [ -e "$t" ] && rm -rf -- "$t" && echo "removed $t"
done
echo "rollback applied"
