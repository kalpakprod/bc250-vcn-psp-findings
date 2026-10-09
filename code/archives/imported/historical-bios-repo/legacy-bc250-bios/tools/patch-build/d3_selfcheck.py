# D3 self-check battery: independent validation of every assumption used in the builds.
import struct, hashlib

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
BASE = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()
D3 = r"C:\Users\OWNER\tmp_bc250\recon\d3"
UNSIGNED = open(r"C:\Users\OWNER\tmp_bc250\recon\bc250_sec_gasket_with_vcn_UNSIGNED_DO_NOT_FLASH.bin", "rb").read()

PASS = []
FAIL = []


def ok(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("  [%s] %s %s" % ("PASS" if cond else "FAIL", name, detail))


def fletcher32(data):
    s1 = s2 = 0
    for i in range(0, len(data), 2):
        w = data[i] | (data[i + 1] << 8)
        s1 = (s1 + w) % 65535
        s2 = (s2 + s1) % 65535
    return (s2 << 16) | s1


print("== 1. fletcher32 formula cross-validated on OTHER stock ROMs ==")
ROMS = [
    ("BC250_3.00.ROM", True), ("Robin5.00", True), ("Robin5 (1).00", True),
    ("dump_5.00.bin", True), ("8_cores_Steam.rom", None), ("bc250-Steam.rom", None),
    ("bc250 modded bios.ROM", None), ("my_4.0_MODED.bin", None),
    (r"..\\..\\bc250_firmware\\4700S\\C0A\\C0A", True),
]
for fn, _ in ROMS:
    try:
        b = open((FILES + "\\" + fn) if ".." not in fn else r"C:\Users\OWNER\tmp_bc250\bc250_firmware\4700S\C0A\C0A", "rb").read()
    except OSError as e:
        print("  [skip] %s (%s)" % (fn, e)); continue
    results = []
    for cookie, esz in ((b"$PSP", 16), (b"$BHD", 24)):
        i = -1
        while True:
            i = b.find(cookie, i + 1)
            if i < 0 or i > len(b) - 0x10:
                break
            cnt = struct.unpack_from("<I", b, i + 8)[0]
            if 0 < cnt <= 64:
                end = i + 0x10 + cnt * esz
                if end <= len(b):
                    stored = struct.unpack_from("<I", b, i + 4)[0]
                    calc = fletcher32(b[i + 8:end])
                    results.append((cookie.decode(), i, cnt, stored == calc))
    line = "; ".join("%s@%#x n=%d %s" % (c, o, n, "MATCH" if m else "MISMATCH") for c, o, n, m in results) or "no dirs"
    print("  %-28s %s" % (fn, line))
    if results:
        ok("fletcher %s" % fn, all(m for _, _, _, m in results), line)

print("\n== 2. base dump: no VALID L2 PSP dir, single gasket pointer ==")
pl2 = []
i = -1
while True:
    i = BASE.find(b"$PL2", i + 1)
    if i < 0:
        break
    pl2.append(i)
# a REAL L2 dir must be aligned, have sane count and a matching fletcher
valid_pl2 = []
for o in pl2:
    sane = (o % 4 == 0) and o + 0x10 <= len(BASE)
    cnt = struct.unpack_from("<I", BASE, o + 8)[0] if sane else -1
    fv = 0 < cnt <= 64 and (o + 0x10 + 16 * cnt <= len(BASE))
    fmatch = fv and struct.unpack_from("<I", BASE, o + 4)[0] == fletcher32(BASE[o + 8: o + 0x10 + 16 * cnt])
    if fmatch:
        valid_pl2.append(o)
    print("    $PL2 @%#x: aligned=%s count=%s fletcher=%s -> %s" % (o, o % 4 == 0, cnt if sane else "?", "MATCH" if fmatch else "no", "NOISE" if not fmatch else "REAL"))
ok("no VALID $PL2 L2 dir in base (raw hits must be compressed-data noise)", not valid_pl2, str([hex(x) for x in pl2]))
ptrs = []
pat = struct.pack("<I", 0xFF982000)
i = -1
while True:
    i = BASE.find(pat, i + 1)
    if i < 0:
        break
    ptrs.append(i)
ok("0xFF982000 referenced only by PSP dir entry (@0x8E0088)", ptrs == [0x8E0088], str([hex(x) for x in ptrs]))

print("\n== 3. D3-B blob audit: header / body / tail ==")
B = open(D3 + r"\D3-B_APCB-DFG-i_gasket-A-B-unsigned_DO_NOT_FLASH_WITHOUT_PROGRAMMER_BACKUP.bin", "rb").read()
hdr_new = B[0x9E0000:0x9E0100]
hdr_old = BASE[0x982000:0x982100]
diffhdr = [i for i in range(0x100) if hdr_new[i] != hdr_old[i]]
expect_hdr = set(range(0x14, 0x1C)) | set(range(0x50, 0x58)) | set(range(0x6C, 0x70))
ok("D3-B header: differs from orig ONLY inside size fields @0x14/@0x50/@0x6C", set(diffhdr) <= expect_hdr, str(sorted(set(diffhdr))))
ok("D3-B header sizes", (struct.unpack_from("<Q", hdr_new, 0x14)[0], struct.unpack_from("<Q", hdr_new, 0x50)[0], struct.unpack_from("<I", hdr_new, 0x6C)[0]) == (0x2E10, 0x2E10, 0x3010))
ok("D3-B header version/nonce preserved", hdr_new[0x58:0x6C] == hdr_old[0x58:0x6C] and hdr_new[0:0x14] == hdr_old[0:0x14] and hdr_new[0x1C:0x50] == hdr_old[0x1C:0x50])
tail_new = B[0x9E0000 + 0x3010 - 0x100: 0x9E0000 + 0x3010]
tail_old = BASE[0x982000 + 0x2E50 - 0x100: 0x982000 + 0x2E50]
ok("D3-B tail (signature area) = original verbatim", tail_new == tail_old)
body = B[0x9E0100: 0x9E0100 + 0x2E10]
bodydiff = [i for i in range(len(body)) if body[i] != UNSIGNED[i]]
expect_body = set(range(0x295C, 0x2960)) | set(range(0x25FC, 0x2600)) | set(range(0x2B74, 0x2B78)) | set(range(0x2604, 0x2608))
ok("D3-B body = UNSIGNED + edits ONLY inside the 4 step-A u32 slots", set(bodydiff) <= expect_body, str(sorted(set(bodydiff))))
for voff, oldv, newv in ((0x295C, 0, 6), (0x25FC, 0x87FF, 0x107FF), (0x2B74, 0x87FF, 0x107FF), (0x2604, 0, 0x10FFF)):
    ok("step-A value @body+%#x = %#x" % (voff, newv), struct.unpack_from("<I", body, voff)[0] == newv and struct.unpack_from("<I", UNSIGNED, voff)[0] == oldv)
# step-A edit targets are real {addr,value} pairs inside group tables (addr precedes value)
for voff, addr in ((0x295C, 0x03E810), (0x25FC, 0x03A2011C), (0x2B74, 0x03A2011C), (0x2604, 0x03A20124)):
    ok("pair check body+%#x: addr=%#x" % (voff, addr), struct.unpack_from("<I", body, voff - 4)[0] == addr)
# group walk + VCN bank
off, groups = 0x40, []
while off + 8 <= len(body):
    t, c = struct.unpack_from("<II", body, off)
    if t == 0 or t > 0xFFFF or c > 0x100000:
        break
    groups.append((t, c)); off += 8 + c * 8
ok("D3-B body group walk ends exactly at 0x2E10, 5 groups (201/203/210/280/281)", off == 0x2E10 and [g[0] for g in groups] == [0x201, 0x203, 0x210, 0x280, 0x281], str([(hex(t), c) for t, c in groups]))
ok("D3-B counts 1281/31/13/105/31 (orig+VCN bank)", [g[1] for g in groups] == [1281, 31, 13, 105, 31])
nvcn = sum(1 for i in range(0, len(body) - 8, 4) if 0x0900C000 <= struct.unpack_from("<I", body, i)[0] <= 0x0900CFFF)
ok("D3-B VCN bank = 56 pairs", nvcn == 56, str(nvcn))
ok("old gasket @0x982000 untouched in D3-B", B[0x982000:0x982000 + 0x2E50] == BASE[0x982000:0x982000 + 0x2E50])

print("\n== 4. D3-C audit: pure mechanics ==")
C = open(D3 + r"\D3-C_SIGNED-gasket-relocation_mechanics-test.bin", "rb").read()
ok("D3-C blob @0x9E0000 byte-identical to original @0x982000", C[0x9E0000:0x9E0000 + 0x2E50] == BASE[0x982000:0x982000 + 0x2E50])
e = None
cnt = struct.unpack_from("<I", C, 0x8E0008)[0]
for i in range(cnt):
    eo = 0x8E0010 + 16 * i
    if struct.unpack_from("<I", C, eo)[0] == 0x24:
        e = struct.unpack_from("<IIQ", C, eo)
ok("D3-C dir entry 0x24: size=0x2E50 (untouched), loc=0xFF9E0000", e == (0x24, 0x2E50, 0xFF9E0000), str([hex(x) for x in e]) if e else "not found")
ck = struct.unpack_from("<I", C, 0x8E0004)[0]
ok("D3-C dir fletcher32 valid", ck == fletcher32(C[0x8E0008: 0x8E0010 + 16 * cnt]), hex(ck))
# D3-C diff confined: dir cks(4B) + loc bytes + blob region
dC = [i for i in range(len(C)) if C[i] != BASE[i]]
outside = [i for i in dC if not (0x8E0004 <= i < 0x8E0008 or 0x8E0088 <= i < 0x8E0090 or 0x9E0000 <= i < 0x9E2E50)]
ok("D3-C diff vs base confined to {dir cks, dir loc, blob copy}", not outside, str([hex(x) for x in outside[:8]]))
ok("D3-C APCB untouched", C[0xAB1000:0xAB2000] == BASE[0xAB1000:0xAB2000])

print("\n== 5. D3-B diff confinement ==")
dB = [i for i in range(len(B)) if B[i] != BASE[i]]
outsideB = [i for i in dB if not (0x8E0004 <= i < 0x8E0008 or 0x8E0080 <= i < 0x8E0090 or 0x9E0000 <= i < 0x9E3010 or i in (0xAB1010, 0xAB1132, 0xAB116E))]
ok("D3-B diff vs base confined to {dir, blob, 3 APCB bytes}", not outsideB, str([hex(x) for x in outsideB[:8]]))

print("\n== 6. region safety / alignment ==")
ok("blob 0x9E0000 0x100-aligned and inside FF-run (>=0x9dc240)", 0x9E0000 % 0x100 == 0 and 0x9E0000 >= 0x9dc240)
ok("blob end 0x9E3010 < BHD dir 0xAB0000 (margin %#x)" % (0xAB0000 - 0x9E3010), 0x9E3010 < 0xAB0000)
ok("base region [0x9E0000,0xAB0000) was fully FF", all(x == 0xFF for x in BASE[0x9E0000:0xAB0000]))
ok("D3-B/C: bytes after blob up to 0xAB0000 still FF", all(x == 0xFF for x in B[0x9E3010:0xAB0000]) and all(x == 0xFF for x in C[0x9E2E50:0xAB0000]))
# sector containment: blob write region fits in whole 4K sectors whose rest is FF in image
ok("blob region 4K-sector-contained (0x9E0000 % 0x1000 == 0)", 0x9E0000 % 0x1000 == 0)

print("\n== 7. BHD dir / APCB references still consistent in D3-B ==")
cntb = struct.unpack_from("<I", B, 0xAB0008)[0]
ok("BHD dir fletcher still valid (untouched)", struct.unpack_from("<I", B, 0xAB0004)[0] == fletcher32(B[0xAB0008: 0xAB0010 + 24 * cntb]))
ok("BHD entry 0x60 -> APCB 0xFFAB1000 size 0x2000 unchanged", B[0xAB0010:0xAB0028] == BASE[0xAB0010:0xAB0028])
ok("D3-B APCB size field unchanged (0xB64)", struct.unpack_from("<I", B, 0xAB1008)[0] == 0xB64)

print("\nRESULT: %d passed, %d failed" % (len(PASS), len(FAIL)))
if FAIL:
    print("FAILED:", FAIL)
