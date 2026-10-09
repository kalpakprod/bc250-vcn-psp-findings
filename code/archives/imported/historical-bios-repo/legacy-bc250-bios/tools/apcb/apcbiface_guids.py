# Extract protocol GUIDs from AmiApcbLibInterface (C92C9385): disasm InstallProtocolInterface /
# locate GUID-looking data in .data; then grep the whole FVMAIN image for these GUIDs and map to modules.
import struct, sys
import capstone

DIR = r"C:\Users\OWNER\tmp_bc250\recon\uefi_ffs"
IFACE = DIR + r"\FV@ae0000_0b_9E21FD93_78.LZMA.dec_07_C92C9385_b5270.PE32"
DEC = DIR + r"\FV@ae0000_0b_9E21FD93_78.LZMA.dec"

d = open(IFACE, "rb").read()
print("AmiApcbLibInterface size:", len(d))

e_lfanew = struct.unpack_from("<I", d, 0x3C)[0]
nsec = struct.unpack_from("<H", d, e_lfanew + 6)[0]
optsz = struct.unpack_from("<H", d, e_lfanew + 20)[0]
secoff = e_lfanew + 24 + optsz
imagebase = struct.unpack_from("<Q", d, e_lfanew + 24 + 24)[0]
secs = []
for i in range(nsec):
    o = secoff + 40 * i
    nm = d[o:o + 8].rstrip(b"\x00").decode()
    vsz, vaddr, rsz, raddr = struct.unpack_from("<IIII", d, o + 8)
    secs.append((nm, vaddr, vsz, raddr, rsz))
    print("sec %-8s VA=%#x VSZ=%#x RAW=%#x RSZ=%#x" % (nm, vaddr, vsz, raddr, rsz))

# GUID heuristic: data1<0xF0000000-ish random, version 4/5, variant 8-b; scan whole module
import re
cands = []
for i in range(0, len(d) - 16, 4):
    d1, d2, d3 = struct.unpack_from("<IHH", d, i)
    if d3 & 0xFFF0 in (0x4000, 0x5000) and (d[10] & 0xC0) == 0x80 and d1 != 0 and d1 < 0xFF000000:
        g = d[i:i + 16]
        # skip PE timestamps etc: require some entropy in tail
        if g[8:16].count(0) < 6:
            cands.append((i, g))
for i, g in cands:
    print("GUID? @+%#x: %08X-%04X-%04X-%s-%s" % (i, struct.unpack("<I", g[:4])[0], struct.unpack("<H", g[4:6])[0], struct.unpack("<H", g[6:8])[0], g[8:10].hex().upper(), g[10:16].hex().upper()))

# Now: grep decompressed FVMAIN for each candidate; map hit offset -> module via uefi_map_hits-style walk
img = open(DEC, "rb").read()
fvstart = 0x10
fvlen = struct.unpack_from("<Q", img, fvstart + 0x20)[0]
hdrlen = struct.unpack_from("<H", img, fvstart + 0x30)[0]
fv = img[fvstart:fvstart + fvlen]
files = []
off = hdrlen
while off + 0x18 <= len(fv):
    g = fv[off:off + 16]
    size = fv[off + 0x14] | (fv[off + 0x15] << 8) | (fv[off + 0x16] << 16)
    if g == b"\xff" * 16:
        if size == 0xFFFFFF or size < 0x18 or off + size > len(fv):
            break
        off = (off + size + 7) & ~7
        continue
    if size == 0xFFFFFF or size < 0x18 or off + size > len(fv):
        break
    o = off + 0x18
    ui = None
    while o + 4 <= off + size:
        ssz = fv[o] | (fv[o + 1] << 8) | (fv[o + 2] << 16)
        stp = fv[o + 3]
        if ssz < 4 or o + ssz > off + size:
            break
        if stp == 0x15:
            ui = fv[o + 4:o + ssz].decode("utf-16-le", "ignore").rstrip("\x00")
        o += ssz
        o = (o + 3) & ~3
    files.append((fvstart + off, fvstart + off + size, ui or "GUID?"))
    off = (off + size + 7) & ~7


def owner(x):
    for s, e, nm in files:
        if s <= x < e:
            return nm
    return "UNMAPPED"


print("\n=== GUID usage across FVMAIN modules ===")
for i, g in cands:
    hits = []
    j = -1
    while True:
        j = img.find(g, j + 1)
        if j < 0:
            break
        hits.append(j)
    if len(hits) > 1:
        print("GUID %08X-%04X-%04X: %d refs" % (struct.unpack("<I", g[:4])[0], struct.unpack("<H", g[4:6])[0], struct.unpack("<H", g[6:8])[0], len(hits)))
        for h in hits[:20]:
            print("   @%#x -> %s" % (h, owner(h)))
