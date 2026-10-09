#!/usr/bin/env bash
# A1 part9: read metrics/telemetry scripts + safe gpu_metrics parse + module params
set +e
OUT=/tmp/a1_part9.out
{
echo "=== PART9 ts=$(date -Is) ==="

echo "--- libexec listing ---"
ls -la /usr/local/libexec/bc250* /usr/local/bin/bc250* 2>/dev/null

echo "--- metrics.py (full, read-only) ---"
timeout 3 sed -n '1,240p' /usr/local/libexec/bc250-metrics.py 2>/dev/null
echo "--- metrics.py grep vclk/dclk/vcn/smu ---"
timeout 3 grep -nE 'vclk|dclk|VCLK|DCLK|vcn|VCN|smu|feature|wgp|gfx|power|domain' /usr/local/libexec/bc250-metrics.py 2>/dev/null

echo "--- pwrwatch.sh ---"
timeout 3 sed -n '1,120p' /usr/local/libexec/bc250-pwrwatch.sh 2>/dev/null

echo "--- telemetry.sh ---"
timeout 3 sed -n '1,160p' /usr/local/libexec/bc250-telemetry.sh 2>/dev/null
timeout 3 grep -nE 'vclk|dclk|vcn|smu|metrics|gpu' /usr/local/libexec/bc250-telemetry.sh 2>/dev/null

echo "--- gpu-watchdog.sh head ---"
timeout 3 sed -n '1,80p' /usr/local/libexec/bc250-gpu-watchdog.sh 2>/dev/null

echo "--- unit files ExecStart ---"
for u in bc250-metrics bc250-pwrwatch bc250-telemetry bc250-gpu-fixed bc250-netconsole bc250-cu-layout; do
  echo "#### $u ####"
  systemctl cat "$u.service" 2>/dev/null | head -40
done

echo "--- gpu_metrics binary parse (timeout, no pp_dpm) ---"
# structure from amdgpu: first bytes already known from probe_vcn3
# try python struct parse of known cyan_skillfish metrics layout if file readable
timeout 5 sudo -n python3 - <<'PY'
import os, struct, time
path='/sys/class/drm/card1/device/gpu_metrics'
try:
    st=os.stat(path)
    print('stat size', st.st_size, 'mtime', st.st_mtime)
except Exception as e:
    print('stat ERR', e)
# non-blocking open attempt with alarm
import signal
def handler(s,f):
    raise TimeoutError('read timeout')
signal.signal(signal.SIGALRM, handler)
signal.alarm(3)
try:
    with open(path,'rb') as f:
        data=f.read(512)
    signal.alarm(0)
    print('read_bytes', len(data))
    print('hex', data[:64].hex())
    # common header: structure_size u16, format_revision u8, content_revision u8
    if len(data)>=4:
        size, fmt, cont = struct.unpack_from('<HBB', data, 0)
        print(f'hdr size={size} format_rev={fmt} content_rev={cont}')
    # dump as u16 grid for first 128 bytes
    u16s=list(struct.unpack_from('<'+'H'*(min(len(data),128)//2), data, 0))
    print('u16:', ' '.join(f'{x:04x}' for x in u16s[:40]))
    # heuristic: look for plausible MHz values 0..3000 in u16
    cands=[]
    for i,x in enumerate(u16s):
        if x in (0, 1111) or (100 <= x <= 3000):
            cands.append((i,x))
    print('mhz_like_u16_idx', cands[:40])
except Exception as e:
    signal.alarm(0)
    print('gpu_metrics ERR', type(e).__name__, e)
PY

echo "--- debugfs list ---"
timeout 2 ls /sys/kernel/debug/dri 2>/dev/null || echo no_debugfs
for d in /sys/kernel/debug/dri/*; do
  [ -d "$d" ] || continue
  echo DIR=$d
  timeout 2 ls "$d" 2>/dev/null | head -80
done

echo "--- amdgpu params subset ---"
for p in /sys/module/amdgpu/parameters/*; do
  n=$(basename "$p")
  case "$n" in
    *vcn*|*ip*|*psp*|*smu*|*runpm*|*aspm*|*discovery*|*fw*|*mes*|*jpeg*|*uvd*|*vce*)
      echo -n "$n="; timeout 1 cat "$p" 2>/dev/null; echo
      ;;
  esac
done

echo "--- netconsole / log destinations ---"
timeout 2 cat /proc/net/netconsole 2>/dev/null || true
timeout 2 grep -RIn '6666\|netconsole\|192.168' /etc/systemd/system /usr/local/libexec 2>/dev/null | head -20

echo "--- packaging patch vclk/dclk emit context ---"
timeout 5 grep -n -A2 -B2 -E 'vclk|dclk|Vclk|Dclk' \
  /home/OWNER/linux-cachyos-bc250/patches/kernel-7.2/0001-bc250-8core-telemetry-gpu-activity.patch 2>/dev/null | head -80

echo "=== PART9 DONE ==="
} >"$OUT" 2>&1
echo wrote:$OUT
wc -c "$OUT"
