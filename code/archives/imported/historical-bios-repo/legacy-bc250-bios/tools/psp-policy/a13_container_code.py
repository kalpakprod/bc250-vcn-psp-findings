# A13: container 0x28 (t28) full-body code hunt: real cmp-with-group-type sites, svc sites,
# nested driver @+0x19f00 (envelope variant), plus code-region map.
import struct, math
import capstone

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
ROM = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()
CON = ROM[0x984F00:0x984F00 + 0x1A790]
body = CON[0x100:]
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
md.detail = False
md.skipdata = True
INS = [(i.address, i.mnemonic, i.op_str) for i in md.disasm(body, 0) if i.mnemonic != ".byte"]
P = print


def entropy(d):
    cnt = [0] * 256
    for b in d:
        cnt[b] += 1
    return -sum((c / len(d)) * math.log2(c / len(d)) for c in cnt if c)


# code-region map: push-lr density per 0x1000 block
P("== container 0x28: code map (push-lr per 4K block) ==")
row = []
for i in range(0, len(body), 0x1000):
    blk = [x for x in INS if i <= x[0] < i + 0x1000]
    plr = sum(1 for a, m, o in blk if m in ("push", "push.w") and "lr" in o)
    svc = sum(1 for a, m, o in blk if m == "svc")
    row.append("%02x:%d/%d" % (i >> 12, plr, svc))
P("  " + " ".join(row))

P("\n== svc sites (all) ==")
for a, m, o in INS:
    if m == "svc":
        P("  svc %-6s @%#x" % (o, a))

P("\n== REAL cmp-with-type sites (branch within 4, no neon/floats nearby) ==")
TYPES = ("0x24", "0x45", "0x201", "0x203", "0x210", "0x211", "0x280", "0x281")
for k, (a, m, o) in enumerate(INS):
    if m.startswith("cmp") and any("#" + t in o for t in TYPES):
        ctx = INS[max(0, k - 4):k + 5]
        ok = any(x[1].startswith("b") for x in ctx[4:]) and not any(x[1].startswith(("v", "vm", "f")) for x in ctx)
        tag = "REAL?" if ok else "noise"
        P("  [%s @%#x] %s" % (tag, a, " | ".join("%s %s" % (x[1], x[2]) for x in ctx)))

P("\n== nested driver @+0x19f00 ==")
d = body[0x19F00:0x19F00 + 0x770]
P("hex[0x10:0x80]: %s" % d[0x10:0x80].hex())
dins = [(i.address, i.mnemonic, i.op_str) for i in md.disasm(d, 0) if i.mnemonic != ".byte"]
plr = sum(1 for a, m, o in dins if m in ("push", "push.w") and "lr" in o)
P("push-lr=%d entropy=%.2f" % (plr, entropy(d)))
for a, m, o in dins[:40]:
    P("  %#08x %-8s %s" % (a, m, o))

P("\n== REG scan (whole body incl. nested) ==")
for o in range(0, len(body) - 3, 4):
    v = struct.unpack_from("<I", body, o)[0]
    if v in (0x03200400, 0x03E810, 0x03A2011C, 0x03A20124, 0x0900C234, 0x0900CB80):
        P("  %#010x @+%#x" % (v, o))
