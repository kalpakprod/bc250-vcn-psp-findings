#!/usr/bin/env bash
set -euo pipefail

USB_MOUNT=$(lsblk -no MOUNTPOINT /dev/sda1 | head -n1 || true)
if [ -z "$USB_MOUNT" ]; then
    USB_MOUNT="/mnt/bc250vcn"
    sudo mkdir -p "$USB_MOUNT"
    sudo mount /dev/sda1 "$USB_MOUNT"
fi

echo "USB_MOUNT=$USB_MOUNT"
sudo cp /tmp/Bc250VcnProbeApp.efi "$USB_MOUNT/Bc250VcnProbeApp.efi"
sudo mkdir -p "$USB_MOUNT/EFI/BOOT"
sudo cp /tmp/Bc250VcnProbeApp.efi "$USB_MOUNT/EFI/BOOT/BOOTX64.EFI"
sync
cd "$USB_MOUNT"
sha256sum Bc250VcnProbeApp.efi EFI/BOOT/BOOTX64.EFI
