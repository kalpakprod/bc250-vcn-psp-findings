#!/usr/bin/env bash
set -Eeuo pipefail

kver=7.2.0-1.1-cachyos-bc250
overlay=/lib/modules/$kver/updates/bc250-vcn/amdgpu.ko.zst

sudo rm -f -- "$overlay"
sudo rmdir "/lib/modules/$kver/updates/bc250-vcn" 2>/dev/null || true
sudo depmod "$kver"

echo '=== RESTORED STABLE PACKAGE MODULE ==='
modinfo -k "$kver" amdgpu | grep -E '^filename:|^srcversion:|^vermagic:'
