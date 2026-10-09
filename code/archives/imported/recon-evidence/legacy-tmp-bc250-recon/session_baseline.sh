#!/bin/bash
set -x
echo "=== 0.1 BIOS / kernel / netconsole ==="
cat /sys/class/dmi/id/bios_version
uname -r
systemctl is-active bc250-netconsole
echo "--- netconsole target ---"
systemctl cat bc250-netconsole 2>/dev/null | grep -iE 'destination|src|udp|6666' | head
echo "--- netconsole pulse (ss udp) ---"
ss -u -n -a 2>/dev/null | grep -i 6666 | head
echo "=== SMU version / test ==="
SP=~/.local/share/pipx/venvs/bc250-smu-oc
$SP/bin/python - <<'PY'
import sys
sys.path.insert(0, "/home/OWNER/.local/share/pipx/venvs/bc250-smu-oc/lib/python3.14/site-packages")
from bc250_smu import Bc250Smu
s = Bc250Smu(bdf="0000:01:00.0")
try:
    print("test_message:", s.check_test_message())
except Exception as e:
    print("test_message ERR:", e)
try:
    print("q3_0x47 status:", hex(s.q3_0x47_return_status_0xfe()))
except Exception as e:
    print("q3_0x47 ERR:", e)
try:
    print("q3_0x48 status:", hex(s.q3_0x48_return_status_0xfe()))
except Exception as e:
    print("q3_0x48 ERR:", e)
s.close()
PY
echo "=== 0.3 gpu_metrics (raw) ==="
cat /sys/kernel/debug/dri0/amdgpu_gpu_metrics 2>/dev/null | head -40
echo "=== CU / features ==="
cat /sys/kernel/debug/dri0/amdgpu_pm_info 2>/dev/null | head -30
echo "=== done ==="
