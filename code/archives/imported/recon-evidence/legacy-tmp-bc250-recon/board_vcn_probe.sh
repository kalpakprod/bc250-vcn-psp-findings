#!/bin/bash
set -x
SP=~/.local/share/pipx/venvs/bc250-smu-oc
echo "=== bc250-detect ==="
bc250-detect 2>&1 | head -50
echo "=== bc250-apply help ==="
bc250-apply --help 2>&1 | head -30
echo "=== bc250-smu-oc bin ==="
ls -la $SP/bin 2>/dev/null
echo "=== SMU PCI config window (01:00.0) ==="
lspci -xxx -s 01:00.0 2>/dev/null | sed -n '1,40p'
echo "=== debugfs mount ==="
mount | grep debugfs
echo "=== dri0 listing (vcn/smn/reg) ==="
ls -la /sys/kernel/debug/dri0/ 2>/dev/null | grep -iE 'vcn|smn|reg|pm|clk' | head -40
echo "=== gpu_metrics (clocks) ==="
cat /sys/kernel/debug/dri0/amdgpu_gpu_metrics 2>/dev/null | head -60
echo "=== dmesg VCN/amdgpu/psp/clock (sudo) ==="
sudo dmesg 2>/dev/null | grep -iE 'vcn|amdgpu|skillfish|psp|clock|clk|dpm|domain' | tail -50
echo "=== done ==="
