#!/usr/bin/env python3
"""Find adjacent SEC_GASKET value pairs that cover selected target addresses."""
from __future__ import annotations

import json
import sys
from pathlib import Path

TARGETS = {
    "VCN_SEG0_MMIO_DW": 0x00007800,
    "VCN_SEG1_MMIO_DW": 0x00007E00,
    "VCN_SEG0_MMIO_BYTE": 0x0001E000,
    "VCN_SEG1_MMIO_BYTE": 0x0001F800,
    "VCN_FABRIC": 0x02403000,
}


def main() -> int:
    for filename in sys.argv[1:]:
        path = Path(filename)
        report = json.loads(path.read_text(encoding="utf-8"))
        print(f"=== {path} ===")
        for name, target in TARGETS.items():
            hits = []
            for group in report["groups"]:
                writes = group["writes"]
                for first, second in zip(writes, writes[1:]):
                    reg_lo = int(first["address"], 16)
                    reg_hi = int(second["address"], 16)
                    value_lo = int(first["value"], 16)
                    value_hi = int(second["value"], 16)
                    if reg_hi == reg_lo + 4 and value_lo <= target <= value_hi:
                        hits.append(
                            (
                                group["type"],
                                reg_lo,
                                reg_hi,
                                value_lo,
                                value_hi,
                            )
                        )
            print(f"{name}=0x{target:08x} hits={len(hits)}")
            for group_type, reg_lo, reg_hi, value_lo, value_hi in hits:
                print(
                    f"  group={group_type} regs=0x{reg_lo:08x}/0x{reg_hi:08x} "
                    f"range=0x{value_lo:08x}..0x{value_hi:08x}"
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
