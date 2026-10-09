#!/usr/bin/env bash
set -Eeuo pipefail

if (( EUID != 0 )); then
  echo "run as root" >&2
  exit 1
fi

DROPIN=/etc/limine-entry-tool.d/90-bc250-vcn-test.conf
CONFIG=/boot/limine.conf
BACKUP=/boot/limine.conf.bc250-vcn-pre-cmdline
BASE='quiet nowatchdog splash rw rootflags=subvol=/@ root=UUID=14fe5cec-acf0-4986-8103-251a5706bbac video=DP-1:1920x1080@60 amdgpu.sg_display=0 ttm.pages_limit=1048576 systemd.zram=0 loglevel=0 mitigations=off acpi_enforce_resources=lax'
CMDLINE="$BASE amdgpu.bc250_vcn=1 amdgpu.fw_load_type=0"

install -d -m 0755 "$(dirname "$DROPIN")"
printf 'KERNEL_CMDLINE[linux-cachyos-rc-bc250]+="%s"\n' "$CMDLINE" >"$DROPIN"
[[ -e "$BACKUP" ]] || cp -a -- "$CONFIG" "$BACKUP"

python3 - "$CONFIG" "$CMDLINE" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
cmdline = sys.argv[2]
lines = path.read_text(encoding="utf-8").splitlines()
in_target = False
replaced = False

for index, line in enumerate(lines):
    stripped = line.strip()
    if stripped == "//linux-cachyos-rc-bc250":
        in_target = True
        continue
    if in_target and stripped.startswith("/"):
        break
    if in_target and stripped.startswith("cmdline:"):
        indent = line[: len(line) - len(line.lstrip())]
        lines[index] = f"{indent}cmdline: {cmdline}"
        replaced = True
        break

if not replaced:
    raise SystemExit("top-level linux-cachyos-rc-bc250 cmdline not found")

path.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY

grep -F "cmdline: $CMDLINE" "$CONFIG"
grep -F "KERNEL_CMDLINE[linux-cachyos-rc-bc250]" "$DROPIN"

# Sync to EFI and USB limine configs if they exist
for dest in "/boot/EFI/limine/limine.conf" "/run/media/steammachine/BC250VCN/limine.conf" "/run/media/steammachine/BC250VCN/EFI/limine/limine.conf" "/mnt/BC250VCN/limine.conf" "/mnt/BC250VCN/EFI/limine/limine.conf"; do
  if [[ -f "$dest" ]]; then
    echo "Syncing $CONFIG -> $dest"
    install -m 0644 "$CONFIG" "$dest"
  fi
done
