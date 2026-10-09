#!/usr/bin/env python3
"""Build a one-field BC-250 AmdSetup memory-clock hypothesis candidate.

The transform pins the existing IFR enumerated 1750 MHz option and deliberately
leaves all UCLK/FCLK/voltage/timing/APCB/PSP fields untouched. It refuses an
unexpected baseline and never overwrites an existing output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

EXPECTED_IMAGE_SIZE = 0x1000000
AMD_SETUP_RECORD_OFFSET = 0x4BB
AMD_SETUP_BODY_OFFSET = 0x4CF
MEMORY_CLOCK_RELATIVE_OFFSET = 0x316
ABSOLUTE_OFFSET = AMD_SETUP_BODY_OFFSET + MEMORY_CLOCK_RELATIVE_OFFSET
OLD_VALUE = 0xFF
NEW_VALUE = 0x23


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--new-value",
        type=lambda s: int(s, 0),
        default=0x23,
        help="MemoryClockSpeed IFR option value to pin (default 0x23 = 1750MHz; 0x14 = 1000MHz)",
    )
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
    if original[AMD_SETUP_RECORD_OFFSET:AMD_SETUP_RECORD_OFFSET + 4] != b"NVAR":
        raise SystemExit("AmdSetup NVAR record magic mismatch")
    if original[AMD_SETUP_RECORD_OFFSET + 0x0B:AMD_SETUP_RECORD_OFFSET + 0x14] != b"AmdSetup\x00":
        raise SystemExit("AmdSetup NVAR name mismatch")
    if original[ABSOLUTE_OFFSET] != OLD_VALUE:
        raise SystemExit(f"unexpected MemoryClockSpeed baseline: 0x{original[ABSOLUTE_OFFSET]:02X}")
    new_value = args.new_value
    known_labels = {0x23: "1750MHz (IFR option)", 0x14: "1000MHz (IFR option)"}
    if new_value not in known_labels:
        raise SystemExit(
            f"refusing unknown IFR option value: 0x{new_value:X}; known: "
            + ", ".join(hex(v) for v in sorted(known_labels))
        )
    candidate = bytearray(original)
    candidate[ABSOLUTE_OFFSET] = new_value
    changed = [i for i, (before, after) in enumerate(zip(original, candidate)) if before != after]
    if changed != [ABSOLUTE_OFFSET]:
        raise SystemExit(f"unexpected changed offsets: {[hex(i) for i in changed]}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as handle:
        handle.write(candidate)
    result = {
        "source": str(source),
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "output": str(output),
        "output_sha256": hashlib.sha256(candidate).hexdigest(),
        "size": len(candidate),
        "nvar_record_offset": hex(AMD_SETUP_RECORD_OFFSET),
        "amdsetup_body_offset": hex(AMD_SETUP_BODY_OFFSET),
        "field": "MemoryClockSpeed",
        "relative_offset": hex(MEMORY_CLOCK_RELATIVE_OFFSET),
        "absolute_offset": hex(ABSOLUTE_OFFSET),
        "old_value": hex(OLD_VALUE),
        "new_value": hex(new_value),
        "new_value_label": known_labels[new_value],
        "changed_offsets": [hex(i) for i in changed],
        "changed_byte_count": len(changed),
        "other_memory_controls_changed": False,
        "voltage_changed": False,
        "apcb_psp_ps1_bhd_fv_changed": False,
        "hardware_written": False,
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
