# D3 pre-check:
# 1) my_4.0_MODED == W25Q128BV hw dump (board state)
# 2) APCB @0xAB1000 in my_4.0_MODED: header, D1 checksum formula verification
# 3) DFG group 0x1703 inside APCB: find wildcard rows 00 ff 1f 00 (patch targets)
# 4) SEC GASKET blob @0x982000: original size vs UNSIGNED step-B blob size
import struct, hashlib

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
base_path = FILES + r"\my_4.0_MODED.bin"
hw_path = FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN"
UNSIGNED = r"C:\Users\OWNER\tmp_bc250\recon\bc250_sec_gasket_with_vcn_UNSIGNED_DO_NOT_FLASH.bin"

b = open(base_path, "rb").read()
h = open(hw_path, "rb").read()
print("base size:", len(b), " hw size:", len(h))
print("md5 base :", hashlib.md5(b).hexdigest())
print("md5 hw   :", hashlib.md5(h[:len(b)]).hexdigest() if len(h) >= len(b) else "hw smaller")

# --- APCB ---
APCB_OFF = 0xAB1000
a = b[APCB_OFF:APCB_OFF + 0x2000]
assert a[:4] == b"APCB", a[:4].hex()
size = struct.unpack_from("<I", a, 8)[0]
inst = struct.unpack_from("<I", a, 0xC)[0]
cks_stored = a[0x10]
print("\nAPCB @0xAB1000: magic=%s size=%#x instance=%#x cks@0x10=%#x" % (a[:4], size, inst, cks_stored))


def apcb_cksum(buf, size):
    s = 0
    for i in range(size):
        if i == 0x10:
            continue
        s += buf[i]
    return (0x100 - s) & 0xFF


got = apcb_cksum(a, size)
print("D1 formula check: computed=%#x stored=%#x -> %s" % (got, cks_stored, "OK" if got == cks_stored else "MISMATCH"))

# verify on all corpus samples
print("\ncross-check D1 formula on corpus:")
for nm, fn, off in [
    ("3.00_CHIPSETMENU", FILES + r"\BC250_3.00_CHIPSETMENU.ROM", 0xAB1000),
    ("dump_5.00", FILES + r"\dump_5.00.bin", 0xAB1000),
    ("Robin5.00", FILES + r"\Robin5.00", 0xAB1000),
    ("Robin5 (1).00", FILES + r"\Robin5 (1).00", 0xAB1000),
    ("hw (2)", FILES + r"\W25Q128BV@WSON8_20250122_140516 (1).BIN", 0xAB1000),
    ("bc250 modded", FILES + r"\bc250 modded bios.ROM", 0xAB1000),
    ("8_cores_Steam", FILES + r"\8_cores_Steam.rom", 0xAB1000),
    ("bc250-Steam", FILES + r"\bc250-Steam.rom", 0xAB1000),
]:
    try:
        d = open(fn, "rb").read()
    except OSError as e:
        print("  %-18s skip (%s)" % (nm, e))
        continue
    if len(d) < off + 0x2000 or d[off:off + 4] != b"APCB":
        # search
        i = d.find(b"APCB")
        if i < 0:
            print("  %-18s no APCB" % nm)
            continue
        off = i
    sz = struct.unpack_from("<I", d, off + 8)[0]
    st = d[off + 0x10]
    cm = apcb_cksum(d[off:off + sz + 0x100], sz)
    print("  %-18s @%#x size=%#x stored=%#x calc=%#x %s" % (nm, off, sz, st, cm, "OK" if st == cm else "FAIL"))

# --- DFG group inside APCB ---
# APCB v2: after 0x20-byte header, groups: {sig u32, GroupId u16, hdr u8 0x10, ver, rsvd, SizeOfGroup u32}
print("\nAPCB groups walk:")
o = 0x20
while o + 0x10 <= size:
    sig = a[o:o + 4]
    gid = struct.unpack_from("<H", a, o + 4)[0]
    hdr = a[o + 6]
    gsz = struct.unpack_from("<I", a, o + 0xC)[0]
    if sig == b"\xff\xff\xff\xff" or gsz == 0 or gsz > size:
        break
    print("  +%#05x sig=%-9r gid=%#06x hdr=%#x size=%#x" % (o, sig, gid, hdr, gsz))
    o += gsz
print("groups end @+%#x (size=%#x)" % (o, size))

# --- DFG 0x1703: dump contents, find wildcard rows ---
i = a.find(struct.pack("<H", 0x1703))
print("\nfirst 0x1703 u16 @APCB+%#x" % i)
# walk groups properly printing DFG block rows
# find wildcard 00 ff 1f 00 across the whole APCB body
w = -1
wild = []
while True:
    w = a.find(bytes.fromhex("00 ff 1f 00"), w + 1)
    if w < 0:
        break
    wild.append(w)
print("wildcard rows 00 ff 1f 00 @APCB offsets:", [hex(x) for x in wild])

# --- SEC GASKET size check ---
u = open(UNSIGNED, "rb").read()
print("\nUNSIGNED gasket size:", len(u))
G_OFF = 0x982000
g_orig = b[G_OFF:G_OFF + 0x300]
print("gasket orig @0x982000: %s ..." % g_orig[:16].hex(" "))
# original full blob size from PSP dir: find via dir or the $PS1 envelope u64 size @+0x10?
# $PS1 header: 16B nonce + '$PS1' + u64 size + ... per doc: header 0x200
if g_orig[0x10:0x14] == b"$PS1":
    psz = struct.unpack_from("<Q", g_orig, 0x14)[0]
    print("orig $PS1 envelope size @0x982000+0x14:", hex(psz))
if u[0x10:0x14] == b"$PS1":
    usz = struct.unpack_from("<Q", u, 0x14)[0]
    print("UNSIGNED $PS1 envelope size:", hex(usz))
