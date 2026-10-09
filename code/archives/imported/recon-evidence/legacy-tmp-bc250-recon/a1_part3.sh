#!/usr/bin/env bash
set +e
OUT=/tmp/a1_part3.out
{
echo "=== PART3 firmware/services/smu ==="
echo "--- cyan_skillfish blobs ---"
ls -la /lib/firmware/amdgpu/cyan_skillfish* 2>/dev/null
echo "--- vcn blobs ---"
ls -la /lib/firmware/amdgpu/*vcn* 2>/dev/null | head -30
echo "--- find skillfish/cyan vcn ---"
timeout 15 sudo -n find /lib/firmware /usr/lib/firmware -iname '*skillfish*vcn*' 2>/dev/null
timeout 15 sudo -n find /lib/firmware /usr/lib/firmware -iname '*cyan*vcn*' 2>/dev/null
echo "--- services ---"
systemctl is-active bc250-cu-layout.service bc250-cpu-oc.service bc250-gpu-fixed.service bc250-netconsole.service bc250-telemetry.service 2>&1
systemctl list-units --type=service --all 2>/dev/null | grep -iE 'bc250|smu|gpu|fan|netconsole|telemetry' || true
echo "--- gpu fixed conf ---"
timeout 2 sudo -n cat /etc/bc250-gpu-fixed.conf 2>/dev/null || echo no_conf
echo "--- SMU safe reads ---"
timeout 25 sudo -n python3 - <<'PY'
import sys
try:
    from bc250_smu.api import Bc250Smu
except Exception as e:
    print('import_fail', e); sys.exit(0)
s=Bc250Smu(use_flock=True, allow_queue0=True)
try:
    s.__enter__()
except Exception as e:
    print('enter', type(e).__name__, e)
for name in ['check_test_message','get_smu_version','get_enabled_smu_features','query_active_wgp','query_gfxclk']:
    fn=getattr(s,name,None)
    if not fn:
        print(name,'ABSENT'); continue
    try:
        print(name, '=', fn())
    except Exception as e:
        print(name,'ERR',type(e).__name__,e)
names=sorted(n for n in dir(s) if not n.startswith('_') and callable(getattr(s,n,None)))
print('methods', ','.join(names))
try:
    s.__exit__(None,None,None)
except Exception:
    pass
PY
echo "=== PART3 DONE ==="
} >"$OUT" 2>&1
echo wrote:$OUT
wc -c "$OUT"
tail -50 "$OUT"
