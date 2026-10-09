#!/usr/bin/env bash
set -euo pipefail

disk=/dev/sda
partition=/dev/sda1
expected_serial=9872541035367756565
mountpoint=/mnt/bc250vcn
source_efi=/tmp/Bc250VcnProbeApp.efi

[[ "$(lsblk -dn -o TRAN "$disk" | xargs)" == usb ]]
[[ "$(lsblk -dn -o RM "$disk" | xargs)" == 1 ]]
[[ "$(lsblk -dn -o SERIAL "$disk" | xargs)" == "$expected_serial" ]]
[[ "$(lsblk -dn -o FSTYPE "$partition" | xargs)" == vfat ]]
[[ "$(lsblk -dn -o LABEL "$partition" | xargs)" == BC250VCN ]]
[[ -s "$source_efi" ]]

mkdir -p "$mountpoint"
mountpoint -q "$mountpoint" || mount "$partition" "$mountpoint"
mkdir -p "$mountpoint/EFI/BOOT" "$mountpoint/results"
install -m 0644 "$source_efi" "$mountpoint/Bc250VcnProbeApp.efi"
install -m 0644 "$source_efi" "$mountpoint/EFI/BOOT/BOOTX64.EFI"
sha256sum "$mountpoint/Bc250VcnProbeApp.efi" "$mountpoint/EFI/BOOT/BOOTX64.EFI" > "$mountpoint/SHA256SUMS.txt"
sync
sha256sum -c "$mountpoint/SHA256SUMS.txt"
find "$mountpoint" -maxdepth 3 -type f -printf '%P %s bytes\n' | sort
umount "$mountpoint"
