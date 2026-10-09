#!/usr/bin/env bash
set -Eeuo pipefail

label='BC250 NVMe Limine'
loader='\EFI\limine\limine_x64.efi'
state_dir=/var/lib/bc250-vcn

[[ -f /boot/EFI/limine/limine_x64.efi ]] || {
  echo 'ERROR: NVMe Limine EFI image missing' >&2
  exit 1
}

bootnum=$(efibootmgr | awk -v label="$label" '$0 ~ "^Boot[0-9A-Fa-f]{4}\\*? " label "([[:space:]]|$)" {print substr($1, 5, 4); exit}')
if [[ -z "$bootnum" ]]; then
  efibootmgr -c -d /dev/nvme0n1 -p 2 -L "$label" -l "$loader"
  bootnum=$(efibootmgr | awk -v label="$label" '$0 ~ "^Boot[0-9A-Fa-f]{4}\\*? " label "([[:space:]]|$)" {print substr($1, 5, 4); exit}')
fi

[[ "$bootnum" =~ ^[0-9A-Fa-f]{4}$ ]] || {
  echo 'ERROR: failed to resolve NVMe Limine boot entry' >&2
  exit 1
}

mkdir -p "$state_dir"
printf '%s\n' "$bootnum" > "$state_dir/nvme_limine_bootnum"
efibootmgr -n "$bootnum"

echo "BOOTNUM=$bootnum"
efibootmgr -v
