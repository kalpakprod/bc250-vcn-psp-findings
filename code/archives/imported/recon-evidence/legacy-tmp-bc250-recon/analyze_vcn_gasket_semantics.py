#!/usr/bin/env python3
"""Infer VCN SEC_GASKET field roles from cross-bank invariants."""
from __future__ import annotations

import json
import sys
from pathlib import Path

VCN_BANK_ID = 0x0C


def complete_ranges(bank: dict[str, object]) -> list[dict[str, object]]:
    return [
        descriptor
        for descriptor in bank["descriptors"]
        if "range_start" in descriptor["fields"] and "range_end" in descriptor["fields"]
    ]


def one_value(bank: dict[str, object], name: str) -> int | None:
    values = bank["controls"].get(name)
    return int(values[-1], 16) if values else None


def main() -> int:
    decoded = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    raw = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    output = Path(sys.argv[3])

    correlations = []
    for bank in decoded["banks"]:
        ranges = complete_ranges(bank)
        bitmap = one_value(bank, "range_enable_bitmap")
        expected = (1 << len(ranges)) - 1 if ranges else 0
        if bitmap is not None:
            correlations.append(
                {
                    "bank_id": bank["bank_id"],
                    "range_count": len(ranges),
                    "bitmap": f"0x{bitmap:08x}",
                    "expected": f"0x{expected:08x}",
                    "matches": bitmap == expected,
                }
            )

    vcn = next(bank for bank in decoded["banks"] if bank["bank_id"] == VCN_BANK_ID)
    ranges = complete_ranges(vcn)
    alternate = [
        row
        for row in raw["working_sibling"]["writes"]
        if row["group"] == "0x280"
    ]
    modes = sorted(
        {
            value
            for descriptor in ranges
            for value in descriptor["fields"].get("policy_mode", [])
        }
    )
    attributes = sorted(
        {
            value
            for descriptor in ranges
            for value in descriptor["fields"].get("attributes", [])
        }
    )
    result = {
        "cross_bank_range_bitmap": {
            "tested": len(correlations),
            "matches": sum(item["matches"] for item in correlations),
            "rows": correlations,
        },
        "vcn": {
            "bank_id": VCN_BANK_ID,
            "range_count": len(ranges),
            "range_enable_bitmap": vcn["controls"].get("range_enable_bitmap"),
            "program_commit": vcn["controls"].get("program_commit"),
            "access_masks": {
                key: vcn["controls"].get(key)
                for key in ("access_mask_0", "access_mask_1", "access_mask_2")
            },
            "policy_masks": {
                key: vcn["controls"].get(key)
                for key in ("policy_mask_0", "policy_mask_1", "policy_class_mask")
            },
            "policy_modes": modes,
            "attributes": attributes,
            "ranges": ranges,
            "alternate_group_0x280": alternate,
        },
        "inferences": {
            "range_enable_bitmap": "high confidence: equals (1 << complete_range_count) - 1 across populated banks",
            "program_commit": "medium confidence: written 0 before programming and 1 after programming",
            "range_start_end": "high confidence: paired ascending addresses map to VCN MMIO subranges",
            "access_masks": "low confidence: 24-bit masks, client/master identities unresolved",
            "policy_mode": "low confidence: 0x36 shared by descriptors, bit semantics unresolved",
            "attributes": "low confidence: 0x307 shared by VCN ranges, bit semantics unresolved",
        },
    }
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(
        f"bitmap_matches={result['cross_bank_range_bitmap']['matches']}/"
        f"{result['cross_bank_range_bitmap']['tested']} "
        f"vcn_ranges={len(ranges)} modes={modes} attributes={attributes}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
