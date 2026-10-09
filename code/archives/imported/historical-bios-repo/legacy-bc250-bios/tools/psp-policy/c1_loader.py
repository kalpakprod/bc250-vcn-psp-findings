# C1: full disassembly of the $PS1 loader fn@0x13468 (to next push-lr fn head),
# annotated literal pool; the dispatcher arm 0xC0DA context; the fn containing
# refs to 0xE25814 @0x3560; and literal scan of 0xE25800-0xE25900 / 0xE254xx.
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
IDX = {a: k for k, (a, _, _) in enumerate(INS)}


def u32(off):
    return struct.unpack_from("<I", body, off)[0]


def dump(lo, hi):
    out = []
    for a, m, o in INS:
        if lo <= a < hi:
            lit = ""
            # annotate pc-relative ldr literals
            if m.startswith("ldr") and "pc" in o:
                try:
                    imm = int(o.split("#")[-1].rstrip("]"), 0)
                    base = (a + 4) & ~3
                    lit = "   ; lit@%#x = %#010x" % (base + imm, u32(base + imm))
                except Exception:
                    pass
            if m == "bl" or (m == "blx" and "#" in o):
                lit = "   ; CALL"
            out.append("%#08x  %-8s %-38s%s" % (a, m, o, lit))
    return "\n".join(out)


fstarts = sorted(a for a, m, o in INS if m in ("push", "push.w") and "lr" in o)


def fn_of(addr):
    prev = fstarts[0]
    for f in fstarts:
        if f <= addr:
            prev = f
        else:
            break
    return prev


LOADER = 0x13468
nxt = min(f for f in fstarts if f > LOADER)
print("== fn@0x13468 .. next-fn@%#x ==" % nxt)
print(dump(LOADER, nxt))
print("\n== following fns up to 0x13660 (incl fn@0x13628 head) ==")
nxt2 = min(f for f in fstarts if f > nxt)
print(dump(nxt, min(nxt2, 0x13680)))

print("\n== dispatcher arm 0xC0DA context ==")
print(dump(0xC060, 0xC120))

print("\n== fn containing 0x3560/0x3586 (refs 0xE25814) ==")
f = fn_of(0x3560)
n = min(x for x in fstarts if x > f)
print("fn@%#x .. %#x" % (f, n))
print(dump(f, n))

print("\n== literal-pool refs into RAM 0xE25400-0xE25900 across container ==")
for off in range(0, len(body) - 4, 4):
    v = u32(off)
    if 0x00E25400 <= v <= 0x00E25900:
        # find ldr pc-relative users of this pool slot
        users = []
        for a, m, o in INS:
            if m.startswith("ldr") and "pc" in o:
                try:
                    imm = int(o.split("#")[-1].rstrip("]"), 0)
                    if ((a + 4) & ~3) + imm == off:
                        users.append(a)
                except Exception:
                    pass
        print("  lit@%#06x = %#010x  users: %s" % (off, v, [hex(u) for u in users]))
