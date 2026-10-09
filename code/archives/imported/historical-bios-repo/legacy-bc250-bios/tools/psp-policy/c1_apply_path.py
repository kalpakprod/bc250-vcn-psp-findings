# C1: raw BL scan for callers of fn@0x2008 (apply-any-type wrapper) and fn@0x1167c
# (registry getter); dump arms/dispatcher context of each caller to see whether the
# TYPE argument comes from the mailbox message (arbitrary-pair runtime apply).
import struct
import capstone

ROM = open(r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
           r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()
CON = ROM[0x984F00:0x984F00 + 0x1A790]
body = CON[0x100:]
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
md.skipdata = True
INS = [(i.address, i.mnemonic, i.op_str) for i in md.disasm(body, 0) if i.mnemonic != ".byte"]


def u32(off):
    return struct.unpack_from("<I", body, off)[0]


def dump(lo, hi):
    out = []
    for a, m, o in INS:
        if lo <= a < hi:
            lit = ""
            if m.startswith("ldr") and "pc" in o:
                try:
                    imm = int(o.split("#")[-1].rstrip("]"), 0)
                    base = (a + 4) & ~3
                    lit = "   ; lit@%#x = %#010x" % (base + imm, u32(base + imm))
                except Exception:
                    pass
            out.append("%#08x  %-8s %-40s%s" % (a, m, o, lit))
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


TARGETS = {0x2008: "apply-any-type", 0x1167C: "registry-getter", 0x13468: "loader",
           0x3528: "token-install", 0x11560: "kdb-register"}
hits = {}
for off in range(0, len(body) - 4, 2):
    h = struct.unpack_from("<H", body, off)[0]
    if (h >> 11) != 0x1E:
        continue
    lo = struct.unpack_from("<H", body, off + 2)[0]
    if (lo >> 12) not in (0xE, 0xF):
        continue
    disp = ((h & 0x7FF) << 12) | ((lo & 0x7FF) << 1)
    if disp & 0x400000:
        disp -= 0x800000
    tgt = off + 4 + disp
    if tgt in TARGETS:
        hits.setdefault(tgt, []).append(off)

for t in sorted(TARGETS):
    print("== %s @%#x callers: %s ==" % (TARGETS[t], t,
                                        [hex(a) for a in hits.get(t, [])]))
    for src in hits.get(t, []):
        f = fn_of(src)
        print("\n---- BL@%#x in fn@%#x ----" % (src, f))
        print(dump(max(f, src - 0x50), src + 0x30))
