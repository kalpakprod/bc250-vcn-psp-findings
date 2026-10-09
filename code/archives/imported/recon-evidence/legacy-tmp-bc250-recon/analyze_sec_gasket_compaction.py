#!/usr/bin/env python3
"""Measure whether an HWID-12 bank can fit without deleting unique SEC_GASKET writes."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ENTRY_SIZE = 8
REQUIRED_WRITES = 56
TARGET_GROUPS = {"0x201", "0x280"}


def main() -> int:
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    report = json.loads(source.read_text(encoding="utf-8"))
    groups = []
    duplicate_writes = 0
    for group in report["groups"]:
        pairs = [(write["address"], write["value"]) for write in group["writes"]]
        unique_pairs = set(pairs)
        duplicates = len(pairs) - len(unique_pairs)
        if group["type"] in TARGET_GROUPS:
            duplicate_writes += duplicates
        groups.append(
            {
                "type": group["type"],
                "count": len(pairs),
                "unique_pairs": len(unique_pairs),
                "duplicate_pair_writes": duplicates,
                "unique_addresses": len({address for address, _ in pairs}),
                "ordered_rewrites": len(pairs) - len({address for address, _ in pairs}),
            }
        )

    required_bytes = REQUIRED_WRITES * ENTRY_SIZE
    duplicate_bytes = duplicate_writes * ENTRY_SIZE
    result = {
        "required_writes": REQUIRED_WRITES,
        "required_bytes": required_bytes,
        "target_group_duplicate_writes": duplicate_writes,
        "theoretical_duplicate_bytes": duplicate_bytes,
        "remaining_shortfall": required_bytes - duplicate_bytes,
        "size_preserving_candidate_possible": False,
        "warning": (
            "Even exact duplicate writes can be side-effectful; theoretical duplicate bytes are not "
            "declared safe to remove. Ordered rewrites include commit/enable transitions."
        ),
        "groups": groups,
    }
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
