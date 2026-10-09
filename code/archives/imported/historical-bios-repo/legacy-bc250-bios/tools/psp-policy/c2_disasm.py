# C2: runtime unlock - final static links.
# 1) fn@0x3528 (token install @0xE25814, dispatcher cmd 0x100B -> arm 0xC0C4)
# 2) fn@0x1167c (registry reader @0xE5CBDC) - does it consult slot table 0xE4E538?
# 3) fn@0x20d4 sequencer + fn@0x2178 apply-one (reads 0xE5CBDC @0x20da, calls 0x1167c @0x218a)
# 4) all literal-pool refs to 0xE4E538 (slot table) and 0xE5CBDC (registry)
# 5) svc inventory of fn@0x3528 and fn@0x13468 (supervisor notification hypothesis)
import struct
import capstone

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
ROM = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()
CON = ROM[0x984F00:0x984F00 + 0x1A790]
body = CON[0x100:]
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
md.skipdata = True
out = []
P = out.append


def dump(name, start, end):
    P("== %s : 0x%04x..0x%04x ==" % (name, start, end))
    for i in md.disasm(body[start:end], start):
        extra = ""
        if i.mnemonic in ("ldr", "ldr.w") and "pc" in i.op_str:
            try:
                imm = int(i.op_str.split("#")[-1].rstrip("]"), 0)
                lit = struct.unpack_from("<I", body, ((i.address + 4) & ~3) + imm)[0]
                extra = " ; lit@0x%04x = 0x%08x" % (((i.address + 4) & ~3) + imm, lit)
            except Exception:
                pass
        if i.mnemonic in ("bl", "blx") and "#" in i.op_str:
            extra += " ; CALL"
        if i.mnemonic == "svc":
            extra += " ; SVC"
        P("0x%06x  %-8s %-40s%s" % (i.address, i.mnemonic, i.op_str, extra))
    P("")


dump("fn@0x3528 token-install (cmd 0x100B -> arm 0xC0C4)", 0x3528, 0x35c2)
dump("arm 0xC0C4 dispatcher context (cmd 0x100B)", 0xC0C4, 0xC0D0)
dump("fn@0x1167c registry reader", 0x1167c, 0x11760)
dump("fn@0x20d4 sequencer (cmd 0x1033)", 0x20D4, 0x2178)
dump("fn@0x2178 apply-one-group", 0x2178, 0x21D0)

# literal scan: which functions load 0xE4E538 / 0xE5CBDC / 0xE25814 / 0xE5CB..0xE5CD..
P("== literal-pool refs (u32 == target) in whole body ==")
for target in (0xE4E538, 0xE5CBDC, 0xE25814):
    P("-- target 0x%08x --" % target)
    off = 0
    while True:
        off = body.find(struct.pack("<I", target), off)
        if off < 0:
            break
        P("   lit@body+0x%04x" % off)
        off += 1
    P("")

# any 0xE5CBxx-range literals (registry spans 0xE5CBDC..0xE5CBDC+0x140?)
P("== all literals in 0xE5CB00..0xE5CD40 range ==")
for off in range(0, len(body) - 4, 4):
    v = struct.unpack_from("<I", body, off)[0]
    if 0xE5CB00 <= v < 0xE5CD40:
        P("   lit@body+0x%04x = 0x%08x" % (off, v))

open(r"C:\Users\OWNER\bc250-bios\evidence\c2_disasm.txt", "w").write("\n".join(out))
print("written c2_disasm.txt, %d lines" % len(out))
