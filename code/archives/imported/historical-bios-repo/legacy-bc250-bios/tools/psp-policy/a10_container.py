# A10: (1) type-0x28 container: parse ALL $PS1 sub-modules, disasm-hunt apply-engine
#      (2) SecOS: 0x75a0 0x201-table hexdump+decode; head disasm; readable blocks svc hunt
#      (3) gap 0x9C3F10-0x9CA400 + 0x4F blob structure peek
#      (4) VCN/bridge register scan in all readable PSP content
import struct, math
import capstone

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
ROM = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()
OUT = open(r"C:\Users\OWNER\tmp_bc250\recon\a10_container.txt", "w", encoding="utf-8")


def P(s=""):
    print(s)
    OUT.write(s + "\n")


md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
md.detail = False
md.skipdata = True


def disas(blob):
    return [(i.address, i.mnemonic, i.op_str) for i in md.disasm(blob, 0) if i.mnemonic != ".byte"]


def dump(ins, lo, hi):
    return "\n".join("%#08x  %-8s %s" % (a, m, o) for a, m, o in ins if lo <= a < hi)


def entropy(d):
    if not d:
        return 0.0
    cnt = [0] * 256
    for b in d:
        cnt[b] += 1
    return -sum((c / len(d)) * math.log2(c / len(d)) for c in cnt if c)


def pushlr(ins):
    return sum(1 for a, m, o in ins if m in ("push", "push.w") and "lr" in o)


REGS = (0x03E810, 0x03A2011C, 0x03A20124, 0x0900C234, 0x0900CB80, 0x03200400)

# ============ 1) container 0x28 sub-modules ============
P("== 1) container type 0x28 @0x984f00: $PS1 sub-modules ==")
CON = ROM[0x984F00:0x984F00 + 0x1A790]
cbody = CON[0x100:0x100 + 0x1A590]
marks = []
i = -1
while True:
    i = cbody.find(bytes.fromhex("24505331"), i + 1)
    if i < 0:
        break
    marks.append(i)
P("markers at: %s" % [hex(m) for m in marks])
for m in marks:
    env = m - 0x10
    if env < 0:
        continue
    sz = struct.unpack_from("<Q", cbody, env + 0x14)[0]
    tot = struct.unpack_from("<I", cbody, env + 0x6C)[0]
    ok = (0x10 <= sz <= len(cbody) - env - 0x200) and (tot == sz + 0x200)
    P("\n---- $PS1 @body+%#x env=+%#x: size=%#x total=%#x plausible=%s ----" % (m, env, sz, tot, ok))
    if not ok:
        P("   (implausible - raw ctx: %s)" % cbody[env:env + 0x40].hex())
        continue
    b = cbody[env + 0x100:env + 0x100 + sz]
    ent = entropy(b)
    ins = disas(b) if ent < 6.3 else []
    P("   body=%#x entropy=%.2f push-lr=%d" % (sz, ent, pushlr(ins)))
    for o in range(0, len(b) - 3, 4):
        v = struct.unpack_from("<I", b, o)[0]
        if v in REGS:
            P("   REG %#010x @body+%#x" % (v, o))
    for a, mm, oo in ins:
        if mm == "svc" and oo.strip() == "#0xf2":
            P("   svc0xf2 @%#x:" % a)
            P("      " + dump(ins, a - 0x30, a + 0x10).replace("\n", "\n      "))
    for k, (a, mm, oo) in enumerate(ins):
        if mm.startswith("cmp") and any(("#" + t) in oo for t in ("0x24", "0x45", "0x201", "0x210", "0x211", "0x280", "0x281")):
            ctx = ins[max(0, k - 3):k + 4]
            if any(x[1].startswith("b") for x in ctx[3:]) and not any(x[1].startswith("v") for x in ctx):
                P("   [cmp @%#x] %s" % (a, " | ".join("%s %s" % (x[1], x[2]) for x in ctx)))

# ============ 2) SecOS readable parts ============
P("\n== 2) SecOS (0x08) readable parts ==")
SEC = ROM[0x8FF000:0x8FF000 + 0x40200]
sbody = SEC[0x100:0x100 + 0x40000]
P("-- 0x201-table @0x75a0: hexdump 0x7560-0x76a0 --")
P("   " + sbody[0x7560:0x76A0].hex())
P("-- decode as {type,count} groups from 0x75a0 --")
off = 0x75A0
for step in range(14):
    if off + 8 > len(sbody):
        break
    t, c = struct.unpack_from("<II", sbody, off)
    P("   +%#06x: grp %#06x count %d" % (off, t, c))
    if t not in (0x201, 0x203, 0x210, 0x211, 0x280, 0x281) or c > 0x10000:
        break
    off += 8 + c * 8
P("-- SecOS head (0x0-0x400) disasm (first 60) --")
hins = disas(sbody[:0x400])
P("\n".join("   " + l for l in dump(hins, 0, 0x200).splitlines()[:60]))
P("-- SecOS svc 0xF2 cmd-ids in READABLE region (<0x19000) --")
rins = disas(sbody[:0x19000])
for k, (a, m, o) in enumerate(rins):
    if m == "svc" and o.strip() == "#0xf2":
        ctx = rins[max(0, k - 12):k]
        cmd = None
        for aa, mm, oo in reversed(ctx):
            if mm in ("movw", "movw.w") and "#0x1" in oo:
                try:
                    cmd = int(oo.split("#")[1], 0)
                except Exception:
                    pass
                break
        P("   svc0xf2 @%#x cmd=%s" % (a, "%#x" % cmd if cmd else "?"))
P("-- SecOS readable-region REG scan --")
for o in range(0, 0x19000 - 3, 4):
    v = struct.unpack_from("<I", sbody, o)[0]
    if v in REGS:
        P("   REG %#010x @+%#x" % (v, o))

# ============ 3) gap + 0x4F ============
P("\n== 3) gap 0x9C3F10-0x9CA400 and 0x4F ==")
gap = ROM[0x9C3F10:0x9CA400]
P("gap len=%#x entropy=%.2f nonzero=%d head=%s" % (len(gap), entropy(gap), sum(1 for b in gap if b), gap[:0x40].hex()))
F4F = ROM[0x9CAB00:0x9CAB00 + 0x10200]
P("0x4F: entropy=%.2f; $PS1-count=%d; push-lr-density in low-ent scan:" % (entropy(F4F), F4F.count(bytes.fromhex("24505331"))))
for base, ln in [(0, 0x1000), (0x1000, 0x1000), (0x2000, 0x2000)]:
    d = F4F[base:base + ln]
    ins = disas(d)
    P("   +%#x..%#x: push-lr=%d svc=%d" % (base, base + ln, pushlr(ins), sum(1 for a, m, o in ins if m == "svc")))

# ============ 4) container+SecOS full-raw REG scan (data too) ============
P("\n== 4) full raw REG scan (container body + SecOS readable + 0x4F) ==")
for tag, d in [("container", cbody), ("secos<0x19000", sbody[:0x19000]), ("0x4F", F4F)]:
    hits = []
    for o in range(0, len(d) - 3, 4):
        v = struct.unpack_from("<I", d, o)[0]
        if v in REGS:
            hits.append((o, v))
    P("   %-14s: %s" % (tag, [("%#x" % o, "%#x" % v) for o, v in hits] or "none"))
OUT.close()
print("\nwritten: recon/a10_container.txt")
