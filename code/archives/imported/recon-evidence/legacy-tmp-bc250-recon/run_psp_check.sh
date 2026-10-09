#!/usr/bin/env bash
set -uo pipefail
echo "=== psp_fw_version ==="
cat /sys/class/drm/card0/device/psp_fw_version 2>/dev/null || echo "(no psp_fw_version)"
echo "=== vcn_fw_version ==="
cat /sys/class/drm/card0/device/amdgpu/vcn_fw_version 2>/dev/null || echo "(no vcn_fw_version)"
echo "=== amdgpu ip_blocks ==="
cat /sys/class/drm/card0/device/amdgpu/ip_block_info 2>/dev/null || echo "(no ip_block_info)"
echo "=== lsmod psp/gc/vcn/sdma ==="
lsmod | grep -iE "psp|amdgpu|gc|vcn|sdma"
echo "=== dmesg psp/vcn (netconsole buffer) ==="
dmesg 2>/dev/null | grep -iE "psp|vcn" | tail -20 || echo "(none)"
echo "DONEPSP"
