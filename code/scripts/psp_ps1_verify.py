#!/usr/bin/env python3
"""Verify AMD PSP `$PS1` container signatures in a BC-250 SPI image.

Scheme (established 2026-09-19, see docs/research/2026-09-19-psp-signature-scheme-solved.md):

    container = header(0x100) || signed_body(N) || signature(0x100, RSA-2048)
    N          = u32 LE at header+0x14
    key        = 16-byte key-id at header+0x38, resolved in the `$KDB` key database
    signature  = RSA-PSS, MGF1-SHA256, salt_length=32, digest SHA-256
                 over (header || signed_body)

Read-only. Prints per-entry verification, never writes.
"""

from __future__ import annotations

import argparse
import hashlib
import struct
import sys
from pathlib import Path

PSP_DIR = 0x8E0000
HEADER = 0x100
SIG_LEN = 0x100


def kdb_keys(image: bytes, scan=True):
    """Collect kid -> (e, n_bytes) by scanning for $KDB records.

    A record is 0x150 bytes: u32 size==0x150, u32 index, u32 0x0E, u32 exponent,
    16-byte key-id at +0x10, u32 bits at +0x20, modulus at +0x50.
    Scanning (rather than hard-coded offsets) makes this work on any BC-250 or
    4700S image, whose $KDB offsets differ per release.
    """
    keys = {}
    need = b"\x50\x01\x00\x00"
    start = 0
    while True:
        i = image.find(need, start)
        if i < 0:
            break
        start = i + 4
        if i + 0x150 > len(image):
            break
        rec = image[i : i + 0x150]
        e = struct.unpack_from("<I", rec, 0x0C)[0]
        bits = struct.unpack_from("<I", rec, 0x20)[0]
        if e not in (3, 5, 17, 65537) or bits not in (1024, 2048):
            continue
        kid = rec[0x10:0x20]
        if kid == b"\x00" * 16:
            continue
        keys.setdefault(kid.hex(), (e, rec[0x50 : 0x50 + bits // 8]))
    return keys


def psp_entries(image: bytes):
    if image[PSP_DIR : PSP_DIR + 4] != b"$PSP":
        raise ValueError("no $PSP directory at 0x8E0000")
    n = struct.unpack_from("<I", image, PSP_DIR + 8)[0]
    for i in range(n):
        o = PSP_DIR + 0x10 + i * 0x10
        typ, size, loc = struct.unpack_from("<IIQ", image, o)
        if typ == 0xFFFFFFFF:
            return
        yield i, typ, size, loc & 0xFFFFFF


def verify_container(blob: bytes, keys):
    """Return (kid, scheme, signed_len) or (kid, None, signed_len)."""
    if blob[0x10:0x14] != b"$PS1":
        return None, "not-a-$PS1-container", None
    kid = blob[0x38:0x48].hex()
    signed = struct.unpack_from("<I", blob, 0x14)[0]
    if signed <= 0 or HEADER + signed + SIG_LEN > len(blob):
        return kid, "bad-signed-size", signed
    if kid not in keys:
        return kid, "kid-not-in-KDB", signed
    hdr = blob[:HEADER]
    body = blob[HEADER : HEADER + signed]
    sig = blob[HEADER + signed : HEADER + signed + SIG_LEN]
    return kid, ("ok", hdr + body, sig, keys[kid]), signed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("image", type=Path)
    ap.add_argument(
        "--blocks",
        type=int,
        default=64,
        help="how many 0x1000-aligned blocks to scan beyond the PSP directory",
    )
    args = ap.parse_args()
    image = args.image.read_bytes()
    keys = kdb_keys(image)
    print(
        f"image {args.image.name} sha256={hashlib.sha256(image).hexdigest()[:16]} bytes={len(image)}"
    )
    print(f"KDB keys: {len(keys)}")

    try:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding, rsa
        from cryptography.exceptions import InvalidSignature
    except Exception as exc:  # pragma: no cover
        print(f"cryptography unavailable: {exc}")
        return 2

    ok = bad = skipped = 0
    for idx, typ, size, spi in psp_entries(image):
        blob = image[spi : spi + size]
        kid, scheme, signed = verify_container(blob, keys)
        if scheme == "not-a-$PS1-container":
            print(f"  [{idx:>2}] type 0x{typ:>02X} @0x{spi:06x} {size:>7}  {scheme}")
            skipped += 1
            continue
        if isinstance(scheme, tuple):
            _, data, sig, (e, mod) = scheme
            pub = rsa.RSAPublicNumbers(e, int.from_bytes(mod, "little")).public_key()
            for name, pad, algo in (
                (
                    "PSS/SHA256/s32",
                    padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
                    hashes.SHA256(),
                ),
                (
                    "PSS/SHA384/s48",
                    padding.PSS(mgf=padding.MGF1(hashes.SHA384()), salt_length=48),
                    hashes.SHA384(),
                ),
                ("PKCS1v15/SHA256", padding.PKCS1v15(), hashes.SHA256()),
            ):
                try:
                    pub.verify(sig, data, pad, algo)
                    print(
                        f"  [{idx:>2}] type 0x{typ:>02X} @0x{spi:06x} {size:>7}  PASS  {name}  kid={kid[:16]} signed=0x{signed:x}"
                    )
                    ok += 1
                    break
                except InvalidSignature:
                    continue
                except Exception:
                    continue
            else:
                print(
                    f"  [{idx:>2}] type 0x{typ:>02X} @0x{spi:06x} {size:>7}  FAIL  kid={kid[:16]} signed=0x{signed:x}"
                )
                bad += 1
        else:
            print(
                f"  [{idx:>2}] type 0x{typ:>02X} @0x{spi:06x} {size:>7}  {scheme}  kid={kid[:16]}"
            )
            bad += 1
    print(f"\nverified {ok}, failed/unresolved {bad}, non-container {skipped}")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
