# C1: dump crypto fn@0xd1fc (called by loader fn@0x13468 before its memcmp checks)
import struct
import capstone

ROM = open(r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
           r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()
body = ROM[0x984F00 + 0x100:0x984F00 + 0x1A790]
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
md.skipdata = True


def u32(o):
    return struct.unpack_from("<I", body, o)[0]


out = []
for i in md.disasm(body, 0):
    if 0xD1FC <= i.address < 0xD340 and i.mnemonic != ".byte":
        lit = ""
        if i.mnemonic.startswith("ldr") and "pc" in i.op_str:
            try:
                imm = int(i.op_str.split("#")[-1].rstrip("]"), 0)
                base = (i.address + 4) & ~3
                lit = "   ; lit@%#x = %#010x" % (base + imm, u32(base + imm))
            except Exception:
                pass
        out.append("%#08x  %-8s %-40s%s" % (i.address, i.mnemonic, i.op_str, lit))
open(r"C:\Users\OWNER\bc250-bios\evidence\c1_d1fc.txt", "w").write("\n".join(out))
print("wrote", len(out))
