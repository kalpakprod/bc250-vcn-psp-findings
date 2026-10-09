# A18: verify case-0x24 bl target (raw hex), dump fn@0x135E4 (registrar?), helpers
# (0x14e4 ARM?, 0x1450, 0xd1fc hash?, 0x88fc 0x100-gate, 0x9f5c gate, 0x17124 logger),
# callers of fn@0x1346a, refs to RAM 0xE4E538 / 0xE25814.
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


def u16(off):
    return struct.unpack_from("<H", body, off)[0]


print("== raw bytes @0xc556..0xc568 + manual bl decode ==")
for off in range(0xC556, 0xC568, 2):
    print("  %#06x: %04x" % (off, u16(off)))
# bl T1: first half 0xF000|(hi10>>11), second 0xF800|(lo11) ; check both orderings
w0, w1 = u16(0xC55C), u16(0xC55E)
print("  words @0xc55c: %04x %04x" % (w0, w1))

print("\n== fn@0x135E4 ==")
print(dump(0x135E4, 0x136E0))

print("\n== fn@0x88fc (0x100 check) ==")
print(dump(0x88FC, 0x89B0))
print("\n== fn@0x9f5c (gate) ==")
print(dump(0x9F5C, 0x9FD0))
print("\n== fn@0x17124 (logger) head ==")
print(dump(0x17124, 0x171A4))

print("\n== callers of fn@0x1346a ==")
for a, m, o in INS:
    if m in ("bl", "blx"):
        try:
            t = int(o.split("#")[1] if "#" in o else o, 0)
        except Exception:
            continue
        if t == 0x1346A:
            print("---- caller @%#x ----" % a)
            print(dump(a - 0x40, a + 0x20))

print("\n== refs to 0x00E4E538 / 0x00E25814 in body ==")
for off in range(0, len(body) - 4, 4):
    v = u32(off)
    if v in (0x00E4E538, 0x00E25814):
        print("  @%#06x -> %#010x" % (off, v))

print("\n== fn@0xd1fc (hash compute?) ==")
print(dump(0xD1FC, 0xD2C0))
