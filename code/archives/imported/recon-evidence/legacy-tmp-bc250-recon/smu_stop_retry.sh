#!/bin/bash
set -x
SP=~/.local/share/pipx/venvs/bc250-smu-oc
echo "=== bc250 services status (before) ==="
systemctl list-units --type=service --all 2>/dev/null | grep -iE 'bc250|gpu|metrics|watchdog|pwr'
echo "=== netconsole script (target) ==="
cat /usr/local/libexec/bc250-netconsole.sh 2>/dev/null | grep -iE 'udp|6666|destination|src|IP|HOST|OFFBOX' | head
echo "=== STOP contenders ==="
sudo systemctl stop bc250-metrics bc250-gpu-watchdog bc250-pwrwatch 2>&1
echo "stopped rc=$?"
echo "=== SMU test (sudo, AFTER stop) ==="
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
echo "=== done ==="
