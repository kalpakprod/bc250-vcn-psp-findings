#!/usr/bin/env python3
"""Read only NBIO registers already proven safe across a cold boot."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

LIB = Path(os.environ.get("BC250_SMU_PATH", "/home/OWNER/vcn_unlock/bc250-smu-unlock"))
sys.path.insert(0, str(LIB))

from bc250_smu import Bc250PciTransport  # noqa: E402

REGISTERS = {
    "iohc_source_5c": 0x13B1005C,
    "iohc_source_60": 0x13B10060,
    "iohc_source_4c": 0x13B0004C,
    "nbio_target_6a140": 0x0006A140,
    "nbio_target_6a144": 0x0006A144,
    "nbio_target_6a148": 0x0006A148,
    "nbio_target_6a14c": 0x0006A14C,
    "nbio_route_33e0": 0x000033E0,
}


def main() -> int:
    result: dict[str, str] = {}
    transport = Bc250PciTransport(bdf="0000:00:00.0", use_flock=True)
    transport.open()
    try:
        for name, address in REGISTERS.items():
            print(f"read {name} 0x{address:08x}", flush=True)
            value = transport.read_smu_reg(address)
            result[name] = f"0x{value:08x}"
            print(f"value {name}={result[name]}", flush=True)
    finally:
        transport.close()

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
