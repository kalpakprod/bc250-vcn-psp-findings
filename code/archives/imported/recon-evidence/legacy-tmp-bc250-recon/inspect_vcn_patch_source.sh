#!/usr/bin/env bash
set -u

repo=/home/OWNER/linux-cachyos-bc250
source_dir=$(find "$repo/build/linux-cachyos-rc/src" -mindepth 1 -maxdepth 1 -type d -exec test -d '{}/drivers/gpu/drm/amd/amdgpu' ';' -print | head -1)

echo '=== KERNEL PATCHSET ==='
find "$repo/patches/kernel-7.2" -maxdepth 1 -type f -name '*.patch' -printf '%f\n' | sort

echo '=== GFXOFF GUARD PATCH ==='
sed -n '1,240p' "$repo/patches/kernel-7.2/0005-gfx1013-compute-gfxoff-guard.patch"

echo '=== SOURCE DIR ==='
echo "$source_dir"

echo '=== SOURCE HITS ==='
grep -RIn -E 'GFX1013|PASID-only|kiq ring mec|compute queue|MEC2' \
  "$source_dir/drivers/gpu/drm/amd/amdgpu/gfx_v10_0.c" | head -120 || true

echo '=== SOURCE KIQ FUNCTIONS ==='
grep -n -A80 -B30 -E 'gfx_v10_0_kiq_init_queue|kiq.*mec|compute_ring.*me' \
  "$source_dir/drivers/gpu/drm/amd/amdgpu/gfx_v10_0.c" | head -260 || true

echo '=== SOURCE DIFF STAT ==='
git -C "$source_dir" diff --stat 2>/dev/null || true
