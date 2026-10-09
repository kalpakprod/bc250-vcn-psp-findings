#!/usr/bin/env bash
set -u

SVCS="bc250-metrics bc250-gpu-watchdog bc250-pwrwatch bc250-telemetry bc250-dpwatch bc250-fan"
sudo systemctl stop $SVCS 2>/dev/null || true

cat << 'EOF' > /tmp/audit_live_gasket_state.py
import json
import os
import sys
import time
from pathlib import Path

SMU_LIB = Path("/home/OWNER/vcn_unlock/bc250-smu-unlock")
sys.path.insert(0, str(SMU_LIB))

import unlock
from bc250_smu import Bc250Smu

def main():
    report = {}
    smu = Bc250Smu()
    report["smu_alive"] = smu.alive()
    is_open = smu.secure_access_enabled()
    report["secure_access_before"] = is_open

    if not is_open:
        print("[*] Unlocking SMU...", flush=True)
        unlock.unlock(smu)
        report["secure_access_after"] = smu.secure_access_enabled()

    # 1. Read Domain 6 state word
    print("[*] Reading dom6...", flush=True)
    try:
        dom6_word = smu.smn_read32(0xF714)
        report["dom6_0xF714"] = f"0x{dom6_word:08x}"
    except Exception as e:
        report["dom6_0xF714_err"] = str(e)

    # 2. Probe NBIO IOHC registers (safe range)
    print("[*] Reading NBIO...", flush=True)
    nbio_addrs = [0x13B1005C, 0x13B10060, 0x13B0004C, 0x13B00084]
    nbio_res = {}
    for addr in nbio_addrs:
        try:
            val = smu.smn_read32(addr)
            nbio_res[f"0x{addr:08x}"] = f"0x{val:08x}"
        except Exception as e:
            nbio_res[f"0x{addr:08x}"] = f"ERR: {e}"
    report["nbio_iohc"] = nbio_res

    # 3. Read Gasket Bank 12 enable register only (0x0900C234)
    print("[*] Reading Gasket 0x0900c234...", flush=True)
    try:
        val = smu.smn_read32(0x0900C234)
        report["gasket_0x0900c234"] = f"0x{val:08x}"
    except Exception as e:
        report["gasket_0x0900c234"] = f"ERR: {e}"

    print("[*] Probe complete.", flush=True)
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
EOF

timeout 30 sudo python3 /tmp/audit_live_gasket_state.py
sudo systemctl start $SVCS 2>/dev/null || true
