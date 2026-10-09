# A20b: fixed dir entry parse + group lists + raw dump of 0x17680..0x17800 (ptr table?)
import struct

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
ROM = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()


def u32(buf, off):
    return struct.unpack_from("<I", buf, off)[0]


print("== $PSP / $BIO dirs ==")
ents = {}
for off in range(0, len(ROM) - 0x100, 4):
    if ROM[off:off + 4] in (b"$PSP", b"$BIO", b"$PL2", b"$B2L"):
        n = u32(ROM, off + 8)
        if n > 0x60:
            continue
        print("  dir @%#08x magic=%r count=%d" % (off, ROM[off:off + 4], n))
        for i in range(n):
            e = off + 0x10 + 0x10 * i
            typ = ROM[e]
            flags = ROM[e + 1]
            size = u32(ROM, e + 4)
            addr = u32(ROM, e + 8) & 0xFFFFFF
            if typ in (0x24, 0x28, 0x45, 0xA4, 0xC5):
                print("    ent[%2d] type=%#04x flags=%#x size=%#x addr=%#08x" % (i, typ, flags, size, addr))
                ents.setdefault(typ, []).append((addr, size))


def parse_blob(name, addr, size):
    print("\n== %s @%#x size=%#x ==" % (name, addr, size))
    m = ROM[addr:addr + 4]
    if m != b"$PS1":
        print("  head: %r" % ROM[addr:addr + 0x20])
        return
    print("  env: size=%#x w2..5: %s" % (u32(ROM, addr + 4),
          " ".join("%08x" % u32(ROM, addr + 8 + 4 * i) for i in range(4))))
    b = addr + 0x100
    cnt = u32(ROM, b)
    print("  body w0=%#x w1..3: %08x %08x %08x" % (cnt, u32(ROM, b + 4), u32(ROM, b + 8), u32(ROM, b + 12)))
    o = b + 0x40
    for i in range(min(cnt, 16)):
        t, c = u32(ROM, o), u32(ROM, o + 4)
        pairs = [(u32(ROM, o + 8 + 8 * j), u32(ROM, o + 12 + 8 * j)) for j in range(min(c, 2))]
        print("    grp[%d] type=%#06x count=%-3d head=%s" % (i, t, c, pairs))
        o += 8 + 8 * c


for typ in (0x24, 0x45):
    for addr, size in ents.get(typ, []):
        parse_blob("TYPE %#x" % typ, addr, size)

print("\n== raw u32s 0x17680..0x17800 (container body tail) ==")
for off in range(0x17680, 0x17800, 4):
    v = u32(ROM, 0x984F00 + 0x100 + off)
    print("  %#06x: %#010x" % (off, v))
