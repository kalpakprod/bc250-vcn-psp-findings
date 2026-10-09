#!/usr/bin/env python3
"""Read SMU power-domain config blocks through the already-unlocked fw window."""
from __future__ import annotations

import json
import os
import struct
import sys
from pathlib import Path

LIB = Path(os.environ.get("BC250_SMU_PATH", "/home/OWNER/vcn_unlock/bc250-smu-unlock"))
TOOL = Path(os.environ.get("BC250_VCN_TOOL", "/home/OWNER/vcn_unlock/daveconde-bc250-vcn-enable"))
sys.path.insert(0, str(LIB))
sys.path.insert(0, str(TOOL))

from bc250_smu import Bc250Smu  # noqa: E402
from enable_vcn import rd_sram, rd_win  # noqa: E402

DOMAIN_TABLE_PTR_LITERAL = 0x17434
DOMAIN_STRIDE = 72
BLOCK_SIZE = 0x200


def read_u32(data: bytes, offset: int = 0) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def main() -> int:
    smu = Bc250Smu()
    try:
        if not smu.alive() or not smu.secure_access_enabled():
            print("SMU debug path is not open", file=sys.stderr)
            return 2
        table_base = rd_sram(smu, DOMAIN_TABLE_PTR_LITERAL)
        result: dict[str, object] = {"table_base": table_base, "domains": {}}
        for domain in range(8):
            entry = table_base + domain * DOMAIN_STRIDE
            block_base = rd_sram(smu, entry + 8)
            state = rd_sram(smu, entry + 0x14) & 0xFF
            words = []
            for offset in range(0, BLOCK_SIZE, 4):
                value = rd_win(smu, block_base + offset, f"dom{domain}+0x{offset:03x}")
                words.append(value)
            result["domains"][str(domain)] = {
                "entry": entry,
                "block_base": block_base,
                "state": state,
                "words": words,
            }
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    finally:
        smu.close()


if __name__ == "__main__":
    raise SystemExit(main())
