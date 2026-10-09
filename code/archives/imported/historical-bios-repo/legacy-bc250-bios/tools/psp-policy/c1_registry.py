# C1: (1) find fn containing the registry SETTER (@0x11660) and its callers (raw BL scan);
# (2) dump helper fns: 0x5fa0 (token derivation?), 0x1628 (filler), 0x1450 (memcmp?),
#     0x14e4 (memcpy?), 0x6800 (stream reader), 0x13680, 0xa430, 0xe930 head;
# (3) raw dump of gasket @0x982000 and policy @0x9CA400 envelope + first 0x40 body bytes;
# (4) raw BL scan for callers of the setter fn and of fn@0x13468 from ANY halfword.
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


SETTER = fn_of(0x11660)
print("== registry SETTER fn@%#x (contains 0x11660) .. next ==" % SETTER)
n = min(f for f in fstarts if f > SETTER)
print(dump(SETTER, min(n + 0x10, SETTER + 0x200)))

print("\n== raw BL/BLX scan: callers of setter@%#x and loader@0x13468 ==" % SETTER)
targets = {SETTER: "setter", 0x13468: "loader"}
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
    src = off
    tgt = src + 4 + disp
    if tgt in targets:
        print("  %s@%#x <- BL@%#x (fn@%#x)" % (targets[tgt], tgt, src, fn_of(src)))

print("\n== helper fn@0x5fa0 (token derive; called from fn@0x3528) ==")
print(dump(0x5FA0, 0x60E0))
print("\n== helper fn@0x1628 (expectation filler) ==")
print(dump(0x1628, 0x16C0))
print("\n== helper fn@0x1450 (compare) ==")
print(dump(0x1450, 0x14A8))
print("\n== helper fn@0x14e4 (copy) ==")
print(dump(0x14E4, 0x1520))
print("\n== stream reader fn@0x6800 head ==")
print(dump(0x6800, 0x6920))
print("\n== fn@0x13680 (dispatcher arm 0xC0E2) head ==")
print(dump(0x13680, 0x13700))
print("\n== fn@0xa430 / 0xe930 heads ==")
print(dump(0xA430, 0xA470))
print(dump(0xE930, 0xE980))

print("\n== blob envelope + body head: gasket 0x982000, policy 0x9CA400, TOS 0x984F00 ==")
for name, off, size in (("GASKET 0x24", 0x982000, 0x2E50), ("POLICY 0x45", 0x9CA400, 0x6E0),
                        ("TOS 0x28", 0x984F00, 0x1A790)):
    blob = ROM[off:off + size]
    print("-- %s @%#x size %#x --" % (name, off, size))
    print("  envelope[0:0x40]:", " ".join("%02x" % b for b in blob[0:0x40]))
    print("  body[0:0x40]:    ", " ".join("%02x" % b for b in blob[0x100:0x140]))
    words = struct.unpack_from("<16I", blob, 0)
    print("  envelope u32[0:16]:", " ".join("%08x" % w for w in words))
    bw = struct.unpack_from("<16I", blob, 0x100)
    print("  body u32[0:16]:    ", " ".join("%08x" % w for w in bw))
    # tail after body per size field at +0x14
    bsz = struct.unpack_from("<I", blob, 0x14)[0]
    print("  size@+0x14=%#x, tail bytes=%#x" % (bsz, size - 0x100 - bsz))
    if 0 <= size - 0x100 - bsz <= 0x400:
        print("  tail:", " ".join("%02x" % b for b in blob[0x100 + bsz:size]))
