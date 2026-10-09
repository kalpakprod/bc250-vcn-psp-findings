# A26: full pair lists of donor (cezanne_uefi BIOS.bin) gasket/0x45 groups 0x201/0x280/0x281/0x210;
# where do D3-B2 VCN-tail addresses {0x0900C234, 0x0900C914, 0x0900C930, 0x0900CB80} live
# (donor vs stock, group, value); xx234-family subset of 0x201 (stock ~40 -> 1, donor 0/absent).
import struct, sys, io, os

DON = r"C:\Users\OWNER\tmp_bc250\recon\cezanne_uefi\BIOS.bin"
STOCK = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files\BC250_3.00.ROM"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), r"..\..\evidence\a26_donor_pairs.txt")
TARGETS = [0x0900C234, 0x0900C914, 0x0900C930, 0x0900CB80]


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


log = io.StringIO()


def P(s=""):
    print(s)
    log.write(s + "\n")


don = open(DON, "rb").read()
sto = open(STOCK, "rb").read()

# locate gasket 0x24 / policy 0x45 blobs: scan ALL dir magics (donor is a multi-image with 4 dir copies)
def find_blobs(buf):
    res = {}
    for doff in range(0, len(buf) - 0x110, 4):
        if buf[doff:doff + 4] not in (b"$PSP", b"$BIO", b"$PL2", b"$B2L"):
            continue
        n = u32(buf, doff + 8)
        if not (0 < n <= 0x60):
            continue
        for i in range(n):
            e = doff + 0x10 + 0x10 * i
            typ = buf[e]
            addr = u32(buf, e + 8) & 0xFFFFFF
            if typ in (0x24, 0x45) and typ not in res:
                gl = groups_of(buf, addr)
                if gl:
                    res[typ] = gl
                    P("blob %#x found via dir@%#x @%#x: %s" % (typ, doff, addr,
                      " ".join("%x:%d" % (t, c) for t, c, _ in gl)))
    return res


don_blobs = find_blobs(don)
sto_blobs = find_blobs(sto)

xx234 = lambda a: (a & 0xFFF) == 0x234 and (a >> 20) == 0x090  # SMN 0x090xxxxx +0x234 family

for tag, blobs, buf in (("DONOR", don_blobs, don), ("STOCK", sto_blobs, sto)):
    for typ in (0x24, 0x45):
        gl = blobs.get(typ)
        if not gl:
            P("%s type %#x: no groups" % (tag, typ))
            continue
        for t, c, po in gl:
            if t not in (0x201, 0x280, 0x281, 0x210):
                continue
            pl = pairlist(buf, po, c)
            P("%s %02x grp %#x count=%d" % (tag, typ, t, c))
            if t in (0x201, 0x280):
                full = os.path.join(os.path.dirname(OUT), "a26_%s_%02x_grp%03x_full.txt" % (tag, typ, t))
                with open(full, "w") as f:
                    for a, v in pl:
                        f.write("%#010x -> %#010x\n" % (a, v))
                P("  full list -> %s" % full)
                # subsets of interest
                hits = [(a, v) for a, v in pl if a in TARGETS]
                P("  D3-B2 tail targets: %s" % (["%#x->%#x" % hv for hv in hits] or "NONE"))
                fam = [(a, v) for a, v in pl if xx234(a)]
                P("  xx234-family (%d): %s" % (len(fam), " ".join("%x->%x" % hv for hv in fam[:50])))
            if t == 0x210:
                P("  pairs: %s" % "; ".join("%x->%x" % pv for pv in pl))

# D3-B2 tail verdict vs donor
P("")
P("== D3-B2 VCN tail cross-check ==")
don280 = None
for t, c, po in don_blobs[0x24]:
    if t == 0x280:
        don280 = pairlist(don, po, c)
dmap = {}
for a, v in don280:
    dmap.setdefault(a, []).append(v)
sto280 = None
for t, c, po in sto_blobs[0x24]:
    if t == 0x280:
        sto280 = pairlist(sto, po, c)
smap = {}
for a, v in sto280:
    smap.setdefault(a, []).append(v)
for a in TARGETS:
    P("  %#010x: donor-0x280=%s stock-0x280=%s" % (a, [hex(v) for v in dmap.get(a, [])] or "ABSENT",
                                                  [hex(v) for v in smap.get(a, [])] or "ABSENT"))

open(OUT, "w").write(log.getvalue())
print("\nsaved: %s" % OUT)
