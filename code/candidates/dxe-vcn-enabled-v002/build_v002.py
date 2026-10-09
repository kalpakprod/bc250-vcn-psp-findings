#!/usr/bin/env python3
"""Replace PE32 section in CoreUnlock FFS, allowing different sizes."""
from __future__ import annotations
import argparse, hashlib, json, lzma, struct
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
    inner = lzma.decompress(old_data[data_offset:], format=lzma.FORMAT_ALONE)

    ffs_pos = inner.find(CORE_UNLOCK_GUID_LE)
    if ffs_pos < 0:
        raise ValueError("CoreUnlock FFS GUID not found")
    section_pos = ffs_pos + 24
    section_size = int.from_bytes(inner[section_pos:section_pos + 3], "little")
    section_type = inner[section_pos + 3]
    if section_type != 0x10:
        raise ValueError(f"first section is not PE32: {section_type:#x}")
    payload_pos = section_pos + 4
    old_payload_size = section_size - 4
    new_payload_size = len(replacement)
    delta = new_payload_size - old_payload_size

    # Build new inner FV: before_payload + new_payload + after_payload
    # Also update section header (3 bytes) and FFS header (size + checksum)
    before = bytearray(inner[:payload_pos])
    after = inner[payload_pos + old_payload_size:]

    # Update PE32 section size
    new_section_size = new_payload_size + 4
    before[section_pos:section_pos + 3] = new_section_size.to_bytes(4, "little")[:3]

    # Update FFS size
    old_ffs_size = int.from_bytes(inner[ffs_pos + 20:ffs_pos + 23], "little")
    new_ffs_size = old_ffs_size + delta
    before[ffs_pos + 20:ffs_pos + 23] = new_ffs_size.to_bytes(4, "little")[:3]

    # Recompute FFS header checksum
    ffs_hdr = bytearray(before[ffs_pos:ffs_pos + 24])
    ffs_hdr[16] = 0
    ffs_hdr[16] = (-(sum(ffs_hdr[:16]) + sum(ffs_hdr[18:23]))) & 0xFF
    before[ffs_pos + 16] = ffs_hdr[16]

    inner_after = bytes(before) + replacement + after
    print(f"PE32: {old_payload_size} -> {new_payload_size} ({delta:+d})")
    print(f"FFS: {old_ffs_size} -> {new_ffs_size} ({delta:+d})")
    print(f"Inner FV: {len(inner)} -> {len(inner_after)} ({len(inner_after)-len(inner):+d})")

    # LZMA compress
    filters = [{"id": lzma.FILTER_LZMA1, "dict_size": 16*1024*1024,
                "lc": 3, "lp": 0, "pb": 2, "mode": lzma.MODE_NORMAL,
                "nice_len": 64, "mf": lzma.MF_BT4}]
    compressed = bytearray(lzma.compress(inner_after, format=lzma.FORMAT_ALONE, filters=filters))
    compressed[5:13] = len(inner_after).to_bytes(8, "little")
    compressed = bytes(compressed)

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

    # Verify re-extraction
    check_size = int.from_bytes(image[CAPSULE_FFS + 20:CAPSULE_FFS + 23], "little")
    check_data = bytes(image[CAPSULE_FFS + 24:CAPSULE_FFS + check_size])
    check_offset = int.from_bytes(check_data[20:22], "little")
    check_inner = lzma.decompress(check_data[check_offset:], format=lzma.FORMAT_ALONE)
    check_ffs = check_inner.find(CORE_UNLOCK_GUID_LE)
    check_sec_size = int.from_bytes(check_inner[check_ffs+24:check_ffs+27], "little")
    check_payload = check_inner[check_ffs + 28:check_ffs + 28 + check_sec_size - 4]
    if check_payload != replacement:
        raise ValueError("replacement PE32 did not survive re-extraction")
    print(f"Re-extraction OK: {len(check_payload)} bytes verified")

    output = bytes(image)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    manifest = {
        "source_sha256": sha256(base), "replacement_sha256": sha256(replacement),
        "output_sha256": sha256(output),
        "original_pe32_size": old_payload_size, "new_pe32_size": new_payload_size,
        "signed_psp_region_identical": base[0x8E0000:0xAE0000] == output[0x8E0000:0xAE0000],
        "old_capsule_size": old_size, "new_capsule_size": new_size,
    }
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Output: {args.output} ({sha256(output)[:16]}...)")
    print(f"PSP region identical: {manifest['signed_psp_region_identical']}")

if __name__ == "__main__":
    main()
