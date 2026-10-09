# B1e: external caller, round 2. Which blob parses the $PSP dir @0x8E0000 or
# references container/gasket sizes (0x1A770/0x1A570/0x2E50)? Context check of the
# u16 hits from b1_extscan (blob 0x01: 3E814/3E810; blobs 0x33/0x34: FEAC/BA98).
# Also: what is the first code at container+0x100 (potential entry/registration)?
import struct
import capstone

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
ROM = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()
u32 = lambda b, o: struct.unpack_from("<I", b, o)[0]
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
md.skipdata = True

out = []
P = out.append
DIR = 0x8E0000
n = u32(ROM, DIR + 8)
blobs = []
for i in range(n):
    e = DIR + 0x10 + 0x10 * i
    blobs.append((ROM[e], u32(ROM, e + 8) & 0xFFFFFF, u32(ROM, e + 4)))

P("== u32 scan: 0x8E0000 (dir), 0x1A770/0x1A570 (container size), 0x2E50, 0x1A790 ==")
NEED = {0x8E0000: "dir base", 0x1A770: "container size (dir)", 0x1A570: "container size ($PS1)",
        0x2E50: "gasket size", 0x1A790: "container size (legacy)"}
for t, a, s in blobs:
    buf = ROM[a:a + s]
    for val, desc in NEED.items():
        k = buf.find(struct.pack("<I", val))
        if k >= 0:
            P("  blob %#04x @%#x +%#x: %#x (%s)" % (t, a, k, val, desc))
    # aligned u16 movw candidates, capped
    for val in NEED:
        cnt = 0
        k = 0
        while cnt < 10:
            k = buf.find(struct.pack("<H", val & 0xFFFF), k)
            if k < 0:
                break
            if k % 2 == 0:
                P("  blob %#04x u16 %#x @+%#x" % (t, val & 0xFFFF, k))
                cnt += 1
            k += 1

P("")
P("== context dump: blob 0x01 (PSP bootloader) around u16 3E810@+0x5fc3 / 3E814@+0x9eee ==")
t01, a01, s01 = [b for b in blobs if b[0] == 0x01][0]
buf = ROM[a01:a01 + s01]
P("  blob 0x01 head: %s" % " ".join("%02x" % c for c in buf[:0x40]))
for k in (0x5fc3 & ~1, 0x9eee & ~1):
    P("  -- around +%#x --" % k)
    for i in md.disasm(buf[k - 0x20:k + 0x40], k - 0x20):
        P("    +%#06x  %-8s %s" % (i.address - 0, i.mnemonic, i.op_str))

P("")
P("== context dump: blobs 0x33/0x34 u16 FEAC/BA98 (disasm around, is it code?) ==")
for t, k in ((0x33, 0x3af1), (0x33, 0x78a7), (0x34, 0x5e68), (0x34, 0x291c)):
    a, s = [(ba, bs) for ty, ba, bs in blobs if ty == t][0]
    b = ROM[a:a + s]
    P("  -- blob %#x around +%#x --" % (t, k))
    for i in md.disasm(b[k - 0x10:k + 0x10], k - 0x10):
        P("    +%#06x  %-8s %s" % (i.address, i.mnemonic, i.op_str))

P("")
P("== container 0x28: first code at +0x100 (entry candidates) ==")
ca, cs = [(ba, bs) for ty, ba, bs in blobs if ty == 0x28][0]
body = ROM[ca + 0x100:ca + 0x100 + 0x200]
for i in md.disasm(body[:0x100], 0):
    P("  %#08x  %-8s %s" % (i.address, i.mnemonic, i.op_str))

P("")
P("== container 0x28: u16 FEAC @+0x99ce, BA98 @+0x51b2 context (own blob) ==")
cb = ROM[ca:ca + cs]
for k in (0x99ce & ~1, 0x51b2):
    P("  -- around +%#x --" % k)
    for i in md.disasm(cb[k - 0x10:k + 0x10], k - 0x10):
        P("    +%#06x  %-8s %s" % (i.address, i.mnemonic, i.op_str))

open(r"C:\Users\OWNER\bc250-bios\evidence\b1_extscan2.txt", "w").write("\n".join(out))
print("written b1_extscan2.txt, %d lines" % len(out))
