#!/bin/bash
set -x
SP=~/.local/share/pipx/venvs/bc250-smu-oc
echo "=== netconsole full (target) ==="
systemctl cat bc250-netconsole
echo "=== SMU test (sudo, 01:00.0) ==="
sudo $SP/bin/python - <<'PY'
import sys
sys.path.insert(0, "/home/OWNER/.local/share/pipx/venvs/bc250-smu-oc/lib/python3.14/site-packages")
from bc250_smu import Bc250Smu
s = Bc250Smu(bdf="0000:01:00.0")
checks = [
    ("test_message", lambda: s.check_test_message()),
    ("q3_0x04", lambda: s._q3_0x04()),
    ("q3_0x0a", lambda: s._q3_0x0a()),
    ("q3_0x98", lambda: s._q3_0x98()),
    ("q3_0x47", lambda: hex(s.q3_0x47_return_status_0xfe())),
    ("q3_0x48", lambda: hex(s.q3_0x48_return_status_0xfe())),
    ("q2_0x03", lambda: s.q2_0x03()),
]
for name, fn in checks:
    try:
        print(f"{name}:", fn())
    except Exception as e:
        print(f"{name} ERR:", repr(e))
s.close()
PY
echo "=== gpu_metrics (sudo) ==="
sudo cat /sys/kernel/debug/dri0/amdgpu_gpu_metrics 2>/dev/null | head -40
echo "=== amdgpu_pm_info (sudo) ==="
sudo cat /sys/kernel/debug/dri0/amdgpu_pm_info 2>/dev/null | head -30
echo "=== done ==="
