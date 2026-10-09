#!/usr/bin/env bash
set -uo pipefail
PY=/home/OWNER/.local/share/pipx/venvs/bc250-smu-oc/bin/python
OUT=/tmp/smu_probe_root.out
rm -f "$OUT"
echo "=== id ==="; id
echo "=== config perms ==="; ls -la /sys/bus/pci/devices/0000:00:00.0/config
echo "=== python version ==="
"$PY" --version
echo "=== run smu_probe.py ==="
"$PY" /tmp/smu_probe.py > "$OUT" 2>&1
echo "rc=$?"
echo "=== output ==="
cat "$OUT"
