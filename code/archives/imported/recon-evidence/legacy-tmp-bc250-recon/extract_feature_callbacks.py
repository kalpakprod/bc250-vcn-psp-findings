#!/usr/bin/env python3
"""Extract BC-250 SMU feature masks and enable/disable callback pointer tables."""
from __future__ import annotations

import re
import struct
import sys
from pathlib import Path

FEATURE_BASE_PTR_LITERAL = 0x17374
FEATURE_RE = re.compile(r"#define\s+FEATURE_([A-Z0-9_]+)_BIT\s+(\d+)")


def u32(data: bytes, address: int) -> int:
    return struct.unpack_from("<I", data, address)[0]


def main() -> None:
    firmware = Path(sys.argv[1]).read_bytes()
    header = Path(sys.argv[2]).read_text(encoding="utf-8", errors="replace")
    names = {int(bit): name for name, bit in FEATURE_RE.findall(header)}
    feature_base = u32(firmware, FEATURE_BASE_PTR_LITERAL)
    enable_table = feature_base + 0x10
    disable_table = feature_base + 0x110
    current = u32(firmware, feature_base) | (u32(firmware, feature_base + 4) << 32)
    requested = u32(firmware, feature_base + 8) | (u32(firmware, feature_base + 12) << 32)
    print(f"feature_base=0x{feature_base:05x}")
    print(f"current=0x{current:016x}")
    print(f"requested=0x{requested:016x}")
    print("bit enabled name                           enable_cb disable_cb")
    for bit in range(64):
        enable = u32(firmware, enable_table + bit * 4)
        disable = u32(firmware, disable_table + bit * 4)
        print(
            f"{bit:02d}  {(current >> bit) & 1}      "
            f"{names.get(bit, 'UNKNOWN'):<30} 0x{enable:05x}   0x{disable:05x}"
        )


if __name__ == "__main__":
    main()
