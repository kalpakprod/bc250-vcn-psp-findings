# A19: (1) fn-ptr scan for 0x1346a/b (+interpreters); (2) dump fn@0x13628 full + pools;
# (3) fn@0x10fd0 head; (4) contexts of 0xE4E538/0xE25814 refs (@0x35b8, @0xd500, @0x155d4);
# (5) parse group lists of gasket @0x9E0000 and 0x45 @0x9E4000 from the donor ROM image? NO - from
#     the BC250 stock we work on; and check body layout vs fn@0x1167c registry layout.
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


def u32b(off):
    return struct.unpack_from("<I", body, off)[0]


def u32r(buf, off):
    return struct.unpack_from("<I", buf, off)[0]


print("== fn-ptr scan (thumb bit set) ==")
WANT = {0x0001346A: "loader/verify fn@0x1346a", 0x0001345A: "weak stub", 0x0001345B: "weak stub|t",
        0x0000FEAC: "interp1 fn@0xfeac", 0x0000FEAD: "interp1|t", 0x00002178: "interp2 fn@0x2178",
        0x00002179: "interp2|t", 0x000020D8: "seq-applier fn@0x20d8", 0x000020D9: "seq-applier|t",
        0x000013628: "init fn@0x13628", 0x000013629: "init|t"}
for off in range(0, len(body) - 4, 4):
    v = u32b(off)
    if v in WANT:
        print("  @%#06x = %#010x  (%s)" % (off, v, WANT[v]))

print("\n== fn@0x13628 (module init?) full ==")
print(dump(0x13628, 0x13680))
print("pools: @0x13670=%#010x @0x13674=%#010x @0x13678=%#010x @0x1367C=%#010x" % (
    u32b(0x13670), u32b(0x13674), u32b(0x13678), u32b(0x1367C)))

print("\n== fn@0x10fd0 head ==")
print(dump(0x10FD0, 0x11070))

print("\n== context @0x35b8 (ref 0xE25814) ==")
print(dump(0x3560, 0x35E0))
print("\n== context @0xd500 (ref 0xE4E538) ==")
print(dump(0xD4C0, 0xD540))
print("\n== context @0x155d4 (ref 0xE4E538) ==")
print(dump(0x15590, 0x15600))

print("\n== donor/stock blob group lists ==")
for name, off in (("GASKET@0x9E0000", 0x9E0000), ("POLICY45@0x9E4000", 0x9E4000)):
    blob = ROM[off:off + 0x100]
    print("%s envelope: magic=%r size=%#x ver=%r" % (
        name, blob[0:4], u32r(blob, 4), blob[8:12]))
    bodyo = off + 0x100
    b = ROM[bodyo:bodyo + 0x200]
    print("  body[0:0x40] u32s: " + " ".join("%08x" % u32r(b, i) for i in range(0, 0x40, 4)))
    # walk groups assuming count@0, groups@0x40
    cnt = u32r(b, 0)
    o = 0x40
    print("  count(word0)=%#x; groups from +0x40:" % cnt)
    for i in range(min(cnt if cnt < 0x40 else 0x40, 0x40)):
        t, c = u32r(b, o), u32r(b, o + 4)
        if o + 8 + 8 * c > len(b):
            print("    grp[%d] type=%#06x count=%d (beyond dump)" % (i, t, c))
            break
        pairs = [(u32r(b, o + 8 + 8 * j), u32r(b, o + 12 + 8 * j)) for j in range(min(c, 2))]
        print("    grp[%d] type=%#06x count=%-3d head=%s" % (i, t, c, pairs))
        o += 8 + 8 * c
