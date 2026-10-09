#!/usr/bin/env python3
"""Build a structurally valid, unsigned BC-250 SEC_GASKET body with the sibling VCN bank.

Research artifact only. It has no AMD signature and must never be flashed.
"""
from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

from parse_sec_gasket import parse

HEADER_SIZE = 0x40
VCN_BANK_START = 0x0900C000
VCN_BANK_END = 0x0900CFFF
TARGET_GROUPS = {0x201, 0x280}


def group_rows(report: dict[str, object]) -> dict[int, list[tuple[int, int]]]:
    result = {}
    for group in report["groups"]:
        group_type = int(group["type"], 16)
        result[group_type] = [
            (int(write["address"], 16), int(write["value"], 16))
            for write in group["writes"]
        ]
    return result


def insert_bank(rows: list[tuple[int, int]], additions: list[tuple[int, int]]) -> list[tuple[int, int]]:
    existing = {address for address, _ in rows}
    if any(address in existing for address, _ in additions):
        raise ValueError("VCN bank collides with an existing BC-250 register write")
    first_later_bank = next(
        (
            index
            for index, (address, _) in enumerate(rows)
            if address > VCN_BANK_END and (address & 0xFFF00000) == 0x09000000
        ),
        len(rows),
    )
    return rows[:first_later_bank] + additions + rows[first_later_bank:]


def encode(header: bytes, groups: list[tuple[int, list[tuple[int, int]]]]) -> bytes:
    output = bytearray(header)
    for group_type, writes in groups:
        output += struct.pack("<II", group_type, len(writes))
        for address, value in writes:
            output += struct.pack("<II", address, value)
    return bytes(output)


def main() -> int:
    source_path = Path(sys.argv[1])
    template_path = Path(sys.argv[2])
    output_path = Path(sys.argv[3])
    manifest_path = Path(sys.argv[4])

    source = source_path.read_bytes()
    source_report = parse(source)
    template = json.loads(template_path.read_text(encoding="utf-8"))
    template_rows: dict[int, list[tuple[int, int]]] = {group: [] for group in TARGET_GROUPS}
    for write in template["working_sibling"]["writes"]:
        group = int(write["group"], 16)
        if group in template_rows:
            template_rows[group].append(
                (int(write["address"], 16), int(write["value"], 16))
            )

    source_groups = group_rows(source_report)
    rebuilt_groups = []
    deltas = {}
    for group in source_report["groups"]:
        group_type = int(group["type"], 16)
        rows = source_groups[group_type]
        if group_type in TARGET_GROUPS:
            additions = template_rows[group_type]
            rows = insert_bank(rows, additions)
            deltas[f"0x{group_type:x}"] = {
                "old_count": len(source_groups[group_type]),
                "added_count": len(additions),
                "new_count": len(rows),
            }
        rebuilt_groups.append((group_type, rows))

    candidate = encode(source[:HEADER_SIZE], rebuilt_groups)
    parsed_candidate = parse(candidate)
    output_path.write_bytes(candidate)
    manifest = {
        "warning": "UNSIGNED RESEARCH ARTIFACT. DO NOT FLASH.",
        "source": str(source_path),
        "source_size": len(source),
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "candidate": str(output_path),
        "candidate_size": len(candidate),
        "candidate_sha256": hashlib.sha256(candidate).hexdigest(),
        "size_delta": len(candidate) - len(source),
        "groups": deltas,
        "parsed_group_count": len(parsed_candidate["groups"]),
        "amd_signature_valid": False,
        "flashable": False,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
