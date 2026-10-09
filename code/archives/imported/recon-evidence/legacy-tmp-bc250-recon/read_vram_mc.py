#!/usr/bin/env python3
"""Read BC-250 VRAM MC location and PSP ring registers through amdgpu debugfs."""
from __future__ import annotations

import os
import struct

REGS = os.environ.get("BC250_REGS", "/sys/kernel/debug/dri/1/amdgpu_regs")
GC_SEG0_DW = 0x1260
GCMC_VM_FB_OFFSET = 0x170B
GCMC_VM_FB_LOCATION_BASE = 0x1720
GCMC_VM_FB_LOCATION_TOP = 0x1721


def read32(file, byte_offset: int) -> int:
    file.seek(byte_offset)
    data = file.read(4)
    if len(data) != 4:
        raise OSError(f"short read at 0x{byte_offset:x}")
    return struct.unpack("<I", data)[0]


def c2pmsg(n: int) -> int:
    return (0x16040 + n) * 4


def main() -> None:
    with open(REGS, "rb", buffering=0) as file:
        fb_offset = read32(file, (GC_SEG0_DW + GCMC_VM_FB_OFFSET) * 4)
        fb_base = read32(file, (GC_SEG0_DW + GCMC_VM_FB_LOCATION_BASE) * 4)
        fb_top = read32(file, (GC_SEG0_DW + GCMC_VM_FB_LOCATION_TOP) * 4)
        ring_lo = read32(file, c2pmsg(69))
        ring_hi = read32(file, c2pmsg(70))
    print(f"GCMC_VM_FB_OFFSET=0x{fb_offset:08x}")
    print(f"GCMC_VM_FB_LOCATION_BASE=0x{fb_base:08x}")
    print(f"GCMC_VM_FB_LOCATION_TOP=0x{fb_top:08x}")
    print(f"PSP_RING=0x{ring_hi:08x}{ring_lo:08x}")
    print(f"FB_MC_BASE_SHIFT24=0x{fb_base << 24:012x}")
    print(f"FB_MC_TOP_SHIFT24=0x{((fb_top + 1) << 24) - 1:012x}")


if __name__ == "__main__":
    main()
