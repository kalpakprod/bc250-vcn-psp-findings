#!/usr/bin/env bash
echo '=== find GPU card (device 0x13fe) ==='
for c in /sys/class/drm/card[0-9]*; do
  dev=$(cat $c/device/dev_id 2>/dev/null); vid=$(cat $c/device/vendor 2>/dev/null)
  echo "$c dev=$dev vid=$vid"
done
echo '=== card0 firmware_info (raw) ==='
cat /sys/class/drm/card0/device/amdgpu_firmware_info 2>/dev/null | head -60 || echo 'NO FILE'
echo '=== card0 ip_blocks (raw) ==='
cat /sys/class/drm/card0/device/amdgpu_info_ip_blocks 2>/dev/null || echo 'NO FILE'
echo '=== dmesg vcn/psp/power/skillfish ==='
dmesg 2>/dev/null | grep -iE 'vcn|psp|skillfish|smu|cyan' | head -40 || echo 'none'
echo '=== smu version / features / wgp ==='
SP=/home/OWNER/.local/share/pipx/venvs/bc250-smu-oc
$SP/bin/python - <<'PY'
import sys
sys.path.insert(0, "/home/OWNER/.local/share/pipx/venvs/bc250-smu-oc/lib/python3.14/site-packages")
from bc250_smu import Bc250Smu
s = Bc250Smu("0000:00:00.0", allow_queue0=True, use_flock=True, timeout=100)
s.check_test_message()
try:
    print("smu_version(0,0x02)=", hex(s.send_message(0,0x02,decode=lambda x:x&0xFFFFFFFF)))
except Exception as e: print("smu_version err", e)
try:
    print("enabled_features(0,0x3D)=", hex(s.send_message(0,0x3D,decode=lambda x:x&0xFFFFFFFF)))
except Exception as e: print("features err", e)
try:
    print("active_wgp(0,0x1E)=", s.send_message(0,0x1E,decode=lambda x:x&0xFFFFFFFF))
except Exception as e: print("wgp err", e)
try:
    print("core_pstate(0,0x0C)=", s.send_message(0,0x0C,arg=0,decode=lambda x:x&0xFFFFFFFF,check_status=False))
except Exception as e: print("pstate err", e)
PY
echo '=== END ==='
