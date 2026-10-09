# D3-C (S-version): pure mechanics test.
# Original SIGNED gasket blob (0x2E50, verbatim, signature stays valid) relocated
# 0x982000 -> 0x9E0000 + PSP dir entry 0x24 repoint + fletcher32 dir checksum.
# NO gasket content change, NO APCB patch, NO header size edits.
import struct, hashlib, json, os

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
OUTDIR = r"C:\Users\OWNER\tmp_bc250\recon\d3"
BASE = FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN"
G_OLD, G_SIZE, G_NEW = 0x982000, 0x2E50, 0x9E0000
DIR = 0x8E0000


def fletcher32(data):
    s1 = s2 = 0
    for i in range(0, len(data), 2):
        w = data[i] | (data[i + 1] << 8)
        s1 = (s1 + w) % 65535
        s2 = (s2 + s1) % 65535
    return (s2 << 16) | s1


base = open(BASE, "rb").read()
img = bytearray(base)
manifest = {"base_md5": hashlib.md5(base).hexdigest(), "changes": []}

# 1) blob verbatim
assert all(x == 0xFF for x in img[G_NEW:G_NEW + G_SIZE]), "target region not empty"
img[G_NEW:G_NEW + G_SIZE] = base[G_OLD:G_OLD + G_SIZE]
assert img[G_NEW:G_NEW + G_SIZE] == base[G_OLD:G_OLD + G_SIZE]
manifest["changes"].append({"what": "SIGNED gasket blob copied verbatim 0x982000->0x9E0000", "offset": G_NEW, "old": "FF", "new": "len=%#x verbatim" % G_SIZE})

# 2) dir entry 0x24: only Location changes; Size stays 0x2E50
cnt = struct.unpack_from("<I", img, DIR + 8)[0]
ent_end = DIR + 0x10 + 16 * cnt
found = False
for i in range(cnt):
    eo = DIR + 0x10 + 16 * i
    t, sz, loc = struct.unpack_from("<IIQ", img, eo)
    if t == 0x24:
        assert (sz, loc) == (G_SIZE, 0xFF000000 + G_OLD), "unexpected entry 0x24: %#x %#x" % (sz, loc)
        struct.pack_into("<Q", img, eo + 8, 0xFF000000 + G_NEW)
        manifest["changes"].append({"what": "dir entry 0x24 loc 0xFF982000->0xFF9E0000 (size untouched)", "offset": eo + 8, "old": "%#x" % loc, "new": "%#x" % (0xFF000000 + G_NEW)})
        found = True
assert found
# 3) dir checksum
span = bytes(img[DIR + 8:ent_end])
struct.pack_into("<I", img, DIR + 4, fletcher32(span))
manifest["changes"].append({"what": "PSP dir fletcher32 recomputed", "offset": DIR + 4})

path = OUTDIR + r"\D3-C_SIGNED-gasket-relocation_mechanics-test.bin"
open(path, "wb").write(img)
manifest["D3-C"] = path
manifest["D3-C_md5"] = hashlib.md5(bytes(img)).hexdigest()
json.dump(manifest, open(OUTDIR + r"\D3-C_build_manifest.json", "w"), indent=1)
print("D3-C:", path)
print("md5:", manifest["D3-C_md5"])
for c in manifest["changes"]:
    print("  ", c["what"])
