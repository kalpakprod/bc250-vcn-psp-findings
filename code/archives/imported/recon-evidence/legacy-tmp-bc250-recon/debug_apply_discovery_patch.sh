#!/usr/bin/env bash
set -u

src=/home/OWNER/linux-cachyos-bc250/build/linux-cachyos-rc/src/cachyos-7.2-rc7-1
patch=/tmp/0010-bc250-amdgpu-discovery-default-offset.patch
file=$src/drivers/gpu/drm/amd/amdgpu/amdgpu_discovery.c

echo '=== MARKER ==='
grep -n -A14 -B3 'Preserve a valid discovery table already present' "$file"
echo "marker_rc=$?"

echo '=== FORWARD CHECK ==='
git -C "$src" apply --check --verbose "$patch"
echo "forward_rc=$?"

echo '=== REVERSE CHECK ==='
git -C "$src" apply --reverse --check --verbose "$patch"
echo "reverse_rc=$?"

echo '=== DIFF ==='
git -C "$src" diff -- "$file" | head -160
echo "diff_rc=${PIPESTATUS[0]}"

echo '=== SOURCE CONTEXT ==='
sed -n '300,340p' "$file"
