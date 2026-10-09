# A30b: full container call graph. (1) every bl target + callers; (2) orphan functions
# (push {.., lr}-headed, never bl-called, never branched-to) = invoked from outside
# the container; (3) full dump of the mailbox dispatcher 0xC4C0 and its handler
# lookup (does it use a pointer/offset table?); (4) full dumps of orchestrator steps
# (0x10fac,0x83e0,0x16340,0xf788,0xaed4,0x16aa4,0x660c) bl-target lists.
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


targets = {}     # t -> [caller addrs]
branches = set() # all branch dests
for a, m, o in INS:
    if m in ("bl", "blx") and ("#" in o or o.startswith("0x")):
        try:
            t = int(o.split("#")[-1], 0)
        except Exception:
            continue
        targets.setdefault(t, []).append(a)
    elif m.startswith("b") or m in ("cbz", "cbnz", "pop", "ldm"):
        for w in o.replace("[", " ").replace("]", " ").replace(",", " ").split():
            if w.startswith("#"):
                try:
                    branches.add(int(w[1:], 0))
                except Exception:
                    pass

# function heads: push with lr
heads = []
for k, (a, m, o) in enumerate(INS):
    if m in ("push", "push.w") and "lr" in o:
        heads.append(a)

print("== 1) call graph: target <- callers (code 0x100..0x1A66E) ==")
for t in sorted(targets):
    cs = sorted(targets[t])[:8]
    extra = " +%d more" % (len(targets[t]) - 8) if len(targets[t]) > 8 else ""
    print("  %#08x <- %s%s" % (t, " ".join("%#x" % c for c in cs), extra))

print("\n== 2) orphan function heads (push{lr} prologue, no bl caller, no b/ldm target) ==")
for h in heads:
    called = [c for c in targets.get(h, [])]
    brt = [b for b in branches if abs(b - h) <= 2]
    if not called and not brt:
        print("  ORPHAN head @%#08x" % h)

print("\n== 3) mailbox dispatcher 0xC4C0 full ==")
print(dump(0xC4C0, 0xC6C0))

print("\n== 4) orchestrator step bl-target lists ==")
for f, lo, hi in ((0x10fac, 0x10FAC, 0x11040), (0x83e0, 0x83E0, 0x8500),
                  (0x16340, 0x16340, 0x16400), (0xf788, 0xF788, 0xF860),
                  (0xaed4, 0xAED4, 0xAF60), (0x16aa4, 0x16AA4, 0x16B40),
                  (0x660c, 0x660C, 0x66C0), (0x4914, 0x4914, 0x49E0)):
    ts = set()
    for a, m, o in INS:
        if lo <= a < hi and m in ("bl", "blx") and "#" in o:
            try:
                ts.add(int(o.split("#")[-1], 0))
            except Exception:
                pass
    ts = sorted(ts)
    svcs = [a for a, m, o in INS if lo <= a < hi and m == "svc"]
    print("  fn@%#x: bl targets %s ; svc count %d" % (f, " ".join("%#x" % t for t in ts), len(svcs)))

print("\n== 5) all svc immediates histogram ==")
from collections import Counter
c = Counter(o for a, m, o in INS if m == "svc")
for k in sorted(c, key=lambda x: int(x.split("#")[-1], 0)):
    print("  svc %-6s x%d" % (k, c[k]))
