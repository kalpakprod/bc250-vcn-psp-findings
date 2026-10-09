#!/usr/bin/env bash
set -Eeuo pipefail

EXPECTED_RUNNING=7.2.0-1.1-cachyos-bc250
EXPECTED_PACKAGE=7.2.0-1.92
MODE1_PATH=CachyOS/linux-cachyos-vcn-bc250-mode1
SAFE_PATH=CachyOS/linux-cachyos-bc250
CONFIG=/boot/limine.conf
STATE_DIR=/var/lib/bc250-vcn-probe
SERVICE=bc250-vcn-verify-once.service

fail() {
  printf 'VCN probe arm failure: %s\n' "$*" >&2
  exit 1
}

set_default_entry() {
  local value=$1 tmp
  tmp=$(mktemp)
  if ! awk -v value="$value" '
    BEGIN { replaced = 0 }
    /^default_entry:/ && !replaced {
      print "default_entry: " value
      replaced = 1
      next
    }
    { print }
    END {
      if (!replaced)
        print "default_entry: " value
    }
  ' "$CONFIG" >"$tmp"; then
    rm -f "$tmp"
    fail "cannot update default_entry"
  fi
  install -m 0644 "$tmp" "$CONFIG"
  rm -f "$tmp"
  grep -Fxq "default_entry: $value" "$CONFIG" \
    || fail "default_entry verification failed"
}

sync_limine_config() {
  local mountpoint

  [[ -f /boot/EFI/limine/limine.conf ]] \
    || fail "missing NVMe Limine config mirror"
  install -m 0644 "$CONFIG" /boot/EFI/limine/limine.conf
  while read -r mountpoint; do
    [[ -n "$mountpoint" ]] || continue
    [[ -f "$mountpoint/limine.conf" ]] \
      && install -m 0644 "$CONFIG" "$mountpoint/limine.conf"
    [[ -f "$mountpoint/EFI/limine/limine.conf" ]] \
      && install -m 0644 "$CONFIG" "$mountpoint/EFI/limine/limine.conf"
  done < <(findmnt -rn -o TARGET,LABEL | awk '$2 == "BC250VCN" { print $1 }')
}

((EUID == 0)) || fail "run as root"
[[ $(uname -r) == "$EXPECTED_RUNNING" ]] || fail "unexpected running kernel: $(uname -r)"
! grep -qE '(^| )amdgpu\.bc250_vcn_mode=' /proc/cmdline \
  || fail "stock recovery boot unexpectedly has a BC-250 VCN mode"
[[ $(pacman -Q linux-cachyos-vcn-bc250 | awk '{print $2}') == "$EXPECTED_PACKAGE" ]] \
  || fail "probe kernel package is not 1.92"
[[ $(pacman -Q linux-cachyos-vcn-bc250-headers | awk '{print $2}') == "$EXPECTED_PACKAGE" ]] \
  || fail "probe headers package is not 1.92"

[[ $(grep -Ec '^[[:space:]]*//linux-cachyos-vcn-bc250-mode1$' "$CONFIG") == 1 ]] \
  || fail "cannot resolve unique top-level mode 1 menu entry"

install -d -m 0755 "$STATE_DIR"
cp -a "$CONFIG" "$STATE_DIR/limine.conf.before-mode1-once"
install -m 0755 /tmp/verify_vcn_probe_boot.sh /usr/local/sbin/verify_vcn_probe_boot.sh
install -m 0755 /tmp/postboot_vcn_probe_once.sh /usr/local/sbin/postboot_vcn_probe_once.sh
install -m 0644 /tmp/bc250-vcn-verify-once.service /etc/systemd/system/$SERVICE

set_default_entry "$SAFE_PATH"
sync_limine_config
systemctl daemon-reload
systemctl enable "$SERVICE"
systemctl is-enabled "$SERVICE" >/dev/null

printf 'VCN_PROBE_BOOT_ARMED manual_path=%s safe_default=%s release=%s\n' \
  "$MODE1_PATH" "$SAFE_PATH" "$EXPECTED_PACKAGE"
