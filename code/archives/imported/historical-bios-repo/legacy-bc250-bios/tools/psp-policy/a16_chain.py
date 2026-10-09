# A16: close the chain: who loads/points the RAM blob @0xE5CBDC; dump fn@0x1345a (case-0x24 target),
# the dispatcher fn start + loop head, raw pools, and the two more pair-appliers (0x1ed0, 0x21b0).
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
AMAP = {a: (m, o) for a, m, o in INS}


def dump(lo, hi):
    return "\n".join("%#08x  %-8s %s" % (a, m, o) for a, m, o in INS if lo <= a < hi)


def u32(off):
    return struct.unpack_from("<I", body, off)[0]


print("== raw pool region 0x116b0..0x11720 ==")
for off in range(0x116B0, 0x11720, 4):
    print("  %#06x: %#010x" % (off, u32(off)))

print("\n== all refs to RAM 0x00E5CBDC (and nearby 0xE5CCxx) in body u32s ==")
for off in range(0, len(body) - 4, 4):
    v = u32(off)
    if 0x00E5C000 <= v <= 0x00E5D000:
        # find enclosing fn (prev push {.., lr} within 0x400)
        fs = max(a for a, m, o in INS if a <= off and "lr}" in o.replace(" ", "")) if any(
            a <= off for a, m, o in INS if "lr}" in o.replace(" ", "")) else 0
        print("  @%#06x -> %#010x (near fn ~%#x)" % (off, v, fs))

print("\n== fn@0x1345a (case 0x24 handler target) ==")
print(dump(0x1345A, 0x135E0))

print("\n== pair-applier @0x1ed0 ==")
print(dump(0x1EB0, 0x1F20))
print("\n== pair-applier @0x21b0 ==")
print(dump(0x2190, 0x21F0))

print("\n== loop head @0xc7aa ==")
print(dump(0xC790, 0xC820))
