#!/usr/bin/env python3
"""Final structural pass over the Robin type-0x24 SEC GASKET policy:
sequentially parse group headers {window u32, count u32} + records,
inventory per window, locate NBIF/NBIO VCN route records."""
import struct, sys

GK = (r"C:\Users\OWNER\tmp_bc250\bc250_firmware\psp_entries"
      r"\BC250_3.00_CHIPSETMENU.ROM\07_t24_0x982000_2E50.bin")

def main():
    with open(GK, "rb") as f:
        g = f.read()
    print(f"blob {len(g):#x} bytes")
    # header sanity
    cookie = g[0x10:0x14]
    ver = struct.unpack_from("<I", g, 0x60)[0]
    total = struct.unpack_from("<I", g, 0x6C)[0]
    print(f"cookie={cookie} version=0x{ver:08X} (B.{(ver>>16)&0xFF:02X}."
          f"{(ver>>8)&0xFF:02X}.{ver&0xFF:02X}) total=0x{total:X}")
    # candidate group start scan: find {0x201,...},{0x203,...},{0x210,...},
    # {0x280,...},{0x281,...} windows with plausible counts
    print("\nSequential group parse from 0x140:")
    p = 0x140
    total_recs = 0
    for gi in range(6):
        if p + 8 > len(g):
            break
        win, cnt = struct.unpack_from("<II", g, p)
        if win not in (0x201, 0x203, 0x210, 0x280, 0x281):
            print(f"  @{p:#06x}: not a group header (win=0x{win:X}) — stop")
            break
        print(f"  group[{gi}] @{p:#06x}: window=0x{win:X} count={cnt}")
        recs = []
        for i in range(cnt):
            a, v = struct.unpack_from("<II", g, p + 8 + 8 * i)
            recs.append((a, v))
        total_recs += cnt
        # notable records in this group
        notable = [(a, v) for (a, v) in recs
                   if a in (0x03A2011C, 0x03A20120, 0x03A20124, 0x0322011C,
                            0x03220124, 0x0322012C, 0x03E810, 0x03E814,
                            0x0900C234, 0x0900CB80, 0x0900C910, 0x0900C914,
                            0x0900C930)
                   or (0x01C760 <= a <= 0x01C790) or (0x01F820 <= a <= 0x01F8B0)]
        for a, v in notable:
            tag = ""
            if a == 0x03E810:
                tag = "  <<< VCN_SEG ENABLE (0 = KILLED, donor 6/absent)"
            if a == 0x03A2011C:
                tag = "  <<< DF window low (0x87FF clamped, donor 0x107FF)"
            if a == 0x03A20120:
                tag = "  <<< DF window high"
            if 0x01C760 <= a <= 0x01C790:
                tag = "  <<< NBIF route"
            if 0x01F820 <= a <= 0x01F8B0:
                tag = "  <<< NBIO VCN route"
            print(f"      0x{a:08X} = 0x{v:08X}{tag}")
        p = p + 8 + 8 * cnt
    print(f"\n  total records parsed: {total_recs} (A1 said 1405 Robin)")
    # VCN_SEG full group dump (window 0x210)
    print("\nFull VCN_SEG group (window 0x210) records:")
    i = g.find(struct.pack("<I", 0x210) + struct.pack("<I", 13))
    if i >= 0:
        for k in range(13):
            a, v = struct.unpack_from("<II", g, i + 8 + 8 * k)
            print(f"  0x{a:08X} = 0x{v:08X}")

if __name__ == "__main__":
    sys.exit(main())
