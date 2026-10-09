#!/usr/bin/env python3
"""Targeted APCB group dump: find PSPG/DFG/MEMG magics, hex-dump the group
start, extract g=1 permission rows from the first subgroups only."""
import sys, struct

IMAGES = [
    ("BC250_3.00", r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files\BC250_3.00_CHIPSETMENU.ROM"),
    ("Robin5.00", r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files\Robin5.00"),
    ("4700S_C0A", r"C:\Users\OWNER\tmp_bc250\bc250_firmware\4700S\C0A\C0A"),
    ("CEZANNE", r"C:\Users\OWNER\tmp_bc250\recon\cezanne_uefi\BIOS.bin"),
]

def dump_at(rom, i, n=0x90):
    for off in range(i, i + n, 16):
        print("    %06X: %s  %s" % (off, rom[off:off+16].hex(" "),
              "".join(chr(c) if 32 <= c < 127 else "." for c in rom[off:off+16])))

def main():
    for label, path in IMAGES:
        try:
            rom = open(path, "rb").read()
        except OSError as e:
            print("!!", label, e)
            continue
        print("=" * 70)
        print("=== %s (%d bytes)" % (label, len(rom)))
        apcb = rom.find(b"APCB")
        print(" APCB magic @0x%X" % apcb if apcb >= 0 else " no APCB magic")
        for magic, nm in ((b"PSPG", "PSPG"), (b"DFG ", "DFG"), (b"MEMG", "MEMG")):
            hits = []
            start = 0
            while True:
                i = rom.find(magic, start)
                if i < 0:
                    break
                start = i + 1
                if rom[i+5] == 0x17 and i > 0x800000:
                    hits.append(i)
            for i in hits[:3]:
                print(" %s @0x%X:" % (nm, i))
                dump_at(rom, i, 0x60)

if __name__ == "__main__":
    main()
