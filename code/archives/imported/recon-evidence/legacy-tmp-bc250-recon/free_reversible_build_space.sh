#!/usr/bin/env bash
set -Eeuo pipefail

STASH=/tmp/bc250-build-space
BUILD=/home/OWNER/linux-cachyos-bc250/build/linux-cachyos-rc
CACHE=/home/OWNER/.cache/llvm-debuginfod
mkdir -p "$STASH"

if [[ -f "$BUILD/cachyos-7.2-rc7-1.tar.gz" ]]; then
  mv "$BUILD/cachyos-7.2-rc7-1.tar.gz" "$STASH/"
fi

if [[ -d "$CACHE" && ! -L "$CACHE" ]]; then
  mv "$CACHE" "$STASH/llvm-debuginfod"
  ln -s "$STASH/llvm-debuginfod" "$CACHE"
fi

btrfs filesystem sync /
df -h / /tmp
systemctl --user is-active bc250-vcn-build
