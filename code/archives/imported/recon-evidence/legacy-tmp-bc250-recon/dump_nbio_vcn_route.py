#!/usr/bin/env python3
"""Read the NBIO/IOHC registers touched by Robin 3.00 AmdNbioGfxInit."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

LIB = Path(os.environ.get("BC250_SMU_PATH", "/home/OWNER/vcn_unlock/bc250-smu-unlock"))
sys.path.insert(0, str(LIB))

from bc250_smu import Bc250PciTransport  # noqa: E402

EXACT = {
    "iohc13b1_plus_5c": 0x13B1005C,
    "iohc13b1_plus_60": 0x13B10060,
    "iohc13b0_plus_4c": 0x13B0004C,
    "iohc13b0_plus_84": 0x13B00084,
    "nbio_target_6a140": 0x0006A140,
    "nbio_target_6a144": 0x0006A144,
    "nbio_target_6a148": 0x0006A148,
    "nbio_target_6a14c": 0x0006A14C,
    "vcn_fabric_base": 0x02403000,
    "gc_fabric_base": 0x02402C00,
}

RANGES = {
    "iohc13b1": (0x13B10040, 0x13B10080),
    "iohc13b0": (0x13B00030, 0x13B000A0),
    "nbio6a1": (0x0006A120, 0x0006A180),
    "vcn_fabric": (0x02403000, 0x02403040),
}


def read32(smu: Bc250PciTransport, addr: int) -> dict[str, object]:
    print(f"read 0x{addr:08x}", flush=True)
    try:
        value = smu.read_smu_reg(addr)
        print(f"read 0x{addr:08x} = 0x{value:08x}", flush=True)
        return {"ok": True, "value": f"0x{value:08x}"}
    except Exception as exc:
        print(f"read 0x{addr:08x} failed: {exc}", flush=True)
        return {"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}


def main() -> int:
    result: dict[str, object] = {
        "bios": Path("/sys/class/dmi/id/bios_version").read_text().strip(),
        "kernel": os.uname().release,
        "exact": {},
        "ranges": {},
    }
    transport = Bc250PciTransport(bdf="0000:00:00.0", use_flock=True)
    transport.open()
    try:
        result["exact"] = {name: read32(transport, addr) for name, addr in EXACT.items()}
        if os.environ.get("BC250_EXACT_ONLY") != "1":
            for name, (start, end) in RANGES.items():
                result["ranges"][name] = {
                    f"0x{addr:08x}": read32(transport, addr) for addr in range(start, end, 4)
                }
    finally:
        transport.close()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
