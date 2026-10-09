# A23: (1) all bl-callers of 0x2178 / 0xfeac / 0x1167c; (2) address-space histogram per group
# of gasket & policy45; (3) fn@0x15e4 (memcpy?); (4) dump fn@0x3520-0x35a8 (record builder).
import struct
import capstone

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
ROM = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()
CON = ROM[0x984F00:0x984F00 + 0x1A790]
body = CON[0x100:]
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
md.detail = False
md.skipdata = True
INS = [(i.address, i.mnemonic, i.op_str) for i in md.disasm(body, 0) if i.mnemonic != ".byte"]


def dump(lo, hi):
    return "\n".join("%#08x  %-8s %s" % (a, m, o) for a, m, o in INS if lo <= a < hi)


print("== callers of 0x2178 / 0xfeac / 0x1167c ==")
for a, m, o in INS:
    if m in ("bl", "blx"):
        try:
            t = int(o.split("#")[1] if "#" in o else o, 0)
        except Exception:
            continue
        if t in (0x2178, 0xFEAC, 0x1167C):
            print("---- %s called @%#x ----" % (hex(t), a))
            print(dump(a - 0x30, a + 0x18))

print("\n== fn@0x15e4 (memcpy?) ==")
print(dump(0x15E4, 0x1628))

print("\n== fn@0x3520 (record builder w/ expected) ==")
print(dump(0x34F0, 0x35A8))


def u32(off):
    return struct.unpack_from("<I", ROM, off)[0]


def space(a):
    if a < 0x1000:
        return "small"
    if 0x030000 <= a < 0x040000:
        return "SMN03"
    if 0x090000 <= a < 0x0A0000:
        return "SMN09"
    if 0x0A0000 <= a < 0x100000:
        return "SMN0A-0F"
    if 0x40000000 <= a < 0x50000000:
        return "PCI4"
    if 0xE000000 <= a < 0xF000000:
        return "PSPRAM_E"
    if 0x1000000 <= a < 0x10000000:
        return "RAM_01"
    return "other:%08x" % a


for name, addr in (("GASKET", 0x982000), ("POLICY45", 0x9CA400)):
    b = addr + 0x100
    cnt = u32(b)
    o = b + 0x40
    print("\n== %s address spaces ==" % name)
    for i in range(cnt):
        t, c = u32(o), u32(o + 4)
        hist = {}
        for j in range(c):
            a = u32(o + 8 + 8 * j)
            s = space(a)
            hist[s] = hist.get(s, 0) + 1
        print("  grp %#06x (%3d): %s" % (t, c, sorted(hist.items(), key=lambda x: -x[1])))
        o += 8 + 8 * c
