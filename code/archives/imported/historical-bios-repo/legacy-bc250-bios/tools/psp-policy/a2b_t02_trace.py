# A2b: t02 deep trace: movw/movt constants, type->handler tables, SMN bridge fns, verify callers.
import struct, re
import capstone

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
ROM = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()
ENV = ROM[0x8EAC00:0x8EAC00 + 0x14350]
TOS = ENV[0x100:0x100 + 0x14150]
N = len(TOS)

md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
md.detail = False
md.skipdata = True
INS = [(i.address, i.mnemonic, i.op_str) for i in md.disasm(TOS, 0) if i.mnemonic != ".byte"]
print("thumb ins:", len(INS))

# --- 1) movw/movt constant materialization ---
consts = {}
for i in range(len(INS) - 1):
    a1, m1, o1 = INS[i]
    a2, m2, o2 = INS[i + 1]
    if m1 == "movw" and m2 == "movt":
        r1 = o1.split(",")[0].strip()
        r2 = o2.split(",")[0].strip()
        if r1 == r2:
            lo = int(o1.split("#")[1], 0) & 0xFFFF
            hi = int(o2.split("#")[1], 0) & 0xFFFF
            consts.setdefault((hi << 16) | lo, []).append(a1)

WATCH = {0x45: "type 0x45 TOS_POLICY", 0x24: "type 0x24 GASKET", 0x210: "grp 0x210", 0x201: "grp 0x201",
         0x280: "grp 0x280", 0x281: "grp 0x281", 0x211: "grp 0x211", 0x03E810: "VCN_SEG", 0x03A2011C: "DF ap low",
         0x0900C234: "VCN commit", 0x0900CB80: "VCN lock", 0x31535024: "$PS1", 0xAB1000: "APCB off"}
print("\n== movw/movt watch hits ==")
for v, name in WATCH.items():
    if v in consts:
        print("  %#010x %-22s materialized at %s" % (v, name, [hex(a) for a in consts[v][:8]]))
print("== movw/movt 0x0320xxxx/0x0322xxxx ==")
for v in sorted(consts):
    if 0x03200000 <= v <= 0x0323FFFF:
        print("  %#010x at %s" % (v, [hex(a) for a in consts[v][:6]]))
print("== movw/movt 0x090xxxxx (SMN periph) sample ==")
n09 = [v for v in sorted(consts) if 0x09000000 <= v <= 0x093FFFFF]
print("  count:", len(n09), "sample:", [hex(v) for v in n09[:12]])

# --- 2) raw scan: type->handler table candidates (run of small u32 types followed by code ptrs) ---
print("\n== candidate {type,handler} tables (u32 pairs, type<=0x60, ptr in body) ==")
hits = []
for off in range(0, N - 8, 4):
    t = struct.unpack_from("<I", TOS, off)[0]
    p = struct.unpack_from("<I", TOS, off + 4)[0]
    if t in (0x24, 0x45, 0x28, 0x13, 0x20, 0x08, 0x02, 0x01) and 0x100 <= p < N and p % 2 == 0:
        hits.append((off, t, p))
for off, t, p in hits[:30]:
    print("  @%#x: type %#04x -> %#x" % (off, t, p))

# --- 3) BL map: who calls where ---
blmap = {}
for a, m, o in INS:
    if m == "bl":
        try:
            tgt = int(o.split("#")[1] if "#" in o else o, 0)
        except Exception:
            continue
        blmap.setdefault(tgt, []).append(a)

# function starts: PUSH {.., lr} (b5xx) or PUSH.W (e92d ... with lr bit)
fstarts = set()
for idx, (a, m, o) in enumerate(INS):
    if m in ("push", "push.w") and ("lr" in o):
        fstarts.add(a)

# --- 4) svc 0xF2 wrapper functions: cluster region ---
svc_f2 = [a for a, m, o in INS if m == "svc" and o.strip() in ("#0xf2", "0xf2", "#242")]
print("\n== svc#0xF2 sites: %d, range %#x..%#x ==" % (len(svc_f2), min(svc_f2), max(svc_f2)))

# --- 5) dump windows for manual reading ---
def dump_window(lo, hi, tag):
    lines = ["\n===== %s [%#x..%#x) =====" % (tag, lo, hi)]
    for a, m, o in INS:
        if lo <= a < hi:
            ann = ""
            if m == "bl":
                try:
                    t = int(o.split("#")[1] if "#" in o else o, 0)
                    ann = "  ; -> %#x (callers: %s)" % (t, [hex(x) for x in blmap.get(t, [])][:5])
                except Exception:
                    pass
            if m == "svc":
                ann = "  ; PSP service"
            lines.append("%#08x  %-8s %s%s" % (a, m, o, ann))
    return "\n".join(lines)


out = []
out.append(dump_window(0x125C0, 0x12840, "prior-session 'verifier @0x12644' region"))
out.append(dump_window(0xEE00, 0xF020, "svc 0xF2 cluster head"))
out.append(dump_window(0x4040, 0x4340, "SMN bridge fns (pool 0x03200400/0x03220050)"))
out.append(dump_window(0x5700, 0x5840, "pool 0x032001f0 @0x57c8"))
out.append(dump_window(0x2200, 0x2320, "pool 0x032001f0 @0x2284"))
out.append(dump_window(0x4FC0, 0x51E0, "pool 0x03230000 @0x50b0"))
open(r"C:\Users\OWNER\tmp_bc250\recon\a2_t02_windows.txt", "w").write("\n".join(out))
print("\nwindows written: recon/a2_t02_windows.txt (%d lines)" % sum(x.count("\n") for x in out))

# --- 6) callers of functions containing svc 0xF2 ---
fs = sorted(fstarts)


def fn_of(addr):
    prev = None
    for f in fs:
        if f <= addr:
            prev = f
        else:
            break
    return prev


svcfns = sorted(set(fn_of(a) for a in svc_f2))
print("\n== functions containing svc#0xF2: %s ==" % [hex(f) for f in svcfns])
for f in svcfns:
    callers = []
    for a, m, o in INS:
        if m == "bl":
            try:
                t = int(o.split("#")[1] if "#" in o else o, 0)
            except Exception:
                continue
            if fn_of(t) == f and fn_of(a) != f:
                callers.append(a)
    print("  fn@%#x callers: %s" % (f, [hex(c) for c in callers[:10]]))
