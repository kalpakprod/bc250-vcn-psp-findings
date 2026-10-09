#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase E: LZMA-decompress the community FV region (0xAE0000) of a ROM into
evidence/fv_extract/<name>.dec. Mirrors rom_fv_scan.py section handling:
LZMA GUID section at FFS+0x78, data offset at section+0x10, stream = that-4.
Usage: e1_fv_decompress.py <rom_path> <out_path>"""
import struct, sys, lzma

LZMA_GUID = bytes.fromhex("98584eee143959429d6edc7bd79403cf")


def main(rom_path, out_path):
    rom = open(rom_path, "rb").read()
    base = 0xAE0000
    # FV header
    assert rom[base + 0x28:base + 0x2C] == b"_FVH", "no FVH at 0xAE0000"
    hdrlen = struct.unpack_from("<H", rom, base + 0x30)[0]
    fvlen = struct.unpack_from("<Q", rom, base + 0x20)[0]
    # first FFS file
    off = base + hdrlen
    g = rom[off:off + 16]
    size = rom[off + 0x14] | (rom[off + 0x15] << 8) | (rom[off + 0x16] << 16)
    o = off + 0x18
    end = off + size
    found = False
    while o + 4 <= end:
        ssz = rom[o] | (rom[o + 1] << 8) | (rom[o + 2] << 16)
        stp = rom[o + 3]
        if ssz < 4 or o + ssz > end:
            break
        payload = rom[o + 4:o + ssz]
        if stp == 0x02 and payload[:16] == LZMA_GUID:
            data_off = struct.unpack_from("<H", payload, 0x10)[0]
            stream = payload[data_off - 4:]
            try:
                dec = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE).decompress(stream)
            except Exception:
                dec = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE).decompress(stream + b"\x00" * 8)
            open(out_path, "wb").write(dec)
            print("decompressed %d bytes -> %s" % (len(dec), out_path))
            found = True
        o += ssz
        o = (o + 3) & ~3
    if not found:
        print("!! LZMA section not found in first file")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
