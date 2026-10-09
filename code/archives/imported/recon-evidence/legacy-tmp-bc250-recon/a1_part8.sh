#!/usr/bin/env bash
# A1 follow-up read-only: SMU snapshot, telemetry vclk/dclk, package surface, no writes
set +e
OUT=/tmp/a1_part8.out
PY=/home/OWNER/.local/share/pipx/venvs/bc250-smu-oc/bin/python
PKG=/home/OWNER/.local/share/pipx/venvs/bc250-smu-oc/lib/python3.14/site-packages
{
echo "=== PART8 ts=$(date -Is) ==="
echo "--- concurrent SMU consumers (status only) ---"
systemctl is-active bc250-metrics.service bc250-pwrwatch.service bc250-gpu-fixed.service bc250-cu-layout.service 2>&1
systemctl show bc250-metrics.service -p ActiveState -p SubState -p NRestarts -p ExecMainStatus 2>/dev/null
ps aux | grep -iE 'bc250|smu|metrics|pwrwatch|governor' | grep -v grep | head -40

echo
echo "--- prior successful probe snapshots (local /tmp) ---"
for f in /tmp/probe_vcn3.out /tmp/probe_vcn2.out /tmp/probe_vcn.out /tmp/smu_probe.out /tmp/smu_probe_root.out; do
  if [ -f "$f" ]; then
    echo "#### $f ####"
    cat "$f"
    echo
  fi
done

echo
echo "--- SMU read-only with flock + retries (NO service stop) ---"
timeout 45 sudo -n "$PY" - <<'PY'
import time, traceback
from bc250_smu.api import Bc250Smu

def try_call(s, label, fn, *a, **k):
    for i in range(5):
        try:
            r = fn(*a, **k)
            print(f"{label} OK try={i} val={r!r}")
            return r
        except Exception as e:
            print(f"{label} try={i} ERR {e}")
            time.sleep(0.15 + i * 0.1)
    return None

s = Bc250Smu(use_flock=True, allow_queue0=True, timeout=200)
# known-safe reads only
try_call(s, "check_test_message", s.check_test_message)
# version via private if public missing
if hasattr(s, "get_smu_version"):
    try_call(s, "get_smu_version", s.get_smu_version)
elif hasattr(s, "_get_smu_version"):
    try_call(s, "_get_smu_version", s._get_smu_version)

for name in [
    "get_enabled_smu_features",
    "query_active_wgp",
    "query_gfxclk",
    "get_gfx_frequency",
    "get_gfx_vid",
]:
    if hasattr(s, name):
        try_call(s, name, getattr(s, name))

# raw_read of arg after failed send is unsafe; only list raw API surface
print("HAS_raw_send", hasattr(s, "raw_send"))
print("HAS_raw_read", hasattr(s, "raw_read"))
print("HAS_send_message", hasattr(s, "send_message"))

# dump method signatures of interest
import inspect
for name in sorted(n for n in dir(s) if not n.startswith("_") and callable(getattr(s, n))):
    if any(k in name.lower() for k in ("vcn", "vclk", "dclk", "power", "domain", "feature", "raw", "send", "test", "wgp", "gfx", "version")):
        try:
            sig = str(inspect.signature(getattr(s, name)))
        except Exception:
            sig = "?"
        print(f"SIG {name}{sig}")

s.close()
print("SMU_CLOSE_OK")
PY

echo
echo "--- package: all public method names + msg ids (grep send_message) ---"
timeout 10 grep -RIn "send_message\|raw_send\|0x[0-9A-Fa-f]\\+" \
  "$PKG/bc250_smu" --include='*.py' 2>/dev/null | grep -E "send_message|raw_send|def " | head -120

echo
echo "--- package: any VCN/vclk/dclk/domain string ---"
timeout 10 grep -RIn -E "VCN|Vcn|vclk|dclk|power.?domain|domain.?6|PowerUp|PowerDown|FUN_" \
  "$PKG" --include='*.py' 2>/dev/null | head -40 || echo "NONE"

echo
echo "--- telemetry / metrics userspace (read configs + recent logs, no start/stop) ---"
# unit files
for u in bc250-metrics bc250-pwrwatch bc250-gpu-fixed bc250-cu-layout bc250-netconsole; do
  f=$(systemctl show -p FragmentPath "$u.service" 2>/dev/null | cut -d= -f2)
  echo "UNIT $u path=$f"
  if [ -n "$f" ] && [ -r "$f" ]; then
    timeout 2 sed -n '1,80p' "$f"
    echo "---"
  fi
done

echo "--- find metrics scripts ---"
timeout 15 find /home/OWNER /usr/local /opt /etc -maxdepth 5 \
  \( -iname '*metrics*' -o -iname '*pwrwatch*' -o -iname '*telemetry*' -o -iname '*gpu-fixed*' \) \
  2>/dev/null | head -60

echo "--- journal metrics last lines ---"
timeout 5 journalctl -u bc250-metrics.service -u bc250-pwrwatch.service -b --no-pager -n 40 2>/dev/null | tail -50

echo "--- look for vclk/dclk in home logs / agent-reach ---"
timeout 10 grep -RIn -E "vclk|dclk|VCLK|DCLK|vcn" \
  /home/OWNER/.agent-reach /home/OWNER/bc250* /var/log/bc250* 2>/dev/null | head -40 || true
ls -la /home/OWNER/.agent-reach/ 2>/dev/null | head
ls -la /var/log/bc250* 2>/dev/null | head
ls -la /tmp/bc250* 2>/dev/null | head

echo
echo "--- cyan_skillfish ppt metrics fields from packaging patch (vclk/dclk emit) ---"
timeout 10 grep -n -E "vclk|dclk|Vclk|Dclk|VCN|Average\\.|Current\\." \
  /home/OWNER/linux-cachyos-bc250/patches/kernel-7.2/0001-bc250-8core-telemetry-gpu-activity.patch 2>/dev/null | head -50

echo
echo "--- debugfs dri listing only (no hangy reads) ---"
timeout 2 ls -la /sys/kernel/debug/dri 2>/dev/null || echo "no_debugfs"
for d in /sys/kernel/debug/dri/*; do
  [ -d "$d" ] || continue
  echo "DIR $d"
  timeout 2 ls "$d" 2>/dev/null | head -60
done

echo
echo "--- amdgpu module params (read) ---"
timeout 3 ls /sys/module/amdgpu/parameters 2>/dev/null | head -80
for p in ip_block_mask ip_discovery_disable runpm aspm modeset; do
  f=/sys/module/amdgpu/parameters/$p
  if [ -r "$f" ]; then echo -n "$p="; timeout 1 cat "$f"; echo; fi
done

echo
echo "--- firmware load path hints from dmesg ring if any ---"
timeout 3 dmesg -T 2>/dev/null | grep -iE 'amdgpu|vcn|psp|firmware|skillfish|smu' | tail -40 || echo "dmesg empty/restricted"

echo "=== PART8 DONE ==="
} >"$OUT" 2>&1
echo wrote:$OUT
wc -c "$OUT"
