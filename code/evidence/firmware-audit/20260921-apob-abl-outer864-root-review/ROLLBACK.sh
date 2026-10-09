#!/usr/bin/env bash
set -euo pipefail
if [ "$#" -ne 1 ]; then echo "usage: $0 TARGET_COPY" >&2; exit 2; fi
TARGET=$1
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
BASELINE="$SCRIPT_DIR/BASELINE.md"
[ -f "$TARGET" ] || { echo "target copy not found: $TARGET" >&2; exit 3; }
[ -f "$BASELINE" ] || { echo "sibling baseline not found: $BASELINE" >&2; exit 4; }
cp -- "$BASELINE" "$TARGET"
