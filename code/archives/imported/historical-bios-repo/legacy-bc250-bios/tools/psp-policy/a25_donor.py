# A25: THE DONOR (cezanne_uefi BIOS.bin): dirs, 0x24/0x45 entries (all!), full group lists,
# grp210/0x280 content, presence of 0x205/0x20a/0x20b, VCN tail pairs, diff vs stock gasket pairs.
import struct

DON = r"C:\Users\OWNER\tmp_bc250\recon\cezanne_uefi\BIOS.bin"
STOCK = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files\BC250_3.00.ROM"


def u32(buf, off):
    return struct.unpack_from("<I", buf, off)[0]


def groups_of(buf, addr):
    if addr + 0x104 > len(buf) or buf[addr + 0x10:addr + 0x14] != b"$PS1":
        return None
    b = addr + 0x100
    cnt = u32(buf, b)
    if cnt > 0x40:
        return None
    out = []
    o = b + 0x40
    for i in range(cnt):
        t, c = u32(buf, o), u32(buf, o + 4)
        if c > 0x20000:
            return None
        out.append((t, c, o + 8))
        o += 8 + 8 * c
    return out


def pairlist(buf, po, c):
    return [(u32(buf, po + 8 * j), u32(buf, po + 4 + 8 * j)) for j in range(c)]


buf = open(DON, "rb").read()
print("donor size: %d" % len(buf))
dirs = []
for off in range(0, len(buf) - 0x110, 4):
    if buf[off:off + 4] in (b"$PSP", b"$BIO", b"$PL2", b"$B2L"):
        n = u32(buf, off + 8)
        if 0 < n <= 0x60:
            dirs.append((off, buf[off:off + 4], n))
print("dirs: %s" % [(hex(o), m.decode(), n) for o, m, n in dirs])

blobs = []
for doff, magic, n in dirs:
    for i in range(n):
        e = doff + 0x10 + 0x10 * i
        typ = buf[e]
        size = u32(buf, e + 4)
        addr = u32(buf, e + 8) & 0xFFFFFF
        if typ in (0x24, 0x45):
            gl = groups_of(buf, addr) if size > 0x200 else None
            desc = " ".join("%x:%d" % (t, c) for t, c, _ in gl) if gl else "not-group"
            print("dir@%#x %r ent[%2d] type=%#04x size=%#x @%#x: %s" % (
                doff, magic, i, typ, size, addr, desc))
            if gl:
                blobs.append((typ, addr, gl))

print("\n== donor blob groups detail ==")
for typ, addr, gl in blobs:
    print("--- donor type %#x @%#x ---" % (typ, addr))
    for t, c, po in gl:
        if t in (0x205, 0x20a, 0x20b):
            print("  *** grp %#x count=%d ***" % (t, c))
        if t == 0x210:
            print("  grp 0x210 (%d): %s" % (c, "; ".join("%x->%x" % pv for pv in pairlist(buf, po, c))))
        if t == 0x280 and c > 100:
            pl = pairlist(buf, po, c)
            print("  grp 0x280 count=%d, tail 12 pairs:" % c)
            for a, v in pl[-12:]:
                print("    %#010x -> %#010x" % (a, v))

# stock gasket 0x280 tail for comparison
s = open(STOCK, "rb").read()
sg = groups_of(s, 0x982000)
for t, c, po in sg:
    if t == 0x280:
        pl = pairlist(s, po, c)
        print("\n== stock gasket 0x280 tail 12 (count=%d) ==" % c)
        for a, v in pl[-12:]:
            print("    %#010x -> %#010x" % (a, v))

# donor vs stock: ALL differing pairs in every shared group (gasket)
print("\n== donor vs stock gasket pair diffs (per group) ==")
for t, c, po in sg:
    slist = dict(pairlist(s, po, c))
    for typ, addr, gl in blobs:
        if typ != 0x24:
            continue
        for t2, c2, po2 in gl:
            if t2 == t:
                dlist = pairlist(buf, po2, c2)
                dmap = {}
                for a, v in dlist:
                    dmap.setdefault(a, []).append(v)
                diffs = []
                for a, v in slist.items():
                    dv = dmap.get(a)
                    if dv is None:
                        diffs.append((a, v, "ABSENT"))
                    elif dv[0] != v:
                        diffs.append((a, v, dv[0]))
                for a in dmap:
                    if a not in slist:
                        diffs.append((a, "absent", dmap[a]))
                print("  grp %#x: %d diffs" % (t, len(diffs)))
                for a, v1, v2 in diffs[:40]:
                    print("    %#010x: stock=%s donor=%s" % (a, v1, v2))
