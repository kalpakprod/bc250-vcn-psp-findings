#!/usr/bin/env python3
"""Build the fresh-baseline BC-250 D3-B2 VCN research candidate.

This adapts the retained historical D3-B2 algorithm to explicit paths and
strict SHA-256/baseline assertions. It never modifies the input in place.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path

BASE_SHA256 = "83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0"
UNSIGNED_SHA256 = "531d27b386d631ccdad3e8397f916ee4b5f9608d9516317b0d661db92d4a1017"
IMAGE_SIZE = 0x1000000
DIR = 0x8E0000
G_OLD, G_SIZE, G_NEW = 0x982000, 0x2E50, 0x9E0000
P_OLD, P_SIZE, P_NEW = 0x9CA400, 0x6E0, 0x9E4000
APCB = 0xAB1000
VCN_TAIL = [
    (0x0900C234, 0),
    (0x0900C914, 0),
    (0x0900C930, 0),
    (0x0900CB80, 0),
    (0x0900C234, 1),
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fletcher32(data: bytes) -> int:
    if len(data) % 2:
        raise ValueError("Fletcher32 span must have even length")
    s1 = s2 = 0
    for offset in range(0, len(data), 2):
        word = data[offset] | (data[offset + 1] << 8)
        s1 = (s1 + word) % 65535
        s2 = (s2 + s1) % 65535
    return (s2 << 16) | s1


def changed_ranges(before: bytes, after: bytes) -> list[dict[str, int | str]]:
    positions = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    if not positions:
        return []
    ranges: list[dict[str, int | str]] = []
    start = previous = positions[0]
    for position in positions[1:]:
        if position != previous + 1:
            ranges.append({"start": f"0x{start:X}", "end": f"0x{previous:X}", "length": previous - start + 1})
            start = position
        previous = position
    ranges.append({"start": f"0x{start:X}", "end": f"0x{previous:X}", "length": previous - start + 1})
    return ranges


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("unsigned_gasket_body", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()

    source = args.source.resolve()
    unsigned_path = args.unsigned_gasket_body.resolve()
    output = args.output.resolve()
    manifest_path = args.manifest.resolve()
    require(output != source, "output must differ from source")
    require(not output.exists(), f"refusing to overwrite existing output: {output}")
    require(not manifest_path.exists(), f"refusing to overwrite existing manifest: {manifest_path}")

    base = source.read_bytes()
    unsigned = unsigned_path.read_bytes()
    require(len(base) == IMAGE_SIZE, f"unexpected source size: {len(base)}")
    require(sha256_bytes(base) == BASE_SHA256, "source SHA-256 mismatch")
    require(len(unsigned) == 0x2E10, f"unexpected unsigned gasket body size: {len(unsigned)}")
    require(sha256_bytes(unsigned) == UNSIGNED_SHA256, "unsigned gasket body SHA-256 mismatch")
    image = bytearray(base)
    transformations: list[dict[str, object]] = []

    def replace(offset: int, old: bytes, new: bytes, reason: str) -> None:
        require(len(old) == len(new), f"non-equal replacement length for {reason}")
        actual = bytes(image[offset : offset + len(old)])
        require(actual == old, f"pre-state mismatch at 0x{offset:X} for {reason}: {actual.hex()} != {old.hex()}")
        image[offset : offset + len(new)] = new
        transformations.append({"reason": reason, "offset": f"0x{offset:X}", "old": old.hex(), "new": new.hex()})

    # Build the modified SEC_GASKET copy.
    gasket_body = bytearray(unsigned)
    gasket_patches = [
        (0x295C, 0, 6, "SEC_GASKET group 0x210: 0x03E810 0 -> 6"),
        (0x25FC, 0x87FF, 0x107FF, "SEC_GASKET group 0x201: 0x03A2011C aperture"),
        (0x2B74, 0x87FF, 0x107FF, "SEC_GASKET group 0x280: 0x03A2011C aperture"),
        (0x2604, 0, 0x10FFF, "SEC_GASKET group 0x201: 0x03A20124 aperture"),
    ]
    for offset, old_value, new_value, reason in gasket_patches:
        require(struct.unpack_from("<I", gasket_body, offset)[0] == old_value, f"{reason} pre-state mismatch")
        struct.pack_into("<I", gasket_body, offset, new_value)
        transformations.append({"reason": reason, "offset": f"gasket_body+0x{offset:X}", "old": f"0x{old_value:X}", "new": f"0x{new_value:X}"})

    gasket_header = bytearray(base[G_OLD : G_OLD + 0x100])
    gasket_tail = base[G_OLD + G_SIZE - 0x100 : G_OLD + G_SIZE]
    require(gasket_header[0x10:0x14] == b"$PS1", "stock SEC_GASKET $PS1 header missing")
    struct.pack_into("<Q", gasket_header, 0x14, len(gasket_body))
    struct.pack_into("<Q", gasket_header, 0x50, len(gasket_body))
    struct.pack_into("<I", gasket_header, 0x6C, 0x100 + len(gasket_body) + 0x100)
    gasket_blob = bytes(gasket_header) + bytes(gasket_body) + gasket_tail
    require(len(gasket_blob) == 0x3010, f"unexpected SEC_GASKET output size: {len(gasket_blob)}")
    require(all(value == 0xFF for value in image[G_NEW : G_NEW + len(gasket_blob)]), "SEC_GASKET destination is not erased")
    image[G_NEW : G_NEW + len(gasket_blob)] = gasket_blob
    transformations.append({"reason": "place modified SEC_GASKET copy", "offset": f"0x{G_NEW:X}", "length": len(gasket_blob), "sha256": sha256_bytes(gasket_blob)})

    # Build the modified TOS_SECURITY_POLICY copy.
    policy_envelope = bytearray(base[P_OLD : P_OLD + P_SIZE])
    require(policy_envelope[0x10:0x14] == b"$PS1", "stock type-0x45 $PS1 header missing")
    policy_size = struct.unpack_from("<Q", policy_envelope, 0x14)[0]
    require(policy_size == 0x4E0, f"unexpected type-0x45 body size: 0x{policy_size:X}")
    policy_body = bytearray(policy_envelope[0x100 : 0x100 + policy_size])
    policy_tail = bytes(policy_envelope[0x100 + policy_size : P_SIZE])
    require(len(policy_tail) == 0x100, f"unexpected type-0x45 signature-tail size: {len(policy_tail)}")
    require(struct.unpack_from("<I", policy_body, 0)[0] == 4, "unexpected type-0x45 group count")

    offset = 0x40
    patched_e810 = patched_aperture = 0
    while offset + 8 <= len(policy_body):
        group_type, count = struct.unpack_from("<II", policy_body, offset)
        require(group_type in (0x210, 0x211, 0x280, 0x281), f"unexpected type-0x45 group 0x{group_type:X}")
        require(count <= 400, f"unbounded type-0x45 group count: {count}")
        if group_type == 0x210:
            for index in range(count):
                pair_offset = offset + 8 + index * 8
                address, value = struct.unpack_from("<II", policy_body, pair_offset)
                if address == 0x03E810:
                    require(value == 0, "type-0x45 0x03E810 pre-state mismatch")
                    struct.pack_into("<I", policy_body, pair_offset + 4, 6)
                    patched_e810 += 1
        if group_type == 0x280:
            for index in range(count):
                pair_offset = offset + 8 + index * 8
                address, value = struct.unpack_from("<II", policy_body, pair_offset)
                if address == 0x03A2011C:
                    require(value == 0x87FF, "type-0x45 0x03A2011C pre-state mismatch")
                    struct.pack_into("<I", policy_body, pair_offset + 4, 0x107FF)
                    patched_aperture += 1
            group_end = offset + 8 + count * 8
            require(group_end == len(policy_body) - (8 + 31 * 8), "type-0x45 group ordering mismatch")
            policy_body[group_end:group_end] = b"".join(struct.pack("<II", address, value) for address, value in VCN_TAIL)
            struct.pack_into("<I", policy_body, offset + 4, count + len(VCN_TAIL))
        offset += 8 + struct.unpack_from("<I", policy_body, offset + 4)[0] * 8
    require(offset == len(policy_body), "type-0x45 group walk did not end at body boundary")
    require((patched_e810, patched_aperture) == (1, 1), "type-0x45 target occurrence mismatch")
    require(len(policy_body) == 0x508, f"unexpected expanded type-0x45 body size: {len(policy_body)}")

    policy_header = bytearray(policy_envelope[:0x100])
    struct.pack_into("<Q", policy_header, 0x14, len(policy_body))
    struct.pack_into("<Q", policy_header, 0x50, len(policy_body))
    struct.pack_into("<I", policy_header, 0x6C, 0x100 + len(policy_body) + len(policy_tail))
    policy_blob = bytes(policy_header) + bytes(policy_body) + policy_tail
    require(len(policy_blob) == 0x708, f"unexpected type-0x45 output size: {len(policy_blob)}")
    require(all(value == 0xFF for value in image[P_NEW : P_NEW + len(policy_blob)]), "type-0x45 destination is not erased")
    image[P_NEW : P_NEW + len(policy_blob)] = policy_blob
    transformations.extend([
        {"reason": "type-0x45 group 0x210: 0x03E810 0 -> 6", "occurrences": patched_e810},
        {"reason": "type-0x45 group 0x280: 0x03A2011C aperture", "occurrences": patched_aperture},
        {"reason": "type-0x45 group 0x280: append VCN tail", "pairs": len(VCN_TAIL)},
        {"reason": "place modified type-0x45 copy", "offset": f"0x{P_NEW:X}", "length": len(policy_blob), "sha256": sha256_bytes(policy_blob)},
    ])

    # Repoint the two PSP directory entries and recompute its Fletcher32.
    count = struct.unpack_from("<I", image, DIR + 8)[0]
    require(count == 19, f"unexpected PSP directory count: {count}")
    entries_end = DIR + 0x10 + count * 16
    found: set[int] = set()
    for index in range(count):
        entry_offset = DIR + 0x10 + index * 16
        entry_type, size, location = struct.unpack_from("<IIQ", image, entry_offset)
        if entry_type == 0x24:
            require((index, size, location) == (7, G_SIZE, 0xFF982000), "type-0x24 directory pre-state mismatch")
            replace(entry_offset + 4, struct.pack("<I", size), struct.pack("<I", len(gasket_blob)), "type-0x24 directory size")
            replace(entry_offset + 8, struct.pack("<Q", location), struct.pack("<Q", 0xFF000000 + G_NEW), "type-0x24 directory location")
            found.add(entry_type)
        elif entry_type == 0x45:
            require((index, size, location) == (15, P_SIZE, 0xFF9CA400), "type-0x45 directory pre-state mismatch")
            replace(entry_offset + 4, struct.pack("<I", size), struct.pack("<I", len(policy_blob)), "type-0x45 directory size")
            replace(entry_offset + 8, struct.pack("<Q", location), struct.pack("<Q", 0xFF000000 + P_NEW), "type-0x45 directory location")
            found.add(entry_type)
    require(found == {0x24, 0x45}, f"missing PSP directory entries: {found}")
    old_directory_checksum = struct.unpack_from("<I", image, DIR + 4)[0]
    new_directory_checksum = fletcher32(bytes(image[DIR + 8 : entries_end]))
    replace(DIR + 4, struct.pack("<I", old_directory_checksum), struct.pack("<I", new_directory_checksum), "PSP directory Fletcher32")

    # Apply APCB DFG changes and recompute the observed byte checksum.
    require(bytes(image[APCB : APCB + 4]) == b"APCB", "APCB signature missing")
    apcb_size = struct.unpack_from("<I", image, APCB + 8)[0]
    require(apcb_size == 0xB70, f"unexpected APCB size: 0x{apcb_size:X}")
    for relative in (0x130, 0x16C):
        replace(APCB + relative, bytes.fromhex("00ff1f00"), bytes.fromhex("00ff7f00"), f"APCB DFG wildcard +0x{relative:X}")
    old_apcb_checksum = image[APCB + 0x10]
    new_apcb_checksum = (0x100 - sum(image[APCB + index] for index in range(apcb_size) if index != 0x10)) & 0xFF
    replace(APCB + 0x10, bytes([old_apcb_checksum]), bytes([new_apcb_checksum]), "APCB byte checksum")
    require(sum(image[APCB : APCB + apcb_size]) & 0xFF == 0, "APCB checksum does not reconcile")

    candidate = bytes(image)
    ranges = changed_ranges(base, candidate)
    changed_bytes = sum(item["length"] for item in ranges if isinstance(item["length"], int))
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(candidate)
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/build_vcn_d3b2_candidate.py",
        "source": {"path": str(source), "size": len(base), "sha256": sha256_bytes(base)},
        "unsigned_gasket_body": {"path": str(unsigned_path), "size": len(unsigned), "sha256": sha256_bytes(unsigned)},
        "output": {"path": str(output), "size": len(candidate), "sha256": sha256_bytes(candidate)},
        "changed_byte_count": changed_bytes,
        "changed_ranges": ranges,
        "transformations": transformations,
        "checks": {
            "psp_directory_fletcher32": f"0x{new_directory_checksum:08X}",
            "apcb_checksum": f"0x{new_apcb_checksum:02X}",
            "apcb_checksum_match": True,
            "gasket_copy_offset": f"0x{G_NEW:X}",
            "gasket_copy_size": len(gasket_blob),
            "policy45_copy_offset": f"0x{P_NEW:X}",
            "policy45_copy_size": len(policy_blob),
            "modified_policy_signature_acceptance": "unverified; signature tails preserved while policy payload bytes changed",
        },
        "classification": "offline unsigned-policy research candidate; hardware acceptance unverified",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "sha256": manifest["output"]["sha256"], "changed_bytes": changed_bytes, "changed_ranges": len(ranges)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
