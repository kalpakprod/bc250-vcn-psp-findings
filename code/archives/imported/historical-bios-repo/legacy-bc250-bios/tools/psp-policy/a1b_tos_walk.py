# A1b: full group walk of TOS_SECURITY_POLICY bodies (Robin + donors) + register overlap vs gasket.
import struct, json, os

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
ROM = open(FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()
G = r"C:\Users\OWNER\tmp_bc250\recon"


def body_of(blob):
    assert blob[0x10:0x14] == b"$PS1"
    size = struct.unpack_from("<I", blob, 0x14)[0]
    return blob[0x100:0x100 + size]


def walk(body, tag):
    groups = []
    off = 0x40
    while off + 8 <= len(body):
        t, c = struct.unpack_from("<II", body, off)
        if t == 0 or t > 0xFFFF or c > 0x100000 or off + 8 + c * 8 > len(body) + 8:
            break
        pairs = [(struct.unpack_from("<II", body, off + 8 + 8 * i)) for i in range(c)]
        groups.append((t, off, pairs))
        off += 8 + c * 8
    print("%s: body %#x, %d groups, walk ends @%#x %s" % (tag, len(body), len(groups), off, "(== len OK)" if off == len(body) else "!! MISMATCH"))
    return groups


def addr_class(a):
    if 0x0900C000 <= a <= 0x0900CFFF:
        return "VCN-BANK"
    if a in (0x03E810,):
        return "E810!"
    if 0x03A20100 <= a <= 0x03A201FF:
        return "DF-APERTURE"
    if 0x09300200 <= a <= 0x093002FF:
        return "DF-FW(930)"
    if 0x09000000 <= a <= 0x093FFFFF:
        return "SMN-090/093"
    return "other"


robin45 = body_of(ROM[0x9CA400:0x9CA400 + 0x6E0])
g45 = walk(robin45, "ROBIN 0x45")
robin_gasket = body_of(ROM[0x982000:0x982000 + 0x2E50])
gg = walk(robin_gasket, "ROBIN gasket 0x24")
print()
# robin 0x45 groups detail
for t, off, pairs in g45:
    cls = {}
    for a, v in pairs:
        cls[addr_class(a)] = cls.get(addr_class(a), 0) + 1
    print("  ROBIN45 grp %#06x @+%#05x n=%2d classes=%s" % (t, off, len(pairs), cls))
    for a, v in pairs:
        print("      {%#010x, %#010x}  %s" % (a, v, addr_class(a)))

print()
# donor 0x45 group summaries (which classes do they touch?)
DON = [
    ("cz_d0/e13", r"keys_raw\cezanne_d0\d00_e13_TOS_SECURITY_POLICY_0x45.bin"),
    ("cz_d0/e14", r"keys_raw\cezanne_d0\d00_e14_TOS_SECURITY_POLICY_0x45.bin"),
    ("cz_d2/e13", r"keys_raw\cezanne_d2\d02_e13_TOS_SECURITY_POLICY_0x45.bin"),
    ("cz_d2/e14", r"keys_raw\cezanne_d2\d02_e14_TOS_SECURITY_POLICY_0x45.bin"),
]
donor_groups = {}
for tag, rel in DON:
    p = os.path.join(G, rel)
    b = body_of(open(p, "rb").read())
    gr = walk(b, tag)
    donor_groups[tag] = (b, gr)
    for t, off, pairs in gr:
        cls = {}
        for a, v in pairs:
            cls[addr_class(a)] = cls.get(addr_class(a), 0) + 1
        print("  %s grp %#06x @+%#05x n=%3d classes=%s" % (tag, t, off, len(pairs), cls))
    print()

# KEY QUESTIONS:
print("== KEY: 0x03E810 values everywhere ==")


def find_addr(groups, tag, addr=0x03E810):
    hits = []
    for t, off, pairs in groups:
        for a, v in pairs:
            if a == addr:
                hits.append((hex(t), hex(v)))
    print("  %s: 0x03E810 in groups: %s" % (tag, hits))


find_addr(g45, "ROBIN 0x45")
find_addr(gg, "ROBIN gasket 0x24")
for tag, (b, gr) in donor_groups.items():
    find_addr(gr, tag)

print("\n== KEY: VCN bank (0x0900Cxxx) presence ==")
def find_bank(groups, tag):
    hits = []
    for t, off, pairs in groups:
        n = sum(1 for a, v in pairs if 0x0900C000 <= a <= 0x0900CFFF)
        if n:
            hits.append((hex(t), n))
    print("  %s: VCN-bank pairs per group: %s" % (tag, hits))


find_bank(g45, "ROBIN 0x45")
find_bank(gg, "ROBIN gasket 0x24")
for tag, (b, gr) in donor_groups.items():
    find_bank(gr, tag)

print("\n== KEY: DF aperture (0x03A201xx) presence ==")
def find_apt(groups, tag):
    hits = []
    for t, off, pairs in groups:
        vals = [(hex(a), hex(v)) for a, v in pairs if 0x03A20100 <= a <= 0x03A201FF]
        if vals:
            hits.append((hex(t), vals))
    print("  %s: %s" % (tag, hits))


find_apt(g45, "ROBIN 0x45")
find_apt(gg, "ROBIN gasket 0x24")
for tag, (b, gr) in donor_groups.items():
    find_apt(gr, tag)
