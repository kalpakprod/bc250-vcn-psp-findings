# B1d: external caller scan. (1) parse $PSP dir @0x8E0000, list all 19 entries.
# (2) dump TOS container 0x28 header (first 0x100 bytes) and interpret.
# (3) scan EVERY directory blob + whole ROM for constants tying an external
# component to the container/gasket: 0x984F00/0x982000 (SPI addrs),
# 0x3E810/0x3E814 (gasket group-0x210 write targets), 0xFEAC/0xBA98/0xC7AA
# (container-relative entry candidates), the 12 gasket command words,
# 0xFFFF0001/0x1033/0x100C (dispatcher commands).
import struct

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
ROM = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()
u32 = lambda b, o: struct.unpack_from("<I", b, o)[0]

out = []
P = out.append

DIR = 0x8E0000
n = u32(ROM, DIR + 8)
P("== $PSP dir @%#x, %d entries ==" % (DIR, n))
blobs = []
for i in range(n):
    e = DIR + 0x10 + 0x10 * i
    typ, flags = ROM[e], ROM[e + 1]
    size = u32(ROM, e + 4)
    addr = u32(ROM, e + 8) & 0xFFFFFF
    P("  ent[%2d] type=%#04x flags=%#x size=%#x addr=%#08x" % (i, typ, flags, size, addr))
    blobs.append((typ, addr, size))

# --- container 0x28 header dump ---
caddr, csize = [(a, s) for t, a, s in blobs if t == 0x28][0]
P("")
P("== TOS container 0x28 @%#08x header (first 0x100 bytes) ==" % caddr)
for off in range(0, 0x100, 4):
    v = u32(ROM, caddr + off)
    asc = "".join(chr(c) if 32 <= c < 127 else "." for c in ROM[caddr + off:caddr + off + 4])
    P("  +%#04x: %010x  %s" % (off, v, asc))

# --- constant scan ---
NEEDLES = {
    0x984F00: "container-0x28 SPI addr",
    0x982000: "gasket-0x24 SPI addr",
    0x3E810: "gasket 0x210 pair addr (trigger)",
    0x3E814: "gasket 0x210 pair addr (command word)",
    0x000FEAC: "interp fn@0xFEAC offset",
    0x000BA98: "dispatcher fn@0xBA98 offset",
    0x00C7AA: "dispatcher tail",
    0xFFFF0001: "cmd apply-all",
    0x00001033: "cmd sequencer",
    0x0000100C: "cmd loader",
    0x00001000: "cmd donor",
}
for w in (0x2232C240, 0x2233C241, 0x2262C24E, 0x226EC250, 0x2278C261, 0x244FC441,
          0x244EC442, 0x244DC443, 0x226CC24F, 0x2440C440, 0x2544C382, 0xF853C480):
    NEEDLES[w] = "gasket word %#010x" % w


def scan(buf, base, label):
    res = []
    for val, desc in NEEDLES.items():
        pat = struct.pack("<I", val)
        start = 0
        while True:
            k = buf.find(pat, start)
            if k < 0:
                break
            res.append((base + k, val, desc))
            start = k + 1
    for a, v, d in res:
        # which blob region
        reg = "outside-dirs"
        for t, ba, bs in blobs:
            if ba <= a < ba + bs:
                reg = "blob type %#x" % t
        P("  hit %#010x %-28s @ROM %#010x (%s)" % (v, d, a, reg))
    return res


P("")
P("== whole-ROM u32 constant scan (blob-attributed) ==")
scan(ROM, 0, "ROM")

P("")
P("== per-blob scan (also u16 halves of key addrs/offsets) ==")
for t, a, s in blobs:
    buf = ROM[a:a + s]
    hits = []
    for val, desc in NEEDLES.items():
        k = buf.find(struct.pack("<I", val))
        if k >= 0:
            hits.append("%#x:%s@+%#x" % (val, desc, k))
    # u16 halves for 0x3E814 / 0xFEAC / 0xBA98 (movw imm16)
    for val, name in ((0x3E814 & 0xFFFF, "3E814"), (0x3E810 & 0xFFFF, "3E810"),
                      (0xFEAC, "FEAC"), (0xBA98, "BA98")):
        k = 0
        while True:
            k = buf.find(struct.pack("<H", val), k)
            if k < 0:
                break
            hits.append("u16 %s@+%#x" % (name, k))
            k += 1
    if hits:
        P("  blob %#04x @%#x size %#x: %s" % (t, a, s, " ; ".join(hits[:12])))

open(r"C:\Users\OWNER\bc250-bios\evidence\b1_extscan.txt", "w").write("\n".join(out))
print("written b1_extscan.txt, %d lines" % len(out))
