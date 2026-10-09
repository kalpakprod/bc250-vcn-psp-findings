#!/usr/bin/env python3
"""Strict RP2350 ARM-S UF2 validation; separate documented E10 marker from program pages."""

import argparse
import hashlib
import json
import struct
from pathlib import Path


def validate(path):
    """Recognize only the exact picotool E10 marker and reserved-sector-safe program blocks."""
    data = Path(path).read_bytes()
    if not data or len(data) % 512:
        raise ValueError("UF2 must contain whole 512-byte blocks")
    indices = set()
    addresses = set()
    expected = None
    metadata = []
    for offset in range(0, len(data), 512):
        block = data[offset : offset + 512]
        m1, m2, flags, address, size, index, total, family = struct.unpack(
            "<8I", block[:32]
        )
        if (m1, m2, struct.unpack("<I", block[508:])[0]) != (
            0x0A324655,
            0x9E5D5157,
            0x0AB16F30,
        ):
            raise ValueError("Bad UF2 magic")
        if family == 0xE48BFF57:
            # Exact gen_abs_block/check_abs_block from local picotool 2.3.1.
            if (
                offset != 0
                or metadata
                or flags != 0xA000
                or size != 256
                or index != 0
                or total != 2
                or block[32:288] != b"\xef" * 256
                or struct.unpack("<I", block[288:292])[0] != 0x9957E304
            ):
                raise ValueError("Unrecognized absolute metadata block")
            metadata.append(
                {
                    "type": "documented_RP2350_E10_ignore_marker",
                    "address": hex(address),
                    "program_data": False,
                    "device_ignore_behavior_hardware_verified": False,
                }
            )
            continue
        if family != 0xE48BFF59 or flags != 0x2000 or size != 256:
            raise ValueError("Unexpected RP2350 program family/flags/payload")
        if address % 256 or not 0x10000000 <= address or address + size > 0x10FFC000:
            raise ValueError("Program page enters protected config/key sectors")
        if index in indices or address in addresses:
            raise ValueError("Duplicate program block")
        indices.add(index)
        addresses.add(address)
        if expected is None:
            expected = total
        if total != expected:
            raise ValueError("Inconsistent program block count")
    if expected is None or indices != set(range(expected)):
        raise ValueError("Incomplete program blocks")
    return {
        "sha256": hashlib.sha256(data).hexdigest(),
        "size": len(data),
        "program_blocks": expected,
        "family_id": "0xe48bff59",
        "metadata": metadata,
        "program_pages_exclude_private_sectors": True,
        "hardware_boot_verified": False,
        "metadata_provenance": "picotool 2.3.1 elf2uf2.cpp gen_abs_block/check_abs_block; pico-sdk boot/uf2.h",
    }


def main():
    """Print structure, not firmware contents; malformed input fails closed."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    args = parser.parse_args()
    try:
        result = validate(args.image)
    except (OSError, ValueError) as error:
        print(json.dumps({"verified": False, "error": str(error)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
