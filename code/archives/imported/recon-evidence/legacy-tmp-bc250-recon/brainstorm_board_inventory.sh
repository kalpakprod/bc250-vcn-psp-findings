#!/usr/bin/env bash
set -u

echo '=== CACHE ==='
lscpu -C 2>/dev/null || lscpu | grep -i cache

echo '=== L3 SYSFS ==='
for dir in /sys/devices/system/cpu/cpu0/cache/index*; do
  printf '%s ' "$dir"
  for name in level type size shared_cpu_list; do
    printf '%s=' "$name"
    cat "$dir/$name" 2>/dev/null || printf '?\n'
  done
done

echo '=== HWMON NAMES ==='
for dir in /sys/class/hwmon/hwmon*; do
  printf '%s name=' "$dir"
  timeout 1 cat "$dir/name" 2>/dev/null || printf 'unreadable\n'
done

echo '=== SENSORS ==='
timeout 5 sensors 2>/dev/null | head -160 || true

echo '=== NCT ==='
lsmod | grep -i nct || true

echo '=== PCI FUNCTIONS ==='
lspci -nn | grep -iE 'audio|multimedia|crypto|usb|vga|display' || true

echo '=== CPU/SMT/CU ==='
nproc
lscpu | grep -E 'CPU\(s\)|Core|Thread|Socket|Model name' || true
cat /sys/class/drm/card1/device/gpu_busy_percent 2>/dev/null || true
