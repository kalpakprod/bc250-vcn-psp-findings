# A20: (1) container envelope fields (load/entry -> RAM base); (2) fn-ptr scan with base;
# (3) find $PSP/$BIO dirs in whole ROM, list entries 0x24/0x28/0x45 with addrs;
# (4) group lists of the 0x24 (gasket) and 0x45 blobs wherever they are.
import struct
import capstone

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
ROM = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()
CON = ROM[0x984F00:0x984F00 + 0x1A790]
body = CON[0x100:]
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
md.detail = False
md.skipdata = True
INS = [(i.address, i.mnemonic, i.op_str) for i in md.disasm(body, 0) if i.mnemonic != ".byte"]


def u32(buf, off):
    return struct.unpack_from("<I", buf, off)[0]


print("== container envelope words ==")
for i in range(0, 0x100, 4):
    v = u32(CON, i)
    if v != 0:
        print("  +%02x: %#010x" % (i, v))
print("magic: %r" % CON[0:4])

# candidate fn-ptr scan with unknown base: match low 17 bits
print("\n== fn-ptr scan (match (v & 0x1FFFF) in target set, excluding tiny offsets) ==")
T = {0x1346A: "loader", 0x1346B: "loader|t", 0x1345A: "weakstub", 0x1345B: "weakstub|t",
     0x0FEAC: "interp1", 0x0FEAD: "interp1|t", 0x02178: "interp2", 0x02179: "interp2|t",
     0x020D8: "seq", 0x020D9: "seq|t", 0x13628: "init", 0x13629: "init|t",
     0x1167C: "registry", 0x1167D: "registry|t"}
for off in range(0, len(body) - 4, 4):
    v = u32(body, off)
    m = v & 0x1FFFF
    if m in T and v > 0x100000:
        print("  @%#06x = %#010x -> base=%#010x (%s)" % (off, v, v & ~0x1FFFF, T[m]))

print("\n== $PSP / $BIO dirs in ROM ==")
dirs = []
for off in range(0, len(ROM) - 0x100, 4):
    if ROM[off:off + 4] in (b"$PSP", b"$BIO", b"$PL2", b"$B2L"):
        dirs.append((off, ROM[off:off + 4]))
for off, magic in dirs:
    n = u32(ROM, off + 8)
    print("  dir @%#08x magic=%r count=%d" % (off, magic, n))
    if n > 0x60:
        continue
    for i in range(n):
        e = off + 0x10 + 0x10 * i
        typ, flags, size, addr = struct.unpack_from("<BBBBII", ROM, e)
        lob, hib = struct.unpack_from("<HH", ROM, e + 8)
        full = (addr & 0xFFFFFF) | (hib << 16)
        if typ in (0x24, 0x28, 0x45, 0x24 + 0x80, 0x28 + 0x80, 0x45 + 0x80):
            print("    ent[%2d] type=%#04x size=%#x addr=%#010x" % (i, typ, size, full))

# group-list parse of blob at given flash addr
def parse_blob(name, addr, size):
    print("\n== %s @%#x size=%#x ==" % (name, addr, size))
    if ROM[addr:addr + 4] != b"$PS1":
        print("  not $PS1: %r" % ROM[addr:addr + 8])
        return
    env_size = u32(ROM, addr + 4)
    print("  envelope: size=%#x, next-words: %s" % (
        env_size, " ".join("%08x" % u32(ROM, addr + 8 + 4 * i) for i in range(6))))
    b = addr + 0x100
    cnt = u32(ROM, b)
    print("  body word0(count?)=%#x, w1..3: %08x %08x %08x" % (
        cnt, u32(ROM, b + 4), u32(ROM, b + 8), u32(ROM, b + 12)))
    o = b + 0x40
    for i in range(min(cnt, 16)):
        t, c = u32(ROM, o), u32(ROM, o + 4)
        pairs = [(u32(ROM, o + 8 + 8 * j), u32(ROM, o + 12 + 8 * j)) for j in range(min(c, 2))]
        print("    grp[%d] type=%#06x count=%-3d head=%s" % (i, t, c, pairs))
        o += 8 + 8 * c


# find gasket/0x45 via dir entries then parse (fill after seeing the listing)
