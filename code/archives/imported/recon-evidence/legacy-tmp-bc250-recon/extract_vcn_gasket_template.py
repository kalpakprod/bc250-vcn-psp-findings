#!/usr/bin/env python3
"""Extract and cross-check the HWID-12/VCN SEC_GASKET register bank."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

VCN_BANK_START = 0x0900C000
VCN_BANK_END = 0x0900CFFF


def extract(path: Path) -> list[dict[str, object]]:
    report = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for group in report["groups"]:
        for write in group["writes"]:
            address = int(write["address"], 16)
            if VCN_BANK_START <= address <= VCN_BANK_END:
                rows.append(
                    {
                        "group": group["type"],
                        "address": write["address"],
                        "value": write["value"],
                    }
                )
    return rows


def digest(rows: list[dict[str, object]]) -> str:
    canonical = json.dumps(rows, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(canonical).hexdigest()


def main() -> int:
    bc250 = extract(Path(sys.argv[1]))
    sibling_a = extract(Path(sys.argv[2]))
    sibling_b = extract(Path(sys.argv[3]))
    if sibling_a != sibling_b:
        raise ValueError("working-sibling VCN gasket banks differ")
    output = Path(sys.argv[4])
    result = {
        "bank": "HWID 12 / VCN",
        "range": [f"0x{VCN_BANK_START:08x}", f"0x{VCN_BANK_END:08x}"],
        "bc250": {"count": len(bc250), "sha256": digest(bc250), "writes": bc250},
        "working_sibling": {
            "count": len(sibling_a),
            "sha256": digest(sibling_a),
            "writes": sibling_a,
        },
    }
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(
        f"bc250_count={len(bc250)} sibling_count={len(sibling_a)} "
        f"bc250_sha={digest(bc250)} sibling_sha={digest(sibling_a)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
