#!/usr/bin/env python3
"""Replace one same-size PE32 section in the existing BC-250 CoreUnlock FFS."""

from __future__ import annotations

import argparse
import hashlib
import json
import lzma
import struct
from pathlib import Path

OUTER_FV = 0xAE0000
CAPSULE_FFS = 0xAE0078
CORE_UNLOCK_GUID_LE = bytes.fromhex("6d423d2f546a6b4a82d01207cc5b6d92")
LZMA_GUID_LE = bytes.fromhex("98584eee143959429d6edc7bd79403cf")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ffs_header_checksum(header: bytearray) -> None:
    header[16] = 0
    header[16] = (-(sum(header[:16]) + sum(header[18:23]))) & 0xFF


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--replacement", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    args = ap.parse_args()

    base = args.base.read_bytes()
    replacement = args.replacement.read_bytes()
    if len(base) != 0x1000000:
        raise ValueError("base is not 16 MiB")

    outer_len = struct.unpack_from("<Q", base, OUTER_FV + 0x20)[0]
    outer_end = OUTER_FV + outer_len
    old_size = int.from_bytes(base[CAPSULE_FFS + 20:CAPSULE_FFS + 23], "little")
    old_header = bytes(base[CAPSULE_FFS:CAPSULE_FFS + 24])
    old_data = base[CAPSULE_FFS + 24:CAPSULE_FFS + old_size]
    data_offset = int.from_bytes(old_data[20:22], "little")
    inner_before = lzma.decompress(old_data[data_offset:], format=lzma.FORMAT_ALONE)

    ffs_pos = inner_before.find(CORE_UNLOCK_GUID_LE)
    if ffs_pos < 0 or inner_before.find(CORE_UNLOCK_GUID_LE, ffs_pos + 1) >= 0:
        raise ValueError("existing CoreUnlock FFS GUID is missing or ambiguous")
    if ffs_pos % 8:
        raise ValueError("existing CoreUnlock FFS is misaligned")
    section_pos = ffs_pos + 24
    section_size = int.from_bytes(inner_before[section_pos:section_pos + 3], "little")
    section_type = inner_before[section_pos + 3]
    if section_type != 0x10:
        raise ValueError(f"first section is not PE32: {section_type:#x}")
    payload_pos = section_pos + 4
    payload_size = section_size - 4
    if payload_size != len(replacement):
        raise ValueError(f"replacement size {len(replacement)} != PE payload {payload_size}")

    inner_after = bytearray(inner_before)
    original_payload = inner_before[payload_pos:payload_pos + payload_size]
    inner_after[payload_pos:payload_pos + payload_size] = replacement
    outside_equal = (
        inner_before[:payload_pos] == inner_after[:payload_pos]
        and inner_before[payload_pos + payload_size:] == inner_after[payload_pos + payload_size:]
        and len(inner_before) == len(inner_after)
    )
    if not outside_equal:
        raise ValueError("decompressed FV changed outside target PE32 payload")

    filters = [{
        "id": lzma.FILTER_LZMA1, "dict_size": 16 * 1024 * 1024,
        "lc": 3, "lp": 0, "pb": 2, "mode": lzma.MODE_NORMAL,
        "nice_len": 64, "mf": lzma.MF_BT4,
    }]
    compressed = lzma.compress(bytes(inner_after), format=lzma.FORMAT_ALONE, filters=filters)
    guided = (0x18 + len(compressed)).to_bytes(4, "little")[:3] + b"\x02"
    guided += LZMA_GUID_LE + struct.pack("<HH", 0x18, 0x01) + compressed
    new_size = 24 + len(guided)
    new_header = bytearray(old_header)
    new_header[20:23] = new_size.to_bytes(4, "little")[:3]
    ffs_header_checksum(new_header)
    capsule = bytes(new_header) + guided
    new_free = (CAPSULE_FFS + len(capsule) + 7) & ~7
    if new_free > outer_end:
        raise ValueError("recompressed capsule exceeds outer FV")

    image = bytearray(base)
    image[CAPSULE_FFS:CAPSULE_FFS + len(capsule)] = capsule
    image[new_free:outer_end] = b"\xff" * (outer_end - new_free)

    # Independent re-extraction from final bytes.
    check_size = int.from_bytes(image[CAPSULE_FFS + 20:CAPSULE_FFS + 23], "little")
    check_data = bytes(image[CAPSULE_FFS + 24:CAPSULE_FFS + check_size])
    check_offset = int.from_bytes(check_data[20:22], "little")
    check_inner = lzma.decompress(check_data[check_offset:], format=lzma.FORMAT_ALONE)
    check_ffs = check_inner.find(CORE_UNLOCK_GUID_LE)
    check_payload = check_inner[check_ffs + 28:check_ffs + 28 + payload_size]
    if check_payload != replacement:
        raise ValueError("replacement PE32 did not survive final re-extraction")
    if check_inner[:payload_pos] != inner_before[:payload_pos] or check_inner[payload_pos + payload_size:] != inner_before[payload_pos + payload_size:]:
        raise ValueError("final decompressed FV differs outside replacement PE32")

    output = bytes(image)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    manifest = {
        "classification": "offline-candidate",
        "source": str(args.base), "source_size": len(base), "source_sha256": sha256(base),
        "replacement": str(args.replacement), "replacement_size": len(replacement), "replacement_sha256": sha256(replacement),
        "original_pe32_size": len(original_payload), "original_pe32_sha256": sha256(original_payload),
        "output": str(args.output), "output_size": len(output), "output_sha256": sha256(output),
        "target_ffs_guid": "2F3D426D-6A54-4A6B-82D0-1207CC5B6D92",
        "target_ffs_offset_in_decompressed_fv": hex(ffs_pos),
        "target_pe32_payload_offset_in_decompressed_fv": hex(payload_pos),
        "decompressed_fv_size_unchanged": len(inner_before) == len(check_inner),
        "decompressed_bytes_outside_target_pe32_identical": True,
        "signed_psp_region_0x8e0000_0xae0000_identical": base[0x8E0000:0xAE0000] == output[0x8E0000:0xAE0000],
        "old_capsule_size": old_size, "new_capsule_size": new_size,
        "unrun": ["BC-250 cold boot", "DXE dispatch", "SMU unlock readback", "VCN function"],
    }
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
