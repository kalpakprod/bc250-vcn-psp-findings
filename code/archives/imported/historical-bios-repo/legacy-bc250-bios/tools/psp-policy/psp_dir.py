#!/usr/bin/env python3
"""Full PSP-directory dump + entry extraction for the BC-250 ROM corpus.

PSP dir @0x8E0000 (L1): header 16B (cookie '$PSP', checksum u32, num_entries u32,
field u32), entries 12B: {type u32, size u24, flags u8, location u32 (0xFF000000
+ SPI offset)}.
Extracts every entry blob to bc250_firmware/psp_entries/<rom>/<type>_<off>.bin
and prints an AMD fw-header decode when the signature matches.
"""
import os, struct, sys

CHAT = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
FIRM = r"C:\Users\OWNER\tmp_bc250\bc250_firmware"
OUT = os.path.join(FIRM, "psp_entries")

ROMS = {
    "BC250_3.00_CHIPSETMENU.ROM": os.path.join(CHAT, "BC250_3.00_CHIPSETMENU.ROM"),
    "bc250_modded": os.path.join(CHAT, "bc250 modded bios.ROM"),
    "bc250-Steam": os.path.join(CHAT, "bc250-Steam.rom"),
    "8_cores_Steam": os.path.join(CHAT, "8_cores_Steam.rom"),
    "Robin5.00": os.path.join(CHAT, "Robin5.00"),
    "W25Q128BV_hw": os.path.join(CHAT, "W25Q128BV@WSON8_20250122_140516.BIN"),
}

def fw_header_decode(blob):
    """AMD fw header: u32 total, u32 hdr2, u32==1, u32 type, u32 ver,
    u32==total-0x100, u32==0x100 at blob+0x100? or at 0. Try both bases."""
    for base in (0x00, 0x100):
        if len(blob) < base + 0x1C:
            continue
        total, hdr2, one, typ, ver, t2, s2 = struct.unpack_from("<IIIIIII", blob, base)
        if one == 1 and total > 0x200 and t2 == total - 0x100 and s2 == 0x100:
            return (base, typ, ver, total, hdr2)
    return None

def main():
    os.makedirs(OUT, exist_ok=True)
    summary = {}
    for name, path in ROMS.items():
        with open(path, "rb") as f:
            blob = f.read()
        print("=" * 96)
        print(f"ROM: {name}  ({len(blob):,} bytes)")
        d = 0x8E0000
        cookie = blob[d:d + 4]
        if cookie != b"$PSP":
            print("  no $PSP at 0x8E0000!")
            continue
        csum, nent, fld = struct.unpack_from("<III", blob, d + 4)
        print(f"  $PSP dir @0x{d:X}: checksum=0x{csum:08X} nent={nent} field=0x{fld:X}")
        entries = []
        for i in range(nent):
            e = d + 16 + 16 * i
            typ, size24, loc = struct.unpack_from("<IIQ", blob, e)
            spi = loc & 0xFFFFFF if (loc >> 24) == 0xFF else None
            entries.append((typ, size24, loc, spi))
        outdir = os.path.join(OUT, name)
        os.makedirs(outdir, exist_ok=True)
        for i, (typ, size24, loc, spi) in enumerate(entries):
            line = (f"  entry[{i:02d}] type=0x{typ:02X} size=0x{size24:X} "
                    f"loc=0x{loc:X}")
            if spi is not None and size24:
                fn = f"{i:02d}_t{typ:02X}_0x{spi:X}_{size24:X}.bin"
                with open(os.path.join(outdir, fn), "wb") as g:
                    g.write(blob[spi:spi + size24])
                hdr = fw_header_decode(blob[spi:spi + size24])
                if hdr:
                    base, htyp, hver, htot, hhdr2 = hdr
                    line += (f"  -> {fn}  FWHDR(base=0x{base:X}) type=0x{htyp:08X} "
                             f"ver=0x{hver:08X} total=0x{htot:X} hdr2=0x{hhdr2:X}")
                else:
                    line += f"  -> {fn}  (no AMD fw hdr)"
            print(line)
        summary[name] = entries
    # cross-ROM diff of entry type sets
    print("=" * 96)
    print("ENTRY-TYPE DIFF (type -> per-rom size/loc):")
    all_types = sorted({t for es in summary.values() for (t, *_ ) in es})
    hdr = f"{'type':>6s} " + " ".join(f"{n[:14]:>22s}" for n in summary)
    print(hdr)
    for t in all_types:
        row = f"0x{t:04X} "
        for n, es in summary.items():
            cell = "-"
            for (tt, sz, fl, loc, spi) in es:
                if tt == t:
                    cell = f"sz0x{sz:X}@{spi:07X}" if spi is not None else f"sz0x{sz:X}"
                    break
            row += f"{cell:>22s} "
        print(row)

if __name__ == "__main__":
    sys.exit(main())
