#!/usr/bin/env bash
set -Eeuo pipefail

kver=7.2.0-1.1-cachyos-bc250
src=/games/bc250-vcn-stable-src/src/cachyos-7.2.0-1
headers=/lib/modules/$kver/build
module_dir=$src/drivers/gpu/drm/amd/amdgpu
module=$module_dir/amdgpu.ko
updates=/lib/modules/$kver/updates/bc250-vcn
state=/var/lib/bc250-vcn/stable-vcn-overlay

[[ $(make -s -C "$src" kernelrelease) == "$kver" ]]
grep -q 'amdgpu_bc250_vcn' "$module_dir/amdgpu_drv.c"
make -C "$src" M=drivers/gpu/drm/amd/amdgpu clean
cp -- "$headers/Module.symvers" "$src/Module.symvers"

make -C "$src" CC=clang LD=ld.lld LLVM=1 LLVM_IAS=1 \
  -j"$(nproc)" M=drivers/gpu/drm/amd/amdgpu modules

[[ -s "$module" ]]
actual_vermagic=$(modinfo -F vermagic "$module")
[[ "$actual_vermagic" == "$kver "* ]] || {
  echo "ERROR: unexpected module vermagic: $actual_vermagic" >&2
  exit 1
}

sudo mkdir -p "$state" "$updates"
if [[ ! -f "$state/original-amdgpu.ko.zst" ]]; then
  original=$(modinfo -k "$kver" -F filename amdgpu)
  sudo cp -- "$original" "$state/original-amdgpu.ko.zst"
  sha256sum "$original" | sudo tee "$state/original-amdgpu.sha256" >/dev/null
fi

zstd -T0 -19 -f "$module" -o /tmp/amdgpu-stable-vcn.ko.zst
sudo install -m 0644 /tmp/amdgpu-stable-vcn.ko.zst "$updates/amdgpu.ko.zst"
sudo depmod "$kver"

echo '=== STABLE VCN OVERLAY MODULE ==='
modinfo -k "$kver" amdgpu | grep -E '^filename:|^srcversion:|^vermagic:|^firmware:.*navi10_vcn|^parm:.*(bc250_cc_write_mode|bc250_vcn)'
sha256sum "$updates/amdgpu.ko.zst"
