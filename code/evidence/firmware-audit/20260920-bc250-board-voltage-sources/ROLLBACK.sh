#!/bin/sh
# Rollback for the BC-250 board voltage sources inventory task (2026-09-20).
#
# Removes only the files this task created:
#   <this directory>                                  (scanner, verifier, result, captures, manifest)
#   docs/research/2026-09-20-bc250-board-voltage-sources.md
# and, with --purge-log, also
#   docs/action-logs/2026-09-20-bc250-board-voltage-sources.md
#
# The append-only action log is kept by default: a rollback must not erase the record
# of what it rolled back. The donor ROM, the pinned 231/233-module corpus and every
# earlier evidence directory are never touched.
set -eu

SELF_DIR=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$SELF_DIR/../../.." && pwd)
REPORT="$ROOT/docs/research/2026-09-20-bc250-board-voltage-sources.md"
LOG="$ROOT/docs/action-logs/2026-09-20-bc250-board-voltage-sources.md"

if [ ! -f "$ROOT/AGENT_CONTRACT.md" ]; then
  echo "REFUSED: $ROOT is not the bc250 project root" >&2
  exit 2
fi
case "$SELF_DIR" in
  */evidence/firmware-audit/20260920-bc250-board-voltage-sources) ;;
  *) echo "REFUSED: unexpected script location $SELF_DIR" >&2; exit 2 ;;
esac

if [ -f "$REPORT" ]; then
  rm "$REPORT"
  echo "REMOVED_REPORT $REPORT"
else
  echo "ABSENT_REPORT $REPORT"
fi

if [ "${1:-}" = "--purge-log" ]; then
  if [ -f "$LOG" ]; then
    rm "$LOG"
    echo "REMOVED_LOG $LOG"
  else
    echo "ABSENT_LOG $LOG"
  fi
else
  echo "KEPT_LOG $LOG (use --purge-log to remove)"
fi

rm -f "$SELF_DIR"/scan_vr_mailbox_writers.py \
      "$SELF_DIR"/vr-mailbox-writers-result.json \
      "$SELF_DIR"/verify_board_voltage_sources.py \
      "$SELF_DIR"/VERIFICATION.txt \
      "$SELF_DIR"/SHA256SUMS.final \
      "$SELF_DIR"/independent-verify.stdout \
      "$SELF_DIR"/independent-verify.stderr \
      "$SELF_DIR"/independent-verify.exit \
      "$SELF_DIR"/worker-scanner.stdout \
      "$SELF_DIR"/worker-scanner.stderr \
      "$SELF_DIR"/worker-scanner.exit
rm -rf "$SELF_DIR"/objdump
rm -f "$0"
rmdir "$SELF_DIR" 2>/dev/null && echo "REMOVED_DIR $SELF_DIR" || echo "DIR_NOT_EMPTY $SELF_DIR"
echo "RESTORED_OK"
