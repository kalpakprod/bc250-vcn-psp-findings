#!/usr/bin/env python3
"""Systematic RSA-verify brute force for AMD PSP $PS1 blob signatures.
Tries all KDB keys, modulus byte/word transforms, signed spans, hash algs.
Read-only research on local firmware."""
import struct, hashlib, itertools, sys

D = r"C:\Users\OWNER\tmp_bc250\bc250_firmware\psp_entries\BC250_3.00_CHIPSETMENU.ROM"

def parse_kdb(fn):
    b = open(D + "\\" + fn, "rb").read()
    body = b[0x100:]
    if body[0x08:0x0C] != b"$KDB":
        return []
    keys, off = [], 0x50
    while off + 0x150 <= len(body):
        rec = body[off:off + 0x150]
        exp = struct.unpack_from("<I", rec, 0x0C)[0]
        if exp != 65537:
            break
        kid = rec[0x10:0x20]
        bits = struct.unpack_from("<I", rec, 0x20)[0]
        if bits != 2048:
            break
        keys.append(dict(kid=kid.hex(), exp=exp, mod=rec[0x50:0x50 + 0x100]))
        off += 0x150
    return keys

def wrev(b, w):
    """reverse byte order in w-byte words"""
    return b"".join(b[i:i + w][::-1] for i in range(0, len(b), w))

MODT = {
    "id": lambda b: b,
    "rev": lambda b: b[::-1],
    "w32rev": lambda b: wrev(b, 4),
    "w64rev": lambda b: wrev(b, 8),
    "w32swap": lambda b: b"".join(b[i:i+4] for i in range(len(b)-4, -1, -4)),
}
SIGT = {"id": lambda b: b, "rev": lambda b: b[::-1], "w32rev": lambda b: wrev(b, 4)}
ALGS = {"sha256": hashlib.sha256, "sha384": hashlib.sha384,
        "sha512": hashlib.sha512, "sha1": hashlib.sha1}

def spans(blob, dirent=None):
    body = blob[0x100:]
    npad = len(body) - (len(body) % 8)
    kid = blob[0x38:0x48]
    sp = {
        "body": body,
        "body_nopad": body[:npad],
        "body_rev": body[::-1],
        "hdr+body": blob[:0x100 + len(body)],
        "hdr10+body": blob[0x10:0x100] + body,
        "hdr18+body": blob[0x18:0x100] + body,
        "hdr30+body": blob[0x30:0x100] + body,
        "hdr38+body": blob[0x38:0x100] + body,
        "hdr58+body": blob[0x58:0x100] + body,
        "body+hdr": body + blob[:0x100],
        "kid+body": kid + body,
        "body+kid": body + kid,
        "kid+hdr+body": kid + blob[:0x100] + body,
    }
    if dirent is not None:
        sp["dir+body"] = dirent + body
        sp["dir+hdr+body"] = dirent + blob[:0x100] + body
    return sp

def check(dec, h):
    # PKCS#1 v1.5: 00 01 FF.. 00 || DI || hash ; or raw hash present
    if dec[0] == 0 and dec[1] == 1:
        i = 2
        while i < len(dec) and dec[i] == 0xFF:
            i += 1
        if i >= 10 and i < len(dec) and dec[i] == 0:
            if h in dec[i+1:]:
                return "PKCS1v15"
    if h in dec:
        return "RAW"
    return None

def main():
    keys = []
    for fn, nm in [("17_t50_0x9DAD00_DD0.bin", "BL"), ("18_t51_0x9DBB00_740.bin", "TOS")]:
        for k in parse_kdb(fn):
            keys.append((nm, k))
    print("loaded %d keys" % len(keys))
    targets = {
        "XHCI_t44": ("14_t44_0x9C3D00_6610.bin", 0x210),
        "GASKET_t24": ("07_t24_0x982000_2E50.bin", 0x2E50),
        "TOS_t45": ("15_t45_0x9CA400_6E0.bin", 0x6E0),
        "HWIP_t20": ("06_t20_0x981900_650.bin", 0x650),
    }
    # PSP L1 dir entries {type,size,loc} for span experiments
    DIRENTS = {
        "XHCI_t44": struct.pack("<IIQ", 0x44, 0x6610, 0xFF000000 + 0x9C3D00),
        "GASKET_t24": struct.pack("<IIQ", 0x24, 0x2E50, 0xFF000000 + 0x982000),
        "TOS_t45": struct.pack("<IIQ", 0x45, 0x6E0, 0xFF000000 + 0x9CA400),
        "HWIP_t20": struct.pack("<IIQ", 0x20, 0x650, 0xFF000000 + 0x981900),
    }
    for tname, (fn, blen) in targets.items():
        blob = open(D + "\\" + fn, "rb").read()[:blen]
        body_len = blen - 0x200
        sig = blob[-0x100:]
        kid = blob[0x38:0x48].hex()
        print("\n=== %s blob=%d body=%d kid=%s" % (tname, blen, body_len, kid))
        bc_hits = 0
        hit = False
        for kn, k in keys:
            for mt, mf in MODT.items():
                n = int.from_bytes(mf(k["mod"]), "big")
                if n == 0:
                    continue
                for st, sf in SIGT.items():
                    s = int.from_bytes(sf(sig), "big")
                    if s >= n:
                        continue
                    m = pow(s, k["exp"], n)
                    for oe in ("big", "little"):
                        dec = m.to_bytes(256, oe)
                        if dec[-1] == 0xBC:
                            bc_hits += 1
                        for sname, msg in spans(blob, DIRENTS[tname]).items():
                            for an, af in ALGS.items():
                                r = check(dec, af(msg).digest())
                                if r:
                                    print("  *** VERIFIED %s: key=%s/%s mod=%s sig=%s out=%s span=%s alg=%s"
                                          % (r, kn, k["kid"][:8], mt, st, oe, sname, an))
                                    hit = True
        print("  PSS-style 0xBC endings: %d" % bc_hits)
        if not hit:
            print("  no hit")
    print("\ndone")

if __name__ == "__main__":
    main()
