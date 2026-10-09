#!/bin/sh
set -eu
if [ "$#" -ne 1 ]; then
    printf '%s\n' "usage: ROLLBACK.sh TARGET_COPY" >&2
    exit 2
fi
script_dir=$(CDPATH= cd "$(dirname "$0")" && pwd)
cp "$script_dir/memory-oc-recheck.baseline.md" "$1"
