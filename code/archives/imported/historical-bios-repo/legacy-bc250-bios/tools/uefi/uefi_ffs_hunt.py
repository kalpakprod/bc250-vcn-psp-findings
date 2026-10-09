#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UEFI FFS walker + LZMA decompress + APCB/DFG constant hunt.

Walks firmware volumes in the UEFI region of the BC250 ROM, extracts
compressed sections (EDK2 LZMA GUID-defined), decompresses, and scans
for the APCB group-id constants / magics we care about.
"""
import struct, re, lzma, os, sys

ROM = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files\BC250_3.00_CHIPSETMENU.ROM"
OUT = r"C:\Users\OWNER\tmp_bc250\recon\uefi_ffs"
os.makedirs(OUT, exist_ok=True)

LZMA_GUID = bytes.fromhex("98584eee143959429d6edc7bd79403cf")  # EE4E5898-3914-4259-9D6E-DC7BD79403CF
FVH = b"_FVH"

data = open(ROM, "rb").read()

HUNT = [
    (bytes.fromhex("03170000"), "DFG gid 0x1703 u32"),
    (bytes.fromhex("01170000"), "PSPG gid 0x1701 u32"),
    (bytes.fromhex("04170000"), "MEMG gid 0x1704 u32"),
    (b"DFG ", "DFG magic"),
    (b"PSPG", "PSPG magic"),
    (b"MEMG", "MEMG magic"),
    (b"APCB", "APCB magic"),
    (bytes.fromhex("4143504220002000"), "APCB v2 hdr"),
    (bytes.fromhex("03170500"), "DFG+type5 hdr"),
    (bytes.fromhex("34c20009"), "SMN 0x0900C234"),
    (bytes.fromhex("20002000"), "{0x20,0x20} hdr pair"),
    (bytes.fromhex("634252ff"), "?"),
]


def safe_name(s):
    s = re.sub(r"[^A-Za-z0-9_.@#-]+", "_", os.path.basename(s))
    return s[-60:] if len(s) > 60 else s


def guid_str(b):
    d1, d2, d3 = struct.unpack_from("<IHH", b, 0)
    return "%08X-%04X-%04X-%s-%s" % (d1, d2, d3, b[8:10].hex().upper(), b[10:16].hex().upper())


def scan(name, blob, where):
    hits = []
    for pat, desc in HUNT:
        n = blob.count(pat)
        if n:
            hits.append((desc, n, [m for m in re.finditer(re.escape(pat), blob)][:3]))
    if hits:
        print("\n### HITS in %s (%s, %d bytes)" % (name, where, len(blob)))
        for desc, n, ms in hits:
            offs = ", ".join("0x%x" % m.start() for m in ms)
            print("   %-24s x%d @ %s" % (desc, n, offs))
    return hits


def lzma_edk2_decompress(stream):
    # EDK2 LzmaCustomDecompressLib: raw LZMA_ALONE (13-byte header props+size)
    try:
        d = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE)
        return d.decompress(stream)
    except Exception:
        return None


def walk_sections(fname, base, blob, depth=0):
    off = 0
    results = []
    while off + 4 <= len(blob):
        s_size = blob[off] | (blob[off + 1] << 8) | (blob[off + 2] << 16)
        s_type = blob[off + 3]
        if s_size == 0xFFFFFF:  # extended
            if off + 8 > len(blob):
                break
            s_size = struct.unpack_from("<I", blob, off + 4)[0]
        if s_size < 4 or off + s_size > len(blob):
            break
        payload = blob[off + 4:off + s_size]
        tname = {0x01: "COMPRESSION", 0x02: "GUID_DEFINED", 0x10: "PE32", 0x15: "USER_INTERFACE",
                 0x19: "RAW", 0x14: "VERSION", 0x17: "FV_IMAGE"}.get(s_type, "T%02X" % s_type)
        if s_type == 0x10:  # PE32 image
            fn = os.path.join(OUT, safe_name("%s+%x.PE32" % (fname, base + off)))
            open(fn, "wb").write(payload)
            results.append((fn, payload))
            scan(os.path.basename(fn), payload, "PE32 @0x%x" % (base + off))
        elif s_type == 0x02 and payload[:16] == LZMA_GUID:
            data_off = struct.unpack_from("<H", payload, 0x10)[0]
            attrs = struct.unpack_from("<H", payload, 0x12)[0]
            stream = payload[data_off - 4:] if data_off >= 4 else payload[0x14:]
            dec = lzma_edk2_decompress(stream)
            if dec:
                fn = os.path.join(OUT, safe_name("%s+%x.LZMA.dec" % (fname, base + off)))
                open(fn, "wb").write(dec)
                results.append((fn, dec))
                scan(os.path.basename(fn), dec, "LZMA section @0x%x" % (base + off))
                # nested FV: find _FVH and locate FV base (sig sits at fvbase+0x28)
                fvstart = None
                for m in re.finditer(re.escape(FVH), dec[:0x100]):
                    fvstart = m.start() - 0x28
                    if fvstart < 0:
                        fvstart = 0
                    fvlen2 = struct.unpack_from("<Q", dec, fvstart + 0x20)[0]
                    if 0x1000 < fvlen2 <= len(dec) - fvstart:
                        break
                    fvstart = None
                if fvstart is not None:
                    results += walk_fv(safe_name(fn), dec[fvstart:fvstart + fvlen2], fvstart)
            else:
                print("  [lzma fail] %s @0x%x (dataoff=%d attrs=%d len=%d)" % (fname, base + off, data_off, attrs, len(stream)))
        elif s_type == 0x01:  # COMPRESSION (EFI standard)
            ulen = struct.unpack_from("<I", payload, 0)[0]
            ctype = payload[4]
            if ctype == 0:
                fn = os.path.join(OUT, safe_name("%s+%x.EFI0.dec" % (fname, base + off)))
                open(fn, "wb").write(payload[5:5 + ulen])
                results.append((fn, payload[5:5 + ulen]))
                scan(os.path.basename(fn), payload[5:5 + ulen], "EFI-compress0 @0x%x" % (base + off))
        elif s_type == 0x15:  # USER_INTERFACE = filename!
            try:
                ui = payload.decode("utf-16-le").rstrip("\x00")
                print("  [FFS %s] UI name: %s" % (fname, ui))
            except Exception:
                pass
        off += s_size
    return results


def walk_fv(fname, fv, fvbase=0):
    results = []
    fv_len = struct.unpack_from("<Q", fv, 0x20)[0]
    hdrlen = struct.unpack_from("<H", fv, 0x30)[0]
    print("[FV] %s len=0x%x hdr=0x%x" % (fname, fv_len, hdrlen))
    off = hdrlen
    idx = 0
    while off + 0x18 <= len(fv):
        g = fv[off:off + 16]
        size = fv[off + 0x14] | (fv[off + 0x15] << 8) | (fv[off + 0x16] << 16)
        state = fv[off + 0x17]
        if g == b"\xff" * 16 and size == 0xFFFFFF:
            break  # true free space
        ftype = fv[off + 0x12]
        if size in (0, 0xFFFFFF) or off + size > len(fv):
            break
        # keep file guid + type
        results += walk_sections("%s[%02x:%s]" % (safe_name(fname), ftype, guid_str(g)[:8]), off, fv[off + 0x18:off + size])
        off = (off + size + 7) & ~7  # PI spec: FFS files are 8-byte aligned
        idx += 1
        if idx > 400:
            break
    return results


def main():
    rom = data
    fv_regions = []
    for m in re.finditer(re.escape(FVH), rom):
        base = m.start() - 0x28
        if base < 0:
            continue
        fvlen = struct.unpack_from("<Q", rom, base + 0x20)[0]
        if 0x1000 < fvlen < 0x2000000 and base + fvlen <= len(rom):
            fv_regions.append((base, fvlen))
    print("FVs found: %d" % len(fv_regions))
    total_dec = []
    for base, fvlen in sorted(set(fv_regions)):
        if not (0xAE0000 <= base <= 0xC30000):
            continue  # UEFI region only (the mods' region)
        fv = rom[base:base + fvlen]
        total_dec += walk_fv("FV@%x" % base, fv, base)
    print("\ntotal decompressed modules: %d" % len(total_dec))


if __name__ == "__main__":
    main()
