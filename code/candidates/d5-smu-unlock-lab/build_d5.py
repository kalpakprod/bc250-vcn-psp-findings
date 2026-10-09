#!/usr/bin/env python3
"""Inject the D5 unlock-only DXE FFS into the exact BC-250 board baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
import lzma
import struct
from pathlib import Path


OUTER_FV_BASE = 0x00AE0000
CAPSULE_FFS_BASE = 0x00AE0078
BDS_GUID_LE = bytes.fromhex("828f4b8f919b284086e6f4db7d4c1dff")
LZMA_GUID_LE = bytes.fromhex("98584eee143959429d6edc7bd79403cf")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def checksum16_header(data: bytearray, start: int, size: int) -> None:
    struct.pack_into("<H", data, start + 0x32, 0)
    words = struct.unpack_from(f"<{size // 2}H", data, start)
    struct.pack_into("<H", data, start + 0x32, (-sum(words)) & 0xFFFF)


def ffs_header_checksum(header: bytearray) -> None:
    header[16] = 0
    header[16] = (-(sum(header[:16]) + sum(header[18:23]))) & 0xFF


def inject(base: bytes, driver_ffs: bytes) -> tuple[bytes, dict[str, object]]:
    image = bytearray(base)
    if len(image) != 0x1000000:
        raise ValueError(f"expected 16 MiB image, got {len(image):#x}")
    if image[OUTER_FV_BASE + 0x28 : OUTER_FV_BASE + 0x2C] != b"_FVH":
        raise ValueError("outer FV signature missing")

    outer_len = struct.unpack_from("<Q", image, OUTER_FV_BASE + 0x20)[0]
    outer_end = OUTER_FV_BASE + outer_len
    old_ffs_size = int.from_bytes(image[CAPSULE_FFS_BASE + 20 : CAPSULE_FFS_BASE + 23], "little")
    old_ffs_header = bytes(image[CAPSULE_FFS_BASE : CAPSULE_FFS_BASE + 24])
    old_ffs_data = bytes(image[CAPSULE_FFS_BASE + 24 : CAPSULE_FFS_BASE + old_ffs_size])
    data_offset = int.from_bytes(old_ffs_data[20:22], "little")
    decompressed = bytearray(lzma.decompress(old_ffs_data[data_offset:], format=lzma.FORMAT_ALONE))

    fv_start = 0x10
    if decompressed[fv_start + 0x28 : fv_start + 0x2C] != b"_FVH":
        raise ValueError("inner FV signature missing")
    if driver_ffs[:16] in decompressed:
        raise ValueError("driver GUID already present")
    bds_pos = decompressed.find(BDS_GUID_LE)
    if bds_pos < 0 or bds_pos % 8:
        raise ValueError(f"BDS FFS not found/aligned: {bds_pos:#x}")

    padded_driver = driver_ffs + b"\xff" * ((-len(driver_ffs)) % 8)
    rebuilt = decompressed[:bds_pos] + padded_driver + decompressed[bds_pos:]
    block_size = 0x1000
    new_fv_len = ((len(rebuilt) - fv_start + block_size - 1) // block_size) * block_size
    rebuilt.extend(b"\xff" * (fv_start + new_fv_len - len(rebuilt)))
    rebuilt[0x0C:0x0F] = (new_fv_len + 4).to_bytes(4, "little")[:3]
    rebuilt[0x0F] = 0x17
    struct.pack_into("<Q", rebuilt, fv_start + 0x20, new_fv_len)
    struct.pack_into("<II", rebuilt, fv_start + 0x38, new_fv_len // block_size, block_size)
    fv_header_len = struct.unpack_from("<H", rebuilt, fv_start + 0x30)[0]
    checksum16_header(rebuilt, fv_start, fv_header_len)

    filters = [{
        "id": lzma.FILTER_LZMA1,
        "dict_size": 16 * 1024 * 1024,
        "lc": 3,
        "lp": 0,
        "pb": 2,
        "mode": lzma.MODE_NORMAL,
        "nice_len": 64,
        "mf": lzma.MF_BT4,
    }]
    compressed = lzma.compress(rebuilt, format=lzma.FORMAT_ALONE, filters=filters)
    guided = (0x18 + len(compressed)).to_bytes(4, "little")[:3] + b"\x02"
    guided += LZMA_GUID_LE + struct.pack("<HH", 0x18, 0x01) + compressed

    new_header = bytearray(old_ffs_header)
    new_size = 24 + len(guided)
    new_header[20:23] = new_size.to_bytes(4, "little")[:3]
    ffs_header_checksum(new_header)
    new_capsule = bytes(new_header) + guided
    new_free = (CAPSULE_FFS_BASE + len(new_capsule) + 7) & ~7
    if new_free > outer_end:
        raise ValueError("rebuilt capsule exceeds outer FV")
    image[CAPSULE_FFS_BASE : CAPSULE_FFS_BASE + len(new_capsule)] = new_capsule
    image[new_free:outer_end] = b"\xff" * (outer_end - new_free)

    check_data = bytes(image[CAPSULE_FFS_BASE + 24 : CAPSULE_FFS_BASE + new_size])
    check_offset = int.from_bytes(check_data[20:22], "little")
    check_inner = lzma.decompress(check_data[check_offset:], format=lzma.FORMAT_ALONE)
    guid_count = check_inner.count(driver_ffs[:16])
    full_ffs_count = check_inner.count(driver_ffs)
    if guid_count < 1 or full_ffs_count != 1:
        raise ValueError(
            f"independent re-extraction mismatch: guid={guid_count}, full_ffs={full_ffs_count}"
        )

    return bytes(image), {
        "outer_fv": [hex(OUTER_FV_BASE), hex(outer_end)],
        "old_capsule_size": old_ffs_size,
        "new_capsule_size": new_size,
        "inner_fv_size": new_fv_len,
        "driver_ffs_size": len(driver_ffs),
        "driver_insertion_offset_in_decompressed_stream": hex(bds_pos),
        "driver_guid_occurrences_after_reextract": guid_count,
        "full_driver_ffs_occurrences_after_reextract": full_ffs_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--ffs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()

    base = args.base.read_bytes()
    ffs = args.ffs.read_bytes()
    output, details = inject(base, ffs)
    args.output.write_bytes(output)
    manifest = {
        "classification": "offline-candidate",
        "source": str(args.base),
        "source_size": len(base),
        "source_sha256": sha256(base),
        "driver_ffs": str(args.ffs),
        "driver_ffs_sha256": sha256(ffs),
        "output": str(args.output),
        "output_size": len(output),
        "output_sha256": sha256(output),
        "signed_psp_region_0x8e0000_0xae0000_identical": base[0x8E0000:0xAE0000] == output[0x8E0000:0xAE0000],
        "apcb_0xab1000_0xab1b70_identical": base[0xAB1000:0xAB1B70] == output[0xAB1000:0xAB1B70],
        "details": details,
        "unrun": ["QEMU hardware semantics", "BC-250 cold boot", "DXE dispatch", "SMU unlock readback", "VCN function"],
    }
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
