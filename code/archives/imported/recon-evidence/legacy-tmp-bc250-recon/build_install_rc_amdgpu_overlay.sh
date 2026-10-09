#!/usr/bin/env bash
set -Eeuo pipefail

kver=7.2.0-rc7-1.90-cachyos-rc-bc250
repo=/home/OWNER/linux-cachyos-bc250
src=$repo/build/linux-cachyos-rc/src/cachyos-7.2-rc7-1
patch=/tmp/0010-bc250-amdgpu-discovery-default-offset.patch
module_rel=drivers/gpu/drm/amd/amdgpu/amdgpu.ko
module=$src/$module_rel
updates=/lib/modules/$kver/updates/bc250
state=/var/lib/bc250-vcn/rc7-discovery-overlay

[[ $(uname -r) == "$kver" ]] || {
  echo "ERROR: running kernel is $(uname -r), expected $kver" >&2
  exit 1
}
[[ -f "$src/drivers/gpu/drm/amd/amdgpu/amdgpu_discovery.c" ]]
[[ -f "$patch" ]]

if ! grep -q 'Preserve a valid discovery table already present' \
  "$src/drivers/gpu/drm/amd/amdgpu/amdgpu_discovery.c"; then
  patch --dry-run --forward -p1 -d "$src" < "$patch"
  patch --forward -p1 -d "$src" < "$patch"
fi

grep -n -A14 -B3 'Preserve a valid discovery table already present' \
  "$src/drivers/gpu/drm/amd/amdgpu/amdgpu_discovery.c"

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

zstd -T0 -19 -f "$module" -o /tmp/amdgpu.ko.zst
sudo install -m 0644 /tmp/amdgpu.ko.zst "$updates/amdgpu.ko.zst"
sudo depmod "$kver"

echo '=== OVERLAY MODULE ==='
modinfo -k "$kver" amdgpu | grep -E '^filename:|^version:|^srcversion:|^vermagic:|^parm:.*(bc250_cc_write_mode|bc250_vcn)'
sha256sum "$updates/amdgpu.ko.zst"
