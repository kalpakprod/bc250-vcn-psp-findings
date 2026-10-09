# Grep decompressed FVMAIN for the APCB interface GUID E857CAF6-C046-45DC-BE3F-EE0765FBA887
# and the AmdApcbObrDxe DEPEX GUIDs; map every hit to its FFS module (UI name).
import struct

DEC = r"C:\Users\OWNER\tmp_bc250\recon\uefi_ffs\FV@ae0000_0b_9E21FD93_78.LZMA.dec"
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
    files.append((fvstart + off, fvstart + off + size, ui or "?"))
    off = (off + size + 7) & ~7


def owner(x):
    for s, e, nm in files:
        if s <= x < e:
            return nm
    return "UNMAPPED"


def fmtguid(g):
    return "%08X-%04X-%04X-%s-%s" % (struct.unpack("<I", g[:4])[0], struct.unpack("<H", g[4:6])[0], struct.unpack("<H", g[6:8])[0], g[8:10].hex().upper(), g[10:16].hex().upper())


GUIDS = {
    "E857CAF6 (APCB interface)": bytes.fromhex("f6ca57e846c0dc45be3fee0765fba887"),
    "DAE670DB (ObrDxe depex 1)": bytes.fromhex("db70e6da652ce941bdf8063c8002de0a"),
    "13A3F0F6 (ObrDxe depex 2)": bytes.fromhex("f6f0a3134a26f03ef2e0dec512342f34"),
}

for name, g in GUIDS.items():
    print("\n=== %s ===" % name)
    j = -1
    n = 0
    while True:
        j = img.find(g, j + 1)
        if j < 0:
            break
        n += 1
        print("  @%#x -> %s" % (j, owner(j)))
    print("  total: %d" % n)
