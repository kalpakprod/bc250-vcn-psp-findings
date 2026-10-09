#!/usr/bin/env bash
set -u

echo '=== BOOT ==='
uname -r
cat /proc/cmdline
uptime

echo '=== PARAMS ==='
for parameter in bc250_vcn_mode bc250_vcn fw_load_type; do
  printf '%s=' "$parameter"
  cat "/sys/module/amdgpu/parameters/$parameter" 2>/dev/null || echo MISSING
done

echo '=== GPU ==='
lspci -nnk -s 01:00.0

echo '=== NODES ==='
ls -l /dev/dri 2>&1 || true
find /dev -maxdepth 1 \( -name 'video*' -o -name 'media*' \) -print 2>/dev/null

echo '=== ONESHOT ==='
systemctl status bc250-vcn-verify-once.service --no-pager -l 2>&1 | head -80 || true

echo '=== LOG ==='
sudo journalctl -b -k --no-pager \
  | grep -iE 'bc250|vcn|uvd|jpeg|ring.*(test|timeout|fail)|amdgpu.*(error|fail|timeout)|firmware' \
  | tail -160 || true
