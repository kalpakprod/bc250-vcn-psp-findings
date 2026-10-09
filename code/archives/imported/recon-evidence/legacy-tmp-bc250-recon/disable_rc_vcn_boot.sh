#!/usr/bin/env bash
set -Eeuo pipefail

config=/boot/limine.conf
dropin=/etc/limine-entry-tool.d/90-bc250-vcn-test.conf

sudo rm -f -- "$dropin"
python3 - "$config" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
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
        args = stripped.split()[1:]
        args = [arg for arg in args if arg not in {
            "amdgpu.bc250_vcn=1", "amdgpu.fw_load_type=0"
        }]
        lines[index] = f"{indent}cmdline: {' '.join(args)}"
        replaced = True
        break
if not replaced:
    raise SystemExit("top-level linux-cachyos-rc-bc250 cmdline not found")
path.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY

for destination in \
  /boot/EFI/limine/limine.conf \
  /run/media/steammachine/BC250VCN/limine.conf \
  /run/media/steammachine/BC250VCN/EFI/limine/limine.conf; do
  [[ -f "$destination" ]] \
    && sudo install -m 0644 "$config" "$destination"
done

awk '
  /^[[:space:]]*\/\/linux-cachyos-rc-bc250[[:space:]]*$/ {found=1; next}
  found && /^[[:space:]]*cmdline:/ {print; exit}
' "$config"
