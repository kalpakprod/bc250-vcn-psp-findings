#!/usr/bin/env bash
set -Eeuo pipefail

ROOT=/home/OWNER/linux-cachyos-bc250
BUILD="$ROOT/build/linux-cachyos-rc"
CHECK="$ROOT/build/vcn-patch-check"
SRC="$CHECK/cachyos-7.2-rc7-1"

rm -rf -- "$CHECK"
mkdir -p -- "$CHECK"
tar -xf "$BUILD/cachyos-7.2-rc7-1.tar.gz" -C "$CHECK"

cd -- "$SRC"
for patch_name in \
  0001-bc250-8core-telemetry-gpu-activity.patch \
  0003-nct6687d-hwmon.patch \
  0004-gfx1013-pasid-tlb-invalidation.patch \
  0005-gfx1013-compute-gfxoff-guard.patch \
  0006-bc250-kfd-flush-tlb-by-runlist.patch \
  0007-amdgpu-ttm-null-page-guard.patch
do
  patch -s -Np1 < "$ROOT/patches/kernel-7.2/$patch_name"
done

patch --dry-run -Np1 < "$ROOT/patches/kernel-7.2/0009-bc250-vcn-safe-direct-load.patch"
patch -s -Np1 < "$ROOT/patches/kernel-7.2/0009-bc250-vcn-safe-direct-load.patch"

printf '%s\n' 'PATCH_APPLY_OK'
grep -n -E 'amdgpu_bc250_vcn|case IP_VERSION\(2, 0, 3\)' \
  drivers/gpu/drm/amd/amdgpu/amdgpu.h \
  drivers/gpu/drm/amd/amdgpu/amdgpu_drv.c \
  drivers/gpu/drm/amd/amdgpu/amdgpu_discovery.c \
  drivers/gpu/drm/amd/amdgpu/amdgpu_ucode.c

if grep -q 'BC-250: VCN MMIO' drivers/gpu/drm/amd/amdgpu/vcn_v2_0.c; then
  printf '%s\n' 'ERROR: unsafe MMIO probe remains' >&2
  exit 1
fi
printf '%s\n' 'NO_UNSAFE_MMIO_PROBE'
