#!/usr/bin/env bash
set +e
OUT=/tmp/a1_part5.out
{
echo "=== PART5 targeted ==="
echo "--- KSRC tree ---"
KSRC=/home/OWNER/linux-cachyos-bc250
ls -la "$KSRC" 2>/dev/null | head -30
ls -la "$KSRC/drivers/gpu/drm/amd/amdgpu" 2>/dev/null | head -20
echo "soc15 exists?"; ls -la "$KSRC/drivers/gpu/drm/amd/amdgpu/soc15.c" 2>/dev/null
echo "--- find cyan/vcn in KSRC (names) ---"
timeout 30 find "$KSRC/drivers/gpu/drm/amd" -iname '*cyan*' 2>/dev/null | head
timeout 30 find "$KSRC/drivers/gpu/drm/amd" -iname '*vcn*' 2>/dev/null | head -40
echo "--- rg cyan in amdgpu (if rg) ---"
if command -v rg >/dev/null; then
  timeout 40 rg -n "cyan_skillfish|CYAN_SKILLFISH|CHIP_CYAN_SKILLFISH|vcn_v2_0" "$KSRC/drivers/gpu/drm/amd" -g'*.c' -g'*.h' 2>/dev/null | head -80
else
  timeout 40 grep -RIn "cyan_skillfish\|CYAN_SKILLFISH\|CHIP_CYAN\|vcn_v2_0" "$KSRC/drivers/gpu/drm/amd/amdgpu" 2>/dev/null | head -80
fi
echo "--- SMU via pipx venv ---"
PY=/home/OWNER/.local/share/pipx/venvs/bc250-smu-oc/bin/python
ls -la "$PY" 2>/dev/null
timeout 25 sudo -n "$PY" - <<'PY'
from bc250_smu.api import Bc250Smu
s=Bc250Smu(use_flock=True, allow_queue0=True)
s.__enter__()
def c(n,f):
    try: print(n,'=',f())
    except Exception as e: print(n,'ERR',type(e).__name__,e)
c('test', s.check_test_message)
for n in ['get_smu_version','get_enabled_smu_features','query_active_wgp','query_gfxclk','get_enabled_smu_features']:
    if hasattr(s,n): c(n, getattr(s,n))
# try common attrs
for n in sorted(dir(s)):
    if n.startswith('_'): continue
    a=getattr(s,n)
    if callable(a):
        pass
    else:
        try:
            print('attr',n,'=',a)
        except Exception:
            pass
print('METHODS', ','.join(sorted(n for n in dir(s) if not n.startswith('_') and callable(getattr(s,n)))))
# dump q0/q3 method names from modules
import bc250_smu.api_q0 as q0, bc250_smu.api_q3 as q3, bc250_smu.api as api
print('Q0', ','.join(sorted(x for x in dir(q0) if not x.startswith('_'))))
print('Q3', ','.join(sorted(x for x in dir(q3) if not x.startswith('_'))))
print('API_MOD', ','.join(sorted(x for x in dir(api) if not x.startswith('_'))))
s.__exit__(None,None,None)
PY
echo "--- api.py head / msg constants ---"
timeout 5 sed -n '1,200p' /home/OWNER/.local/share/pipx/venvs/bc250-smu-oc/lib/python3.14/site-packages/bc250_smu/api.py 2>/dev/null
echo "--- grep VCN/power/domain in smu pkg ---"
timeout 10 grep -RIn -E "VCN|vclk|dclk|power.?domain|domain.?6|PowerUp|0x16|0x17|0x18" \
  /home/OWNER/.local/share/pipx/venvs/bc250-smu-oc/lib/python3.14/site-packages 2>/dev/null | head -40
echo "--- safe hwmon only ---"
for h in /sys/class/drm/card1/device/hwmon/hwmon*; do
  [ -d "$h" ] || continue
  echo HWMON=$h
  timeout 1 cat "$h/name" 2>/dev/null; echo
  for x in "$h"/temp*_input "$h"/freq*_input "$h"/power1_average "$h"/power1_cap; do
    [ -e "$x" ] || continue
    echo "$(basename "$x")=$(timeout 1 cat "$x" 2>/dev/null)"
  done
done
echo "--- debugfs list (no read of hangy nodes) ---"
timeout 2 ls /sys/kernel/debug/dri 2>/dev/null || echo no_debugfs_dri
timeout 2 ls /sys/kernel/debug/dri/1 2>/dev/null | head -40 || true
echo "--- mesa ---"
ls -la /opt/bc250-gfx1013 2>/dev/null | head
ls /usr/share/vulkan/icd.d 2>/dev/null
echo "=== PART5 DONE ==="
} >"$OUT" 2>&1
echo wrote:$OUT
wc -c "$OUT"
