# A22: (1) full 0x210 groups of gasket & policy45; (2) VCN/DF pairs per group; (3) group-type
# lists of ALL 19 dir entries (find the blob with 0x205/0x20a/0x20b for fn@0x20d8).
import struct

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
ROM = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()


def u32(off):
    return struct.unpack_from("<I", ROM, off)[0]


def groups_of(addr):
    """Return list of (type,count,pairs_off) or None if not a $PS1-group blob."""
    if ROM[addr + 0x10:addr + 0x14] != b"$PS1":
        return None
    b = addr + 0x100
    cnt = u32(b)
    if cnt > 0x40:
        return None
    out = []
    o = b + 0x40
    for i in range(cnt):
        t, c = u32(o), u32(o + 4)
        if c > 0x20000:
            return None
        out.append((t, c, o + 8))
        o += 8 + 8 * c
    return out


def dump_group(addr, pairs_off, count, filt=None):
    hits = 0
    for j in range(count):
        a, v = u32(pairs_off + 8 * j), u32(pairs_off + 4 + 8 * j)
        if filt is None or filt(a):
            print("      %#010x -> %#010x" % (a, v))
            hits += 1
    return hits


G = 0x982000
P = 0x9CA400
print("== gasket 0x210 group (all 13 pairs) ==")
for t, c, po in groups_of(G):
    if t == 0x210:
        dump_group(G, po, c)
print("== policy45 0x210 group (all 13 pairs) ==")
for t, c, po in groups_of(P):
    if t == 0x210:
        dump_group(P, po, c)

VCN = {0x03E810, 0x03A2011C, 0x0900C234, 0x0900C914, 0x0900C930, 0x0900CB80,
       0x03E810 & 0xFFFFFF, 0x0090C234, 0x0090C914}
print("\n== VCN/DF/bridge pairs in gasket groups ==")
for t, c, po in groups_of(G):
    n = dump_group(G, po, c, filt=lambda a: (a & 0xFFFFFF) in {0x0E810, 0xA2011C, 0x00C234, 0x00C914, 0x00C930, 0x00CB80} or a in VCN)
    if n:
        print("    ^ in grp %#x (%d pairs scanned)" % (t, c))
print("== VCN/DF/bridge pairs in policy45 groups ==")
for t, c, po in groups_of(P):
    n = dump_group(P, po, c, filt=lambda a: (a & 0xFFFFFF) in {0x0E810, 0xA2011C, 0x00C234, 0x00C914, 0x00C930, 0x00CB80} or a in VCN)
    if n:
        print("    ^ in grp %#x (%d pairs scanned)" % (t, c))

print("\n== group-type lists of all dir entries ==")
DIR = 0x8E0000
n = u32(DIR + 8)
for i in range(n):
    e = DIR + 0x10 + 0x10 * i
    typ = ROM[e]
    size = u32(e + 4)
    addr = u32(e + 8) & 0xFFFFFF
    gl = groups_of(addr) if size > 0x200 else None
    tag = ROM[addr:addr + 0x10].hex() if size else ""
    if gl is not None:
        print("  ent[%2d] type=%#04x size=%#07x @%#08x groups: %s" % (
            i, typ, size, addr, [(hex(t), c) for t, c, _ in gl]))
    else:
        print("  ent[%2d] type=%#04x size=%#07x @%#08x tag=%s (not group-blob)" % (i, typ, size, addr, tag[:16]))
