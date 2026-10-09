#!/usr/bin/env bash
set -Eeuo pipefail

if (( EUID != 0 )); then
  echo "run as root" >&2
  exit 1
fi

DROPIN=/etc/limine-entry-tool.d/90-bc250-vcn-test.conf
KERNEL_PKG=linux-cachyos-rc-bc250
HEADERS_PKG=linux-cachyos-rc-bc250-headers

if [[ $(uname -r) == *cachyos-rc-bc250* ]]; then
  echo "boot the known-good linux-cachyos-bc250 entry before rollback" >&2
  exit 1
fi

rm -f -- "$DROPIN"

installed=()
pacman -Qq "$KERNEL_PKG" >/dev/null 2>&1 && installed+=("$KERNEL_PKG")
pacman -Qq "$HEADERS_PKG" >/dev/null 2>&1 && installed+=("$HEADERS_PKG")
if (( ${#installed[@]} )); then
  pacman -R --noconfirm "${installed[@]}"
fi

limine-entry-tool --remove-kernel "$KERNEL_PKG" --keep-files || true
for dest in \
  /boot/EFI/limine/limine.conf \
  /run/media/steammachine/BC250VCN/limine.conf \
  /run/media/steammachine/BC250VCN/EFI/limine/limine.conf; do
  [[ -f "$dest" ]] && install -m 0644 /boot/limine.conf "$dest"
done
printf '%s\n' "rollback complete; running kernel: $(uname -r)"
