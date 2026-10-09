#!/usr/bin/env bash
set -uo pipefail
PY=/home/OWNER/.local/share/pipx/venvs/bc250-smu-oc/bin/python
echo "=== amd_psp / amdgpu modules ==="
lsmod | grep -iE "amd_psp|amdgpu|psp"
echo "=== bc250-detect --help ==="
"$PY" -m bc250_detect --help
echo "=== bc250 bins ==="
ls -la /home/OWNER/.local/share/pipx/venvs/bc250-smu-oc/bin/ | grep -iE "bc250|python"
echo "=== amd_psp in kernel? ==="
grep -i psp /boot/config-$(uname -r) 2>/dev/null | head -n 20
echo "DONE2"
