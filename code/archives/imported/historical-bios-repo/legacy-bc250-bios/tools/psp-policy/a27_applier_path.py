# A27: how does the stock gasket get applied? fn@0xfeac (interpreter #1) and fn@0x1346a
# ($PS1 loader-verifier) have NO direct bl callers -> they are registered via pointers.
# Hunt: literal-pool occurrences of {0xfeac,0xfead,0x1346a,0x1346b,0x16658,0x16659,
# 0x2178,0x2179} in the TOS-policy container (type 0x28 @0x984F00); disasm around each
# registration site; full dump of fn@0x16658 (suspected service/dispatch table helper);
# all bl-callers of 0x16658.
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
BYADDR = {a: k for k, (a, m, o) in enumerate(INS)}


def dump(lo, hi):
    return "\n".join("%#08x  %-8s %s" % (a, m, o) for a, m, o in INS if lo <= a < hi)


def u32(off):
    return struct.unpack_from("<I", body, off)[0]


def ctx(off):
    """disasm window around a literal-pool offset (code usually precedes the pool)"""
    k = BYADDR.get(off - 2)
    lo = off - 0x60
    return dump(lo, off) if any(lo <= a < off for a, m, o in INS) else "(no code window)"


print("== 1) literal-pool / data occurrences of applier pointers ==")
NEEDLES = {0xFEAC: "fn@0xfeac interp1", 0xFEAD: "fn@0xfeac|thumb",
           0x1346A: "fn@0x1346a loader", 0x1346B: "fn@0x1346a|thumb",
           0x16658: "fn@0x16658 table?", 0x16659: "fn@0x16658|thumb",
           0x2178: "fn@0x2178 interp2", 0x2179: "fn@0x2178|thumb"}
for off in range(0, len(body) - 4, 4):
    v = u32(off)
    if v in NEEDLES:
        print("---- %#010x @ body+%#06x (%s) ----" % (v, off, NEEDLES[v]))
        print(ctx(off))

print("\n== 2) fn@0x16658 full ==")
print(dump(0x16658, 0x166E0))

print("\n== 3) bl-callers of 0x16658 ==")
for a, m, o in INS:
    if m in ("bl", "blx"):
        try:
            t = int(o.split("#")[1] if "#" in o else o, 0)
        except Exception:
            continue
        if t in (0x16658,):
            print("---- 0x16658 called @%#x ----" % a)
            print(dump(a - 0x40, a + 0x20))

print("\n== 4) bl-callers of 0x6800 (stream reader used by loader) ==")
n = 0
for a, m, o in INS:
    if m == "bl":
        try:
            t = int(o.split("#")[1] if "#" in o else o, 0)
        except Exception:
            continue
        if t == 0x6800 and n < 6:
            n += 1
            print("---- 0x6800 called @%#x ----" % a)
            print(dump(a - 0x30, a + 0x14))
