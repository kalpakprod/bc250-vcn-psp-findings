#!/usr/bin/env python3
"""Build the BC-250 APCB-only DFG wildcard candidate without touching the source image.

This is a deliberately narrow offline transform. It refuses an unexpected baseline and
never overwrites an existing output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

APCB_OFFSET = 0xAB1000
EXPECTED_IMAGE_SIZE = 0x1000000
EXPECTED_APCB_SIZE = 0xB70
DFG_RELS = (0x130, 0x16C)
OLD_DFG = 0x001FFF00
NEW_DFG = 0x007FFF00
EXPECTED_OLD_CHECKSUM = 0xF2


def apcb_checksum(data: bytes, offset: int, size: int) -> int:
    return (-(sum(data[offset:offset + size]) - data[offset + 0x10])) & 0xFF


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    source = args.source.resolve()
    output = args.output.resolve()
    if source == output:
        raise SystemExit("refusing in-place transform")
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing output: {output}")

    original = source.read_bytes()
    if len(original) != EXPECTED_IMAGE_SIZE:
        raise SystemExit(f"unexpected image size: 0x{len(original):X}")
    if original[APCB_OFFSET:APCB_OFFSET + 4] != b"APCB":
        raise SystemExit("APCB magic mismatch")
    apcb_size = struct.unpack_from("<I", original, APCB_OFFSET + 8)[0]
    if apcb_size != EXPECTED_APCB_SIZE:
        raise SystemExit(f"unexpected APCB size: 0x{apcb_size:X}")
    old_checksum = original[APCB_OFFSET + 0x10]
    calculated = apcb_checksum(original, APCB_OFFSET, apcb_size)
    if old_checksum != EXPECTED_OLD_CHECKSUM or old_checksum != calculated:
        raise SystemExit(
            f"unexpected APCB checksum: stored=0x{old_checksum:02X} calculated=0x{calculated:02X}"
        )
    old_words = {
        rel: struct.unpack_from("<I", original, APCB_OFFSET + rel)[0]
        for rel in DFG_RELS
    }
    if any(value != OLD_DFG for value in old_words.values()):
        raise SystemExit(f"unexpected DFG baseline: {old_words!r}")

    candidate = bytearray(original)
    for rel in DFG_RELS:
        struct.pack_into("<I", candidate, APCB_OFFSET + rel, NEW_DFG)
    candidate[APCB_OFFSET + 0x10] = apcb_checksum(candidate, APCB_OFFSET, apcb_size)
    if candidate[APCB_OFFSET + 0x10] != 0x32:
        raise SystemExit(f"unexpected recalculated checksum: 0x{candidate[APCB_OFFSET + 0x10]:02X}")

    changed = [index for index, (before, after) in enumerate(zip(original, candidate)) if before != after]
    expected_changed = [APCB_OFFSET + 0x10, APCB_OFFSET + 0x130 + 2,
                        APCB_OFFSET + 0x16C + 2]
    # The low two bytes and the top byte of both DFG words are unchanged; only byte +2 changes.
    if changed != expected_changed:
        raise SystemExit(f"unexpected changed offsets: {[hex(x) for x in changed]}")

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as handle:
        handle.write(candidate)

    result = {
        "source": str(source),
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "output": str(output),
        "output_sha256": hashlib.sha256(candidate).hexdigest(),
        "size": len(candidate),
        "apcb_offset": hex(APCB_OFFSET),
        "apcb_size": hex(apcb_size),
        "changes": [
            {"absolute_offset": hex(APCB_OFFSET + rel), "old_u32": hex(OLD_DFG), "new_u32": hex(NEW_DFG)}
            for rel in DFG_RELS
        ],
        "checksum": {"relative_offset": "0x10", "old": "0xF2", "new": "0x32"},
        "changed_offsets": [hex(index) for index in changed],
        "changed_byte_count": len(changed),
        "signed_regions_touched": False,
        "hardware_written": False,
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
