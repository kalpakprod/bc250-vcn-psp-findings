# A30c: exhaustive RAW scan for Thumb BL encodings at EVERY halfword offset of the
# whole blob (disassembler stream alignment can hide bl). Also BLX imm.
# Then: same scan for branches (B.W) to the applier heads. Targets of interest are
# the orphan appliers: 0xfeac 0x20d8 0x1346a 0xa4e6 0x4914 0x13628 0x16658 0xfe04.
import struct

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
ROM = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()
CON = ROM[0x984F00:0x984F00 + 0x1A790]

INTEREST = {0xFEAC: "interp1", 0x20D8: "sequencer", 0x1346A: "loader", 0xA4E6: "donor",
            0x4914: "stage-select", 0x13628: "boot-fn", 0x16658: "orchestrator",
            0xFE04: "apply-all", 0xFF30: "type-clear", 0x10F30: "type-set",
            0x10BF8: "type-walk", 0x504C: "per-type", 0x2178: "interp2", 0x1EF4: "g211"}

hits = {}
for off in range(0, len(CON) - 4, 2):
    h = struct.unpack_from("<H", CON, off)[0]
    if (h >> 11) != 0x1E:  # 0xF000..0xF7FF upper bl/blx-imm
        continue
    lo = struct.unpack_from("<H", CON, off + 2)[0]
    if (lo >> 12) != 0xE and (lo >> 12) != 0xF:  # 0xE800..0xFFFF lower
        continue
    H = h & 0x7FF
    L = lo & 0x7FF
    disp = (H << 12) | (L << 1)
    if disp & 0x400000:
        disp -= 0x800000
    src = off - 0x100  # body-relative (code addressing: body+0 = +0x100)
    tgt = src + 4 + disp
    blx = (lo >> 12) == 0xE
    hits.setdefault(tgt, []).append((src, blx, off))

print("== raw BL/BLX-imm callers of interesting targets (body-relative) ==")
for t in sorted(INTEREST):
    cs = hits.get(t, [])
    print("  %#08x %-12s <- %s" % (t, INTEREST[t],
          " ".join("%#x%s" % (a, "(blx)" if b else "") for a, b, _ in cs) or "NONE"))

print("\n== ALL raw-bl targets that fall in code range with NO disasm-stream caller ==")
# cross-check: which targets receive raw-bl hits at all (any), count
import capstone
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
md.skipdata = True
body = CON[0x100:]
stream = {}
for i in md.disasm(body, 0):
    if i.mnemonic in ("bl", "blx") and "#" in i.op_str:
        try:
            stream.setdefault(int(i.op_str.split("#")[-1], 0), []).append(i.address)
        except Exception:
            pass

print("\n== raw vs stream sanity (interp2/apply-all) ==")
for t in (0x2178, 0xFE04, 0x20D8, 0xFEAC):
    print("  target %#x: raw=%s stream=%s" % (t,
          [hex(a) for a, _, _ in hits.get(t, [])][:6],
          [hex(a) for a in stream.get(t, [])][:6]))
