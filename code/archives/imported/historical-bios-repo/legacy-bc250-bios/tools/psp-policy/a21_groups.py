# A21: group lists of gasket@0x982000 and policy45@0x9CA400; also envelope details, and the
# 0x10-byte tag; locate E810 pairs and VCN/DF regs; check which blob matches fn@0x20d8's
# {0x201,0x205,0x203,0x20a,0x20b,0x210} vs fn@0xfeac's {0x201,0x203,0x280,0x281}.
import struct

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
ROM = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()


def u32(off):
    return struct.unpack_from("<I", ROM, off)[0]


def parse(name, addr, dsize):
    print("== %s @%#x (dir size %#x) ==" % (name, addr, dsize))
    print("  tag[0:0x10]: %s" % ROM[addr:addr + 0x10].hex())
    e = addr + 0x10
    print("  $PS1 @+%#x: magic=%r size=%#x" % (0x10, ROM[e:e + 4], u32(e + 4)))
    print("  env words +0x08..0x30: " + " ".join("%08x" % u32(e + 8 + 4 * i) for i in range(11)))
    b = addr + 0x100
    cnt = u32(b)
    print("  body: w0(count)=%#x w1=%#x w2=%#x w3=%#x" % (cnt, u32(b + 4), u32(b + 8), u32(b + 12)))
    o = b + 0x40
    total = 0
    for i in range(min(cnt, 20)):
        t, c = u32(o), u32(o + 4)
        print("    grp[%d] type=%#06x count=%-4d pairs@+ %#06x" % (i, t, c, o + 8 - b))
        o += 8 + 8 * c
        total += 1
        if c > 0x10000:
            print("    (bad count, stop)")
            break
    print("    body end offset ~%#x (dir size %#x)" % (o - b, dsize))
    return b


def show_pairs(b, gtype, label, want=None, limit=8):
    cnt = u32(b)
    o = b + 0x40
    for i in range(cnt):
        t, c = u32(o), u32(o + 4)
        if t == gtype:
            print("  %s grp %#x count=%d:" % (label, t, c))
            for j in range(min(c, 0x200)):
                a, v = u32(o + 8 + 8 * j), u32(o + 12 + 8 * j)
                if want is None or a in want or any((a & m) == w for m, w in want if isinstance(w, int)):
                    print("    %#010x -> %#010x" % (a, v))
                    if limit and j >= limit:
                        break
            return o
        o += 8 + 8 * c
    print("  %s: no grp %#x" % (label, gtype))
    return None


G = parse("GASKET 0x24", 0x982000, 0x2E50)
P = parse("POLICY 0x45", 0x9CA400, 0x6E0)

VCN = (0x03E810, 0x03A2011C, 0x0900C234, 0x0900C914, 0x0900C930, 0x0900CB80)
print("\n== VCN/DF/bridge pairs in gasket ==")
for gt in (0x201, 0x203, 0x210, 0x280, 0x281):
    show_pairs(G, gt, "gasket", want=lambda a: a in VCN, limit=6)
print("\n== VCN/DF/bridge pairs in policy45 ==")
for gt in (0x210, 0x211, 0x280, 0x281):
    show_pairs(P, gt, "policy45", want=lambda a: a in VCN, limit=6)

print("\n== full small-group dumps (gasket grp0x210; policy grp0x210) ==")
show_pairs(G, 0x210, "gasket")
show_pairs(P, 0x210, "policy45")
