#!/bin/sh
set -eu
if [ "$#" -ne 1 ]; then
  printf '%s\n' "usage: $0 TARGET_COPY" >&2
  exit 2
fi
target=$1
base_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
baseline=$base_dir/BASELINE.outer864_origin_verify.py
if [ ! -f "$baseline" ]; then
  printf '%s\n' "missing sibling baseline: $baseline" >&2
  exit 1
fi
cp "$baseline" "$target"
if ! cmp -s "$baseline" "$target"; then
  printf '%s\n' "rollback byte comparison failed: $target" >&2
  exit 1
fi
printf '%s\n' "rollback restored $target from $baseline"
