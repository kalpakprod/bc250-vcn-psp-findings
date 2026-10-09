# Extract Setup module PE32 from decompressed FVMAIN; dump regions around
# DFG 0x1703 (+0x102a4) and SMN 0x0900CC00 (+0x12f56); also list all
# {0x20,0x20} APCB-ish headers in CbsSetupDxe PE32.
import struct

DEC = r"C:\Users\OWNER\tmp_bc250\recon\uefi_ffs\FV@ae0000_0b_9E21FD93_78.LZMA.dec"
img = open(DEC, "rb").read()

TARGETS = {0x105550: "Setup", 0xb781c - 0x18: "CbsSetupDxe"}
# note: 0xb781c was the PE32 section offset inside CbsSetupDxe file; find file starts by UI walk below.

fvstart = 0x10
fvlen = struct.unpack_from("<Q", img, fvstart + 0x20)[0]
hdrlen = struct.unpack_from("<H", img, fvstart + 0x30)[0]
fv = img[fvstart:fvstart + fvlen]

off = hdrlen
files = []
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
    pe = None
    while o + 4 <= off + size:
        ssz = fv[o] | (fv[o + 1] << 8) | (fv[o + 2] << 16)
        stp = fv[o + 3]
        if ssz < 4 or o + ssz > off + size:
            break
        if stp == 0x15:
            ui = fv[o + 4:o + ssz].decode("utf-16-le", "ignore").rstrip("\x00")
        if stp == 0x10:
            pe = fv[o + 4:o + ssz]
        o += ssz
        o = (o + 3) & ~3
    if ui:
        files.append((ui, fvstart + off, pe))
    off = (off + size + 7) & ~7

for ui, foff, pe in files:
    if ui in ("Setup", "CbsSetupDxe"):
        fn = r"C:\Users\OWNER\tmp_bc250\recon\uefi_ffs\%s.PE32" % ui
        open(fn, "wb").write(pe)
        print("saved %s (%d bytes) file@%#x" % (fn, len(pe), foff))

# Setup regions
d = open(r"C:\Users\OWNER\tmp_bc250\recon\uefi_ffs\Setup.PE32", "rb").read()
for ctr, note in ((0x102a4, "DFG 0x1703"), (0x12f56, "SMN 0x0900CC00")):
    print("\n=== Setup around +%#x (%s) ===" % (ctr, note))
    a = ctr - 0x40
    for o in range(a, ctr + 0x60, 16):
        row = d[o:o + 16]
        print("+%#06x: %s  %s" % (o, row.hex(" "), "".join(chr(c) if 32 <= c < 127 else "." for c in row)))

# all 0x1703 + all 0900Cxxx in Setup
print("\nall DFG 0x1703 in Setup:", [hex(i) for i in range(len(d) - 3) if struct.unpack_from("<I", d, i)[0] == 0x1703])
print("all 0900Cxxx in Setup:", [hex(struct.unpack_from("<I", d, i)[0]) for i in range(len(d) - 3) if 0x0900C000 <= struct.unpack_from("<I", d, i)[0] <= 0x0900CFFF])

# CbsSetupDxe: dump {0x20,0x20} header contexts (embedded APCB groups?)
c = open(r"C:\Users\OWNER\tmp_bc250\recon\uefi_ffs\CbsSetupDxe.PE32", "rb").read()
print("\nCbsSetupDxe size:", len(c))
hits = [i for i in range(len(c) - 8) if c[i:i + 4] == b"\x20\x20\x00\x00" and c[i + 4:i + 8] == b"\x20\x20\x00\x00"]
print("double-{0x20,0x20} sites:", len(hits))
for i in hits[:12]:
    print("\n+%#x:" % i)
    for o in range(i - 0x10, i + 0x30, 16):
        row = c[o:o + 16]
        print("  +%#06x: %s  %s" % (o, row.hex(" "), "".join(chr(x) if 32 <= x < 127 else "." for x in row)))
