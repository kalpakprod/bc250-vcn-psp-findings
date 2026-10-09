#!/usr/bin/env bash
set +e
OUT=/tmp/a1_part6.out
{
echo "=== PART6 SMU+patches+ip ==="
PKG=/home/OWNER/.local/share/pipx/venvs/bc250-smu-oc/lib/python3.14/site-packages
PY=/home/OWNER/.local/share/pipx/venvs/bc250-smu-oc/bin/python
echo "--- list queue mixins methods via python ---"
timeout 20 sudo -n "$PY" - <<'PY'
from bc250_smu.api import Bc250Smu
s=Bc250Smu(use_flock=True, allow_queue0=True)
# open transport if needed
if hasattr(s,'_transport'):
    try: s._transport.open()
    except Exception as e: print('transport_open',type(e).__name__,e)
methods=sorted(n for n in dir(s) if not n.startswith('_') and callable(getattr(s,n)))
print('METHODS_COUNT',len(methods))
print('METHODS',','.join(methods))
# safe known reads from earlier probe_vcn3
for name in ['check_test_message','get_smu_version','get_enabled_smu_features','query_active_wgp','query_gfxclk','get_gfx_clock','get_enabled_features']:
    if hasattr(s,name):
        try:
            print(name,'=',getattr(s,name)())
        except Exception as e:
            print(name,'ERR',type(e).__name__,e)
# try send helpers existence
for name in methods:
    if any(k in name.lower() for k in ['vcn','vclk','dclk','power','domain','feature','version','test','wgp','gfx']):
        print('CAND',name)
PY
echo "--- sed api_q0/q3 method defs ---"
timeout 5 grep -nE "def |0x|MSG|msg" "$PKG/bc250_smu/api_q0.py" 2>/dev/null | head -80
echo "---- q3 ----"
timeout 5 grep -nE "def |0x|MSG|msg" "$PKG/bc250_smu/api_q3.py" 2>/dev/null | head -80
echo "---- mailbox ----"
timeout 5 sed -n '1,160p' "$PKG/bc250_smu/mailbox.py" 2>/dev/null
echo "--- packaging patches list ---"
KSRC=/home/OWNER/linux-cachyos-bc250
ls -la "$KSRC/patches" 2>/dev/null
timeout 10 find "$KSRC/patches" -type f 2>/dev/null | head -80
echo "--- grep vcn/cyan in patches+scripts+README ---"
timeout 15 grep -RIn -E "vcn|VCN|cyan_skillfish|skillfish" "$KSRC/patches" "$KSRC/scripts" "$KSRC/README.md" 2>/dev/null | head -60
echo "--- installed kernel modules path ---"
MODDIR=/lib/modules/$(uname -r)
echo MODDIR=$MODDIR
ls "$MODDIR/kernel/drivers/gpu/drm/amd/amdgpu" 2>/dev/null | head -40
timeout 10 strings "$MODDIR/kernel/drivers/gpu/drm/amd/amdgpu/amdgpu.ko"* 2>/dev/null | grep -iE "cyan_skillfish|vcn_v2|PowerUpVcn|CHIP_CYAN" | sort -u | head -40
# zstd ko?
ls "$MODDIR/kernel/drivers/gpu/drm/amd/amdgpu/" 2>/dev/null | head
echo "--- ip discovery via debugfs name list only ---"
timeout 2 ls /sys/kernel/debug/dri 2>/dev/null
for d in /sys/kernel/debug/dri/*; do
  [ -d "$d" ] || continue
  echo DIR=$d
  timeout 2 ls "$d" 2>/dev/null | head -50
done
echo "--- hwmon ---"
for h in /sys/class/drm/card1/device/hwmon/hwmon*; do
  [ -d "$h" ]||continue
  echo name=$(timeout 1 cat $h/name)
  for x in $h/temp*_input $h/freq*_input $h/power1_average $h/power1_cap; do
    [ -e $x ]||continue
    echo $(basename $x)=$(timeout 1 cat $x)
  done
done
echo "=== PART6 DONE ==="
} >"$OUT" 2>&1
echo wrote:$OUT
wc -c "$OUT"
