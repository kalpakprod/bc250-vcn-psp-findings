# D3 build: two test images from the board's own dump (W25Q128BV).
#  D3-B (main): step A (3 gasket register edits) + step B (VCN bank, UNSIGNED) relocated
#               to 0x9E0000 + PSP dir repoint + fletcher32 dir checksum + APCB DFG patch (i).
#  D3-A (control): APCB patch only (expected false-negative per two-lock model).
import struct, hashlib, json, os

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
UNSIGNED = r"C:\Users\OWNER\tmp_bc250\recon\bc250_sec_gasket_with_vcn_UNSIGNED_DO_NOT_FLASH.bin"
OUTDIR = r"C:\Users\OWNER\tmp_bc250\recon\d3"
os.makedirs(OUTDIR, exist_ok=True)

BASE = FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN"
G_OLD = 0x982000          # original gasket blob (header @+0, body @+0x100, tail @+0x2D50..+0x2E50)
G_OLD_SIZE = 0x2E50
G_NEW_OFF = 0x9E0000      # relocation target (inside FF run 0x9dc240-0xab0000)
DIR = 0x8E0000            # PSP L1 directory
APCB = 0xAB1000           # APCB (BIOS dir entry 0x60)


def fletcher32(data):
    assert len(data) % 2 == 0
    s1 = s2 = 0
    for i in range(0, len(data), 2):
        w = data[i] | (data[i + 1] << 8)
        s1 = (s1 + w) % 65535
        s2 = (s2 + s1) % 65535
    return (s2 << 16) | s1


def apcb_cksum(buf, size):
    return (0x100 - sum(buf[i] for i in range(size) if i != 0x10)) & 0xFF


base = open(BASE, "rb").read()
manifest = {"base": BASE, "base_md5": hashlib.md5(base).hexdigest(), "changes": []}


def note(img, off, old, new, what):
    assert img[off:off + len(new)] == old, "mismatch at %#x: %s != %s" % (off, img[off:off + len(new)].hex(), old.hex())
    img[off:off + len(new)] = new
    manifest["changes"].append({"what": what, "offset": off, "old": old.hex(), "new": new.hex()})


# ---------- common: APCB DFG patch (i) ----------
def apply_apcb_patch(img):
    a_off = APCB
    assert img[a_off:a_off + 4] == b"APCB"
    size = struct.unpack_from("<I", img, a_off + 8)[0]
    # wildcard rows inside DFG group (APCB+0xf4 .. +0x17c): rows at +0x130 and +0x16c
    for w in (0x130, 0x16C):
        off = a_off + w
        old = bytes(img[off:off + 4])
        assert old == bytes.fromhex("00 ff 1f 00"), "wildcard row not found at +%#x: %s" % (w, old.hex())
        note(img, off, old, bytes.fromhex("00 ff 7f 00"), "APCB DFG wildcard 0x1f->0x7f (+%#x)" % w)
    # recompute u8 checksum @+0x10
    oldcks = img[a_off + 0x10]
    region = bytes(img[a_off:a_off + size])
    newcks = apcb_cksum(region, size)
    note(img, a_off + 0x10, bytes([oldcks]), bytes([newcks]), "APCB checksum u8@+0x10 recalc")
    return newcks


# ---------- D3-B ----------
img = bytearray(base)

# 1) gasket body: UNSIGNED + step-A edits
body = bytearray(open(UNSIGNED, "rb").read())
assert len(body) == 0x2E10
# step A edits (verified offsets from scan):
STEP_A = [  # (value offset = addr offset + 4; addr offsets from scan: 0x2958/0x25f8/0x2b70/0x2600)
    (0x295C, 0x00000000, 0x00000006, "A1: 0x03E810 (grp 0x210) VCN_SEG enable 0->6"),
    (0x25FC, 0x000087FF, 0x000107FF, "A2: 0x03A2011C (grp 0x201) DF window low bit-12"),
    (0x2B74, 0x000087FF, 0x000107FF, "A2: 0x03A2011C (grp 0x280) DF window low bit-12"),
    (0x2604, 0x00000000, 0x00010FFF, "A3: 0x03A20124 (grp 0x201) DF window high"),
]
for off, oldv, newv, what in STEP_A:
    cur = struct.unpack_from("<I", body, off)[0]
    assert cur == oldv, "step A mismatch at body+%#x: %#x != %#x" % (off, cur, oldv)
    struct.pack_into("<I", body, off, newv)
    manifest["changes"].append({"what": what, "offset": "body+%#x" % off, "old": "%#x" % oldv, "new": "%#x" % newv})

# 2) new blob = orig header(0x100) + body + orig tail(0x100)
hdr = bytearray(base[G_OLD:G_OLD + 0x100])
tail = bytearray(base[G_OLD + G_OLD_SIZE - 0x100:G_OLD + G_OLD_SIZE])
struct.pack_into("<Q", hdr, 0x14, len(body))          # size
struct.pack_into("<Q", hdr, 0x50, len(body))          # size (repeat)
struct.pack_into("<I", hdr, 0x6C, 0x100 + len(body) + 0x100)  # total
blob = bytes(hdr) + bytes(body) + bytes(tail)
assert len(blob) == 0x3010

# 3) verify target region is erased
assert all(x == 0xFF for x in img[G_NEW_OFF:G_NEW_OFF + len(blob)]), "target region not empty"
img[G_NEW_OFF:G_NEW_OFF + len(blob)] = blob
manifest["changes"].append({"what": "gasket blob (A+B unsigned) placed", "offset": G_NEW_OFF, "old": "FF..." , "new": "len=%#x sha256=%s" % (len(blob), hashlib.sha256(blob).hexdigest())})

# 4) PSP dir: repoint entry type 0x24
count = struct.unpack_from("<I", img, DIR + 8)[0]
ent_end = DIR + 0x10 + 16 * count
found = False
for i in range(count):
    eo = DIR + 0x10 + 16 * i
    t, sz, loc = struct.unpack_from("<IIQ", img, eo)
    if t == 0x24:
        note(img, eo + 4, struct.pack("<I", sz), struct.pack("<I", len(blob)), "dir entry 0x24 size")
        note(img, eo + 8, struct.pack("<Q", loc), struct.pack("<Q", 0xFF000000 + G_NEW_OFF), "dir entry 0x24 loc -> 0x9E0000")
        found = True
assert found, "type 0x24 entry not found"

# 5) dir checksum: fletcher32 over [DIR+8, ent_end)
span = bytes(img[DIR + 8:ent_end])
newcks = fletcher32(span)
note(img, DIR + 4, struct.pack("<I", struct.unpack_from("<I", img, DIR + 4)[0]), struct.pack("<I", newcks), "PSP dir fletcher32 checksum")

# 6) APCB patch
newcks_apcb = apply_apcb_patch(img)

d3b_path = OUTDIR + r"\D3-B_APCB-DFG-i_gasket-A-B-unsigned_DO_NOT_FLASH_WITHOUT_PROGRAMMER_BACKUP.bin"
open(d3b_path, "wb").write(img)
manifest["D3-B"] = d3b_path
manifest["D3-B_md5"] = hashlib.md5(bytes(img)).hexdigest()
manifest["D3-B_apcb_cksum"] = "%#x" % newcks_apcb

# ---------- D3-A (control: APCB only) ----------
img2 = bytearray(base)
newcks_apcb2 = apply_apcb_patch(img2)
d3a_path = OUTDIR + r"\D3-A_APCB-DFG-i-only_CONTROL_expected-false-negative.bin"
open(d3a_path, "wb").write(img2)
manifest["D3-A"] = d3a_path
manifest["D3-A_md5"] = hashlib.md5(bytes(img2)).hexdigest()
manifest["D3-A_apcb_cksum"] = "%#x" % newcks_apcb2

mf = OUTDIR + r"\D3_build_manifest.json"
json.dump(manifest, open(mf, "w"), indent=1)
print("D3-B:", d3b_path)
print("  md5:", manifest["D3-B_md5"], " changes:", len(manifest["changes"]))
print("D3-A:", d3a_path)
print("  md5:", manifest["D3-A_md5"])
print("manifest:", mf)
for c in manifest["changes"]:
    print("   %-55s @%s" % (c["what"], c["offset"]))
