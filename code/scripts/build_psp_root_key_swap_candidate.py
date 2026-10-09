#!/usr/bin/env python3
"""Build the PSP root-key swap discriminator for BC-250 (lane V3, rung 1).

Question (decides the whole attack tree): does the on-die PSP ROM hash-anchor
the raw type-0x09 key blob (kid ffc8acd4..., SPI 0x93F000, 0x440 B, no $PS1
envelope, no signature)? It is the key that verifies the $KDB carriers
(0x50/0x51), which hold the leaf key 96ea7cfe that verifies the two VCN-lock
carriers (0x24/0x45).

Rung 1 changes ONLY the RSA modulus inside the 0x09 blob (in place, same
size/convention). Nothing else: no directory changes, no re-signing.

Outcomes (one cold boot, programmer-reversible):
- board boots normally        -> ROM does NOT anchor this blob; the full
  software re-root ladder (re-sign KDB with our root, swap 96ea7cfe, re-sign
  the locks) becomes buildable -> rung 2.
- board parks (no video/LAN)  -> the blob (or its tail) IS anchored; software
  re-rooting is dead at the root and the EMFI/glitch target is CONFIRMED as
  the ROM hash check of exactly this blob.

No flash happens here. Flashing needs the operator's exact hash approval.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

BLOB_SPI = 0x93F000
BLOB_SIZE = 0x440
KID = bytes.fromhex("ffc8acd45bb748e082d2100ed808fa54")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    ap.add_argument(
        "--key", type=Path, help="PEM to reuse; otherwise a fresh key is generated"
    )
    ap.add_argument(
        "--key-out",
        type=Path,
        help="where to store a freshly generated PEM (default: <report>.key.pem)",
    )
    args = ap.parse_args()

    base_bytes = args.base.read_bytes()
    blob = bytearray(base_bytes[BLOB_SPI : BLOB_SPI + BLOB_SIZE])

    # ---- layout assertions (fail loudly, never guess) ----------------------
    assert blob[0:4] == struct.pack("<I", 1), "version u32 @0x00 != 1"
    assert blob[0x14:0x24] == KID, "key_id @0x14 != ffc8acd4..."
    e_hits = [
        o for o in range(0x30, 0x50) if struct.unpack_from("<I", blob, o)[0] == 65537
    ]
    assert e_hits == [0x40], f"e=65537 not uniquely at 0x40: {[hex(o) for o in e_hits]}"

    mod_off = 0x48
    orig_mod = bytes(blob[mod_off : mod_off + 256])
    # convention detection: a 2048-bit modulus has its top bit set.
    if orig_mod[0] >= 0x80 and orig_mod[-1] >= 0x80:
        raise SystemExit("ambiguous modulus endianness (both ends >= 0x80) - stop")
    endian = "big" if orig_mod[0] >= 0x80 else "little"
    assert int.from_bytes(orig_mod, endian).bit_length() >= 2047, (
        f"modulus at 0x48 does not look like RSA-2048 ({endian}-endian)"
    )

    # ---- our key -----------------------------------------------------------
    if args.key:
        key = serialization.load_pem_private_key(args.key.read_bytes(), password=None)
        key_path = args.key
    else:
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        key_path = args.key_out or args.report.with_suffix(
            args.report.suffix + ".key.pem"
        )
        key_path.parent.mkdir(parents=True, exist_ok=True)
        key_path.write_bytes(
            key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
        )
    pub = key.public_key().public_numbers()
    assert pub.e == 65537
    new_mod = pub.n.to_bytes(256, endian)
    new_kid = hashlib.sha256(pub.n.to_bytes(256, "little")).digest()[:16]

    # ---- the single transformation -----------------------------------------
    rom = bytearray(base_bytes)
    rom[BLOB_SPI + mod_off : BLOB_SPI + mod_off + 256] = new_mod

    # ---- self-checks -------------------------------------------------------
    diff = [i for i in range(len(rom)) if rom[i] != base_bytes[i]]
    checks = {
        "diff_count": len(diff),
        "diff_confined": bool(diff)
        and all(BLOB_SPI + mod_off <= i < BLOB_SPI + mod_off + 256 for i in diff),
        "kid_unchanged": rom[BLOB_SPI + 0x14 : BLOB_SPI + 0x24] == KID,
        "e_unchanged": struct.unpack_from("<I", rom, BLOB_SPI + 0x40)[0] == 65537,
        "endian_used": endian,
        "other_modulus_copies": [
            hex(i) for i in range(0, len(base_bytes) - 256, 1) if False
        ],  # filled below
    }
    # where else does the original modulus appear? (consistency risk, untouched)
    hits, start = [], 0
    while True:
        i = base_bytes.find(orig_mod, start)
        if i < 0:
            break
        hits.append(hex(i))
        start = i + 1
    checks["other_modulus_copies"] = hits

    out_sha = hashlib.sha256(rom).hexdigest()
    ok = checks["diff_confined"] and checks["kid_unchanged"] and checks["e_unchanged"]
    report = {
        "base": str(args.base),
        "base_sha256": hashlib.sha256(base_bytes).hexdigest(),
        "out": str(args.out),
        "out_sha256": out_sha,
        "blob": {"spi": hex(BLOB_SPI), "size": hex(BLOB_SIZE), "kid": KID.hex()},
        "our_key": {"kid": new_kid.hex(), "e": pub.e, "endian": endian},
        "tail_0x400": "untouched 64 B high-entropy field (purpose unknown; risk recorded)",
        "checks": checks,
        "gate": "PASS" if ok else "FAIL",
        "claim_boundary": "static discriminator only; boot outcome UNRUN; no flash",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(bytes(rom))

    print(json.dumps(report, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
