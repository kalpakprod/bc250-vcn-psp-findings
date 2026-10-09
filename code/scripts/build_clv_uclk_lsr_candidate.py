#!/usr/bin/env python3
"""Build the UCLK-division-patch candidate on the clv 5.00 base.

One behavioral variable: ABL1 +0x5F32 0x54 -> 0x04, i.e.
  LSR.W R8,R4,#1  ->  LSL.W R8,R4,#0 == MOV.W R8,R4
so the UCLK SVC28 service argument becomes the input word instead of
input>>1. Proven on the native ABL1 code in Unicorn
(evidence/firmware-audit/20260923-abl95fc-next/emulate_pll_apcb_uclkpatch.py):
control (1800)->UCLK 900, patched -> 1800, patched input 1750 -> 1750.

Infrastructure (same class as build_glitch_unlock_candidate.py):
- our RSA-2048 key installed in $KDB t50 slot 0 (private key never in
  the repo; /tmp path, --key to reuse);
- the ABL1 $PS1 container (type 0x31 @0x99FD00) is rebuilt: zlib
  recompressed patched payload, sizes refreshed, re-signed
  RSA-PSS/MGF1-SHA256/salt32 over header||body with our key;
- $PSP directory entry repointed + Fletcher32 refreshed.

BOOT BOUNDARY (unchanged from the glitch-signed class): the PSP accepts
re-signed bodies only if the ROM accepts our key entry — which per the
cross-image anchor test (2026-09-19) requires the physical key-acceptance
step (glitch, hardware). This artifact completes the SOFTWARE side and
is staged, not flashable as-is.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

PSP_DIR = 0x8E0000
KDB_T50 = 0x9DB400
ABL1_SPI = 0x99FD00
ABL1_ENTRY_SIZE = 0xC020
# the stock region has no growth slack (the $KDB t50 container starts at
# 0x9ABE00), so the rebuilt container is RELOCATED to the free 0xFF region,
# exactly as the glitch-signed builder did for 0x24/0x45.
ABL1_NEW_SPI = 0x9E0000
CTR_HDR = 0x100
SIG = 0x100
SIG_PAD = padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32)
SIG_HASH = hashes.SHA256()
ZLIB_LEVEL = 9

ORIG_ABL1_SHA = "af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a"
PATCH_OFF = 0x5F32
PATCH_OLD = 0x54
PATCH_NEW = 0x04
# tied to the emulator run's patched payload
PATCHED_ABL1_SHA = None  # filled by --patched-sha, enforced if given


def fletcher32(data: bytes) -> int:
    if len(data) % 2:
        data += b"\0"
    s1 = s2 = 0
    for off in range(0, len(data), 2):
        word = data[off] | (data[off + 1] << 8)
        s1 = (s1 + word) % 65535
        s2 = (s2 + s1) % 65535
    return (s2 << 16) | s1


def repoint_psp_entry(rom: bytearray, ptype: int, spi: int, size: int) -> dict:
    count = struct.unpack_from("<I", rom, PSP_DIR + 8)[0]
    for i in range(count):
        o = PSP_DIR + 0x10 + i * 0x10
        if rom[o] == ptype:
            was = (
                struct.unpack_from("<I", rom, o + 4)[0],
                struct.unpack_from("<I", rom, o + 8)[0],
            )
            struct.pack_into("<I", rom, o + 4, size)
            struct.pack_into("<I", rom, o + 8, 0xFF000000 | spi)
            end = PSP_DIR + 0x10 + 16 * count
            struct.pack_into(
                "<I", rom, PSP_DIR + 4, fletcher32(bytes(rom[PSP_DIR + 8 : end]))
            )
            return {
                "index": i,
                "was_size": was[0],
                "was_location": hex(was[1]),
                "now_size": size,
                "now_location": hex(0xFF000000 | spi),
            }
    raise SystemExit(f"PSP entry type 0x{ptype:02X} not found")


def sign_container(header: bytearray, body: bytes, key) -> bytes:
    header[0x14:0x18] = struct.pack("<I", len(body))
    header[0x50:0x54] = struct.pack("<I", len(body))
    header[0x6C:0x70] = struct.pack("<I", CTR_HDR + len(body) + SIG)
    sig = key.sign(bytes(header) + body, SIG_PAD, SIG_HASH)
    assert len(sig) == SIG, len(sig)
    return bytes(header) + body + sig


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--base",
        type=Path,
        default=Path("evidence/donor/retroweb-20260916/BC250_5.00_clv.bin"),
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("candidates/BC250_5.00_clv_UCLK_MOV_GlitchSigned_v001.bin"),
    )
    ap.add_argument("--key", type=Path, default=Path("/tmp/bc250_glitch_key.pem"))
    ap.add_argument(
        "--report",
        type=Path,
        default=Path("evidence/firmware-audit/20260924-uclk-lsr/build-report.json"),
    )
    ap.add_argument(
        "--patched-sha",
        default=None,
        help="expected sha256 of the patched decompressed ABL1 (from the emulator run)",
    )
    a = ap.parse_args()
    a.report.parent.mkdir(parents=True, exist_ok=True)

    base_bytes = a.base.read_bytes()
    rom = bytearray(base_bytes)
    assert len(rom) == 0x1000000
    base_sha = hashlib.sha256(base_bytes).hexdigest()

    # ---- our key -----------------------------------------------------------
    if a.key.exists():
        key = serialization.load_pem_private_key(a.key.read_bytes(), password=None)
    else:
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        a.key.write_bytes(
            key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
        )
    pub = key.public_key().public_numbers()
    kid = hashlib.sha256(pub.n.to_bytes(256, "little")).digest()[:16]
    print(f"our key: kid={kid.hex()} e={pub.e} bits={pub.n.bit_length()}")

    # ---- extract + patch ABL1 ----------------------------------------------
    stock = bytes(rom[ABL1_SPI : ABL1_SPI + ABL1_ENTRY_SIZE])
    assert stock[0x10:0x14] == b"$PS1", stock[0x10:0x14]
    signed_n = struct.unpack_from("<I", stock, 0x14)[0]
    assert signed_n == 48672, signed_n
    abl1 = zlib.decompress(stock[CTR_HDR : CTR_HDR + signed_n])
    assert hashlib.sha256(abl1).hexdigest() == ORIG_ABL1_SHA
    assert abl1[PATCH_OFF] == PATCH_OLD and abl1[0x5F30:0x5F32] == b"\x4f\xea"
    patched = bytearray(abl1)
    patched[PATCH_OFF] = PATCH_NEW
    patched = bytes(patched)
    diff = [i for i in range(len(abl1)) if abl1[i] != patched[i]]
    assert diff == [PATCH_OFF], diff
    patched_sha = hashlib.sha256(patched).hexdigest()
    if a.patched_sha:
        assert patched_sha == a.patched_sha, (patched_sha, a.patched_sha)
    print(
        f"ABL1 patch: +0x{PATCH_OFF:X} {PATCH_OLD:#04x}->{PATCH_NEW:#04x}, "
        f"payload sha {patched_sha[:16]}…"
    )

    # ---- rebuild the container ----------------------------------------------
    comp = zlib.compress(patched, ZLIB_LEVEL)
    # field semantics for a COMPRESSED container differ from the gasket class:
    # +0x14 = signed (compressed) body length, +0x50 = DECOMPRESSED load size
    # (stock 0x171A0 = 94624+0x20; the patched payload has the same length, so
    # +0x50 keeps the stock value), +0x6C = total container size.
    hdr = bytearray(stock[:CTR_HDR])
    hdr[0x38:0x48] = kid
    hdr[0x14:0x18] = struct.pack("<I", len(comp))
    hdr[0x6C:0x70] = struct.pack("<I", CTR_HDR + len(comp) + SIG)
    assert struct.unpack_from("<I", hdr, 0x50)[0] == 0x171A0  # untouched
    sig = key.sign(bytes(hdr) + comp, SIG_PAD, SIG_HASH)
    assert len(sig) == SIG
    new_entry = bytes(hdr) + comp + sig
    # relocation target must be 0xFF in the base and fit before 0xAB0000
    assert set(base_bytes[ABL1_NEW_SPI : ABL1_NEW_SPI + len(new_entry)]) == {0xFF}, (
        "relocation region not free"
    )
    assert ABL1_NEW_SPI + len(new_entry) <= 0xAB0000
    rom[ABL1_NEW_SPI : ABL1_NEW_SPI + len(new_entry)] = new_entry
    print(
        f"ABL1 container: signed {signed_n:#x} -> {len(comp):#x} (zlib L{ZLIB_LEVEL}), "
        f"container 0x{ABL1_ENTRY_SIZE:X} -> 0x{len(new_entry):X}, "
        f"relocated 0x{ABL1_SPI:X} -> 0x{ABL1_NEW_SPI:X}"
    )

    # round-trip: decompress the candidate's own container back to the patched payload
    chk = zlib.decompress(
        bytes(rom[ABL1_NEW_SPI + CTR_HDR : ABL1_NEW_SPI + CTR_HDR + len(comp)])
    )
    assert chk == patched, "candidate container round-trip mismatch"

    # ---- install our key into $KDB t50 slot 0 -------------------------------
    rec = KDB_T50 + 0x150
    assert struct.unpack_from("<I", rom, rec)[0] == 0x150
    old_kid = bytes(rom[rec + 0x10 : rec + 0x20]).hex()
    struct.pack_into("<I", rom, rec + 0x0C, pub.e)
    struct.pack_into("<I", rom, rec + 0x20, 2048)
    rom[rec + 0x10 : rec + 0x20] = kid
    rom[rec + 0x50 : rec + 0x50 + 256] = pub.n.to_bytes(256, "little")
    print(f"$KDB t50 slot0: {old_kid} -> {kid.hex()}")

    # ---- repoint the $PSP directory -----------------------------------------
    rep = repoint_psp_entry(rom, 0x31, ABL1_NEW_SPI, len(new_entry))
    print(f"$PSP repointed: 0x31 {rep}")

    # ---- write ---------------------------------------------------------------
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_bytes(bytes(rom))
    out_sha = hashlib.sha256(bytes(rom)).hexdigest()
    d = [i for i in range(len(rom)) if rom[i] != base_bytes[i]]
    ranges = []
    if d:
        s = p = d[0]
        for x in d[1:]:
            if x != p + 1:
                ranges.append([hex(s), hex(p)])
                s = x
            p = x
        ranges.append([hex(s), hex(p)])
    report = {
        "base": str(a.base),
        "base_sha256": base_sha,
        "out": str(a.out),
        "out_sha256": out_sha,
        "patch": {
            "kind": "UCLK division removal: LSR.W R8,R4,#1 -> MOV.W R8,R4",
            "abl1_offset": hex(PATCH_OFF),
            "old": hex(PATCH_OLD),
            "new": hex(PATCH_NEW),
            "original_payload_sha256": ORIG_ABL1_SHA,
            "patched_payload_sha256": patched_sha,
            "zlib_level": ZLIB_LEVEL,
            "compressed_size": len(comp),
            "container_size": len(new_entry),
            "relocated_to": hex(ABL1_NEW_SPI),
            "hdr_0x50_decompressed_load_size": "0x171A0 (stock, untouched)",
            "emulator_proof": "evidence/firmware-audit/20260923-abl95fc-next/emulate_pll_apcb_uclkpatch.py",
        },
        "our_kid": kid.hex(),
        "kdb_t50_slot0": {"was": old_kid, "now": kid.hex()},
        "psp_entry_0x31": rep,
        "changed_bytes": len(d),
        "changed_ranges": ranges,
        "scheme": "RSA-PSS/MGF1-SHA256/salt32 over header(0x100)||body; kid at header+0x38",
        "boot_boundary": "PSP acceptance requires the ROM key-acceptance step (physical glitch, hardware); software side complete; NOT flashable as-is",
        "flashed": False,
    }
    a.report.write_text(json.dumps(report, indent=2) + "\n")
    print(f"\nwrote {a.out}")
    print(f"  sha256 {out_sha}")
    print(f"  changed {len(d)} bytes in {len(ranges)} ranges: {ranges}")
    print(f"  report {a.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
