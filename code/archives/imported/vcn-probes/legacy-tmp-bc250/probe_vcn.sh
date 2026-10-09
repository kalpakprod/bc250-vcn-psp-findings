#!/usr/bin/env bash
set -e
echo '=== VCN firmware files ==='
ls -la /lib/firmware/amdgpu/ 2>/dev/null | grep -iE 'vcn|skillfish|psp' || echo 'none'
echo '=== amdgpu_firmware_info (vcn/psp/me) ==='
cat /sys/class/drm/card0/device/amdgpu_firmware_info 2>/dev/null | grep -iE 'vcn|psp|me|mei|pfp|ce|rb|pm4' || echo 'none'
echo '=== IP blocks ==='
cat /sys/class/drm/card0/device/amdgpu_info_ip_blocks 2>/dev/null || echo 'none'
echo '=== umr present ==='
command -v umr || echo 'umr MISSING'
echo '=== drm dir ==='
ls /sys/class/drm/card0/device/drm/ 2>/dev/null
echo '=== dmesg VCN/PSP ==='
dmesg 2>/dev/null | grep -iE 'vcn|psp' || echo 'none'
echo '=== gpu_metrics VCN ==='
cat /sys/class/drm/card0/device/gpu_metrics 2>/dev/null | head -c 200 || echo 'none'
echo
echo '=== END ==='
