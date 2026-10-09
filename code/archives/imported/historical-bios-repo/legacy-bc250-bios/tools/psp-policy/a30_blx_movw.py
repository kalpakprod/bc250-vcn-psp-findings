# A30: hypothesis 2+5 hunt. (a) every blx rN in the container -> trace how rN is loaded
# (literal pool ldr, movw/movt pair, add rN,pc, movs imm); (b) every movw/movt pair that
# builds an address in code range 0x100..0x1A790 or ROM/RAM ranges; (c) code coverage of
# the blob: first 0x100 bytes (header) + tail after last decoded instruction.
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
BY = {a: k for k, (a, m, o) in enumerate(INS)}


def dump(lo, hi):
    return "\n".join("%#08x  %-8s %s" % (a, m, o) for a, m, o in INS if lo <= a < hi)


def u32(off):
    return struct.unpack_from("<I", body, off)[0]


print("== 0) blob layout / coverage ==")
last = INS[-1][0] if INS else 0
print("  body size %#x, last decoded insn @%#06x, tail bytes %#x" % (len(body), last, len(body) - last))
print("  header u32s (blob+0x00..0x100):")
for off in range(0, 0x100, 4):
    v = struct.unpack_from("<I", CON, off)[0]
    tag = ""
    if 0x101 <= (v | 1) <= 0x1A790:
        tag = "  <== code-range pointer (thumb=%s)" % (v & 1)
    print("  +%#04x: %#010x%s" % (off, v, tag))

print("\n== 1) header disasm (ARM + Thumb, both) ==")
for mode, name in ((capstone.CS_MODE_ARM, "ARM"), (capstone.CS_MODE_THUMB, "THUMB")):
    m2 = capstone.Cs(capstone.CS_ARCH_ARM, mode)
    m2.skipdata = True
    n = 0
    for i in m2.disasm(CON[:0x100], 0):
        if i.mnemonic != ".byte":
            n += 1
            print("  [%s] %#04x  %-8s %s" % (name, i.address, i.mnemonic, i.op_str))
    if n == 0:
        print("  [%s] no code" % name)

print("\n== 2) tail after last decoded insn (try disasm from last..end) ==")
tail_off = last
m3 = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
m3.skipdata = True
cnt = 0
for i in m3.disasm(body[tail_off:], tail_off):
    if i.mnemonic != ".byte":
        cnt += 1
        if cnt <= 80:
            print("  %#06x  %-8s %s" % (i.address, i.mnemonic, i.op_str))
print("  tail decoded insns: %d" % cnt)

print("\n== 3) all blx rN (register indirect calls) ==")
for k, (a, m, o) in enumerate(INS):
    if m == "blx" and not o.startswith("#"):
        print("---- blx %s @%#06x ----" % (o, a))
        print(dump(max(0, a - 0x50), a + 0x10))

print("\n== 4) movw/movt pairs building addresses ==")
# collect movw/movt; pair per register within 8-insn window
mw = {}
for k, (a, m, o) in enumerate(INS):
    if m in ("movw", "movt") and o.startswith("r"):
        parts = o.split(", ")
        if len(parts) != 2:
            continue
        rd = parts[0]
        imm = int(parts[1].lstrip("#"), 0)
        key = (m, rd)
        if key not in mw or a - mw[key][0] > 0x40:
            pass
        mw.setdefault(rd, []).append((a, m, imm))
for rd in sorted(mw):
    evs = mw[rd]
    i = 0
    while i < len(evs):
        if evs[i][1] == "movw":
            val = evs[i][2]
            j = i + 1
            while j < len(evs) and evs[j][0] - evs[i][0] <= 0x20:
                if evs[j][1] == "movt":
                    val = (evs[j][2] << 16) | evs[i][2]
                    if 0x100 <= val <= 0x1A790 or 0x984F00 <= val <= 0x99F690 \
                       or 0xE00000 <= val <= 0xF00000:
                        print("  r%-2s = %#010x  movw@%#06x movt@%#06x" % (rd, val, evs[i][0], evs[j][0]))
                    i = j
                    break
                j += 1
            else:
                if 0xE00000 <= (evs[i][2] << 16) <= 0xF00000:
                    print("  r%-2s  movw@%#06x = #%#x (hi?) unpaired" % (rd, evs[i][0], evs[i][2]))
            i = max(i + 1, j if j < len(evs) and evs[j][1] == "movt" else i + 1)
        else:
            i += 1

print("\n== 5) bare movt with code-range/ROM/RAM high halves ==")
for a, m, o in INS:
    if m == "movt" and o.startswith("r"):
        try:
            imm = int(o.split(", ")[1].lstrip("#"), 0)
        except Exception:
            continue
        if imm in (0x0, 0x98, 0x99, 0xE4, 0xE5, 0xE2):
            print("  movt @%#06x %s" % (a, o))

print("\n== 6) add rN, pc (PIC table base) ==")
for k, (a, m, o) in enumerate(INS):
    if m in ("add", "add.w", "addw", "adr", "sub") and "pc" in o and o.split(",")[0].startswith("r"):
        print("  @%#06x  %-6s %s" % (a, m, o))

print("\n== 7) ldr rN,[pc,#imm] with code-range or 0xE4/0xE5/0xE2 literal ==")
for k, (a, m, o) in enumerate(INS):
    if m.startswith("ldr") and "[pc" in o:
        try:
            imm = int(o[o.index("#") + 1:o.index("]")].rstrip("]"), 0)
        except Exception:
            continue
        lit = ((a + 4) & ~3) + imm
        if 0 <= lit <= len(body) - 4:
            v = u32(lit)
            if (0x100 <= v <= 0x1A790) or (0xE20000 <= v <= 0xE70000):
                print("  @%#06x %-8s %-24s -> lit@%#06x = %#010x" % (a, m, o, lit, v))
