#!/bin/sh
# ROLLBACK.sh — BC-250 board voltage sources recheck (task-owned evidence package).
#
# Restores pristine bytes of verify_board_voltage_sources.py from the sibling baseline
# verify_board_voltage_sources.py.orig, and optionally deletes this task's own artifacts.
#
# Usage:
#   ./ROLLBACK.sh                 restore the sibling verify_board_voltage_sources.py in place
#   ./ROLLBACK.sh <target-copy>   restore pristine bytes onto another copy of the file
#   ./ROLLBACK.sh --remove        delete only this task's owned artifacts
#
# Read-only analysis task: no ROM, NVRAM, register, candidate or hardware write is undone
# here, because none was performed.
set -eu

DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
BASE="$DIR/verify_board_voltage_sources.py.orig"
PRISTINE_SHA256="a1551700443086d1c097ae44d516eb152c88c9174b277ba0825c982d77b0e5b4"

if [ "${1:-}" = "--remove" ]; then
  rm -rf -- "$DIR"
  printf '%s\n' "removed $DIR"
  exit 0
fi

TARGET=${1:-$DIR/verify_board_voltage_sources.py}

[ -f "$BASE" ] || { printf '%s\n' "baseline missing: $BASE" >&2; exit 1; }
[ -f "$TARGET" ] || { printf '%s\n' "target missing: $TARGET" >&2; exit 1; }

cp -- "$BASE" "$TARGET"
SHA=$(sha256sum -- "$TARGET" | cut -d' ' -f1)
printf 'restored %s\nsha256 %s\n' "$TARGET" "$SHA"
[ "$SHA" = "$PRISTINE_SHA256" ] || { printf '%s\n' "restored hash != pristine" >&2; exit 1; }
printf '%s\n' "pristine hash verified"
