#!/usr/bin/env bash
echo '=== card1 firmware_info (raw) ==='
cat /sys/class/drm/card1/device/amdgpu_firmware_info 2>/dev/null | head -80 || echo 'NO FILE'
echo '=== card1 ip_blocks (raw) ==='
cat /sys/class/drm/card1/device/amdgpu_info_ip_blocks 2>/dev/null | head -60 || echo 'NO FILE'
echo '=== card1 gpu_metrics (hexdump head) ==='
sudo hexdump -C /sys/class/drm/card1/device/gpu_metrics 2>/dev/null | head -20 || echo 'NO METRICS'
echo '=== dmesg vcn/psp/power/skillfish (sudo) ==='
sudo dmesg 2>/dev/null | grep -iE 'vcn|psp|skillfish|smu|cyan|0x13fe' | head -40 || echo 'none'
echo '=== smu queries (sudo) ==='
sudo -n bash -lc '/home/OWNER/.local/share/pipx/venvs/bc250-smu-oc/bin/python - <<PY
import sys
sys.path.insert(0, "/home/OWNER/.local/share/pipx/venvs/bc250-smu-oc/lib/python3.14/site-packages")
from bc250_smu import Bc250Smu
s = Bc250Smu("0000:00:00.0", allow_queue0=True, use_flock=True, timeout=100)
try:
    s.check_test_message(); print("test_message OK")
except Exception as e: print("test_message err:", e)
def q(label, fn):
    try:
        v = fn(); print(label, "=", hex(v) if isinstance(v,int) else v)
    except Exception as e:
        print(label, "ERR:", type(e).__name__, str(e)[:150])
q("smu_version(0,0x02)", lambda: s.send_message(0,0x02,decode=lambda x:x&0xFFFFFFFF))
q("enabled_features(0,0x3D)", lambda: s.send_message(0,0x3D,decode=lambda x:x&0xFFFFFFFF))
q("active_wgp(0,0x1E)", lambda: s.send_message(0,0x1E,decode=lambda x:x&0xFFFFFFFF))
q("core_pstate0(0,0x0C)", lambda: s.send_message(0,0x0C,arg=0,decode=lambda x:x&0xFFFFFFFF,check_status=False))
q("q3_0x98", lambda: s.send_message(3,0x98))
q("q3_0x27_secure", lambda: s.send_message(3,0x27))
q("q3_0x2a_secure", lambda: s.send_message(3,0x2A))
q("q3_0x2b_dat00008b0c", lambda: s.send_message(3,0x2B,arg=0))
PY'
echo '=== END ==='