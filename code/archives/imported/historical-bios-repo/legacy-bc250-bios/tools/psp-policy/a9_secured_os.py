# A9: (A) t02 service#1 (svc 0xF2) wrapper/caller semantics - find the table-walk apply loop
#     (B) Secured OS (type 0x08) analysis: entropy map, disasm, svc/const/type hunts
#     (C) nested $PSP + $PS1 inside type-0x28 container
#     (D) type-0x44 blob: svc 0xF2 sites, head
#     (E) t02 bridge literal pool raw values
import struct, math
import capstone

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
ROM = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()
OUT = open(r"C:\Users\OWNER\tmp_bc250\recon\a9_secured_os.txt", "w", encoding="utf-8")


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


# ============ A) t02 service#1 sites ============
P("== A) t02: svc 0xF2 service#1 wrapper + call sites ==")
TOS = ROM[0x8EAC00 + 0x100:0x8EAC00 + 0x100 + 0x14150]
INS = disas(TOS)
BYA = {a: k for k, (a, m, o) in enumerate(INS)}
fstarts = sorted(a for a, m, o in INS if m in ("push", "push.w") and "lr" in o)


def fn_of(addr):
    prev = fstarts[0]
    for f in fstarts:
        if f <= addr:
            prev = f
        else:
            break
    return prev


s1 = []
for k, (a, m, o) in enumerate(INS):
    if m == "svc" and o.strip() == "#0xf2":
        for j in range(k - 1, max(0, k - 7), -1):
            am, mm, om = INS[j]
            if mm in ("movs", "mov", "mov.w") and om.lower().startswith("r0,"):
                try:
                    n = int(om.split("#")[1], 0)
                except Exception:
                    n = None
                if n == 1:
                    s1.append(a)
                break
            if mm in ("push", "push.w", "pop", "pop.w"):
                break
P("service#1 sites: %d" % len(s1))
P("-- first wrapper (fn containing first site) --")
if s1:
    f = fn_of(s1[0])
    P(dump(INS, f, min(f + 0x60, fstarts[-1])))
P("-- all service#1 call sites with 0x18 ctx (compact) --")
for a in s1:
    P("---- @%#x (fn@%#x) ----" % (a, fn_of(a)))
    P(dump(INS, a - 0x18, a + 0x10))

# ============ E) bridge literal pool ============
P("\n== E) t02 literal pool 0x4080-0x40A0 raw ==")
for o in range(0x4080, 0x40A0, 4):
    P("  +%#05x: %#010x" % (o, struct.unpack_from("<I", TOS, o)[0]))

# ============ B) Secured OS type 0x08 ============
P("\n== B) Secured OS (type 0x08 @0x8ff000, 0x40200) ==")
SEC = ROM[0x8FF000:0x8FF000 + 0x40200]
body = SEC[0x100:0x100 + 0x40000]
P("envelope: size@0x14=%#x total@0x6C=%#x ver@0x40=%s" % (
    struct.unpack_from("<Q", SEC, 0x14)[0], struct.unpack_from("<I", SEC, 0x6C)[0], SEC[0x40:0x58].hex()))
P("-- entropy map (0x1000 blocks) --")
row = []
for i in range(0, len(body), 0x1000):
    e = entropy(body[i:i + 0x1000])
    row.append("%02x:%4.1f" % (i >> 12, e))
P("  " + " ".join(row))
SINS = disas(body)
P("-- svc sites in SecOS --")
svcs = {}
for a, m, o in SINS:
    if m == "svc":
        svcs.setdefault(o, []).append(a)
for o, lst in sorted(svcs.items(), key=lambda kv: -len(kv[1]))[:12]:
    P("  svc %-6s : %d sites %s" % (o, len(lst), [hex(x) for x in lst[:6]]))
P("-- svc 0xF2 sites with ctx --")
for a, m, o in SINS:
    if m == "svc" and o.strip() == "#0xf2":
        P("---- @%#x ----" % a)
        P(dump(SINS, a - 0x28, a + 0x10))
P("-- cmp-with-type sites (branch within 4 ins, no neon) --")
for k, (a, m, o) in enumerate(SINS):
    if m.startswith("cmp") and any(("#" + t) in o for t in ("0x24", "0x45", "0x201", "0x203", "0x210", "0x211", "0x280", "0x281")):
        ctx = SINS[max(0, k - 4):k + 5]
        txt = " | ".join("%s %s" % (mm, oo) for aa, mm, oo in ctx)
        if any(mm.startswith(("b", "it")) for aa, mm, oo in ctx[4:]) and not any("vt" in mm or mm.startswith("v") for aa, mm, oo in ctx):
            P("[cmp @%#x] %s" % (a, txt))
P("-- raw const hits (bridge/gasket regs) --")
for o in range(0, len(body) - 3, 4):
    v = struct.unpack_from("<I", body, o)[0]
    if v in (0x03200400, 0x03A2011C, 0x03E810, 0x0900C234, 0x0900CB80):
        P("  %#010x @+%#x" % (v, o))
P("-- grp-type u32 hits (offsets only) --")
g = {}
for o in range(0, len(body) - 3, 4):
    v = struct.unpack_from("<I", body, o)[0]
    if v in (0x201, 0x203, 0x210, 0x211, 0x280, 0x281):
        g.setdefault(v, []).append(o)
for v, lst in g.items():
    P("  %#05x: %s" % (v, [hex(x) for x in lst]))

# ============ C) type 0x28 container ============
P("\n== C) container type 0x28 @0x984f00 (0x1a790) ==")
CON = ROM[0x984F00:0x984F00 + 0x1A790]
cbody = CON[0x100:] if struct.unpack_from("<I", CON, 0x10)[0] == 0x31535024 else CON
psp_off = cbody.find(bytes.fromhex("24505350"))
P("$PSP at body+%#x" % psp_off)
if psp_off >= 0:
    d = cbody[psp_off:]
    cnt = struct.unpack_from("<I", d, 8)[0]
    P("nested dir: count=%d checksum=%#x" % (cnt, struct.unpack_from("<I", d, 4)[0]))
    for i in range(min(cnt, 40)):
        eo = 0x10 + 16 * i
        t, sz = struct.unpack_from("<II", d, eo)
        loc = struct.unpack_from("<Q", d, eo + 8)[0]
        P("  [%2d] type=%#04x size=%#x loc=%#x" % (i, t, sz, loc))
for m in ("$PS1",):
    pat = bytes.fromhex("24505331")
    i = -1
    while True:
        i = cbody.find(pat, i + 1)
        if i < 0:
            break
        sz = struct.unpack_from("<Q", cbody, i + 0x14 - 0x10)[0] if i >= 0x10 else 0
        tot = struct.unpack_from("<I", cbody, i + 0x6C - 0x10)[0] if i >= 0x10 else 0
        P("  $PS1 @body+%#x: size@+4=%#x(?) tail-bytes=%s" % (i, sz, cbody[i:i + 0x30].hex()))

# ============ D) type 0x44 ============
P("\n== D) blob type 0x44 @0x9c3d00 (0x6610) ==")
B44 = ROM[0x9C3D00:0x9C3D00 + 0x6610]
P("head 0x40: %s" % B44[:0x40].hex())
P("envelope: size@0x14=%#x total@0x6C=%#x" % (struct.unpack_from("<Q", B44, 0x14)[0], struct.unpack_from("<I", B44, 0x6C)[0]))
b44 = B44[0x100:]
I44 = disas(b44)
for a, m, o in I44:
    if m == "svc":
        P("---- svc %s @%#x ----" % (o, a))
        P(dump(I44, a - 0x40, a + 0x18))
OUT.close()
print("\nwritten: recon/a9_secured_os.txt")
