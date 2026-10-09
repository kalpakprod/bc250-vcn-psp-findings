# Brute-force the PSP L1 directory checksum algorithm @0x8E0000 (stored 0x63FFFCC8).
import struct, zipfile

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
for nm, fn in [("hw1", FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN"),
               ("3.00", FILES + r"\BC250_3.00_CHIPSETMENU.ROM")]:
    b = open(fn, "rb").read()
    DIR = 0x8E0000
    stored = struct.unpack_from("<I", b, DIR + 4)[0]
    count = struct.unpack_from("<I", b, DIR + 8)[0]
    total = struct.unpack_from("<I", b, DIR + 12)[0]
    print("\n%s: stored=%#x count=%d total=%#x" % (nm, stored, count, total))

    def negsum(start, end, skip4=True):
        s = 0
        for o in range(start, end, 4):
            if skip4 and o == 4:
                continue
            s += struct.unpack_from("<I", b, DIR + o)[0]
        return (-s) & 0xFFFFFFFF

    candidates = []
    for end in (0x190, 0x194, 0x5D0, 0x5D4, 0x1000, 0x400):
        v = negsum(0, end)
        candidates.append(("neg-u32 [0,%#x) skip+4" % end, v))
        v2 = (-sum(struct.unpack_from("<I", b, DIR + o)[0] for o in range(0, end, 4) if o != 4)) & 0xFFFFFFFF
        candidates.append(("neg-u32 [0,%#x) (same)" % end, v2))
    # byte sum variants
    for end in (0x5D0, 0x190):
        s = sum(b[DIR:DIR + end]) - (b[DIR + 4] + b[DIR + 5] + b[DIR + 6] + b[DIR + 7]) if False else sum(b[i] for i in range(DIR, DIR + end) if not (DIR + 4 <= i < DIR + 8))
        candidates.append(("neg-u8 [0,%#x) skip+4" % end, (-s) & 0xFFFFFFFF))
        candidates.append(("0x100-neg-u8? [0,%#x)" % end, (0x100 - (s & 0xFF)) & 0xFF))
    # u16 sums
    for end in (0x5D0, 0x190):
        s = 0
        for o in range(0, end, 2):
            if 4 <= o < 8:
                continue
            s += struct.unpack_from("<H", b, DIR + o)[0]
        candidates.append(("neg-u16 [0,%#x) skip+4" % end, (-s) & 0xFFFFFFFF))
    # crc32 variants
    for end in (0x5D0, 0x190):
        z = bytearray(b[DIR:DIR + end])
        z[4:8] = b"\x00\x00\x00\x00"
        candidates.append(("crc32 [0,%#x) zero+4" % end, zipfile.zlib.crc32(bytes(z)) & 0xFFFFFFFF))
        candidates.append(("neg-crc32 [0,%#x)" % end, (-zipfile.zlib.crc32(bytes(z))) & 0xFFFFFFFF))
    # sum-included (checksum part of sum) => total should be 0 or 0x100000000-multiple
    for end in (0x5D0, 0x190):
        s = sum(struct.unpack_from("<I", b, DIR + o)[0] for o in range(0, end, 4))
        candidates.append(("raw-u32 sum [0,%#x)" % end, s & 0xFFFFFFFF))
    # xor
    x = 0
    for o in range(0, 0x5D0, 4):
        if o == 4:
            continue
        x ^= struct.unpack_from("<I", b, DIR + o)[0]
    candidates.append(("xor-u32 [0,0x5D0)", x))

    for name, v in candidates:
        mark = "  <<<< MATCH" if v == stored else ""
        if v == stored or "0x5D0" in name or "0x190" in name:
            print("  %-36s %#010x%s" % (name, v, mark))
