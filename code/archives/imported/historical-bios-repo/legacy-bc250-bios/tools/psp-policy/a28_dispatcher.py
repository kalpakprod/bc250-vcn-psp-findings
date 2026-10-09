# A28: who applies the stock gasket?
# 1) weak stub 0x1345a + its pool (does the pool point to an overridable handler var?)
# 2) full dispatcher around case 0x24 @0xc556 (switch structure: table or if-chain?)
# 3) scan whole container for function-pointer tables (runs of >=4 u32 in code range)
# 4) dump fn@0x13628 (calls 0x11e34 -> 0x16658 -> 0x660c chain; entry into processing?)
# 5) bl-callers of 0x13628 / 0x11e34 / 0x660c
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


print("== 1) weak stub region 0x13440..0x13470 ==")
print(dump(0x13440, 0x13470))
for off in range(0x13470, 0x13490, 4):
    print("  pool @%#06x = %#010x" % (off, u32(off)))

print("\n== 2) dispatcher 0xc4c0..0xc7a0 (case 0x24 @0xc556, case 0x28 @0xc72e) ==")
print(dump(0xC4C0, 0xC7A0))

print("\n== 3) function-pointer table scan (>=4 consecutive u32 in [0x1000,0x1a790)) ==")
run = []
runs = []
for off in range(0, len(body) - 4, 4):
    v = u32(off)
    ok = 0x1000 <= v < 0x1A790 and (v & 1) == 1  # thumb fn ptrs are odd
    if ok:
        run.append((off, v))
    else:
        if len(run) >= 4:
            runs.append(list(run))
        run = []
if len(run) >= 4:
    runs.append(run)
for r in runs:
    print("  table @%#06x..%#06x: %s" % (r[0][0], r[-1][0], " ".join("%#x" % v for _, v in r)))

print("\n== 4) fn@0x13628 full (pre-0x16658 chain) ==")
print(dump(0x13628, 0x13690))
for off in range(0x13690, 0x136C0, 4):
    print("  pool @%#06x = %#010x" % (off, u32(off)))

print("\n== 5) bl-callers of 0x13628 / 0x11e34 / 0x660c ==")
for a, m, o in INS:
    if m in ("bl", "blx"):
        try:
            t = int(o.split("#")[1] if "#" in o else o, 0)
        except Exception:
            continue
        if t in (0x13628, 0x11E34, 0x660C):
            print("---- %#x called @%#x ----" % (t, a))
            print(dump(a - 0x28, a + 0x14))
