#!/usr/bin/env bash
set -Eeuo pipefail

kver=7.2.0-rc7-1.90-cachyos-rc-bc250
overlay=/lib/modules/$kver/updates/bc250/amdgpu.ko.zst

sudo rm -f -- "$overlay"
sudo rmdir "/lib/modules/$kver/updates/bc250" 2>/dev/null || true
sudo depmod "$kver"

echo '=== RESTORED PACKAGE MODULE ==='
modinfo -k "$kver" amdgpu | grep -E '^filename:|^srcversion:|^vermagic:'
