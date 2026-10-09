# A14: focused dumps - fn containing 0xfec6 (0x280/0x281 dispatch), fn@0x1167c, fn with 0xbe5e switch.
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


print("== fn containing @0xfec6 (0x280/0x281 dispatch) ==")
print(dump(0xFE40, 0xFF80))
print("\n== fn@0x1167c (called before dispatch; maybe 'valid group type?') ==")
print(dump(0x1167C, 0x11760))
print("\n== fn containing @0xbe5e (0x24-0x27 switch) ==")
print(dump(0xBE00, 0xBF90))
