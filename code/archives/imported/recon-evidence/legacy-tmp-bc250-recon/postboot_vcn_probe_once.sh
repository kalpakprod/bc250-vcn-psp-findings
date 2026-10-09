#!/usr/bin/env bash
set -Eeuo pipefail

STATE_DIR=/var/lib/bc250-vcn-probe
OUTPUT=$STATE_DIR/mode1-1.92.out
STATUS=$STATE_DIR/mode1-1.92.status
VERIFY=/usr/local/sbin/verify_vcn_probe_boot.sh
CONFIG=/boot/limine.conf
SAFE_PATH=CachyOS/linux-cachyos-bc250

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
    return 1
  fi
  install -m 0644 "$tmp" "$CONFIG"
  rm -f "$tmp"
  grep -Fxq "default_entry: $value" "$CONFIG"
}

sync_limine_config() {
  local destination mountpoint
  local -a destinations=(/boot/EFI/limine/limine.conf)

  while read -r mountpoint; do
    [[ -n "$mountpoint" ]] || continue
    destinations+=("$mountpoint/limine.conf" "$mountpoint/EFI/limine/limine.conf")
  done < <(findmnt -rn -o TARGET,LABEL | awk '$2 == "BC250VCN" { print $1 }')

  for destination in "${destinations[@]}"; do
    if [[ -f "$destination" ]]; then
      install -m 0644 "$CONFIG" "$destination"
    fi
  done
}

restore_safe_default() {
  local rc=0

  set_default_entry "$SAFE_PATH" || rc=1
  sync_limine_config || rc=1
  systemctl disable bc250-vcn-verify-once.service >/dev/null 2>&1 || rc=1
  return "$rc"
}

install -d -m 0755 "$STATE_DIR"
trap restore_safe_default EXIT

if "$VERIFY" 1 "$OUTPUT"; then
  printf 'PASS %s\n' "$(date --iso-8601=seconds)" >"$STATUS"
else
  rc=$?
  printf 'FAIL rc=%d %s\n' "$rc" "$(date --iso-8601=seconds)" >"$STATUS"
  exit "$rc"
fi
