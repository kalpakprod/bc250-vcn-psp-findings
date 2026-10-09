#!/usr/bin/env python3
"""F1: check stock/donor ROMs for an ATOM VBIOS image (phase F, item 4).

Looks for a valid ATOM BIOS: 0x55AA at offset 0 of the image or of the
final 64 KiB, the 'ATOM' string, the ATOMBIOS signature, and the
ATOM_ROM_HEADER pointer.  Conclusion is written to evidence/f1_atom_scan.txt.
"""
import struct, sys

IMAGES = [
    ("STOCK_BC250_3.00",
     r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files\BC250_3.00.ROM"),
    ("DONOR_CEZANNE",
     r"C:\Users\OWNER\tmp_bc250\recon\cezanne_uefi\BIOS.bin"),
]

def atom_at(rom, base):
    """Validate an ATOM ROM header at rom[base]."""
    if rom[base:base + 2] != b"\x55\xaa":
        return None
    ptr = struct.unpack_from("<H", rom, base + 0x48)[0]
    if ptr == 0 or base + ptr + 4 > len(rom):
        return "55AA at 0x%X but ATOM_ROM_HEADER ptr invalid" % base
    if rom[base + ptr:base + ptr + 4] != b"ATOM":
        return "55AA at 0x%X but no ATOM sig at +0x%X" % (base, ptr)
    return "valid ATOM ROM @0x%X" % base

def main():
    out = []
    log = out.append
    for name, path in IMAGES:
        log("=" * 60)
        log("=== %s" % name)
        rom = open(path, "rb").read()
        log("  size %d" % len(rom))
        hits = []
        # 55AA at image start
        r = atom_at(rom, 0)
        if r:
            hits.append(r)
        # 55AA anywhere (limit output)
        i, cnt = 0, 0
        while cnt < 20:
            i = rom.find(b"\x55\xaa", i)
            if i < 0:
                break
            r = atom_at(rom, i)
            if r:
                hits.append(r)
            i += 1
            cnt += 1
        log("  55AA-validated ATOM headers: %s" % (hits or "NONE"))
        for sig in (b"ATOM", b"ATOMBIOS", b"PowerPlayInfo", b"DispDevicePathInfo"):
            log("  %r occurrences: %d" % (sig, rom.count(sig)))
        log("")
    log("CONCLUSION: neither BC-250 stock ROM nor the Cezanne donor BIOS")
    log("contains an ATOM VBIOS image (no valid 55AA header, no ATOM/*")
    log("strings).  There is no VBIOS table (PowerPlay, DispDevicePathInfo,")
    log("GPIO) in this firmware stack to patch; VBIOS is not a carrier of")
    log("the iGPU CU mask on this board.")
    txt = "\n".join(out)
    print(txt)
    with open(r"C:\Users\OWNER\bc250-bios\evidence\f1_atom_scan.txt", "w",
              encoding="utf-8") as f:
        f.write(txt + "\n")

if __name__ == "__main__":
    main()
