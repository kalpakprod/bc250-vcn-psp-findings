#!/bin/sh
# Restore the pristine zero-byte report baseline on a separate target copy.
set -eu
if [ "$#" -ne 1 ]; then
	echo "usage: $0 TARGET_COPY" >&2
	exit 2
fi
[ -f "$1" ] || {
	echo "missing target copy: $1" >&2
	exit 3
}
: >"$1"
[ ! -s "$1" ]
