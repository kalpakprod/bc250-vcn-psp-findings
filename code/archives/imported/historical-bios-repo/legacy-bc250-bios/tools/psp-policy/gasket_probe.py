#!/usr/bin/env python3
"""Probe the extracted PSP type-0x24 (SEC GASKET) policy blob:
structure hexdump + search for known A1-replay address/value byte patterns."""
import os, struct, sys

BASE = (r"C:\Users\OWNER\tmp_bc250\bc250_firmware\psp_entries"
        r"\BC250_3.00_CHIPSETMENU.ROM")

def hexdump(data, base=0, rows=12, width=16):
    out = []
    for r in range(rows):
        chunk = data[base + width * r: base + width * (r + 1)]
        if not chunk:
            break
        hexs = " ".join(f"{b:02x}" for b in chunk)
        txt = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        out.append(f"  {base + width * r:06X}: {hexs}  {txt}")
    return "\n".join(out)

def main():
    p24 = os.path.join(BASE, "07_t24_0x982000_2E50.bin")
    p45 = os.path.join(BASE, "15_t45_0x9CA400_6E0.bin")
    p08 = os.path.join(BASE, "02_t08_0x8FF000_40200.bin")
    for name, p in [("type0x24 gasket", p24), ("type0x45 TOS", p45),
                    ("type0x08 PMFW head", p08)]:
        with open(p, "rb") as f:
            data = f.read()
        print("=" * 96)
        print(f"{name}: {p}  ({len(data):,} bytes)")
        print(hexdump(data, 0, rows=10))
    # pattern search in gasket policy
    with open(p24, "rb") as f:
        g = f.read()
    pats = {
        "A1addr 0x09023234": struct.pack("<I", 0x09023234),
        "A1addr 0x09300034": struct.pack("<I", 0x09300034),
        "VCN_SEG 0x03E810": struct.pack("<I", 0x03E810),
        "VCN_SEG 0x03E814": struct.pack("<I", 0x03E814),
        "donor val 0x2544C382": struct.pack("<I", 0x2544C382),
        "A1addr 0x0900C234": struct.pack("<I", 0x0900C234),
        "DF win 0x03A2011C": struct.pack("<I", 0x03A2011C),
        "DF win 0x0322011C": struct.pack("<I", 0x0322011C),
        "value 0x000107FF": struct.pack("<I", 0x000107FF),
        "value 0x000087FF": struct.pack("<I", 0x000087FF),
    }
    print("=" * 96)
    print("PATTERN SEARCH in type-0x24 gasket policy:")
    for name, pat in pats.items():
        idxs = []
        i = 0
        while len(idxs) < 6:
            j = g.find(pat, i)
            if j < 0:
                break
            idxs.append(j)
            i = j + 1
        print(f"  {name:22s}: {len(idxs)} hits {[hex(x) for x in idxs]}")
    # 32-bit LE dword histogram of first 64 dwords for structure guessing
    print("  first 64 dwords:",
          " ".join(f"{x:08x}" for x in struct.unpack_from("<64I", g, 0)))

if __name__ == "__main__":
    sys.exit(main())
