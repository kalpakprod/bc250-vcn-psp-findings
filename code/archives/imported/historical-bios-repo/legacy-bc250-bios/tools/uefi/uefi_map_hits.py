# Map gid-constant hits in decompressed FVMAIN to FFS modules (UI names).
import struct, re, sys

DEC = r"C:\Users\OWNER\tmp_bc250\recon\uefi_ffs\FV@ae0000_0b_9E21FD93_78.LZMA.dec"
d = open(DEC, "rb").read()
FVH = b"_FVH"

# locate nested FV base (sig at fvbase+0x28)
m = re.search(re.escape(FVH), d[:0x100])
fvstart = m.start() - 0x28
fvlen = struct.unpack_from("<Q", d, fvstart + 0x20)[0]
hdrlen = struct.unpack_from("<H", d, fvstart + 0x30)[0]
print("FV base=%#x len=%#x hdrlen=%#x" % (fvstart, fvlen, hdrlen))

fv = d[fvstart:fvstart + fvlen]

HITS = {
    0x1703: [0x24dec, 0xa708c, 0x115870],
    0x1701: [0xa70b6, 0x2d821b, 0x30baea],
    0x1704: [0xa7073, 0x30baa7],
    "APCB": [0xa6a84, 0xa6adb, 0xa7a63],
}

files = []  # (start_img, end_img, guid, ui, ftype)
off = hdrlen
while off + 0x18 <= len(fv):
    g = fv[off:off + 16]
    if g == b"\xff" * 16:
        # pad file (FF guid, plausible size) -> skip; free space -> stop
        size = fv[off + 0x14] | (fv[off + 0x15] << 8) | (fv[off + 0x16] << 16)
        if size == 0xFFFFFF or size < 0x18 or off + size > len(fv):
            break
        off = (off + size + 7) & ~7
        continue
    ftype = fv[off + 0x12]
    size = fv[off + 0x14] | (fv[off + 0x15] << 8) | (fv[off + 0x16] << 16)
    state = fv[off + 0x17]
    if size == 0xFFFFFF or size < 0x18 or off + size > len(fv):
        break
    if state == 0xFF:
        break
    # sections: find UI section (type 0x15) and PE32 (0x10)
    soff = off + 0x18
    ui = None
    pe = []
    o = soff
    while o + 4 <= off + size:
        ssz = fv[o] | (fv[o + 1] << 8) | (fv[o + 2] << 16)
        stp = fv[o + 3]
        if ssz < 4 or o + ssz > off + size:
            break
        if stp == 0x15:  # UI
            ui = fv[o + 4:o + ssz].decode("utf-16-le", "ignore").rstrip("\x00")
        if stp == 0x10:  # PE32
            pe.append((fvstart + o + 4, fvstart + o + ssz))
        o += ssz
        o = (o + 3) & ~3
    gs = "%08X-%04X-%04X" % (struct.unpack("<I", g[:4])[0], struct.unpack("<H", g[4:6])[0], struct.unpack("<H", g[6:8])[0])
    files.append((fvstart + off, fvstart + off + size, gs, ui, ftype, pe))
    off = (off + size + 7) & ~7

print("files:", len(files))


def owner(x):
    for (s, e, gs, ui, ft, pe) in files:
        if s <= x < e:
            return ui or gs, s, e, ft, pe
    return None, None, None, None, None


print("\n=== hit mapping (image coords) ===")
for k, offs in HITS.items():
    for x in offs:
        nm, s, e, ft, pe = owner(x)
        info = "%s [%#x-%#x] type=%02x" % (nm, s, e, ft) if nm else "UNMAPPED"
        extra = ""
        if pe:
            for (ps, pe_) in pe:
                if ps <= x < pe_:
                    extra = " PE32+%#x" % (x - ps)
        print("  %s @ %#x -> %s%s" % (k, x, info, extra))

print("\n=== gid x86 code region 0xa7060-0xa70e0 owner ===")
nm, s, e, ft, pe = owner(0xa7060)
print("  owner:", nm, hex(s), hex(e), "type=%02x" % ft)

# also: which module contains 0x1703 in its PE32 CONTENT
print("\n=== modules whose PE32 contains gid u32s ===")
for (s, e, gs, ui, ft, pe) in files:
    if not pe:
        continue
    for (ps, pe_) in pe:
        blob = d[ps:pe_]
        for gid, name in ((0x1703, "DFG"), (0x1701, "PSPG"), (0x1704, "MEMG"), (0x1702, "CCXG"), (0x1705, "GNBG")):
            n = blob.count(struct.pack("<I", gid))
            if n:
                first = blob.find(struct.pack("<I", gid))
                print("  %-22s PE32@%#x  %s x%d first@+%#x" % (ui or gs, ps, name, n, first))
