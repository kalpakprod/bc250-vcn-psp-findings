#!/usr/bin/env python3
"""
Find which PSP/ABL module parses and dispatches SEC_GASKET (Type 0x24).
Scans for group IDs (0x201, 0x203, 0x206, 0x210, 0x280, 0x281),
entry type 0x24, and Gasket register aperture bases (0x0900, 0x03a2, 0x0322).
"""
import struct
from pathlib import Path

BODIES_DIR = Path("tmp_bc250/recon/robin3_psp_bodies")

TARGET_CONSTANTS = {
    "TYPE_0x24_WORD": b"\x24\x00\x00\x00",
    "GRP_0x201": struct.pack("<I", 0x201),
    "GRP_0x203": struct.pack("<I", 0x203),
    "GRP_0x206": struct.pack("<I", 0x206),
    "GRP_0x210": struct.pack("<I", 0x210),
    "GRP_0x280": struct.pack("<I", 0x280),
    "GRP_0x281": struct.pack("<I", 0x281),
    "BASE_0x0900": struct.pack("<H", 0x0900),
    "BASE_0x03a2": struct.pack("<H", 0x03a2),
    "BASE_0x0322": struct.pack("<H", 0x0322),
}

def main():
    results = {}
    for p in sorted(BODIES_DIR.glob("*.body")):
        data = p.read_bytes()
        hits = {}
        for name, pattern in TARGET_CONSTANTS.items():
            offsets = []
            idx = 0
            while True:
                idx = data.find(pattern, idx)
                if idx == -1:
                    break
                offsets.append(hex(idx))
                idx += len(pattern)
            if offsets:
                hits[name] = offsets
        if hits:
            results[p.name] = {
                "size": len(data),
                "hits": hits,
            }
            print(f"=== {p.name} (size={len(data)}) ===")
            for k, v in hits.items():
                print(f"  {k}: {len(v)} hits -> {v[:10]}")

if __name__ == "__main__":
    main()
