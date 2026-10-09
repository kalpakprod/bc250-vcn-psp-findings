#!/usr/bin/env python3
"""Parse the Robin 3.00 SEC_GASKET register-programming table."""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

HEADER_SIZE = 0x40
PAIR_SIZE = 8


def parse(data: bytes) -> dict[str, object]:
    if len(data) < HEADER_SIZE:
        raise ValueError("SEC_GASKET payload is shorter than its header")

    header = list(struct.unpack_from("<16I", data, 0))
    groups: list[dict[str, object]] = []
    offset = HEADER_SIZE
    while offset < len(data):
        if len(data) - offset < 8:
            raise ValueError(f"truncated group header at 0x{offset:x}")
        group_type, count = struct.unpack_from("<II", data, offset)
        group_offset = offset
        offset += 8
        byte_count = count * PAIR_SIZE
        if byte_count > len(data) - offset:
            raise ValueError(
                f"group 0x{group_type:x} at 0x{group_offset:x} needs "
                f"0x{byte_count:x} bytes, only 0x{len(data) - offset:x} remain"
            )
        writes = []
        for index in range(count):
            address, value = struct.unpack_from("<II", data, offset + index * PAIR_SIZE)
            writes.append({"address": f"0x{address:08x}", "value": f"0x{value:08x}"})
        groups.append(
            {
                "offset": f"0x{group_offset:x}",
                "type": f"0x{group_type:x}",
                "count": count,
                "writes": writes,
            }
        )
        offset += byte_count

    if offset != len(data):
        raise ValueError(f"parser stopped at 0x{offset:x}, payload ends at 0x{len(data):x}")
    return {"size": len(data), "header": [f"0x{word:08x}" for word in header], "groups": groups}


def main() -> int:
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    report = parse(source.read_bytes())
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    groups = report["groups"]
    print(f"size=0x{report['size']:x} groups={len(groups)} writes={sum(g['count'] for g in groups)}")
    for group in groups:
        addresses = [int(write["address"], 16) for write in group["writes"]]
        address_range = (
            f"0x{min(addresses):08x}..0x{max(addresses):08x}" if addresses else "empty"
        )
        print(
            f"{group['offset']} type={group['type']} count={group['count']} "
            f"range={address_range}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
