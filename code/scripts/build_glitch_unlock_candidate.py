#!/usr/bin/env python3
"""Build the glitch-path VCN-unlock candidate for BC-250.

Everything except the voltage glitch itself is produced here, and the result is
verified end-to-end offline with the now-solved AMD PSP `$PS1` scheme
(RSA-PSS / MGF1-SHA256 / salt 32 over header||body; key id at header+0x38
resolved in the `$KDB`).

Pipeline
  1. base = BC250_5.00_clv.bin (stock, hash recorded)
  2. generate (or load) our own RSA-2048 key
  3. install our public key into `$KDB` t50 slot 0 (the ROM-anchored slot)
  4. rebuild the SEC_GASKET (type 0x24) body with the donor VCN bank + DF window
     values, and re-sign the container with our key
  5. rebuild the TOS_SECURITY_POLICY (type 0x45) body with the same donor values,
     and re-sign it with our key
  6. write the candidate ROM; all other containers keep their original signatures

The private key is NEVER written into the repository; pass --key to reuse one.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

PSP_DIR = 0x8E0000
KDB_T50 = 0x9DB400
CTR_HDR = 0x100
SIG = 0x100
SIG_PAD = padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32)
SIG_HASH = hashes.SHA256()

GASKET_SPI, GASKET_SIZE = 0x982000, 0x2E50
TOS_SPI, TOS_SIZE = 0x9CAB00, 0x6E0
# relocated slots: the signed containers grow once the VCN bank/pairs are added,
# so both are placed in the free 0x9E0000..0xAB0000 region (all 0xFF in stock) and
# the $PSP directory entry is repointed, exactly as the D3/D3-B2 packages did.
GASKET_NEW_SPI = 0x9E0000
TOS_NEW_SPI = 0x9E4000

# donor values (archives/imported/historical-bios-repo/legacy-bc250-bios/docs/source-docs/VCN-LOCK-MECHANISM.md §3, roadmap_A_results.md)
DF_LOW = (0x03A2011C, 0x000107FF)
DF_HIGH = (0x03A20124, 0x00010FFF)
MAILBOX_HDR = (0x03E810, 0x00000006)
MAILBOX_CMD = (0x03E814, 0x2544C382)
VCN_TAIL = [
    (0x0900C234, 0),
    (0x0900C914, 0),
    (0x0900C930, 0),
    (0x0900CB80, 0),
    (0x0900C234, 1),
]


def parse_groups(body: bytes):
    """body = 0x40 header + [type u32, count u32, count*(addr,value)] ..."""
    groups = []
    off = 0x40
    while off + 8 <= len(body):
        gtype, count = struct.unpack_from("<II", body, off)
        end = off + 8 + count * 8
        if count > 0x2000 or end > len(body):
            break
        pairs = [struct.unpack_from("<II", body, off + 8 + i * 8) for i in range(count)]
        groups.append([gtype, pairs])
        off = end
    return groups


def serialize_groups(groups) -> bytes:
    out = bytearray(b"\x00" * 0x40)
    for gtype, pairs in groups:
        out += struct.pack("<II", gtype, len(pairs))
        for a, v in pairs:
            out += struct.pack("<II", a, v)
    return bytes(out)


def set_pairs(groups, wanted):
    """Set existing (addr -> value) inside any group; report which were missing."""
    hits = {a: 0 for a, _ in wanted}
    for gtype, pairs in groups:
        for i, (a, v) in enumerate(pairs):
            for wa, wv in wanted:
                if a == wa:
                    pairs[i] = (wa, wv)
                    hits[wa] += 1
    return hits


def append_pairs(groups, gtype, pairs_to_add):
    for g in groups:
        if g[0] == gtype:
            g[1].extend(pairs_to_add)
            return True
    return False


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
    """Repoint the $PSP directory entry for `ptype`, then refresh the fletcher32.

    Entry layout (PSPTool / firmware_audit.py): u8 type, u8 subprogram, u16 flags,
    u32 size, u32 location, u32 reserved = 16 bytes, table at 0x8E0010.
    """
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


def key_entry(e: int, n: int, kid: bytes) -> bytes:
    """AMD public-key entry: 0x40 header || e || n (sizes in bits)."""
    size = n.bit_length()
    hdr = (
        struct.pack("<I", 1)
        + kid
        + kid
        + struct.pack("<I", 0)
        + b"\x00" * 16
        + struct.pack("<I", size)
        + struct.pack("<I", size)
    )
    assert len(hdr) == 0x40
    return hdr + e.to_bytes(size // 8, "little") + n.to_bytes(size // 8, "little")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--base",
        type=Path,
        default=Path("evidence/donor/retroweb-20260916/BC250_5.00_clv.bin"),
    )
    ap.add_argument(
        "--unsigned-gasket",
        type=Path,
        default=Path(
            "archives/imported/recon-evidence/legacy-tmp-bc250-recon/"
            "bc250_sec_gasket_with_vcn_UNSIGNED_DO_NOT_FLASH.bin"
        ),
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("candidates/BC250_5.00_clv_VcnUnlock_GlitchSigned_v001.bin"),
    )
    ap.add_argument("--key", type=Path, default=Path("/tmp/bc250_glitch_key.pem"))
    ap.add_argument(
        "--report",
        type=Path,
        default=Path("evidence/firmware-audit/20260919-glitch-path/build-report.json"),
    )
    args = ap.parse_args()

    rom = bytearray(args.base.read_bytes())
    assert len(rom) == 0x1000000
    base_sha = hashlib.sha256(rom).hexdigest()

    # ---- 2. our key --------------------------------------------------------
    if args.key.exists():
        key = serialization.load_pem_private_key(args.key.read_bytes(), password=None)
    else:
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        args.key.write_bytes(
            key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
        )
    pub = key.public_key().public_numbers()
    kid = hashlib.sha256(pub.n.to_bytes(256, "little")).digest()[:16]
    entry = key_entry(pub.e, pub.n, kid)
    print(f"our key: kid={kid.hex()} e={pub.e} bits={pub.n.bit_length()}")
    print(
        f"key entry: 0x{len(entry):x} bytes  sha256={hashlib.sha256(entry).hexdigest()[:16]}"
    )

    # ---- 3. install our key into $KDB t50 slot 0 ---------------------------
    rec = KDB_T50 + 0x150
    assert struct.unpack_from("<I", rom, rec)[0] == 0x150, (
        "unexpected $KDB record layout"
    )
    old_kid = bytes(rom[rec + 0x10 : rec + 0x20]).hex()
    struct.pack_into("<I", rom, rec + 0x0C, pub.e)
    struct.pack_into("<I", rom, rec + 0x20, 2048)
    rom[rec + 0x10 : rec + 0x20] = kid
    rom[rec + 0x50 : rec + 0x50 + 256] = pub.n.to_bytes(256, "little")
    print(f"$KDB t50 slot0: {old_kid} -> {kid.hex()}")

    # ---- 4. gasket ---------------------------------------------------------
    stock_ctr = bytes(rom[GASKET_SPI : GASKET_SPI + GASKET_SIZE])
    stock_body = stock_ctr[
        CTR_HDR : CTR_HDR + struct.unpack_from("<I", stock_ctr, 0x14)[0]
    ]
    vcn_body = args.unsigned_gasket.read_bytes()
    g_ctr = bytearray(stock_ctr[:CTR_HDR])
    g_ctr[0x38:0x48] = kid
    gasket_signed = sign_container(g_ctr, vcn_body, key)
    assert GASKET_NEW_SPI + len(gasket_signed) <= TOS_NEW_SPI, (
        "gasket would overlap the TOS slot"
    )
    rom[GASKET_NEW_SPI : GASKET_NEW_SPI + len(gasket_signed)] = gasket_signed
    print(
        f"gasket: stock body 0x{len(stock_body):x} -> donor body 0x{len(vcn_body):x}; "
        f"container 0x{len(gasket_signed):x} @0x{GASKET_NEW_SPI:x}"
    )

    # ---- 5. TOS policy -----------------------------------------------------
    tos_ctr = bytes(rom[TOS_SPI : TOS_SPI + TOS_SIZE])
    tos_signed_len = struct.unpack_from("<I", tos_ctr, 0x14)[0]
    tos_body = bytearray(tos_ctr[CTR_HDR : CTR_HDR + tos_signed_len])
    groups = parse_groups(tos_body)
    print(f"tos groups: " + ", ".join(f"0x{g[0]:x}:{len(g[1])}" for g in groups))
    hits = set_pairs(groups, [DF_LOW, DF_HIGH, MAILBOX_HDR, MAILBOX_CMD])
    appended = append_pairs(groups, 0x280, VCN_TAIL)
    tos_body = serialize_groups(groups)
    t_ctr = bytearray(tos_ctr[:CTR_HDR])
    t_ctr[0x38:0x48] = kid
    tos_signed = sign_container(t_ctr, bytes(tos_body), key)
    rom[TOS_NEW_SPI : TOS_NEW_SPI + len(tos_signed)] = tos_signed
    print(
        f"tos: applied {hits}, appended 5 VCN tail pairs to 0x280={appended}; "
        f"body 0x{len(tos_body):x} container 0x{len(tos_signed):x} @0x{TOS_NEW_SPI:x}"
    )

    # ---- 5b. repoint the $PSP directory + refresh its fletcher32 -----------
    rep_g = repoint_psp_entry(rom, 0x24, GASKET_NEW_SPI, len(gasket_signed))
    rep_t = repoint_psp_entry(rom, 0x45, TOS_NEW_SPI, len(tos_signed))
    print(f"$PSP repointed: 0x24 {rep_g}; 0x45 {rep_t}")

    # ---- 6. write ----------------------------------------------------------
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(bytes(rom))
    out_sha = hashlib.sha256(rom).hexdigest()
    base_bytes = args.base.read_bytes()
    diff = [i for i in range(len(rom)) if rom[i] != base_bytes[i]]
    report = {
        "base": str(args.base),
        "base_sha256": base_sha,
        "out": str(args.out),
        "out_sha256": out_sha,
        "out_size": len(rom),
        "our_kid": kid.hex(),
        "our_key_entry_sha256": hashlib.sha256(entry).hexdigest(),
        "our_key_bits": pub.n.bit_length(),
        "our_key_e": pub.e,
        "private_key_path_not_in_repo": str(args.key),
        "kdb_t50_slot0": {"was": old_kid, "now": kid.hex()},
        "gasket": {
            "stock_body": len(stock_body),
            "new_body": len(vcn_body),
            "container": len(gasket_signed),
        },
        "tos": {
            "groups_before": len(groups),
            "set_pairs_hits": {hex(k): v for k, v in hits.items()},
            "vcn_tail_appended_to_0x280": appended,
            "new_body": len(tos_body),
            "container": len(tos_signed),
        },
        "changed_bytes": len(diff),
        "changed_range": [hex(min(diff)), hex(max(diff))] if diff else None,
        "scheme": "RSA-PSS/MGF1-SHA256/salt32 over header(0x100)||body; kid at header+0x38",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(f"\nwrote {args.out}")
    print(f"  sha256 {out_sha}")
    print(f"  changed {len(diff)} bytes, range {report['changed_range']}")
    print(f"  report {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
