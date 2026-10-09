#!/usr/bin/env python3
"""Decode recurring per-HWID SEC_GASKET banks without assigning unknown bit semantics."""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

BANK_FRAME = 0x09000000
BANK_MASK = 0xFFFFF000
DESCRIPTOR_BASE = 0x92C
DESCRIPTOR_STRIDE = 0x24
DESCRIPTOR_FIELDS = {
    0x00: "selector",
    0x04: "policy_mode",
    0x08: "range_start",
    0x0C: "range_end",
    0x18: "attributes",
}
CONTROL_OFFSETS = {
    0x234: "program_commit",
    0x830: "access_mask_0",
    0x834: "access_mask_1",
    0x838: "access_mask_2",
    0x910: "policy_mask_0",
    0x914: "policy_mask_1",
    0x920: "policy_class_mask",
    0xB80: "range_enable_bitmap",
}


def decode(path: Path, group_type: str = "0x201") -> dict[str, object]:
    source = json.loads(path.read_text(encoding="utf-8"))
    banks: dict[int, list[tuple[int, int]]] = collections.defaultdict(list)
    for group in source["groups"]:
        if group["type"] != group_type:
            continue
        for write in group["writes"]:
            address = int(write["address"], 16)
            if address & 0xFFF00000 != BANK_FRAME:
                continue
            banks[address & BANK_MASK].append((address & 0xFFF, int(write["value"], 16)))

    decoded = []
    for bank_base, writes in sorted(banks.items()):
        values: dict[int, list[int]] = collections.defaultdict(list)
        for offset, value in writes:
            values[offset].append(value)
        controls = {
            name: [f"0x{value:08x}" for value in values.get(offset, [])]
            for offset, name in CONTROL_OFFSETS.items()
            if offset in values
        }
        descriptors = []
        for index in range(16):
            slot_base = DESCRIPTOR_BASE + index * DESCRIPTOR_STRIDE
            fields = {}
            for field_offset, name in DESCRIPTOR_FIELDS.items():
                values_here = values.get(slot_base + field_offset, [])
                if values_here:
                    fields[name] = [f"0x{value:08x}" for value in values_here]
            if fields:
                descriptors.append({"index": index, "fields": fields})
        decoded.append(
            {
                "bank_base": f"0x{bank_base:08x}",
                "bank_id": (bank_base >> 12) & 0xFF,
                "write_count": len(writes),
                "controls": controls,
                "descriptors": descriptors,
            }
        )
    return {"source": str(path), "group": group_type, "banks": decoded}


def main() -> int:
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    result = decode(source)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    mode_counts = collections.Counter()
    attribute_counts = collections.Counter()
    for bank in result["banks"]:
        for descriptor in bank["descriptors"]:
            fields = descriptor["fields"]
            mode_counts.update(fields.get("policy_mode", []))
            attribute_counts.update(fields.get("attributes", []))
    print(f"banks={len(result['banks'])} output={output}")
    print(f"policy_mode={dict(mode_counts)}")
    print(f"attributes={dict(attribute_counts)}")
    for bank in result["banks"]:
        print(
            f"bank={bank['bank_base']} id=0x{bank['bank_id']:02x} "
            f"writes={bank['write_count']} descriptors={len(bank['descriptors'])}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
