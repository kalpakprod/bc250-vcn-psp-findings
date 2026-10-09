# A4+A5+A6 combined:
#  A4: 0x0900CC00 IFR question in Setup.PE32 + CbsSetupDxe SMN poke registry + donor comparison
#  A5: identify 0x4F blob + DEBUG_UNLOCK 0x13 stub check
#  A6: HW_IP_CONFIG 0x20 vs live discovery dump
import struct, math, os

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
ROM = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()
FF = r"C:\Users\OWNER\tmp_bc250\recon\uefi_ffs"


def entropy(b):
    if not b:
        return 0
    c = [0] * 256
    for x in b:
        c[x] += 1
    n = len(b)
    return -sum((k / n) * math.log2(k / n) for k in c if k)


print("== A4: 0x0900CC00 / 0x0900Cxxx constants in x86 modules ==")
for mod in ("Setup.PE32", "CbsSetupDxe.PE32", "CbsBaseDxe.PE32", "AmdPspDxeV2.PE32", "PspDxe.PE32"):
    p = os.path.join(FF, mod)
    if not os.path.exists(p):
        print("  %s: (нет файла)" % mod)
        continue
    b = open(p, "rb").read()
    hits = []
    for a in range(0x0900C000, 0x0900D000, 4):
        pat = struct.pack("<I", a)
        i = b.find(pat)
        if i >= 0:
            hits.append((a, i))
    print("  %-22s: %d констант 0x0900Cxxx: %s" % (mod, len(hits), [("%#x@%#x" % h) for h in hits[:10]]))

# donor: scan whole cezanne BIOS for 0x0900CC00
DON = r"C:\Users\OWNER\tmp_bc250\recon\cezanne_uefi\BIOS.bin"
if os.path.exists(DON):
    b = open(DON, "rb").read()
    pat = struct.pack("<I", 0x0900CC00)
    idx = []
    i = -1
    while True:
        i = b.find(pat, i + 1)
        if i < 0:
            break
        idx.append(i)
    print("  донор cezanne BIOS: 0x0900CC00 встречается %d раз: %s" % (len(idx), [hex(x) for x in idx[:8]]))
else:
    print("  (донор BIOS.bin не найден)")

# IFR context around 0x0900CC00 in Setup.PE32 (find the form opcodes)
p = os.path.join(FF, "Setup.PE32")
if os.path.exists(p):
    b = open(p, "rb").read()
    i = b.find(struct.pack("<I", 0x0900CC00))
    if i >= 0:
        print("\n  IFR context around hit @Setup+%#x:" % i)
        lo = max(0, i - 0x40)
        seg = b[lo:i + 0x40]
        for k in range(0, len(seg), 16):
            print("    +%#06x: %s" % (lo + k, seg[k:k + 16].hex()))

print("\n== A5: blob 0x4F @0x9cab00 (0x10200) ==")
blob = ROM[0x9CAB00:0x9CAB00 + 0x10200]
print("  head:", blob[:0x20].hex())
print("  entropy head 0x100: %.2f; whole: %.2f" % (entropy(blob[:0x100]), entropy(blob)))
nz = sum(1 for x in blob if x)
print("  non-zero bytes: %d / %d (%.1f%%)" % (nz, len(blob), 100 * nz / len(blob)))
if blob[0x10:0x14] == b"$PS1":
    print("  $PS1 envelope: size=%#x type@58=%#x ver@60=%#x" % (
        struct.unpack_from("<I", blob, 0x14)[0], struct.unpack_from("<I", blob, 0x58)[0],
        struct.unpack_from("<I", blob, 0x60)[0]))
# strings
s = bytes(x if 32 <= x < 127 else 46 for x in blob[:0x200])
print("  ascii head:", s[:96].decode("ascii", "replace"))
# where does content actually start (skip zeros)?
j = 0
while j < len(blob) and blob[j] == 0:
    j += 1
print("  первый ненулевой байт @+%#x: %s" % (j, blob[j:j + 16].hex()))

print("\n== A5: DEBUG_UNLOCK 0x13 @0x97f900 (0x2000) ==")
db = ROM[0x97F900:0x97F900 + 0x2000]
print("  head:", db[:0x20].hex())
if db[0x10:0x14] == b"$PS1":
    print("  $PS1 envelope: size=%#x type@58=%#x ver@60=%#x" % (
        struct.unpack_from("<I", db, 0x14)[0], struct.unpack_from("<I", db, 0x58)[0],
        struct.unpack_from("<I", db, 0x60)[0]))
    body = db[0x100:0x100 + struct.unpack_from("<I", db, 0x14)[0]]
    print("  body len=%#x entropy=%.2f head=%s" % (len(body), entropy(body), body[:24].hex()))
    nz = sum(1 for x in body if x)
    print("  body non-zero: %d/%d (%.1f%%)" % (nz, len(body), 100 * nz / len(body)))

print("\n== A6: HW_IP_CONFIG 0x20 @0x981900 (0x650) ==")
ip = ROM[0x981900:0x981900 + 0x650]
print("  head:", ip[:0x20].hex())
if ip[0x10:0x14] == b"$PS1":
    size = struct.unpack_from("<I", ip, 0x14)[0]
    body = ip[0x100:0x100 + size]
    print("  $PS1 size=%#x; body entropy=%.2f" % (size, entropy(body)))
    print("  body head:", body[:0x40].hex())
    # u32 view
    for k in range(0, min(0x80, len(body)), 16):
        print("    +%#04x: %08x %08x %08x %08x" % ((k,) + struct.unpack_from("<IIII", body, k)))

print("\n== A6: live discovery_robin.bin ==")
for cand in (r"C:\Users\OWNER\tmp_bc250\bc250_firmware\discovery_robin.bin",):
    if os.path.exists(cand):
        d = open(cand, "rb").read()
        print("  len=%#x entropy=%.2f head=%s" % (len(d), entropy(d), d[:0x40].hex()))
        # IP discovery table: header {hwip offset...} binary: {u16 size?}; try u16/u32 walk
        # classic AMD discovery: {ip_discovery_headers[]}: each {u8 hwip, u8 major, u8 minor, u8 num_instances?} + die headers
        # print u8 quadruple view
        for k in range(0, 0x80, 8):
            row = d[k:k + 8]
            print("    +%#04x: %s   ips: %s" % (k, row.hex(), [hex(x) for x in row[:4]]))
    else:
        print("  (нет файла %s)" % cand)
