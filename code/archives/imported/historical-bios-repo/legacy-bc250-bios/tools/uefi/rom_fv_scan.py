# Enumerate ALL FVs in the 16MB ROM; walk each (incl. LZMA-compressed FV images);
# in every PE32 module: search E857CAF6 and u32s 0x0900Cxxx (gasket bank).
import struct, re, lzma
import capstone

ROM = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files\BC250_3.00_CHIPSETMENU.ROM"
rom = open(ROM, "rb").read()
print("ROM size:", len(rom))

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
APCB_G = bytes.fromhex("f6ca57e846c0dc45be3fee0765fba887")
LZMA_GUID = bytes.fromhex("98584eee143959429d6edc7bd79403cf")


def lzma_edk2(data):
    try:
        return lzma.LZMADecompressor(format=lzma.FORMAT_ALONE).decompress(data)
    except Exception:
        try:
            return lzma.LZMADecompressor(format=lzma.FORMAT_ALONE).decompress(data + b"\x00" * 8)
        except Exception:
            return None


def report(off, name, payload):
    hits_g = payload.find(APCB_G)
    smn = []
    for i in range(0, len(payload) - 3):
        v = struct.unpack_from("<I", payload, i)[0]
        if 0x0900C000 <= v <= 0x0900CFFF:
            smn.append((i, v))
    if hits_g >= 0 or smn:
        print("  MODULE %-26s @rom%#x  APCB_GUID@+%#x  SMN0900C:%s" % (name[:26], off, hits_g, ["%#x@+%#x" % (v, i) for i, v in smn[:6]] or "-"))


def walk_sections(blob):
    out = []
    o = 0
    while o + 4 <= len(blob):
        ssz = blob[o] | (blob[o + 1] << 8) | (blob[o + 2] << 16)
        stp = blob[o + 3]
        if ssz < 4 or o + ssz > len(blob):
            break
        payload = blob[o + 4:o + ssz]
        out.append((stp, payload))
        o += ssz
        o = (o + 3) & ~3
    return out


def walk_fv(fv, base, depth=0):
    files = []
    if len(fv) < 0x48 or fv[0x28:0x2C] != b"_FVH":
        return files
    fvlen = struct.unpack_from("<Q", fv, 0x20)[0]
    hdrlen = struct.unpack_from("<H", fv, 0x30)[0]
    if fvlen > len(fv):
        fvlen = len(fv)
    off = hdrlen
    while off + 0x18 <= fvlen and depth < 4:
        g = fv[off:off + 16]
        size = fv[off + 0x14] | (fv[off + 0x15] << 8) | (fv[off + 0x16] << 16)
        state = fv[off + 0x17]
        if g == b"\xff" * 16:
            if size == 0xFFFFFF or size < 0x18 or off + size > fvlen:
                break
            off = (off + size + 7) & ~7
            continue
        if size == 0xFFFFFF or size < 0x18 or off + size > fvlen or state == 0xFF:
            break
        ftype = fv[off + 0x12]
        ui = None
        pe = None
        inner_fv = None
        for stp, payload in walk_sections(fv[off + 0x18:off + size]):
            if stp == 0x15:
                try:
                    ui = payload.decode("utf-16-le", "ignore").rstrip("\x00")
                except Exception:
                    pass
            elif stp == 0x10:
                pe = payload
            elif stp == 0x02 and payload[:16] == LZMA_GUID:
                data_off = struct.unpack_from("<H", payload, 0x10)[0]
                stream = payload[data_off - 4:] if data_off >= 4 else payload[0x14:]
                dec = lzma_edk2(stream)
                if dec:
                    m = re.search(re.escape(b"_FVH"), dec[:0x100])
                    if m:
                        fvstart = max(0, m.start() - 0x28)
                        inner_fv = dec[fvstart:]
        gs = "%08X" % struct.unpack("<I", g[:4])[0]
        nm = ui or gs
        if pe is not None:
            files.append(("PE32", base + off, nm, pe))
            report(base + off, nm + "/" + gs, pe)
        if inner_fv is not None:
            files.append(("FVIN", base + off, nm, inner_fv))
        files.append(("FILE", base + off, nm + "/" + gs, None))
        off = (off + size + 7) & ~7
    return files


def fmtg(g):
    return "%08X-%04X-%04X-%s-%s" % (struct.unpack("<I", g[:4])[0], struct.unpack("<H", g[4:6])[0], struct.unpack("<H", g[6:8])[0], g[8:10].hex().upper(), g[10:16].hex().upper())


fvs = []
for m in re.finditer(re.escape(b"_FVH"), rom):
    s = m.start() - 0x28
    if s < 0:
        continue
    fvlen = struct.unpack_from("<Q", rom, s + 0x20)[0]
    hdrlen = struct.unpack_from("<H", rom, s + 0x30)[0]
    if 0x48 <= hdrlen <= 0x100 and 0x1000 <= fvlen <= len(rom) - s:
        fvs.append((s, fvlen))
        print("FV @%#x len=%#x guid=%s" % (s, fvlen, fmtg(rom[s + 0x10:s + 0x20])))


def process(fv, base, depth=0):
    for kind, off, nm, payload in walk_fv(fv, base, depth):
        if kind == "FVIN" and payload is not None:
            print(" [inner FV @%#x from %s]" % (off, nm))
            process(payload, off, depth + 1)


for s, fvlen in fvs:
    print("\n== walking FV @%#x ==" % s)
    process(rom[s:s + fvlen], s)
