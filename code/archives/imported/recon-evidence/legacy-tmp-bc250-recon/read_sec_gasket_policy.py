#!/usr/bin/env python3
"""Read the live PSP security-gasket policy registers listed by SEC_GASKET."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

LIB = Path(os.environ.get("BC250_SMU_PATH", "/home/OWNER/vcn_unlock/bc250-smu-unlock"))
sys.path.insert(0, str(LIB))

from bc250_smu import Bc250PciTransport  # noqa: E402

NORMAL = {
    0x0322011C: 0x00008000,
    0x03220124: 0x00008707,
    0x0322012C: 0x00008707,
    0x03220174: 0x000087FF,
    0x0322017C: 0x000087FF,
    0x03220184: 0x000087FF,
    0x0322018C: 0x000081FF,
}
DEBUG = {
    0x0322011C: 0x000080FF,
    0x03220124: 0x000087FF,
    0x0322012C: 0x000087FF,
    0x03220174: 0x000087FF,
    0x0322017C: 0x000087FF,
    0x03220184: 0x000087FF,
    0x0322018C: 0x000081FF,
}
EXTRA = (
    0x03220120,
    0x03220128,
    0x03220130,
    0x03220178,
    0x03220180,
    0x03220188,
    0x03220190,
    0x01033974,
    0x01033978,
    0x09033910,
    0x09033914,
    0x09033934,
    0x09033938,
    0x09033974,
    0x09033978,
)


def main() -> int:
    result = {}
    transport = Bc250PciTransport(bdf="0000:00:00.0", use_flock=True)
    transport.open()
    try:
        for address in (*NORMAL, *EXTRA):
            print(f"read 0x{address:08x}", flush=True)
            value = transport.read_smu_reg(address)
            result[f"0x{address:08x}"] = f"0x{value:08x}"
            print(f"value 0x{value:08x}", flush=True)
    finally:
        transport.close()

    normal_matches = sum(int(result[f"0x{address:08x}"], 16) == value for address, value in NORMAL.items())
    debug_matches = sum(int(result[f"0x{address:08x}"], 16) == value for address, value in DEBUG.items())
    print(json.dumps(result, indent=2, sort_keys=True))
    print(f"normal_matches={normal_matches}/{len(NORMAL)}")
    print(f"debug_matches={debug_matches}/{len(DEBUG)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
