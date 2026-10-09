#!/usr/bin/env bash
set +e
OUT=/tmp/a1_part7.out
{
echo "=== PART7 final gaps ==="
# SMU alone, no concurrent metrics service interference note
echo "--- stop? NO writes; just retry SMU reads with flock ---"
PY=/home/OWNER/.local/share/pipx/venvs/bc250-smu-oc/bin/python
timeout 30 sudo -n "$PY" - <<'PY'
from bc250_smu.api import Bc250Smu
import time
s=Bc250Smu(use_flock=True, allow_queue0=True)
for i in range(3):
    try:
        print('try',i,'test',s.check_test_message())
        break
    except Exception as e:
        print('try',i,'test ERR',e); time.sleep(0.2)
for name in ['get_enabled_smu_features','query_active_wgp','query_gfxclk','get_gfx_frequency','get_gfx_vid','test_message']:
    if not hasattr(s,name):
        continue
    try:
        print(name,'=',getattr(s,name)())
    except Exception as e:
        print(name,'ERR',e)
# device name q2
try:
    print('q2_name', s.q2_0x04_get_device_name())
except Exception as e:
    print('q2_name ERR',e)
s.close()
PY
echo "--- patches mentioning vcn ---"
timeout 20 grep -RIn -E "\bvcn\b|VCN|vclk|dclk|PowerUpVcn|vcn_v2" \
  /home/OWNER/linux-cachyos-bc250/patches 2>/dev/null | head -40 || echo none
echo "--- kernel-7.2 patch list ---"
ls -1 /home/OWNER/linux-cachyos-bc250/patches/kernel-7.2/
echo "--- mesa patch list ---"
ls -1 /home/OWNER/linux-cachyos-bc250/patches/mesa /home/OWNER/linux-cachyos-bc250/patches/mesa-git 2>/dev/null
echo "--- amdgpu.ko strings ---"
MOD=/lib/modules/$(uname -r)
echo MOD=$MOD
ls "$MOD/kernel/drivers/gpu/drm/amd/amdgpu" 2>/dev/null | head
KO=$(ls "$MOD"/kernel/drivers/gpu/drm/amd/amdgpu/amdgpu.ko* 2>/dev/null | head -1)
echo KO=$KO
if [ -n "$KO" ]; then
  case "$KO" in
    *.zst) timeout 20 zstdcat "$KO" 2>/dev/null | strings | grep -iE 'cyan_skillfish|vcn_v2|PowerUpVcn|CHIP_CYAN|VCN_' | sort -u | head -50 ;;
    *) timeout 20 strings "$KO" | grep -iE 'cyan_skillfish|vcn_v2|PowerUpVcn|CHIP_CYAN|VCN_' | sort -u | head -50 ;;
  esac
fi
echo "--- hwmon ---"
for h in /sys/class/drm/card1/device/hwmon/hwmon*; do
  [ -d "$h" ]||continue
  echo name=$(timeout 1 cat "$h/name" 2>/dev/null)
  for x in "$h"/temp*_input "$h"/freq*_input "$h"/power1_average "$h"/power1_cap "$h"/fan*_input; do
    [ -e "$x" ]||continue
    echo "$(basename "$x")=$(timeout 1 cat "$x" 2>/dev/null)"
  done
done
echo "--- drm clients ---"
timeout 2 cat /sys/class/drm/card1/device/client* 2>/dev/null | head
ls /dev/dri/
echo "--- no video nodes confirm ---"
ls -l /dev/video* /dev/media* 2>&1 | head
echo "=== PART7 DONE ==="
} >"$OUT" 2>&1
echo wrote:$OUT
wc -c "$OUT"
