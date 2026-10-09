#!/usr/bin/env python3
"""Parse PSP $KDB key databases (t50/t51) and try to RSA-verify the
SEC_GASKET (t24) signature tail offline. Read-only research."""
import struct, hashlib, sys

D = r"C:\Users\OWNER\tmp_bc250\bc250_firmware\psp_entries\BC250_3.00_CHIPSETMENU.ROM"
KDB_MAGIC = b"$KDB"

def parse_kdb(path):
    b = open(path, "rb").read()
    body = b[0x100:]
    if body[0x08:0x0C] != KDB_MAGIC:
        print("  !! no $KDB magic in", path)
        return []
    keys, off = [], 0x50
    while off + 0x150 <= len(body):
        rec = body[off:off + 0x150]
        size, idx = struct.unpack_from("<II", rec, 0)
        exp = struct.unpack_from("<I", rec, 0x0C)[0]
        kid = rec[0x10:0x20]
        bits = struct.unpack_from("<I", rec, 0x20)[0]
        mod = rec[0x50:0x50 + 0x100] if bits == 2048 else None
        keys.append(dict(off=off, size=size, idx=idx, exp=exp,
                         kid=kid.hex(), bits=bits, mod=mod))
        off += 0x150
    return keys

def rsa_raw_verify(sig, exp, mod_bytes):
    n = int.from_bytes(mod_bytes, "little")
    s = int.from_bytes(sig, "little")
    m = pow(s, exp, n)
    return m.to_bytes(len(mod_bytes), "little")

def raw_pow(sig, exp, mod_bytes, mod_endian, sig_endian, out_endian):
    n = int.from_bytes(mod_bytes, mod_endian)
    if n == 0:
        return None
    s = int.from_bytes(sig, sig_endian)
    m = pow(s, exp, n)
    nb = (n.bit_length() + 7) // 8
    return m.to_bytes(max(nb, 256 // 8 * (2048 // 8 // 32) or 256 // 8), out_endian) if False else \
           m.to_bytes(256, out_endian)

def try_pkcs1_v15(decrypted, msg_hash, halg="sha256"):
    """decrypted: 256B; check 00 01 FF..FF 00 || DigestInfo || hash"""
    if decrypted[0] != 0 or decrypted[1] != 1:
        return False
    i = 2
    while i < len(decrypted) and decrypted[i] == 0xFF:
        i += 1
    if i < 10 or i >= len(decrypted) or decrypted[i] != 0:
        return False
    digestinfo = decrypted[i+1:]
    return msg_hash in digestinfo  # hash bytes appear at the end

# SHA-256 DigestInfo prefix (DER)
DI_SHA256 = bytes.fromhex("3031300d060960864801650304020105000420")

def main():
    blobs = {}
    for name, fn in [("BL_KDB", "17_t50_0x9DAD00_DD0.bin"),
                     ("TOS_KDB", "18_t51_0x9DBB00_740.bin"),
                     ("GASKET", "07_t24_0x982000_2E50.bin"),
                     ("TOS_POLICY", "15_t45_0x9CA400_6E0.bin")]:
        blobs[name] = open(D + "\\" + fn, "rb").read()

    all_keys = []
    for name in ("BL_KDB", "TOS_KDB"):
        ks = parse_kdb(D + "\\" +
            ("17_t50_0x9DAD00_DD0.bin" if name == "BL_KDB" else "18_t51_0x9DBB00_740.bin"))
        print("=== %s: %d keys" % (name, len(ks)))
        for k in ks:
            print("  idx=%d exp=%d bits=%d kid=%s" % (k["idx"], k["exp"], k["bits"], k["kid"]))
            all_keys.append((name, k))

    g = blobs["GASKET"]
    gkid = g[0x38:0x48].hex()
    gsig = g[0x2D50:0x2E50]
    ghdr = g[:0x100]
    gbody = g[0x100:0x2D50]
    print("\nGASKET key-id: %s" % gkid)
    print("GASKET sig[0:16]: %s" % gsig[:16].hex())
    match = [ (n,k) for n,k in all_keys if k["kid"] == gkid ]
    print("key-id matches in KDBs: %s" % ([n for n,k in match] or "NONE (fused key?)"))

    # candidate message spans
    gbody_nopad = gbody[: len(gbody) - 8]
    spans = {
        "body(11344)": gbody,
        "body-no-pad8": gbody_nopad,
        "hdr+body": g[:0x2D50],
        "hdr[0x10:]+body": g[0x10:0x100] + gbody,
        "hdr[0x18:]+body": g[0x18:0x100] + gbody,
        "hdr[0x30:]+body": g[0x30:0x100] + gbody,
        "hdr+body+sig?": g,  # (self-referential, unlikely)
    }
    algos = (("sha256", hashlib.sha256), ("sha384", hashlib.sha384),
             ("sha1", hashlib.sha1), ("md5", hashlib.md5))
    ends = (("little", "little"), ("little", "big"),
            ("big", "little"), ("big", "big"))
    print("\n=== RSA verify attempts (keys x spans x hashes x endianness) ===")
    found = False
    for kname, k in all_keys:
        if k["mod"] is None or k["bits"] != 2048: continue
        for sname, msg in spans.items():
            for halg, hfn in algos:
                h = hfn(msg).digest()
                for mod_e, sig_e in ends:
                    for out_e in ("little", "big"):
                        try:
                            dec = raw_pow(gsig, k["exp"], k["mod"], mod_e, sig_e, out_e)
                        except (OverflowError, ValueError):
                            continue
                        if dec is None: continue
                        if try_pkcs1_v15(dec, h) or h in dec:
                            print("VERIFIED: key %s kid=%s span=%s alg=%s mod=%s sig=%s out=%s"
                                  % (kname, k["kid"][:8], sname, halg, mod_e, sig_e, out_e))
                            found = True
    if not found:
        print("no verification yet — dumping diag decrypts for the gasket key")
        for kname, k in all_keys:
            if k["kid"] != gkid: continue
            for mod_e, sig_e in ends:
                for out_e in ("little", "big"):
                    try:
                        dec = raw_pow(gsig, k["exp"], k["mod"], mod_e, sig_e, out_e)
                    except (OverflowError, ValueError):
                        continue
                    print("  %s mod=%s sig=%s out=%s: %s..." % (kname, mod_e, sig_e, out_e, dec[:24].hex()))

if __name__ == "__main__":
    main()
