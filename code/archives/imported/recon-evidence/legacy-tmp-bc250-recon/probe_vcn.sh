#!/usr/bin/env bash
set -uo pipefail
OUT=/tmp/probe_vcn.out
{
echo "############ dmesg (full amdgpu/vcn/psp/smu) ############"
dmesg -T 2>/dev/null | grep -iE 'amdgpu|vcn|psp|smu|skillfish|gc|sdma|cp' | tail -80
echo "--- dmesg raw count ---"; dmesg 2>/dev/null | wc -l
echo
echo "############ find cyan_skillfish2_vcn anywhere ############"
find / -name '*cyan_skillfish*vcn*' 2>/dev/null
find / -name '*skillfish*vcn*' 2>/dev/null
echo "(end find)"
echo
echo "############ SMU enabled features + core mask (bc250_smu API) ############"
SP=/home/OWNER/.local/share/pipx/venvs/bc250-smu-oc
"$SP/bin/python" - <<'PY'
import sys
sys.path.insert(0, "/home/OWNER/.local/share/pipx/venvs/bc250-smu-oc/lib/python3.14/site-packages")
try:
    from bc250_smu.api_q0 import Bc250Smu
    smu = Bc250Smu()
    print("=== enabled_smu_features (hex) ===")
    try:
        print(hex(smu.get_enabled_smu_features()))
    except Exception as e:
        print("get_enabled_smu_features err:", e)
    print("=== core freq per core (q3_0x43) ===")
    for i in range(8):
        try:
            print(f"core{i}:", smu.q3_0x43_get_core_freq(i))
        except Exception as e:
            print(f"core{i} err:", e)
    print("=== set_core_enable_mask signature ===")
    import inspect
    print(inspect.getsource(Bc250Smu.set_core_enable_mask))
except Exception as e:
    print("IMPORT/INIT err:", repr(e))
PY
echo
echo "############ api_q0.py (full) ############"
cat /home/OWNER/.local/share/pipx/venvs/bc250-smu-oc/lib/python3.14/site-packages/bc250_smu/api_q0.py
echo
echo "############ api.py (head 120) ############"
head -n 120 /home/OWNER/.local/share/pipx/venvs/bc250-smu-oc/lib/python3.14/site-packages/bc250_smu/api.py
echo
echo "############ done ############"
} > "$OUT" 2>&1
echo "rc=$? wrote $OUT"