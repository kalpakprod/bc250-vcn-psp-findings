# C1: (1) full 19-entry dump of $PSP dir @0x8E0000 of the stock W25Q128 image;
# (2) parse $KDB key databases (own image 0x50/0x51 if present, plus recon BC250_3.00
#     chipset-ROM entries and cezanne donor);
# (3) brute RSA-2048 verification of GASKET 0x24 and POLICY 0x45 signature tails:
#     key selection by kid @envelope+0x38, spans x hashes x endianness, PKCS#1 v1.5.
import struct
import hashlib

ROM = open(r"C:\Users\OWNER\Downloads\AyuGram Desktop\ChatExport_2026-09-02\files"
           r"\W25Q128BV@WSON8_20250122_140516.BIN", "rb").read()
D = r"C:\Users\OWNER\tmp_bc250\bc250_firmware\psp_entries\BC250_3.00_CHIPSETMENU.ROM"


def u32(buf, off):
    return struct.unpack_from("<I", buf, off)[0]


print("== full $PSP directory @0x8E0000 ==")
ents = []
n = u32(ROM, 0x8E0008)
for i in range(n):
    e = 0x8E0010 + 0x10 * i
    typ, flags = ROM[e], ROM[e + 1]
    size, addr = u32(ROM, e + 4), u32(ROM, e + 8) & 0xFFFFFF
    ents.append((i, typ, flags, size, addr))
    print("  ent[%2d] type=%#04x flags=%#02x size=%#08x addr=%#08x" % (i, typ, flags, size, addr))


def parse_kdb(buf, tag):
    body = buf[0x100:]
    if body[0x08:0x0C] != b"$KDB":
        print("  %s: no $KDB magic (head=%r)" % (tag, buf[0x108:0x110]))
        return []
    keys, off = [], 0x50
    while off + 0x150 <= len(body):
        rec = body[off:off + 0x150]
        size, idx = struct.unpack_from("<II", rec, 0)
        exp = struct.unpack_from("<I", rec, 0x0C)[0]
        kid = rec[0x10:0x20]
        bits = struct.unpack_from("<I", rec, 0x20)[0]
        mod = rec[0x50:0x50 + 0x100] if bits == 2048 else None
        keys.append(dict(tag=tag, off=off, size=size, idx=idx, exp=exp,
                         kid=kid.hex(), bits=bits, mod=mod))
        off += 0x150
    return keys


all_keys = []
print("\n== key databases ==")
# own image: 0x50 / 0x51 entries
for i, typ, flags, size, addr in ents:
    if typ in (0x50, 0x51):
        ks = parse_kdb(ROM[addr:addr + size], "own t%02x @%#x" % (typ, addr))
        print("  own t%02x @%#x: %d keys" % (typ, addr, len(ks)))
        all_keys += ks
# recon chipset-ROM KDBs
for tag, fn in [("chipset t50", "17_t50_0x9DAD00_DD0.bin"),
                ("chipset t51", "18_t51_0x9DBB00_740.bin")]:
    try:
        b = open(D + "\\" + fn, "rb").read()
        ks = parse_kdb(b, tag)
        print("  %s: %d keys" % (tag, len(ks)))
        for k in ks:
            print("    idx=%d exp=%d bits=%d kid=%s" % (k["idx"], k["exp"], k["bits"], k["kid"]))
        all_keys += ks
    except OSError as ex:
        print("  %s: missing (%s)" % (tag, ex))

DI = {"sha256": bytes.fromhex("3031300d060960864801650304020105000420"),
      "sha1": bytes.fromhex("3021300906052b0e03021a05000414"),
      "sha384": bytes.fromhex("3041300d060960864801650304020205000430")}


def raw_pow(sig, exp, mod, mod_e, sig_e, out_e):
    n = int.from_bytes(mod, mod_e)
    if n == 0:
        return None
    m = pow(int.from_bytes(sig, sig_e), exp, n)
    return m.to_bytes(256, out_e)


def verify_blob(name, addr, size):
    blob = ROM[addr:addr + size]
    kid = blob[0x38:0x48]
    sig = blob[size - 0x100:]
    signed = blob[:size - 0x100]
    print("\n== %s @%#x size=%#x ==" % (name, addr, size))
    print("  kid@+0x38 = %s  sig[0:16]=%s" % (kid.hex(), sig[:16].hex()))
    cands = [k for k in all_keys if bytes.fromhex(k["kid"]) == kid]
    if not cands:
        cands = all_keys
        print("  no kid match; trying all %d keys" % len(cands))
    spans = {
        "signed[0:size-0x100]": signed,
        "body only": blob[0x100:size - 0x100],
        "hdr[0x10:]+body": blob[0x10:size - 0x100],
        "hdr[0x18:]+body": blob[0x18:size - 0x100],
        "hdr[0x30:]+body": blob[0x30:size - 0x100],
        "whole blob": blob,
    }
    algos = {"sha256": hashlib.sha256, "sha384": hashlib.sha384,
             "sha1": hashlib.sha1, "md5": hashlib.md5}
    found = []
    for k in cands:
        if k["mod"] is None:
            continue
        for sname, msg in spans.items():
            for halg, hfn in algos.items():
                h = hfn(msg).digest()
                for mod_e in ("little", "big"):
                    for sig_e in ("little", "big"):
                        for out_e in ("little", "big"):
                            try:
                                dec = raw_pow(sig, k["exp"], k["mod"], mod_e, sig_e, out_e)
                            except (OverflowError, ValueError):
                                continue
                            if dec is None:
                                continue
                            # PKCS1 v1.5 or raw hash
                            ok_p = (dec[0] == 0 and dec[1] == 1
                                    and b"\x00" in dec[2:24]
                                    and (DI[halg] + h) in dec) if halg in DI else False
                            ok_r = (h in dec) or (h[::-1] in dec)
                            if ok_p or ok_r:
                                found.append((k, sname, halg, mod_e, sig_e, out_e,
                                              "PKCS1" if ok_p else "raw"))
                                print("  VERIFIED: %s kid=%s key_idx=%s span=%s alg=%s "
                                      "mod=%s sig=%s out=%s mode=%s"
                                      % (k["tag"], k["kid"][:12], k["idx"], sname, halg,
                                         mod_e, sig_e, out_e, "PKCS1" if ok_p else "raw"))
    if not found:
        print("  NO verification found with available keys")


for i, typ, flags, size, addr in ents:
    if typ in (0x24, 0x45):
        verify_blob("TYPE %#x" % typ, addr, size)
