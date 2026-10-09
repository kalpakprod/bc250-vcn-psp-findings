#!/usr/bin/env bash
set -Eeuo pipefail

config=/boot/limine.conf
dropin=/etc/limine-entry-tool.d/41-bc250-stable-vcn.conf

cmdline=$(awk '
  /^[[:space:]]*\/\/linux-cachyos-bc250[[:space:]]*$/ {in_entry=1; next}
  in_entry && /^[[:space:]]*cmdline:/ {
    sub(/^[[:space:]]*cmdline:[[:space:]]*/, "")
    print
    exit
  }
' "$config")
[[ -n "$cmdline" ]]
cmdline=" ${cmdline} "
cmdline=${cmdline// amdgpu.fw_load_type=0 / }
cmdline=$(xargs <<<"$cmdline")

for arg in amdgpu.bc250_vcn=1; do
  [[ " $cmdline " == *" $arg "* ]] || cmdline+=" $arg"
done

sudo install -d -m 0755 /etc/limine-entry-tool.d
printf 'KERNEL_CMDLINE[linux-cachyos-bc250]+="%s"\n' "$cmdline" \
  | sudo tee "$dropin" >/dev/null

python3 - "$config" "$cmdline" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
cmdline = sys.argv[2]
lines = path.read_text(encoding="utf-8").splitlines()
in_target = False
replaced = False
for index, line in enumerate(lines):
    stripped = line.strip()
    if stripped == "//linux-cachyos-bc250":
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
    raise SystemExit("top-level linux-cachyos-bc250 cmdline not found")
path.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY

for dest in \
  /boot/EFI/limine/limine.conf \
  /run/media/steammachine/BC250VCN/limine.conf \
  /run/media/steammachine/BC250VCN/EFI/limine/limine.conf; do
  [[ -f "$dest" ]] && sudo install -m 0644 /boot/limine.conf "$dest"
done

echo '=== STABLE VCN CMDLINE ==='
awk '
  /^[[:space:]]*\/\/linux-cachyos-bc250[[:space:]]*$/ {in_entry=1; next}
  in_entry && /^[[:space:]]*cmdline:/ {print; exit}
' /boot/limine.conf
