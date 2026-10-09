#!/usr/bin/env python3
"""F1: enumerate APCB groups in BC-250 stock and Cezanne donor images.

Walks the APCB v3 container at the given offsets, lists every group
(magic, type, sizes) and flags any group that could carry GPU/GFX config.
Usage: python f1_apcb_groups.py [rom_path offset ...]
"""
import sys

ROMS = [
    ("STOCK_BC250_3.00",
     r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files\BC250_3.00.ROM",
     0xAB1000),
    ("DONOR_CEZANNE",
     r"C:\Users\OWNER\tmp_bc250\recon\cezanne_uefi\BIOS.bin",
     None),
]

# names from AMD APCB usage (subset); unknown magics are printed raw
KNOWN = {
    b"PSPG": "PSP generic",
    b"DFG ": "DF generic",
    b"MEMG": "memory generic",
    b"UNKN": "unknown",
    b"VBLK": "variable block",
}

def find_apcb(rom):
    i = rom.find(b"APCB")
    return i if i >= 0 else None

def walk(rom, base, log):
    hdr = rom[base:base + 0x20]
    if hdr[:4] != b"APCB":
        log("  !! no APCB magic at 0x%X" % base)
        return
    hdr_size = int.from_bytes(hdr[6:8], "little")
    total = int.from_bytes(hdr[8:12], "little")
    groups_off = int.from_bytes(hdr[16:20], "little") if len(hdr) >= 20 else 0x9C
    log("  APCB @0x%X: hdr=0x%X total=0x%X" % (base, hdr_size, total))
    o = base + (groups_off or 0x9C)
    end = base + total
    n = 0
    while o + 16 <= end and n < 200:
        magic = rom[o:o + 4]
        b1, b2 = rom[o + 4], rom[o + 5]
        hsz = int.from_bytes(rom[o + 6:o + 8], "little")
        flags = int.from_bytes(rom[o + 8:o + 12], "little")
        gsz = int.from_bytes(rom[o + 12:o + 16], "little")
        if gsz < 16 or o + gsz > end:
            log("  !! bad size at +%#X (magic=%r gsz=%#X) - stop" %
                (o - base, magic, gsz))
            break
        log("  grp[%02d] @+%#06x %-8r b1=%02X b2=%02X hsz=%#04x flags=%08X size=%#06x %s"
            % (n, o - base, magic, b1, b2, hsz, flags, gsz,
               KNOWN.get(magic, "")))
        n += 1
        o += gsz
    log("  groups walked: %d" % n)

def main():
    args = sys.argv[1:]
    out = []
    log = out.append
    if args:
        rom = open(args[0], "rb").read()
        walk(rom, int(args[1], 0), log)
    else:
        for name, path, off in ROMS:
            log("=" * 70)
            log("=== %s (%s)" % (name, path))
            try:
                rom = open(path, "rb").read()
            except OSError as e:
                log("  !! %s" % e)
                continue
            if off is None:
                off = find_apcb(rom)
                if off is None:
                    log("  !! APCB magic not found")
                    continue
            walk(rom, off, log)
    txt = "\n".join(out)
    print(txt)
    with open(r"C:\Users\OWNER\bc250-bios\evidence\f1_apcb_groups.txt", "w",
              encoding="utf-8") as f:
        f.write(txt + "\n")

if __name__ == "__main__":
    main()
