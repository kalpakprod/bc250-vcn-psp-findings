#!/usr/bin/env bash
set -Eeuo pipefail

SRC=/home/OWNER/linux-cachyos-bc250/build/vcn-patch-check/cachyos-7.2-rc7-1
CONFIG=/home/OWNER/linux-cachyos-bc250/build/linux-cachyos-rc/config
LOG=/tmp/bc250-vcn-compile.log

cd -- "$SRC"
cp -- "$CONFIG" .config
make LLVM=1 olddefconfig >"$LOG" 2>&1
make LLVM=1 -j"$(nproc)" \
  drivers/gpu/drm/amd/amdgpu/amdgpu_drv.o \
  drivers/gpu/drm/amd/amdgpu/amdgpu_discovery.o \
  drivers/gpu/drm/amd/amdgpu/amdgpu_ucode.o \
  >>"$LOG" 2>&1

printf '%s\n' 'TARGETED_COMPILE_OK'
for object in \
  drivers/gpu/drm/amd/amdgpu/amdgpu_drv.o \
  drivers/gpu/drm/amd/amdgpu/amdgpu_discovery.o \
  drivers/gpu/drm/amd/amdgpu/amdgpu_ucode.o
do
  test -s "$object"
  printf '%s %s bytes\n' "$object" "$(stat -c %s "$object")"
done

tail -n 40 "$LOG"
