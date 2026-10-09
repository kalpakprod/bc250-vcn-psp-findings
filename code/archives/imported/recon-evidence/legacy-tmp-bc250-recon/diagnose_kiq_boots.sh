#!/usr/bin/env bash
set -u

echo '=== BOOTS ==='
sudo journalctl --list-boots --no-pager | tail -12

for boot in 0 -1 -2 -3 -4 -5 -6 -7; do
  echo "=== BOOT $boot ==="
  sudo journalctl -b "$boot" -k --no-pager 2>/dev/null \
    | grep -iE 'Linux version|Command line:|bc250-40cu|detected ip block.*vcn|Found VCN firmware|firmware load|kiq ring|KCQ enable|amdgpu_device_ip_init|probe with driver amdgpu|Initialized amdgpu|fb0: amdgpudrmfb|drm.*Initialized amdgpu' \
    | tail -80 || true
done

echo '=== 40CU PATCH ==='
sed -n '1,240p' /home/OWNER/linux-cachyos-bc250/patches/kernel-7.2/0008-bc250-40cu.patch

echo '=== CMDLINE DROPIN ==='
sudo cat /etc/limine-entry-tool.d/40-bc250-vcn.conf 2>/dev/null || true

echo '=== MODPROBE 40CU ==='
sudo cat /etc/modprobe.d/bc250-40cu.conf 2>/dev/null || true
