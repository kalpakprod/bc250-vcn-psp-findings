#!/usr/bin/env bash
set -uo pipefail
echo "=== amdgpu_firmware_info (VCN section) ==="
cat /sys/class/drm/card0/device/amdgpu/amdgpu_firmware_info 2>/dev/null | grep -iA3 "vcn" || echo "(no vcn in firmware_info)"
echo "=== all VCN/psp files on board (non-firmware-dir) ==="
find / -xdev -name '*vcn*' 2>/dev/null | grep -vE "/lib/firmware/amdgpu/" | head -40
find / -xdev -name '*psp*' 2>/dev/null | grep -vE "/lib/firmware/amdgpu/" | head -20
echo "=== PSP signature / region files ==="
find / -xdev -iname '*signature*' -o -iname '*region*' 2>/dev/null | grep -iE "psp|vcn|amd|firmware" | head -20
echo "=== dmesg netconsole: VCN/PSP load lines (from kmsg) ==="
cat /dev/kmsg 2>/dev/null | grep -iE "vcn|psp|skillfish" | tail -30 || echo "(no kmsg vcn/psp)"
echo "DONEVCN"
