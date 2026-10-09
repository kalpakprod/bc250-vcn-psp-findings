#!/usr/bin/env bash
set -euo pipefail

disk=/dev/sda
expected_serial=9872541035367756565
mountpoint=/mnt/bc250vcn

[[ "$(lsblk -dn -o TRAN "$disk" | xargs)" == usb ]]
[[ "$(lsblk -dn -o RM "$disk" | xargs)" == 1 ]]
[[ "$(lsblk -dn -o SERIAL "$disk" | xargs)" == "$expected_serial" ]]

size=$(lsblk -dn -b -o SIZE "$disk" | xargs)
(( size >= 3900000000 && size <= 4100000000 ))

root_source=$(findmnt -no SOURCE /)
[[ "$root_source" != /dev/sda* ]]

umount /dev/sda1 2>/dev/null || true
wipefs -a "$disk"
printf 'label: gpt\n, , U, *\n' | sfdisk "$disk"
partprobe "$disk"
udevadm settle
mkfs.fat -F 32 -n BC250VCN /dev/sda1
mkdir -p "$mountpoint"
mount /dev/sda1 "$mountpoint"
mkdir -p "$mountpoint/EFI/BOOT" "$mountpoint/results"
sync

lsblk -f "$disk"
sfdisk -d "$disk"
