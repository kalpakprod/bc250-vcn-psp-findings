#!/usr/bin/env bash
set -Eeuo pipefail

echo '=== STABLE MODULE ==='
modinfo -k 7.2.0-1.1-cachyos-bc250 amdgpu \
  | grep -E '^filename:|^srcversion:|^vermagic:'

echo '=== STABLE CMDLINE ==='
sudo awk '
  /^[[:space:]]*\/\/linux-cachyos-bc250[[:space:]]*$/ {found=1; next}
  found && /^[[:space:]]*cmdline:/ {print; exit}
' /boot/limine.conf

echo '=== INITRAMFS OVERLAY CHECK ==='
if sudo lsinitcpio \
  /boot/37093be247af4335846b136167e6aa31/linux-cachyos-bc250/initramfs \
  | grep -q 'updates/bc250-vcn'; then
  echo OVERLAY_PRESENT
  exit 1
else
  echo OVERLAY_ABSENT
fi

echo '=== CONFIG SYNC ==='
sudo install -m 0644 /boot/limine.conf /boot/EFI/limine/limine.conf
for destination in \
  /run/media/steammachine/BC250VCN/limine.conf \
  /run/media/steammachine/BC250VCN/EFI/limine/limine.conf; do
  [[ -f "$destination" ]] \
    && sudo install -m 0644 /boot/limine.conf "$destination"
done
sudo sha256sum \
  /boot/limine.conf \
  /boot/EFI/limine/limine.conf \
  /run/media/steammachine/BC250VCN/limine.conf \
  /run/media/steammachine/BC250VCN/EFI/limine/limine.conf 2>/dev/null

echo '=== LIVE BOOT ==='
uname -r
cat /proc/cmdline
for parameter in bc250_cc_write_mode bc250_vcn fw_load_type; do
  if [[ -r "/sys/module/amdgpu/parameters/$parameter" ]]; then
    printf '%s=' "$parameter"
    cat "/sys/module/amdgpu/parameters/$parameter"
  else
    echo "$parameter=MISSING"
  fi
done
lspci -nnk -s 01:00.0
ls -l /dev/dri

echo '=== CURRENT-BOOT FATAL GPU FAILURES ==='
if sudo journalctl -b -k --no-pager \
  | grep -iE 'ring kiq.*test failed|KCQ enable failed|hw_init of IP block <gfx_v10_0> failed|amdgpu_device_ip_init failed|Fatal error during GPU init|unknown parameter.*bc250_vcn'; then
  exit 1
else
  echo NONE
fi
