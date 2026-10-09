#!/usr/bin/env python3
"""Read-only detailed AMD BC-250 APCB/DFG/MEMG group auditor."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path
from typing import Any

APCB_OFFSET = 0xAB1000


def checksum_byte(data: bytes, offset: int, size: int) -> int:
    return (-(sum(data[offset:offset + size]) - data[offset + 0x10])) & 0xFF


def token_rows(body: bytes) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rel in range(0, len(body) - 3, 4):
        rows.append({
            "body_offset": f"0x{rel:X}",
            "u8_0": body[rel],
            "u8_1": body[rel + 1],
            "u16_le": struct.unpack_from("<H", body, rel + 2)[0],
        })
    return rows


def parse_apcb(data: bytes, offset: int = APCB_OFFSET) -> dict[str, Any]:
    if offset + 0x20 > len(data) or data[offset:offset + 4] != b"APCB":
        raise ValueError(f"APCB magic not found at 0x{offset:X}")
    size = struct.unpack_from("<I", data, offset + 8)[0]
    if size < 0x20 or offset + size > len(data):
        raise ValueError(f"APCB size 0x{size:X} is outside image at 0x{offset:X}")
    stored = data[offset + 0x10]
    calculated = checksum_byte(data, offset, size)
    groups: list[dict[str, Any]] = []
    cursor = offset + 0x20
    end = offset + size
    errors: list[str] = []
    while cursor + 0x10 <= end:
        signature = data[cursor:cursor + 4].decode("latin1", "replace")
        gid, flags, instance, group_size = struct.unpack_from("<HHII", data, cursor + 4)
        if group_size < 0x10 or cursor + group_size > end:
            errors.append(f"invalid group at 0x{cursor - offset:X}: size=0x{group_size:X}")
            break
        group_end = cursor + group_size
        group: dict[str, Any] = {
            "offset": f"0x{cursor - offset:X}",
            "absolute_offset": f"0x{cursor:X}",
            "signature": signature,
            "gid": f"0x{gid:04X}",
            "flags": f"0x{flags:04X}",
            "instance": instance,
            "size": group_size,
            "body_sha256": hashlib.sha256(data[cursor + 0x10:group_end]).hexdigest(),
            "subgroups": [],
            "unparsed_body_bytes": 0,
        }
        subcursor = cursor + 0x10
        while subcursor + 8 <= group_end:
            sgid, sinstance, subgroup_size = struct.unpack_from("<HHI", data, subcursor)
            if sgid != gid or subgroup_size < 8 or subcursor + subgroup_size > group_end:
                group["unparsed_body_bytes"] = group_end - subcursor
                break
            body = data[subcursor + 8:subcursor + subgroup_size]
            group["subgroups"].append({
                "offset": f"0x{subcursor - offset:X}",
                "absolute_offset": f"0x{subcursor:X}",
                "gid": f"0x{sgid:04X}",
                "instance": sinstance,
                "size": subgroup_size,
                "body_length": len(body),
                "body_sha256": hashlib.sha256(body).hexdigest(),
                "token_rows": token_rows(body),
            })
            subcursor += subgroup_size
        groups.append(group)
        cursor = group_end
    result: dict[str, Any] = {
        "offset": f"0x{offset:X}",
        "size": size,
        "stored_checksum_byte": f"0x{stored:02X}",
        "calculated_checksum_byte": f"0x{calculated:02X}",
        "checksum_match": stored == calculated,
        "dfg_words": {
            f"0x{rel:X}": f"0x{int.from_bytes(data[offset + rel:offset + rel + 4], 'little'):08X}"
            for rel in (0x130, 0x16C) if rel + 4 <= size
        },
        "group_count": len(groups),
        "groups": groups,
        "errors": errors,
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--offset", type=lambda value: int(value, 0), default=APCB_OFFSET)
    args = parser.parse_args()
    reports = []
    failed = False
    for image in args.images:
        raw = image.read_bytes()
        try:
            parsed = parse_apcb(raw, args.offset)
        except Exception as exc:
            failed = True
            parsed = {"error": str(exc)}
        reports.append({
            "path": str(image.resolve()),
            "size": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "apcb": parsed,
        })
    result = {"tool": "scripts/apcb_detail.py", "images": reports}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output.resolve()), "images": len(reports), "failed": failed}))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
