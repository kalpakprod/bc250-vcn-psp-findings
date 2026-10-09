# A8: hunt the gasket/0x45 APPLY ENGINE across all PSP dir blobs.
# A) t02: callers of bridge-driver fn@0x1d78, full dump of bridge fn@0x405c,
#    cmp-with-type sites {0x24,0x45,0x201,0x203,0x210,0x211,0x280,0x281}
# B) every PSP dir blob: entropy, $PS1?, raw constant scan
#    (SMN bridge 0x03200400, VCN regs, group types, $PSP/$BHD magics)
# C) unencrypted blobs: Thumb disasm + cmp-type sites + svc histogram
import struct, math
import capstone

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
ROM = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()
OUT = open(r"C:\Users\OWNER\tmp_bc250\recon\a8_apply_hunt.txt", "w", encoding="utf-8")


def P(s=""):
    print(s)
    OUT.write(s + "\n")


md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
md.detail = False
md.skipdata = True
TYPES = ["0x24", "0x45", "0x201", "0x203", "0x210", "0x211", "0x280", "0x281"]


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
    e = 0.0
    for c in cnt:
        if c:
            p = c / len(d)
            e -= p * math.log2(p)
    return e


# ================= A) t02 =================
P("== A) t02 ==")
TOS = ROM[0x8EAC00 + 0x100:0x8EAC00 + 0x100 + 0x14150]
INS = disas(TOS)
P("-- callers of bridge-driver fn@0x1d78 (ctx 0x60) --")
for a, m, o in INS:
    if m == "bl":
        try:
            t = int(o.split("#")[1] if "#" in o else o, 0)
        except Exception:
            continue
        if t == 0x1D78:
            P("---- caller @%#x ----" % a)
            P(dump(INS, a - 0x60, a + 0x60))
P("\n-- full bridge engine fn@0x405c --")
P(dump(INS, 0x405C, 0x41E0))
P("\n-- cmp-with-type sites in t02 --")
for k, (a, m, o) in enumerate(INS):
    if m.startswith("cmp") and any(("#" + t) in o for t in TYPES):
        P("[%s %#x] ctx:" % (m, a))
        P(dump(INS, a - 0x18, a + 0x18))
        P("")

# ================= B) all PSP dir blobs =================
P("\n== B) PSP dir blobs: scan ==")
DIR = 0x8E0000
cnt = struct.unpack_from("<I", ROM, DIR + 8)[0]
WATCH = {0x03200400: "SMNbridge", 0x03E810: "VCN-gate", 0x03A2011C: "DF-1C", 0x0900C234: "VCN-commit",
         0x0900CB80: "VCN-lock", 0x50535024: "$PSP", 0x44484224: "$BHD", 0x31535024: "$PS1",
         0x201: "grp201", 0x203: "grp203", 0x210: "grp210", 0x211: "grp211", 0x280: "grp280", 0x281: "grp281"}
blobs = []
for i in range(cnt):
    eo = DIR + 0x10 + 16 * i
    t, sz, loc = struct.unpack_from("<IIQ", ROM, eo)
    off = loc & 0xFFFFFF if loc >> 32 == 0 else (loc & 0xFFFFFFFF) - 0xFF000000
    off = (loc & 0xFFFFFFFF) - 0xFF000000 if (loc & 0xFFFFFFFF) > 0xFF000000 else (loc & 0xFFFFFFFF)
    blobs.append((i, t, sz, off))
P("%2s %-6s %-8s %-9s %-7s %-6s %s" % ("idx", "type", "size", "romoff", "$PS1", "ent", "hits"))
for i, t, sz, off in blobs:
    d = ROM[off:off + sz]
    ps1 = struct.unpack_from("<I", d, 0x10)[0] == 0x31535024 if len(d) > 0x14 else False
    ent = entropy(d[0x100:] if ps1 else d)
    hits = {}
    body = d[0x100:] if ps1 else d
    for o2 in range(0, len(body) - 3, 4):
        v = struct.unpack_from("<I", body, o2)[0]
        if v in WATCH and v not in (0x201, 0x203, 0x210, 0x211, 0x280, 0x281) or (v in (0x201, 0x203, 0x210, 0x211, 0x280, 0x281)):
            # count group types only once per blob address-bucket to reduce noise
            hits[WATCH[v]] = hits.get(WATCH[v], 0) + 1
    hits = {k: v for k, v in hits.items() if k not in ("grp201", "grp203", "grp210", "grp211", "grp280", "grp281") or v >= 2}
    P("%2d %#04x %8d %#08x %-7s %5.2f  %s" % (i, t, sz, off, ps1, ent, hits or "-"))

# ================= C) unencrypted blobs: disasm hunt =================
P("\n== C) per-blob disasm hunt (skip $PS1 0x100 hdr; entropy<6.2) ==")
for i, t, sz, off in blobs:
    d = ROM[off:off + sz]
    ps1 = struct.unpack_from("<I", d, 0x10)[0] == 0x31535024 if len(d) > 0x14 else False
    body = d[0x100:] if ps1 else d
    ent = entropy(body)
    if ent > 6.2 or len(body) < 0x400:
        continue
    ins = disas(body)
    svcs = {}
    for a, m, o in ins:
        if m == "svc":
            svcs[o] = svcs.get(o, 0) + 1
    type_sites = [(a, m, o) for a, m, o in ins if m.startswith("cmp") and any(("#" + tt) in o for tt in TYPES)]
    raw_hits = []
    for o2 in range(0, len(body) - 3, 4):
        v = struct.unpack_from("<I", body, o2)[0]
        if v in (0x03200400, 0x03E810, 0x03A2011C, 0x0900C234, 0x0900CB80, 0x50535024):
            raw_hits.append((o2, v))
    P("\n---- blob idx=%d type=%#x romoff=%#x size=%#x ent=%.2f ----" % (i, t, off, sz, ent))
    P("   svc histogram: %s" % sorted(svcs.items(), key=lambda kv: -kv[1])[:8])
    P("   raw const hits: %s" % [("%#x" % a, "%#x" % v) for a, v in raw_hits[:10]])
    if type_sites or raw_hits or any(x in svcs for x in ("#0xf2",)):
        for a, m, o in type_sites[:12]:
            P("   [cmp %s @%#x] %s" % (m, a, o))
            P("      " + dump(ins, a - 0x10, a + 0x10).replace("\n", "\n      "))
OUT.close()
print("\nwritten: recon/a8_apply_hunt.txt")
