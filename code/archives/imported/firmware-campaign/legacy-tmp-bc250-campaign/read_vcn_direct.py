#!/usr/bin/env python3
"""Read VCN and UVD registers directly through amdgpu_regs to test fabric response."""
from __future__ import annotations

import os
import struct

REGS = os.environ.get("BC250_REGS", "/sys/kernel/debug/dri/1/amdgpu_regs")
VCN_BASE_DWORD = 0x7800  # VCN 2.0 register frame in amdgpu


def read32(f, byte_off: int) -> int:
    f.seek(byte_off)
    return struct.unpack("<I", f.read(4))[0]


def main() -> None:
    with open(REGS, "rb", buffering=0) as f:
        print(f"[*] Reading amdgpu_regs from {REGS}")
        for reg_name, dword_off in [
            ("mmUVD_POWER_STATUS", 0x7800 + 0x00BC),
            ("mmUVD_STATUS", 0x7800 + 0x00BD),
            ("mmUVD_SEMA_ADDR_LOW", 0x7800 + 0x0001),
            ("mmUVD_SCRATCH9", 0x7800 + 0x00C9),
            ("mmUVD_VERSION", 0x7800 + 0x00CA),
        ]:
            byte_off = dword_off * 4
            val = read32(f, byte_off)
            print(f"  {reg_name} (@dword 0x{dword_off:04x}, byte 0x{byte_off:06x}) = 0x{val:08x}")


if __name__ == "__main__":
    main()
