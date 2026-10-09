#!/bin/bash
set -x
echo "=== remove amdgpu ==="
sudo modprobe -r amdgpu
echo "removed rc=$?"
echo "=== lsmod amdgpu ==="
lsmod | grep amdgpu || echo "amdgpu NOT loaded"
echo "=== SMU test (no amdgpu) ==="
SP=~/.local/share/pipx/venvs/bc250-smu-oc
sudo $SP/bin/python - <<'PY'
import sys
sys.path.insert(0, "/home/OWNER/.local/share/pipx/venvs/bc250-smu-oc/lib/python3.14/site-packages")
from bc250_smu import Bc250Smu
s = Bc250Smu(bdf="0000:01:00.0")
for name, fn in [
    ("test_message", lambda: s.check_test_message()),
    ("q3_0x47", lambda: hex(s.q3_0x47_return_status_0xfe())),
    ("q3_0x48", lambda: hex(s.q3_0x48_return_status_0xfe())),
    ("q3_0x98", lambda: s._q3_0x98()),
    ("q2_0x03", lambda: s.q2_0x03()),
]:
    try:
        print(f"{name}:", fn())
    except Exception as e:
        print(f"{name} ERR:", repr(e))
s.close()
PY
echo "=== re-add amdgpu ==="
sudo modprobe amdgpu
echo "added rc=$?"
echo "=== done ==="
