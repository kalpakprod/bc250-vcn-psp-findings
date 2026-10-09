# A29: find the applier via the registry. fn@0xfeac reads the blob registry @0xE5CBDC
# (via fn@0x1167c). Whoever else references 0xE5CBDC (literal pool) is a registry user
# = candidate applier caller. Also: bl-callers of 0x20d8 / 0x9f5c / 0xd1fc; unaligned
# scan for thumb ptrs 0xFEAD/0x1346B/0x2179/0x20D9; heads of the two interpreters.
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


print("== 1) literal-pool refs to registry 0xE5CBDC and blob table 0xE4E538 ==")
for off in range(0, len(body) - 4, 4):
    v = u32(off)
    if v in (0xE5CBDC, 0xE4E538):
        print("---- %#010x @ body+%#06x ----" % (v, off))
        print(dump(off - 0x70, off))

print("\n== 2) bl-callers of 0x20d8 / 0x9f5c / 0xd1fc / 0x1167c ==")
for a, m, o in INS:
    if m in ("bl", "blx"):
        try:
            t = int(o.split("#")[1] if "#" in o else o, 0)
        except Exception:
            continue
        if t in (0x20D8, 0x9F5C, 0xD1FC, 0x1167C):
            print("---- %#x called @%#x ----" % (t, a))
            print(dump(a - 0x30, a + 0x14))

print("\n== 3) unaligned thumb-ptr scan (0xFEAD, 0x1346B, 0x2179, 0x20D9) ==")
for off in range(0, len(body) - 4, 2):
    v = u32(off) if off % 4 == 0 else struct.unpack_from("<I", body, off)[0]
    if v in (0xFEAD, 0x1346B, 0x2179, 0x20D9):
        print("  %#08x @ body+%#06x (align %d)" % (v, off, off % 4))

print("\n== 4) interpreter heads ==")
print("-- fn@0xfeac --")
print(dump(0xFEAC, 0xFF30))
print("-- fn@0x2178 --")
print(dump(0x2178, 0x21D0))
print("-- fn@0x20d8 --")
print(dump(0x20D8, 0x2130))
