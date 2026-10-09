# A12: the hidden $PS1 module inside type-0x44 region @0x9C3F10 (body 0x3000) - last readable PSP module.
import struct, math
import capstone

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
ROM = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
md.detail = False
md.skipdata = True

# enumerate ALL plausible $PS1 envelopes in the 0x44 dir region 0x9C3D00..0x9CA310
P = print
region = (0x9C3D00, 0x9CA310)
hits = []
for off in range(region[0], region[1] - 0x210, 4):
    if struct.unpack_from("<I", ROM, off + 0x10)[0] == 0x31535024:
        sz = struct.unpack_from("<Q", ROM, off + 0x14)[0]
        tot = struct.unpack_from("<I", ROM, off + 0x6C)[0]
        if 0x10 <= sz <= region[1] - off - 0x200 and tot == sz + 0x200:
            hits.append((off, sz, tot))
P("$PS1 envelopes in 0x44 region:")
for off, sz, tot in hits:
    body = ROM[off + 0x100:off + 0x100 + sz]
    ins = [(i.address, i.mnemonic, i.op_str) for i in md.disasm(body, 0) if i.mnemonic != ".byte"]
    plr = sum(1 for a, m, o in ins if m in ("push", "push.w") and "lr" in o)
    cnt = [0] * 256
    for b in body:
        cnt[b] += 1
    ent = -sum((c / len(body)) * math.log2(c / len(body)) for c in cnt if c)
    P("  @%#x size=%#x ent=%.2f push-lr=%d" % (off, sz, ent, plr))
    if plr >= 5:
        P("  -- svc / cmp-type / REG hunt --")
        for a, m, o in ins:
            if m == "svc":
                P("     svc %-6s @%#x" % (o, a))
        for a, m, o in ins:
            if m.startswith("cmp") and any("#" + t in o for t in ("0x24", "0x45", "0x201", "0x210", "0x280", "0x281")):
                P("     [cmp @%#x] %s %s" % (a, m, o))
        for o in range(0, len(body) - 3, 4):
            v = struct.unpack_from("<I", body, o)[0]
            if v in (0x03200400, 0x03E810, 0x03A2011C, 0x0900C234, 0x0900CB80):
                P("     REG %#010x @+%#x" % (v, o))
        # first 0x60 of code
        P("  -- head --")
        for a, m, o in ins[:24]:
            P("     %#08x %-8s %s" % (a, m, o))
