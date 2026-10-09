#!/usr/bin/env python3
"""Read-only C2P preflight for the BC-250 S2 runtime experiment.

Maps PCI resource5 (BAR5, 512 KiB) of 0000:01:00.0 and reads the MP0 C2P
mailbox status registers documented in bc250-bios/docs/10-runtime-unlock-recipe.md.
No writes are performed.
"""
import mmap
import os
import sys

RES = "/sys/bus/pci/devices/0000:01:00.0/resource5"

REGS = {
    "C2PMSG_35 (cmd/status) 0x5818C": 0x5818C,
    "C2PMSG_36 (arg lo)    0x58190": 0x58190,
    "C2PMSG_37 (arg hi)    0x58194": 0x58194,
    "C2PMSG_64 (TOS ready) 0x58200": 0x58200,
    "C2PMSG_67 (ring WPTR) 0x5820C": 0x5820C,
    "C2PMSG_81 (SOS alive) 0x58244": 0x58244,
}

def main():
    size = os.path.getsize(RES)
    print(f"resource5 size = 0x{size:X}")
    if size < 0x58248:
        print("FAIL: BAR5 smaller than required offsets")
        sys.exit(1)
    fd = os.open(RES, os.O_RDONLY | os.O_SYNC)
    try:
        mm = mmap.mmap(fd, 0x58248, mmap.MAP_SHARED, mmap.PROT_READ)
        for name, off in REGS.items():
            val = int.from_bytes(mm[off:off + 4], "little")
            print(f"{name}: 0x{val:08X}  bit31={bool(val & 0x80000000)}")
        mm.close()
    finally:
        os.close(fd)

if __name__ == "__main__":
    main()
