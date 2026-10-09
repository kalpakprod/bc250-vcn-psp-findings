#!/usr/bin/env bash
set -Eeuo pipefail

kver=7.2.0-1.1-cachyos-bc250
repo=/home/OWNER/linux-cachyos-bc250
build=/games/bc250-vcn-stable-src
vcn_patch=$repo/patches/kernel-7.2/0009-bc250-vcn-safe-direct-load.patch
patch_name=$(basename "$vcn_patch")
headers=/lib/modules/$kver/build
updates=/lib/modules/$kver/updates/bc250-vcn
state=/var/lib/bc250-vcn/stable-vcn-overlay

[[ -f "$vcn_patch" ]]
[[ -d "$headers" ]]

CACHYOS_SOURCE_VARIANT=linux-cachyos \
BC250_PKGREL=1 \
BUILD_DIR="$build" \
  "$repo/scripts/prepare-pkgbuild.sh"

cp -- "$vcn_patch" "$build/$patch_name"
python3 - "$build/PKGBUILD" "$build/$patch_name" <<'PY'
from pathlib import Path
import subprocess
import sys

pkgbuild = Path(sys.argv[1])
patch = Path(sys.argv[2])
text = pkgbuild.read_text(encoding="utf-8")
name = patch.name
checksum = subprocess.check_output(["b2sum", str(patch)], text=True).split()[0]

if name not in text:
    if text.count("source=(\n") != 1 or text.count("b2sums=(") != 1:
        raise SystemExit("ERROR: unexpected PKGBUILD source/checksum layout")
    text = text.replace("source=(\n", f"source=(\n  \"{name}\"\n", 1)
    text = text.replace("b2sums=(", f"b2sums=('{checksum}'\n         ", 1)

skip_anchor = '''        src="${src%.zst}"
        [[ $src = *.patch ]] || continue
'''
skip_replacement = '''        src="${src%.zst}"
        [[ $src = *.patch ]] || continue
        # Linux 7.2 final already contains the BC-250 audio change.
        [[ $src == 0002-bc250-audio.patch ]] && continue
'''
if text.count(skip_anchor) != 1:
    raise SystemExit("ERROR: expected prepare patch-loop anchor exactly once")
text = text.replace(skip_anchor, skip_replacement, 1)
pkgbuild.write_text(text, encoding="utf-8", newline="\n")
PY

cd "$build"
makepkg --nobuild --nodeps --noconfirm --skippgpcheck

src=$(find "$build/src" -mindepth 1 -maxdepth 1 -type d \
  -exec test -f '{}/drivers/gpu/drm/amd/amdgpu/Makefile' ';' -print | head -1)
[[ -n "$src" ]]
module_dir=$src/drivers/gpu/drm/amd/amdgpu
module=$module_dir/amdgpu.ko

grep -n -A8 -B3 'case IP_VERSION(2, 0, 3)' \
  "$module_dir/amdgpu_discovery.c"
grep -n 'amdgpu_bc250_vcn' "$module_dir/amdgpu_drv.c"

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
