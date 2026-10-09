#!/usr/bin/env bash
set -Eeuo pipefail

if (( EUID != 0 )); then
  echo "run as root" >&2
  exit 1
fi

BUILD_DIR=${1:-/tmp/bc250-vcn-packages}
DROPIN=/etc/limine-entry-tool.d/90-bc250-vcn-test.conf
KERNEL_PKG=linux-cachyos-rc-bc250
HEADERS_PKG=linux-cachyos-rc-bc250-headers

mapfile -t packages < <(find "$BUILD_DIR" -maxdepth 1 -type f \
  \( -name "${KERNEL_PKG}-*.pkg.tar.zst" -o -name "${HEADERS_PKG}-*.pkg.tar.zst" \) \
  -print | sort)

if (( ${#packages[@]} != 2 )); then
  printf 'expected kernel + headers packages, found %d\n' "${#packages[@]}" >&2
  printf '%s\n' "${packages[@]:-}" >&2
  exit 1
fi

if grep -qE '(^| )(amdgpu\.bc250_vcn=1|amdgpu\.fw_load_type=0)( |$)' /proc/cmdline; then
  echo "refusing installation from an already experimental boot" >&2
  exit 1
fi

BASE='quiet nowatchdog splash rw rootflags=subvol=/@ root=UUID=14fe5cec-acf0-4986-8103-251a5706bbac video=DP-1:1920x1080@60 amdgpu.sg_display=0 ttm.pages_limit=1048576 systemd.zram=0 loglevel=0 mitigations=off acpi_enforce_resources=lax'
CMDLINE="$BASE amdgpu.bc250_vcn=1 amdgpu.fw_load_type=0"

install -d -m 0755 "$(dirname "$DROPIN")"
printf 'KERNEL_CMDLINE[linux-cachyos-rc-bc250]+="%s"\n' "$CMDLINE" >"$DROPIN"

pacman -U --needed --noconfirm "${packages[@]}"

pacman -Q "$KERNEL_PKG" "$HEADERS_PKG"
grep -F "cmdline: $CMDLINE" /boot/limine.conf

for dest in \
  /boot/EFI/limine/limine.conf \
  /run/media/steammachine/BC250VCN/limine.conf \
  /run/media/steammachine/BC250VCN/EFI/limine/limine.conf; do
  [[ -f "$dest" ]] && install -m 0644 /boot/limine.conf "$dest"
done

echo "installed test kernel; current kernel unchanged: $(uname -r)"
echo "next boot: start through the BC250VCN USB chainloader, then select $KERNEL_PKG"
