#!/usr/bin/env bash
set -Eeuo pipefail

if ((EUID != 0)); then
  echo "run as root" >&2
  exit 1
fi

KERNEL_PACKAGE=linux-cachyos-vcn-bc250
HEADERS_PACKAGE=linux-cachyos-vcn-bc250-headers
MODE0_NAME=${KERNEL_PACKAGE}-mode0
MODE1_NAME=${KERNEL_PACKAGE}-mode1
DROPIN=/etc/limine-entry-tool.d/90-bc250-vcn-probe.conf
STATE_DIR=/var/lib/bc250-vcn-probe

sync_limine_config() {
  local destination mountpoint
  local -a destinations=(/boot/EFI/limine/limine.conf)

  while read -r mountpoint; do
    [[ -n "$mountpoint" ]] || continue
    destinations+=("$mountpoint/limine.conf" "$mountpoint/EFI/limine/limine.conf")
  done < <(findmnt -rn -o TARGET,LABEL | awk '$2 == "BC250VCN" { print $1 }')

  destinations+=(
    /run/media/steammachine/BC250VCN/limine.conf
    /run/media/steammachine/BC250VCN/EFI/limine/limine.conf
    /mnt/BC250VCN/limine.conf
    /mnt/BC250VCN/EFI/limine/limine.conf
  )

  for destination in "${destinations[@]}"; do
    if [[ -f "$destination" ]]; then
      install -m 0644 /boot/limine.conf "$destination"
    fi
  done
}

if [[ $(uname -r) != 7.2.0-1.1-cachyos-bc250 ]]; then
  echo "boot exact stock release 7.2.0-1.1-cachyos-bc250 before rollback; running $(uname -r)" >&2
  exit 1
fi

pacman -Q linux-cachyos-bc250 >/dev/null \
  || { echo "stock linux-cachyos-bc250 package is not installed" >&2; exit 1; }

limine-entry-tool --remove-kernel "$MODE0_NAME" --keep-files --quiet || true
limine-entry-tool --remove-kernel "$MODE1_NAME" --keep-files --quiet || true
limine-entry-tool --remove-kernel "$KERNEL_PACKAGE" --keep-files --quiet || true

if [[ -f "$STATE_DIR/90-bc250-vcn-probe.conf.before-install" ]]; then
  install -m 0644 "$STATE_DIR/90-bc250-vcn-probe.conf.before-install" "$DROPIN"
else
  rm -f -- "$DROPIN"
fi

installed=()
pacman -Qq "$KERNEL_PACKAGE" >/dev/null 2>&1 && installed+=("$KERNEL_PACKAGE")
pacman -Qq "$HEADERS_PACKAGE" >/dev/null 2>&1 && installed+=("$HEADERS_PACKAGE")
if ((${#installed[@]})); then
  pacman -R --noconfirm "${installed[@]}"
fi

sync_limine_config
pacman -Q linux-cachyos-bc250 >/dev/null
[[ $(uname -r) == 7.2.0-1.1-cachyos-bc250 ]] \
  || { echo "unexpected running kernel after rollback: $(uname -r)" >&2; exit 1; }

printf 'VCN_PROBE_ROLLBACK_PASS running=%s\n' "$(uname -r)"
