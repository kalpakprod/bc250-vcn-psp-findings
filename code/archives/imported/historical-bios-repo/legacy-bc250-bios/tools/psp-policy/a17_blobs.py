# A17: (1) fn@0x20d8 cluster (2nd interpreter + blob ptr usage); (2) baked 10-pair pool + flag;
# (3) fn@0x6800 parser ({0x9000,0x7F} struct); (4) fn@0x1346a true start + pools 0x135D4/0x135DC.
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


def dump(lo, hi):
    return "\n".join("%#08x  %-8s %s" % (a, m, o) for a, m, o in INS if lo <= a < hi)


def u32(off):
    return struct.unpack_from("<I", body, off)[0]


def hexd(off, n):
    return " ".join("%08x" % u32(off + 4 * i) for i in range(n // 4))


print("== fn@0x20d8 cluster (2nd interpreter) ==")
print(dump(0x20D8, 0x2192))

print("\n== baked pair pool fn@0x1ec6: pools ==")
# ldr r6,[pc,#0x1c] @0x1ed0 -> base 0x1ED4+0x1C=0x1EF0 ; flag ldr r0,[pc,#0x24]@0x1ec4 -> 0x1EC8+0x24=0x1EEC
print("flag pool @0x1EEC = %#010x" % u32(0x1EEC))
print("pairs pool @0x1EF0 (10 pairs = 0x50 bytes):")
for i in range(10):
    print("  pair[%2d] addr=%#010x value=%#010x" % (i, u32(0x1EF0 + 8 * i), u32(0x1EF4 + 8 * i)))

print("\n== fn@0x6800 ({0x9000,0x7F} parser) ==")
print(dump(0x6800, 0x6920))

print("\n== fn containing 0x1346a: start search 0x133F0..0x13470 ==")
print(dump(0x133F0, 0x13470))
print("\n== loader pools: 0x135CC..0x135E4 ==")
for off in range(0x135CC, 0x135E8, 4):
    print("  %#06x: %#010x" % (off, u32(off)))
print("expected 0x20B @0x135D4: " + hexd(0x135D4, 0x20))
print("16-slot table @0x135DC: " + hexd(0x135DC, 0x40))
