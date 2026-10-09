# B1: mailbox dispatcher command map. Locate the dispatcher function head
# (arms span 0xBE00..0xC7AA), dump the head 0xBBA0..0xBE00, find tbb/tbh
# jump tables (byte/halfword) or if-chains mapping mailbox command number -> arm,
# and resolve every table entry to its arm + first action (bl target / svc).
import struct
import capstone

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
ROM = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()
CON = ROM[0x984F00:0x984F00 + 0x1A790]
body = CON[0x100:]
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
md.detail = True
md.skipdata = True

out = []
P = out.append

INS = list(md.disasm(body, 0))

P("== 1) dispatcher head region 0xBBA0..0xBE00 (linear disasm) ==")
for i in INS:
    if 0xBBA0 <= i.address < 0xBE00:
        P("%#08x  %-8s %s" % (i.address, i.mnemonic, i.op_str))

P("")
P("== 2) all tbb/tbh instructions in container ==")
for i in INS:
    if i.mnemonic in ("tbb", "tbh"):
        P("%#08x  %-8s %s" % (i.address, i.mnemonic, i.op_str))

P("")
P("== 3) function head candidates just before arms: push{lr} in 0xB000..0xBE00 ==")
for k, i in enumerate(INS):
    if 0xB000 <= i.address < 0xBE00 and i.mnemonic.startswith("push") and "lr" in i.op_str:
        P("  head @%#08x: %s %s" % (i.address, i.mnemonic, i.op_str))

open(r"C:\Users\OWNER\bc250-bios\evidence\b1_dispmap.txt", "w").write("\n".join(out))
print("\n".join(out[:0]))
print("written b1_dispmap.txt, %d lines" % len(out))
