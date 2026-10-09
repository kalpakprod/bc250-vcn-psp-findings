#!/usr/bin/env bash
# one-shot gpu_metrics + metrics kmsg sample; no SMU writes; no pp_dpm
set +e
OUT=/tmp/a1_part10.out
{
echo "=== PART10 ts=$(date -Is) ==="
# single read of gpu_metrics with hard timeout; metrics service may contend
timeout 8 sudo -n python3 - <<'PY'
import os, struct, time, fcntl
path='/sys/class/drm/card1/device/gpu_metrics'
LAYOUT = "<HBB" + "HH" + "8H" + "2H" + "HH" + "Q" + "HHHH" + "8H" + "6H" + "6H" + "8H" + "2H" + "I" + "H" + "3H" + "Q"
FIELDS = [
    "size","fmt","cont","t_gfx","t_soc",
    *[f"t_core{i}" for i in range(8)],
    "t_l3_0","t_l3_1","act_gfx","act_mm","clock_counter",
    "p_socket","p_cpu","p_soc","p_gfx",
    *[f"p_core{i}" for i in range(8)],
    "avg_gfxclk","avg_socclk","avg_uclk","avg_fclk","avg_vclk","avg_dclk",
    "cur_gfxclk","cur_socclk","cur_uclk","cur_fclk","cur_vclk","cur_dclk",
    *[f"coreclk{i}" for i in range(8)],
    "l3clk_0","l3clk_1","throttle","fan_pwm","pad0","pad1","pad2","indep_throttle",
]
need=struct.calcsize(LAYOUT)
print('layout_need', need)
for attempt in range(5):
    t0=time.time()
    try:
        fd=os.open(path, os.O_RDONLY)
        try:
            data=os.read(fd, 512)
        finally:
            os.close(fd)
        dt=time.time()-t0
        print(f'attempt={attempt} dt={dt:.3f}s n={len(data)}')
        print('hex64', data[:64].hex())
        if len(data) >= need:
            vals=struct.unpack_from(LAYOUT, data, 0)
            m=dict(zip(FIELDS, vals))
            for k in ["size","fmt","cont","avg_gfxclk","avg_socclk","avg_uclk","avg_fclk","avg_vclk","avg_dclk","cur_gfxclk","cur_socclk","cur_uclk","cur_fclk","cur_vclk","cur_dclk","act_gfx","act_mm","t_gfx","t_soc","throttle"]:
                print(f'{k}={m[k]}')
            break
    except Exception as e:
        print(f'attempt={attempt} ERR {type(e).__name__}: {e}')
        time.sleep(0.2)
PY

echo "--- last BC250-METRICS from journal/kmsg ---"
timeout 5 journalctl -k -b --no-pager 2>/dev/null | grep -E 'BC250-METRICS|BC250-THROTTLE|vclk|dclk' | tail -20
timeout 3 dmesg 2>/dev/null | grep -E 'BC250-METRICS|BC250-THROTTLE' | tail -20

echo "--- metrics.py does it emit vclk? ---"
grep -n 'vclk\|dclk\|gfxclk\|fields' /usr/local/libexec/bc250-metrics.py | head -40

echo "--- netconsole target ---"
timeout 3 sed -n '1,80p' /usr/local/libexec/bc250-netconsole.sh
timeout 2 cat /proc/net/netconsole 2>/dev/null || true

echo "=== PART10 DONE ==="
} >"$OUT" 2>&1
echo wrote:$OUT
wc -c "$OUT"
cat "$OUT"
