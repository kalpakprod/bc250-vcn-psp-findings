#!/usr/bin/env bash
set -u

echo '=== BOOT ==='
uname -r
cat /proc/cmdline
uptime

echo '=== MODULE PARAMS ==='
for param in bc250_cc_write_mode bc250_vcn fw_load_type; do
  printf '%s=' "$param"
  cat "/sys/module/amdgpu/parameters/$param" 2>/dev/null || echo MISSING
done

echo '=== GPU ==='
lspci -nnk -s 01:00.0
modinfo -k 7.2.0-1.1-cachyos-bc250 amdgpu | grep -E '^(filename|srcversion):' || true

echo '=== DRM/VIDEO ==='
ls -l /dev/dri /dev/video* /dev/media* 2>&1 || true

echo '=== VCN LOG ==='
sudo journalctl -b -k --no-pager \
  | grep -iE 'bc250|bc-250|vcn|uvd|kiq|ring.*test|amdgpu.*(error|fail|timeout)|firmware.*(load|direct)|REG_WAIT' \
  | tail -240 || true

echo '=== SERVICES ==='
systemctl is-active \
  bc250-metrics bc250-gpu-watchdog bc250-pwrwatch bc250-telemetry \
  bc250-dpwatch bc250-fan bc250-netconsole 2>/dev/null || true
