# D3-B v2 build: v1 (gasket A+B @0x9E0000 + APCB (i)) + MIRROR PATCH of TOS_SECURITY_POLICY 0x45:
#   - {0x03E810, 0->6} (grp 0x210, in place)
#   - {0x03A2011C, 0x87FF->0x107FF} (grp 0x280, in place)
#   - append donor VCN tail 5 pairs to grp 0x280 (100->105), body 0x4E0->0x508
#   - relocate 0x45 blob to 0x9E4000 (total 0x708), repoint dir entry idx15, fletcher32.
# Rationale (A1/A2): dir order = gasket (idx7) BEFORE 0x45 (idx15) => last-writer-wins;
# stock 0x45 would re-lock E810/1C after our gasket unlock. Donor carries unlock in BOTH.
import struct, hashlib, json, os

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
UNSIGNED = r"C:\Users\OWNER\tmp_bc250\recon\bc250_sec_gasket_with_vcn_UNSIGNED_DO_NOT_FLASH.bin"
OUTDIR = r"C:\Users\OWNER\tmp_bc250\recon\d3"
BASE = FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN"
G_OLD, G_SIZE, G_NEW = 0x982000, 0x2E50, 0x9E0000
P_OLD, P_SIZE, P_NEW = 0x9CA400, 0x6E0, 0x9E4000
DIR, APCB = 0x8E0000, 0xAB1000
VCN_TAIL = [(0x0900C234, 0), (0x0900C914, 0), (0x0900C930, 0), (0x0900CB80, 0), (0x0900C234, 1)]


def fletcher32(data):
    s1 = s2 = 0
    for i in range(0, len(data), 2):
        w = data[i] | (data[i + 1] << 8)
        s1 = (s1 + w) % 65535
        s2 = (s2 + s1) % 65535
    return (s2 << 16) | s1


base = open(BASE, "rb").read()
img = bytearray(base)
man = {"base_md5": hashlib.md5(base).hexdigest(), "changes": []}


def note(off, old, new, what):
    assert bytes(img[off:off + len(old)]) == old, "pre-state mismatch @%#x" % off
    img[off:off + len(new)] = new
    man["changes"].append({"what": what, "offset": off, "old": old.hex(), "new": new.hex()})


# ---------- 1) gasket blob (as v1) ----------
body = bytearray(open(UNSIGNED, "rb").read())
assert len(body) == 0x2E10
for off, oldv, newv, what in [
        (0x295C, 0, 6, "A1: 0x03E810 (gasket grp 0x210) 0->6"),
        (0x25FC, 0x87FF, 0x107FF, "A2: 0x03A2011C (gasket grp 0x201) 0x87FF->0x107FF"),
        (0x2B74, 0x87FF, 0x107FF, "A2: 0x03A2011C (gasket grp 0x280) 0x87FF->0x107FF"),
        (0x2604, 0, 0x10FFF, "A3: 0x03A20124 (gasket grp 0x201) 0->0x10FFF")]:
    assert struct.unpack_from("<I", body, off)[0] == oldv
    struct.pack_into("<I", body, off, newv)
    man["changes"].append({"what": what, "offset": "gbody+%#x" % off, "old": "%#x" % oldv, "new": "%#x" % newv})
hdr = bytearray(base[G_OLD:G_OLD + 0x100])
tail = bytearray(base[G_OLD + G_SIZE - 0x100:G_OLD + G_SIZE])
struct.pack_into("<Q", hdr, 0x14, len(body))
struct.pack_into("<Q", hdr, 0x50, len(body))
struct.pack_into("<I", hdr, 0x6C, 0x100 + len(body) + 0x100)
gblob = bytes(hdr) + bytes(body) + bytes(tail)
assert all(x == 0xFF for x in img[G_NEW:G_NEW + len(gblob)])
img[G_NEW:G_NEW + len(gblob)] = gblob
man["changes"].append({"what": "gasket blob (A+B) @0x9E0000", "offset": G_NEW, "new": "len=%#x md5=%s" % (len(gblob), hashlib.md5(gblob).hexdigest())})

# ---------- 2) TOS_SECURITY_POLICY 0x45 mirror ----------
penv = bytearray(base[P_OLD:P_OLD + P_SIZE])
psize = struct.unpack_from("<I", penv, 0x14)[0]
assert psize == 0x4E0
pbody = bytearray(penv[0x100:0x100 + psize])
ptail = bytes(penv[0x100 + psize:P_SIZE])
# group walk, patch in place + extend grp 0x280
off = 0x40
ngrp = struct.unpack_from("<I", pbody, 0)[0]
assert ngrp == 4
patched = {"E810": 0, "1C": 0}
while off + 8 <= len(pbody):
    t, c = struct.unpack_from("<II", pbody, off)
    assert t in (0x210, 0x211, 0x280, 0x281) and c <= 400
    if t == 0x210:
        for i in range(c):
            ao = off + 8 + 8 * i
            a, v = struct.unpack_from("<II", pbody, ao)
            if a == 0x03E810:
                assert v == 0
                struct.pack_into("<I", pbody, ao + 4, 6)
                patched["E810"] += 1
    if t == 0x280:
        for i in range(c):
            ao = off + 8 + 8 * i
            a, v = struct.unpack_from("<II", pbody, ao)
            if a == 0x03A2011C:
                assert v == 0x87FF
                struct.pack_into("<I", pbody, ao + 4, 0x107FF)
                patched["1C"] += 1
        # append VCN tail
        end = off + 8 + c * 8
        assert end == len(pbody) - (8 + 31 * 8)  # grp 0x281 follows
        pbody[end:end] = b"".join(struct.pack("<II", a, v) for a, v in VCN_TAIL)
        struct.pack_into("<I", pbody, off + 4, c + 5)
        man["changes"].append({"what": "0x45 grp 0x280: VCN tail +5 pairs (100->105)", "offset": "pbody+%#x" % end})
    off += 8 + struct.unpack_from("<I", pbody, off + 4)[0] * 8
assert patched == {"E810": 1, "1C": 1}, patched
man["changes"].append({"what": "0x45 grp 0x210: {0x03E810,0}->6", "offset": "pbody"})
man["changes"].append({"what": "0x45 grp 0x280: {0x03A2011C,0x87FF}->0x107FF", "offset": "pbody"})
assert len(pbody) == 0x508
# walk ends exactly at len
off = 0x40
while off + 8 <= len(pbody):
    off += 8 + struct.unpack_from("<I", pbody, off + 4)[0] * 8
assert off == len(pbody)
phdr = bytearray(penv[:0x100])
struct.pack_into("<Q", phdr, 0x14, len(pbody))
struct.pack_into("<Q", phdr, 0x50, len(pbody))
struct.pack_into("<I", phdr, 0x6C, 0x100 + len(pbody) + 0x100)
pblob = bytes(phdr) + bytes(pbody) + ptail
assert len(pblob) == 0x708
assert all(x == 0xFF for x in img[P_NEW:P_NEW + len(pblob)])
img[P_NEW:P_NEW + len(pblob)] = pblob
man["changes"].append({"what": "TOS_SECURITY_POLICY (mirror A+B) @0x9E4000", "offset": P_NEW, "new": "len=%#x md5=%s" % (len(pblob), hashlib.md5(pblob).hexdigest())})

# ---------- 3) dir entries: 0x24 (idx7) + 0x45 (idx15) ----------
cnt = struct.unpack_from("<I", img, DIR + 8)[0]
ent_end = DIR + 0x10 + 16 * cnt
for i in range(cnt):
    eo = DIR + 0x10 + 16 * i
    t, sz, loc = struct.unpack_from("<IIQ", img, eo)
    if t == 0x24:
        assert (i, sz, loc) == (7, 0x2E50, 0xFF982000)
        note(eo + 4, struct.pack("<I", sz), struct.pack("<I", len(gblob)), "dir 0x24 size")
        note(eo + 8, struct.pack("<Q", loc), struct.pack("<Q", 0xFF000000 + G_NEW), "dir 0x24 loc")
    if t == 0x45:
        assert (i, sz, loc) == (15, 0x6E0, 0xFF9CA400)
        note(eo + 4, struct.pack("<I", sz), struct.pack("<I", len(pblob)), "dir 0x45 size")
        note(eo + 8, struct.pack("<Q", loc), struct.pack("<Q", 0xFF000000 + P_NEW), "dir 0x45 loc")
struct.pack_into("<I", img, DIR + 4, fletcher32(bytes(img[DIR + 8:ent_end])))
man["changes"].append({"what": "PSP dir fletcher32 recomputed (2 entries changed)", "offset": DIR + 4})

# ---------- 4) APCB patch (i) ----------
assert img[APCB:APCB + 4] == b"APCB"
asize = struct.unpack_from("<I", img, APCB + 8)[0]
for w in (0x130, 0x16C):
    note(APCB + w, bytes.fromhex("00ff1f00"), bytes.fromhex("00ff7f00"), "APCB DFG wildcard +%#x" % w)
oldcks = img[APCB + 0x10]
newcks = (0x100 - sum(img[APCB + i] for i in range(asize) if i != 0x10)) & 0xFF
note(APCB + 0x10, bytes([oldcks]), bytes([newcks]), "APCB checksum")
man["D3-B2_apcb_cksum"] = "%#x" % newcks

# ---------- save ----------
path = OUTDIR + r"\D3-B2_APCB-DFG-i_gasket+TOSpolicy_A-B-unsigned.bin"
open(path, "wb").write(img)
man["D3-B2"] = path
man["D3-B2_md5"] = hashlib.md5(bytes(img)).hexdigest()
json.dump(man, open(OUTDIR + r"\D3-B2_build_manifest.json", "w"), indent=1)
print("D3-B2:", path)
print("md5:", man["D3-B2_md5"])
for c in man["changes"]:
    print("  ", c["what"])
