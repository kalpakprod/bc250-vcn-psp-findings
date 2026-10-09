# A15: settle the apply-engine question:
#  1) literal pool values of fn@0x1167c (registry ptr) + registry content
#  2) callers of the interpreter fn@0xfeac
#  3) dispatcher case 0x24 handler (0xc556) + case 0x28 (0xc72e) + iterator merge 0xc394
#  4) svc 0x7c call sites histogram (to see its role)
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


print("== 1) fn@0x1167c literal pool ==")
for off in (0x116B4, 0x116B8):
    print("  pool @%#06x = %#010x" % (off, u32(off)))
R = u32(0x116B8)
print("registry R = %#x; if R < len(body): in-container, else RAM/other" % R)
if 0 < R < len(body) - 0x200:
    print("  count @R+0x100 = %d" % u32(R + 0x100))
    off = R + 0x140
    for i in range(u32(R + 0x100)):
        t, c = u32(off), u32(off + 4)
        print("  group[%d] type=%#06x count=%d  pairs-head=%s" % (
            i, t, c, " ".join("%#010x:%#010x" % (u32(off + 8 + 8 * j), u32(off + 12 + 8 * j)) for j in range(min(c, 3)))))
        off += 8 + c * 8

print("\n== 2) callers of interpreter fn@0xfeac ==")
for a, m, o in INS:
    if m == "bl":
        try:
            t = int(o.split("#")[1] if "#" in o else o, 0)
        except Exception:
            continue
        if t == 0xFEAC:
            print("---- caller @%#x ----" % a)
            print(dump(a - 0x50, a + 0x30))

print("\n== 3) case 0x24 handler @0xc556 ==")
print(dump(0xC556, 0xC65A))
print("\n== case 0x28 handler @0xc72e + merge @0xc394 ==")
print(dump(0xC72E, 0xC790))
print(dump(0xC394, 0xC410))

print("\n== 4) svc 0x7c sites (first 12 with tiny ctx) ==")
n = 0
for k, (a, m, o) in enumerate(INS):
    if m == "svc" and o.strip() == "#0x7c" and n < 12:
        n += 1
        ctx = INS[max(0, k - 3):k + 2]
        print("  @%#x: %s" % (a, " | ".join("%s %s" % (x[1], x[2]) for x in ctx)))
