#!/usr/bin/env python3
"""
Inspect and map the live hardware state across SMN, NBIO, and Gasket apertures
on the live BC-250 board running 7.2.0-1.92-cachyos-vcn-bc250.
"""
from __future__ import annotations

import json
import os
import struct
import sys
import time
from pathlib import Path

SMU_LIB = Path(os.environ.get("BC250_SMU_PATH", "/home/OWNER/vcn_unlock/bc250-smu-unlock"))
sys.path.insert(0, str(SMU_LIB))

import unlock  # noqa: E402
from bc250_smu import Bc250Smu, SmuError, SmuTimeout  # noqa: E402


def main() -> int:
    report: dict[str, object] = {
        "timestamp": time.time(),
        "smu_alive": False,
        "secure_access": False,
        "gasket_bank12": {},
        "gasket_other_banks": {},
        "nbio_iohc": {},
        "dom6": {},
    }

    try:
        smu = Bc250Smu()
        report["smu_alive"] = smu.alive()
        if not smu.alive():
            print("[-] SMU not alive")
            print(json.dumps(report, indent=2))
            return 1

        is_open = smu.secure_access_enabled()
        report["secure_access_before"] = is_open
        if not is_open:
            print("[*] Secure access closed. Unlocking...")
            unlock.unlock(smu)
            report["secure_access_after"] = smu.secure_access_enabled()
        else:
            report["secure_access_after"] = True

        # 1. Read Domain 6 state word
        try:
            dom6_word = smu.smn_read32(0xF714)
            report["dom6"]["0xF714"] = f"0x{dom6_word:08x}"
        except Exception as e:
            report["dom6"]["0xF714_err"] = str(e)

        # 2. Probe Gasket Bank 12 (VCN) addresses
        gasket_b12_addrs = [
            0x0900C234,  # enable / control
            0x0900C830,  # mask 0
            0x0900C834,  # mask 1
            0x0900C838,  # mask 2
            0x0900C910,  # size / limit
            0x0900C914,  # attr / mode
            0x0900C920,  # bitmap
            0x0900C92C,  # desc 0
            0x0900C930,  # desc 0 mode
            0x0900C934,  # range 0 start
            0x0900C938,  # range 0 end
            0x0900CB80,  # lock
        ]
        b12_res = {}
        for addr in gasket_b12_addrs:
            try:
                val = smu.smn_read32(addr)
                b12_res[f"0x{addr:08x}"] = f"0x{val:08x}"
            except Exception as e:
                b12_res[f"0x{addr:08x}"] = f"ERR: {e}"
        report["gasket_bank12"] = b12_res

        # 3. Compare with neighboring working banks (e.g. Bank 0x03, 0x06, 0x0e, 0x22)
        sample_banks = [0x09003234, 0x09006234, 0x0900E234, 0x09022234]
        other_res = {}
        for addr in sample_banks:
            try:
                val = smu.smn_read32(addr)
                other_res[f"0x{addr:08x}"] = f"0x{val:08x}"
            except Exception as e:
                other_res[f"0x{addr:08x}"] = f"ERR: {e}"
        report["gasket_other_banks"] = other_res

        # 4. Probe NBIO IOHC registers (safe range)
        nbio_addrs = [
            0x13B1005C,
            0x13B10060,
            0x13B0004C,
            0x13B00084,
        ]
        nbio_res = {}
        for addr in nbio_addrs:
            try:
                val = smu.smn_read32(addr)
                nbio_res[f"0x{addr:08x}"] = f"0x{val:08x}"
            except Exception as e:
                nbio_res[f"0x{addr:08x}"] = f"ERR: {e}"
        report["nbio_iohc"] = nbio_res

    except Exception as e:
        report["fatal"] = str(e)

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
