#!/usr/bin/env bash
set -Eeuo pipefail

SRC=/home/OWNER/linux-cachyos-bc250/build/vcn-patch-check/cachyos-7.2-rc7-1
LOG=/tmp/bc250-vcn-module-build.log

cd -- "$SRC"
make LLVM=1 -j8 M=drivers/gpu/drm/amd/amdgpu modules >"$LOG" 2>&1
printf '%s\n' 'AMDGPU_MODULE_BUILD_OK'
find drivers/gpu/drm/amd/amdgpu -maxdepth 1 -type f -name '*.ko' -printf '%p %s bytes\n'
tail -n 60 "$LOG"
