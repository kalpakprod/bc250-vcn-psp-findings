# A7: trace svc#0x63 semantics + find the gasket/0x45 apply engine.
# 1) vector table -> SVC handler -> dispatch by immediate -> handler of 0x63
# 2) full disasm of fn@0x12544 ($PS1 load+verify) and its caller fn@0x11a04
# 3) constant hunt (raw u32 scan + movw/movt pairs): SMN bridge, $PSP/$PS1, dir addrs
# 4) callers of the SMN bridge engine fn@0x405c
import struct
import capstone

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
ROM = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()
TOS = ROM[0x8EAC00 + 0x100:0x8EAC00 + 0x100 + 0x14150]
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
md.detail = False
md.skipdata = True
INS = [(i.address, i.mnemonic, i.op_str) for i in md.disasm(TOS, 0) if i.mnemonic != ".byte"]
BYINS = {a: (m, o) for a, m, o in INS}
OUT = open(r"C:\Users\OWNER\tmp_bc250\recon\a7_t02_flow.txt", "w", encoding="utf-8")


def P(s=""):
    print(s)
    OUT.write(s + "\n")


def dump(lo, hi):
    return "\n".join("%#08x  %-8s %s" % (a, m, o) for a, m, o in INS if lo <= a < hi)


# ---------- 1) vector table ----------
P("== PART 1: vector table (body offsets; ROM 0x8EAD00 + off) ==")
for i in range(16):
    w = struct.unpack_from("<I", TOS, i * 4)[0]
    note = ""
    if w & 1 and w >> 24 in (0x00, 0x08):
        note = " -> thumb addr %#x (ROM %#x)" % (w & ~1, 0x8EAD00 + (w & ~1))
    elif (w >> 24) == 0xEA:
        off = w & 0xFFFFFF
        if off & 0x800000:
            off -= 0x1000000
        tgt = 8 + i * 4 + 2 * off
        note = " -> ARM branch to %#x" % tgt
    P("  [%2d] +0x%02x: %#010x %s" % (i, i * 4, w, note))

# ---------- 2) svc histogram ----------
P("\n== PART 2: svc immediate histogram ==")
hist = {}
for a, m, o in INS:
    if m == "svc":
        hist[o] = hist.get(o, 0) + 1
for o, n in sorted(hist.items(), key=lambda kv: -kv[1]):
    P("  svc %-8s : %d sites" % (o, n))

# ---------- 3) full fn dumps ----------
fstarts = sorted(a for a, m, o in INS if m in ("push", "push.w") and "lr" in o)


def fn_end(start):
    nxt = None
    for f in fstarts:
        if f > start:
            nxt = f
            break
    return nxt if nxt else min(len(TOS), start + 0x2000)


P("\n== PART 3: fn@0x12544 FULL ($PS1 load+verify) ==")
P(dump(0x12544, fn_end(0x12544)))
P("\n== PART 4: fn@0x11a04 FULL (caller; incl. 0x12434 site) ==")
P(dump(0x11a04, min(fn_end(0x11a04), 0x12490)))

# ---------- 5) constants ----------
P("\n== PART 5a: raw u32 scan (literal pools / data) ==")
WATCH = {
    0x03200400: "SMN bridge window", 0x03200401: "SMN bridge idx", 0x10000: "bridge enable", 0x10001: "bridge cmd",
    0x50535024: "$PSP magic", 0x44484224: "$BHD magic", 0x31535024: "$PS1 magic",
    0xFF8E0000: "PSP dir addr", 0xFF982000: "gasket addr", 0xFF9CA400: "TOS0x45 addr",
    0xFF000000: "SPI base", 0x8E0000: "dir off", 0x982000: "gasket off", 0x9CA400: "0x45 off",
    0x03E810: "VCN gate reg", 0x03A2011C: "DF aperture 1C", 0x0900C234: "VCN bank commit",
    0x6F8000: "addr seen @0x12410", 0x30000: "size? @0x12408",
}
for off in range(0, len(TOS) - 3, 4):
    v = struct.unpack_from("<I", TOS, off)[0]
    if v in WATCH:
        # referenced by a nearby ldr [pc,#x]?
        ref = ""
        for a, m, o in INS:
            if m.startswith("ldr") and "pc" in o and abs(a - off) < 0x60:
                try:
                    imm = int(o.split("#")[1].rstrip("]"), 0)
                except Exception:
                    continue
                if a + 4 + (imm & ~3) == off:
                    ref = "  <== ldr @%#x" % a
                    break
        P("  %#08x @body+%#06x (ROM %#x): %-22s%s" % (v, off, 0x8EAD00 + off, WATCH[v], ref))
P("\n== PART 5b: movw/movt pairs ==")
for k, (a, m, o) in enumerate(INS):
    if m in ("movw", "movw.w") and "," in o:
        reg, rest = o.split(",", 1)
        try:
            lo16 = int(rest.strip().lstrip("#"), 0)
        except Exception:
            continue
        for j in range(k + 1, min(k + 5, len(INS))):
            a2, m2, o2 = INS[j]
            if m2 in ("movt", "movt.w") and o2.startswith(reg + ","):
                try:
                    hi16 = int(o2.split("#")[1], 0)
                except Exception:
                    continue
                v = (hi16 << 16) | lo16
                if v in WATCH:
                    P("  %#010x @%#x (movw@%#x+movt@%#x): %s" % (v, a, a, a2, WATCH[v]))
                break

# ---------- 6) callers of SMN bridge fn@0x405c ----------
P("\n== PART 6: callers of SMN-bridge fn@0x405c (context 0x50 before/after) ==")
for a, m, o in INS:
    if m == "bl":
        try:
            t = int(o.split("#")[1] if "#" in o else o, 0)
        except Exception:
            continue
        if t == 0x405C:
            P("---- caller @%#x ----" % a)
            P(dump(a - 0x50, a + 0x50))

# ---------- 7) SVC handler hunt ----------
P("\n== PART 7: around svc-vector handler candidates ==")
svc_vec = struct.unpack_from("<I", TOS, 0x18)[0]
P("svc vector entry u32: %#x" % svc_vec)
if svc_vec & 1:
    h = svc_vec & ~1
    P("handler @%#x dump:" % h)
    P(dump(h, h + 0x100))
OUT.close()
print("\nwritten: recon/a7_t02_flow.txt")
