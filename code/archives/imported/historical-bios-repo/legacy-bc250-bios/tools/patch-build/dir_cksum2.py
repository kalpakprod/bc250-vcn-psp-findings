# Brute directory checksum with TWO known dirs as constraints:
#   PSP @0x8E0000 (stored 0x63FFFCC8, count 19)
#   BHD @0xAB0000 (stored 0xECE7B2E6, count 4)
# Find (span rule, algorithm) that reproduces BOTH.
import struct, zipfile

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
b = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()
b3 = open(FILES + r"\BC250_3.00_CHIPSETMENU.ROM", "rb").read()

DIRS = [(0x8E0000, 0x63FFFCC8, 19, 0x5D0), (0xAB0000, 0xECE7B2E6, 4, 0x420)]


def u32sum(d, off, end):
    s = 0
    for o in range(off, end, 4):
        s += struct.unpack_from("<I", d, o)[0]
    return s


def u16sum(d, off, end):
    s = 0
    for o in range(off, end, 2):
        s += struct.unpack_from("<H", d, o)[0]
    return s


def u8sum(d, off, end):
    return sum(d[off:end])


def try_algos(d, base, count, field):
    """yield (rule, value) for many span/algo combos"""
    ent_end = base + 0x10 + 16 * count
    spans = {
        "hdr+ent [0,ent)": (base, ent_end),
        "ent [0x10,ent)": (base + 0x10, ent_end),
        "hdr+ent+1": (base, ent_end + 4),
        "field [0,field)": (base, base + field),
        "field-4": (base, base + field - 4),
        "[0,0x400)": (base, base + 0x400),
    }
    out = {}
    for sname, (s, e) in spans.items():
        # u32 sums, checksum field zeroed (skip base+4..+8)
        z = bytearray(d[s:e])
        if s == base:
            z[4:8] = b"\x00\x00\x00\x00"
        out["neg-u32 " + sname] = (-u32sum(z, 0, len(z))) & 0xFFFFFFFF
        out["crc32 " + sname] = zipfile.zlib.crc32(bytes(z)) & 0xFFFFFFFF
        out["neg-crc32 " + sname] = (-zipfile.zlib.crc32(bytes(z))) & 0xFFFFFFFF
        out["adler32 " + sname] = (zipfile.zlib.adler32(bytes(z))) & 0xFFFFFFFF
        out["neg-u16 " + sname] = (-u16sum(z, 0, len(z) if len(z) % 2 == 0 else len(z) - 1)) & 0xFFFFFFFF
        out["neg-u8 " + sname] = (-u8sum(z, 0, len(z))) & 0xFFFFFFFF
        # 1's complement sum (folded)
        s32 = u32sum(z, 0, len(z))
        while s32 >> 32:
            s32 = (s32 & 0xFFFFFFFF) + (s32 >> 32)
        out["onescomp32 " + sname] = (~s32) & 0xFFFFFFFF
    return out


res = [try_algos(b, base, count, field) for base, stored, count, field in DIRS]
res3 = [try_algos(b3, base, count, field) for base, stored, count, field in DIRS]

keys = set(res[0]) | set(res[1])
print("Searching algos matching BOTH dirs:")
found = []
for k in sorted(keys):
    ok0 = res[0].get(k) == DIRS[0][1]
    ok1 = res[1].get(k) == DIRS[1][1]
    if ok0 and ok1:
        print("  [MATCH-BOTH] %s: %#x / %#x" % (k, res[0].get(k), res[1].get(k)))
        found.append(k)
if not found:
    print("  none. partial matches:")
    for k in sorted(keys):
        ok0 = res[0].get(k) == DIRS[0][1]
        ok1 = res[1].get(k) == DIRS[1][1]
        if ok0 or ok1:
            print("  [partial] %s: psp=%s bhd=%s" % (k, "OK" if ok0 else hex(res[0].get(k)), "OK" if ok1 else hex(res[1].get(k))))

# Also: what would the sum need to be?
for i, (base, stored, count, field) in enumerate(DIRS):
    ent_end = base + 0x10 + 16 * count
    for sname, (s, e) in {"hdr+ent": (base, ent_end), "field": (base, base + field)}.items():
        z = bytearray(b[s:e])
        if s == base:
            z[4:8] = b"\x00\x00\x00\x00"
        print("dir%d %s: sum=%#010x need=%#010x diff=%#x" % (i, sname, u32sum(z, 0, len(z)), (-stored) & 0xFFFFFFFF, (u32sum(z, 0, len(z)) - ((-stored) & 0xFFFFFFFF)) & 0xFFFFFFFF))
