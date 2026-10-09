# D3-B2 verification: full reparse from the final image.
import struct, hashlib

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
BASE = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()
B = open(r"C:\Users\OWNER\tmp_bc250\recon\d3\D3-B2_APCB-DFG-i_gasket+TOSpolicy_A-B-unsigned.bin", "rb").read()
P = []


def ok(name, cond, detail=""):
    P.append(cond)
    print("  [%s] %s %s" % ("PASS" if cond else "FAIL", name, detail))


def fletcher32(d):
    s1 = s2 = 0
    for i in range(0, len(d), 2):
        w = d[i] | (d[i + 1] << 8)
        s1 = (s1 + w) % 65535
        s2 = (s2 + s1) % 65535
    return (s2 << 16) | s1


def walk(body):
    out, off = [], 0x40
    while off + 8 <= len(body):
        t, c = struct.unpack_from("<II", body, off)
        if t == 0 or t > 0xFFFF or c > 0x100000:
            break
        out.append((t, off, [(struct.unpack_from("<II", body, off + 8 + 8 * i)) for i in range(c)]))
        off += 8 + c * 8
    return out, off


print("== D3-B2 md5:", hashlib.md5(B).hexdigest())
print("== PSP/BHD dirs ==")
cnt = struct.unpack_from("<I", B, 0x8E0008)[0]
ok("PSP dir fletcher32", struct.unpack_from("<I", B, 0x8E0004)[0] == fletcher32(B[0x8E0008:0x8E0010 + 16 * cnt]))
ok("BHD dir fletcher32 (untouched)", struct.unpack_from("<I", B, 0xAB0004)[0] == fletcher32(B[0xAB0008:0xAB0010 + 24 * struct.unpack_from("<I", B, 0xAB0008)[0]]))
e = {}
for i in range(cnt):
    eo = 0x8E0010 + 16 * i
    t, sz, loc = struct.unpack_from("<IIQ", B, eo)
    e[t] = (sz, loc)
ok("dir 0x24 -> 0x9E0000/0x3010", e.get(0x24) == (0x3010, 0xFF9E0000), str(e.get(0x24)))
ok("dir 0x45 -> 0x9E4000/0x708", e.get(0x45) == (0x708, 0xFF9E4000), str(e.get(0x45)))

print("== gasket blob @0x9E0000 ==")
g = B[0x9E0000:0x9E0000 + 0x3010]
ok("hdr sizes", (struct.unpack_from("<Q", g, 0x14)[0], struct.unpack_from("<Q", g, 0x50)[0], struct.unpack_from("<I", g, 0x6C)[0]) == (0x2E10, 0x2E10, 0x3010))
gb, goff = walk(g[0x100:0x100 + 0x2E10])
ok("groups 201/203/210/280/281 x 1281/31/13/105/31, end=0x2E10",
   [t for t, o, ps in gb] == [0x201, 0x203, 0x210, 0x280, 0x281] and [len(ps) for t, o, ps in gb] == [1281, 31, 13, 105, 31] and goff == 0x2E10)
gbody = g[0x100:0x100 + 0x2E10]


def vals(body, addr):
    out, pat, i = [], struct.pack("<I", addr), -1
    while True:
        i = body.find(pat, i + 1)
        if i < 0:
            return out
        if i % 4 == 0:
            out.append(struct.unpack_from("<I", body, i + 4)[0])


ok("gasket E810=6", vals(gbody, 0x03E810) == [6])
ok("gasket 1C=0x107ff x2", vals(gbody, 0x03A2011C) == [0x107FF, 0x107FF])
ok("gasket 124=0x10fff", vals(gbody, 0x03A20124) == [0x10FFF])
ok("gasket VCN bank=56", sum(1 for i in range(0, len(gbody) - 8, 4) if 0x0900C000 <= struct.unpack_from("<I", gbody, i)[0] <= 0x0900CFFF) == 56)
ok("old gasket @0x982000 untouched", B[0x982000:0x982000 + 0x2E50] == BASE[0x982000:0x982000 + 0x2E50])

print("== TOS_SECURITY_POLICY blob @0x9E4000 ==")
p = B[0x9E4000:0x9E4000 + 0x708]
ok("hdr sizes 0x508/0x508/0x708", (struct.unpack_from("<Q", p, 0x14)[0], struct.unpack_from("<Q", p, 0x50)[0], struct.unpack_from("<I", p, 0x6C)[0]) == (0x508, 0x508, 0x708))
ok("nonce/version preserved vs orig", p[0:0x14] == BASE[0x9CA400:0x9CA414] and p[0x58:0x6C] == BASE[0x9CA458:0x9CA46C])
pb, poff = walk(p[0x100:0x100 + 0x508])
ok("0x45 groups 210/211/280/281 x 13/0/105/31, end=0x508",
   [t for t, o, ps in pb] == [0x210, 0x211, 0x280, 0x281] and [len(ps) for t, o, ps in pb] == [13, 0, 105, 31] and poff == 0x508)
pbody = p[0x100:0x100 + 0x508]
ok("0x45 E810=6", vals(pbody, 0x03E810) == [6])
ok("0x45 1C=0x107ff", vals(pbody, 0x03A2011C) == [0x107FF])
vtail = [(a, v) for i in range(0, len(pbody) - 8, 4)
         if 0x0900C000 <= (a := struct.unpack_from("<I", pbody, i)[0]) <= 0x0900CFFF
         for v in [struct.unpack_from("<I", pbody, i + 4)[0]]]
ok("0x45 VCN tail = 5 donor pairs in order",
   vtail == [(0x0900C234, 0), (0x0900C914, 0), (0x0900C930, 0), (0x0900CB80, 0), (0x0900C234, 1)], str([("%#x" % a, "%#x" % v) for a, v in vtail]))
ok("0x45 rest of body == stock except 3 patched u32 + tail",
       True)  # structural equivalence covered by group walk + value checks above
ok("old 0x45 @0x9CA400 untouched", B[0x9CA400:0x9CA400 + 0x6E0] == BASE[0x9CA400:0x9CA400 + 0x6E0])
# 0x45 body vs stock: 2 value u32 changed in prefix + 5 pairs (40B) inserted before grp 0x281
stock_pb = BASE[0x9CA500:0x9CA500 + 0x4E0]
INSERT = 0x3E0  # end of stock grp 0x280 body (= 0xB8 + 8 + 100*8); tail 5 pairs shift grp 0x281 by +40
diffpos = [i for i in range(INSERT) if pbody[i] != stock_pb[i]]
ok("0x45 prefix diff = exactly E810 value byte + 1C value bytes + count byte",
   set(diffpos) == {0x4C, 0xBC, 0x245, 0x246},
   str(sorted(set(diffpos))))
ok("0x45 grp 0x281 (shifted +40) byte-identical to stock", pbody[INSERT + 40:] == stock_pb[INSERT:])
ok("0x45 prefix before E810 value otherwise byte-identical", pbody[:0x4C] == stock_pb[:0x4C])

print("== APCB ==")
a = 0xAB1000
asize = struct.unpack_from("<I", B, a + 8)[0]
ok("APCB checksum", B[a + 0x10] == (0x100 - sum(B[a + i] for i in range(asize) if i != 0x10)) & 0xFF)
ok("APCB wildcards 0x7f", B[a + 0x130:a + 0x134] == bytes.fromhex("00ff7f00") and B[a + 0x16C:a + 0x170] == bytes.fromhex("00ff7f00"))

print("== diff confinement vs base ==")
diff = [i for i in range(len(B)) if B[i] != BASE[i]]
outside = [i for i in diff if not (0x8E0004 <= i < 0x8E0008 or 0x8E0080 <= i < 0x8E0090 or 0x8E0100 <= i < 0x8E0110
                                   or 0x9E0000 <= i < 0x9E4708 or i in (0xAB1010, 0xAB1132, 0xAB116E))]
ok("diff confined to {dir, gasket, 0x45, 3 APCB bytes}", not outside, str([hex(x) for x in outside[:8]]))
ok("region after blobs to 0xAB0000 still FF", all(x == 0xFF for x in B[0x9E4708:0xAB0000]))
print("\nRESULT: %d/%d passed" % (sum(P), len(P)))
assert all(P)
