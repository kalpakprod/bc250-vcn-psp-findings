# A11: are gasket/0x45 $PS1 tails real per-content RSA signatures - or constants?
# Extract 0x24 + 0x45 from all ROMs, compare bodies vs tails.
# Decisive cases: (a) identical tail with different body => not a signature;
# (b) community-modded ROMs that boot in the field with a changed gasket => not enforced.
import struct, hashlib

FILES = r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
ROMS = [
    ("robin-hw(base)", FILES + r"\W25Q128BV@WSON8_20250122_140516.BIN"),
    ("BC250_3.00", FILES + r"\BC250_3.00.ROM"),
    ("Robin5.00", FILES + r"\Robin5.00"),
    ("Robin5(1)", FILES + r"\Robin5 (1).00"),
    ("dump_5.00", FILES + r"\dump_5.00.bin"),
    ("8cores_Steam", FILES + r"\8_cores_Steam.rom"),
    ("bc250-Steam", FILES + r"\bc250-Steam.rom"),
    ("modded.ROM", FILES + r"\bc250 modded bios.ROM"),
    ("my_4.0_MODED", FILES + r"\my_4.0_MODED.bin"),
    ("4700S_C0A", r"C:\Users\OWNER\tmp_bc250\bc250_firmware\4700S\C0A\C0A"),
]


def psp_entries(b):
    """return dict type->(idx,size,romoff) from the first plausible $PSP dir"""
    i = -1
    while True:
        i = b.find(b"$PSP", i + 1)
        if i < 0 or i > len(b) - 0x10:
            return None
        cnt = struct.unpack_from("<I", b, i + 8)[0]
        if 0 < cnt <= 64:
            out = {}
            for k in range(cnt):
                eo = i + 0x10 + 16 * k
                t, sz = struct.unpack_from("<II", b, eo)
                loc = struct.unpack_from("<Q", b, eo + 8)[0] & 0xFFFFFFFF
                off = loc - 0xFF000000 if loc > 0xFF000000 else loc
                if 0 <= off < len(b):
                    out.setdefault(t, (k, sz, off))
            return out
    # unreachable


rows = {}
for name, path in ROMS:
    try:
        b = open(path, "rb").read()
    except OSError as e:
        print("[skip] %-14s %s" % (name, e))
        continue
    ent = psp_entries(b)
    if not ent:
        print("[no $PSP] %-14s" % name)
        continue
    for t, tag in ((0x24, "gasket"), (0x45, "tos45")):
        if t in ent:
            idx, sz, off = ent[t]
            blob = b[off:off + sz]
            hdr, tail = blob[:0x100], blob[-0x100:]
            body = blob[0x100:sz - 0x100]
            rows.setdefault(tag, []).append((name, off, sz,
                                             hashlib.md5(body).hexdigest()[:12],
                                             hashlib.md5(tail).hexdigest()[:12],
                                             tail[:8].hex(), hashlib.md5(hdr).hexdigest()[:12]))
        else:
            rows.setdefault(tag, []).append((name, None, None, None, None, None, None))

for tag in ("gasket", "tos45"):
    print("\n== %s (0x%s) across ROMs ==" % (tag, {"gasket": "24", "tos45": "45"}[tag]))
    print("%-14s %-9s %-7s %-13s %-13s %-8s" % ("ROM", "romoff", "size", "body.md5", "tail.md5", "tail[0:8]"))
    for r in rows.get(tag, []):
        print("%-14s %-9s %-7s %-13s %-13s %-16s" % (
            r[0], hex(r[1]) if r[1] is not None else "-",
            hex(r[2]) if r[2] is not None else "-",
            r[3] or "-", r[4] or "-", r[5] or "-"))
    # summaries
    tails = [r for r in rows.get(tag, []) if r[4]]
    bodies = [r for r in rows.get(tag, []) if r[3]]
    tu, bu = len(set(r[4] for r in tails)), len(set(r[3] for r in bodies))
    print("unique tails: %d / %d blobs; unique bodies: %d / %d" % (tu, len(tails), bu, len(bodies)))
    # tail-identical groups with different bodies?
    bytail = {}
    for r in tails:
        bytail.setdefault(r[4], []).append(r[0])
    for tm, names in bytail.items():
        if len(names) > 1:
            bd = set(r[3] for r in tails if r[4] == tm)
            print("  tail %s shared by %s (bodies %s)" % (tm, names, "SAME" if len(bd) == 1 else "DIFFERENT -> tail NOT content-signature!"))

# donor cezanne gasket/0x45 for reference
import glob
print("\n== donor cezanne_d0 blobs ==")
for p in glob.glob(r"C:\Users\OWNER\tmp_bc250\recon\keys_raw\cezanne_d0\*.bin"):
    d = open(p, "rb").read()
    if len(d) > 0x200 and struct.unpack_from("<I", d, 0x10)[0] == 0x31535024:
        sz = struct.unpack_from("<I", d, 0x6C)[0]
        print("  %-52s total=%#x body.md5=%s tail.md5=%s tail[0:8]=%s" % (
            p.split("\\")[-1], sz,
            hashlib.md5(d[0x100:sz - 0x100]).hexdigest()[:12],
            hashlib.md5(d[-0x100:]).hexdigest()[:12], d[-0x100:-0xF8].hex()))
