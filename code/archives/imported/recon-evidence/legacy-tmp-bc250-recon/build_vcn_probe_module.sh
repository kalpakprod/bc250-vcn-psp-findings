#!/usr/bin/env bash
set -Eeuo pipefail

kver=7.2.0-1.1-cachyos-bc250
src=/games/bc250-vcn-stable-src/src/cachyos-7.2.0-1
module_dir=$src/drivers/gpu/drm/amd/amdgpu
patch=/tmp/0011-bc250-vcn-probe-mode.patch
checker=/tmp/check_vcn_probe_patch.py

[[ $(make -s -C "$src" kernelrelease) == "$kver" ]]
patch --dry-run --forward -p1 -d "$src" < "$patch"
patch --forward -p1 -d "$src" < "$patch"
python3 "$checker" "$module_dir"

make -C "$src" CC=clang LD=ld.lld LLVM=1 LLVM_IAS=1 modules_prepare
cp /lib/modules/$kver/build/Module.symvers "$src/Module.symvers"
make -C "$src" CC=clang LD=ld.lld LLVM=1 LLVM_IAS=1 \
  -j"$(nproc)" M=drivers/gpu/drm/amd/amdgpu modules

module=$module_dir/amdgpu.ko
[[ -s "$module" ]]
[[ $(modinfo -F vermagic "$module") == "$kver "* ]]

echo '=== PROBE MODULE ==='
modinfo "$module" | grep -E '^filename:|^srcversion:|^vermagic:|^parm:.*bc250_vcn_mode|^firmware:.*navi10_vcn'
sha256sum "$module"
