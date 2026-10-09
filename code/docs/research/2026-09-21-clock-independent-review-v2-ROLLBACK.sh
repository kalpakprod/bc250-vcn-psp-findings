#!/bin/sh
# Restore a separate modified review copy from the pristine sibling baseline.
set -eu
if [ "$#" -ne 1 ]; then
	echo "usage: $0 TARGET_COPY" >&2
	exit 2
fi
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
BASELINE="$SCRIPT_DIR/2026-09-21-clock-independent-review-v2-pristine.md"
[ -f "$BASELINE" ] || {
	echo "missing baseline: $BASELINE" >&2
	exit 3
}
cp "$BASELINE" "$1"
cmp -s "$BASELINE" "$1"
