#!/usr/bin/env python3
"""Build a BC-250 combined VCN-policy candidate with stock APCB."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path

IMAGE_SIZE = 0x1000000
STOCK_SHA256 = "83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0"
D3B2_SHA256 = "439e248141ef6a9c1313bc7815696d570be8fed5471262596186f3da8914747d"
APCB = 0xAB1000


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ranges(before: bytes, after: bytes) -> list[dict[str, int | str]]:
    positions = [index for index, (a, b) in enumerate(zip(before, after)) if a != b]
    if not positions:
        return []
    result: list[dict[str, int | str]] = []
    start = previous = positions[0]
    for position in positions[1:]:
        if position != previous + 1:
            result.append({"start": f"0x{start:X}", "end": f"0x{previous:X}", "length": previous - start + 1})
            start = position
        previous = position
    result.append({"start": f"0x{start:X}", "end": f"0x{previous:X}", "length": previous - start + 1})
    return result


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stock", type=Path)
    parser.add_argument("d3b2", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    stock_path = args.stock.resolve()
    d3b2_path = args.d3b2.resolve()
    output = args.output.resolve()
    manifest_path = args.manifest.resolve()
    require(not output.exists(), f"refusing to overwrite existing output: {output}")
    require(not manifest_path.exists(), f"refusing to overwrite existing manifest: {manifest_path}")

    stock = stock_path.read_bytes()
    d3b2 = d3b2_path.read_bytes()
    require(len(stock) == len(d3b2) == IMAGE_SIZE, "input size mismatch")
    require(sha256(stock) == STOCK_SHA256, "stock SHA-256 mismatch")
    require(sha256(d3b2) == D3B2_SHA256, "D3-B2 SHA-256 mismatch")
    require(stock[APCB:APCB + 4] == d3b2[APCB:APCB + 4] == b"APCB", "APCB signature mismatch")
    apcb_size = struct.unpack_from("<I", stock, APCB + 8)[0]
    require(apcb_size == 0xB70, f"unexpected APCB size: 0x{apcb_size:X}")
    apcb_diff = [index for index, (a, b) in enumerate(zip(stock[APCB:APCB + apcb_size], d3b2[APCB:APCB + apcb_size])) if a != b]
    require(apcb_diff == [0x10, 0x132, 0x16E], f"unexpected D3-B2 APCB delta: {[hex(i) for i in apcb_diff]}")

    candidate = bytearray(d3b2)
    candidate[APCB:APCB + apcb_size] = stock[APCB:APCB + apcb_size]
    candidate_bytes = bytes(candidate)
    require(candidate_bytes[APCB:APCB + apcb_size] == stock[APCB:APCB + apcb_size], "APCB restore failed")
    require(candidate_bytes[0x9E0000:0x9E4708] == d3b2[0x9E0000:0x9E4708], "policy region changed unexpectedly")
    require(candidate_bytes[0x8E0000:0x8E0140] == d3b2[0x8E0000:0x8E0140], "PSP directory changed unexpectedly")

    changed_ranges = ranges(stock, candidate_bytes)
    changed_count = sum(int(item["length"]) for item in changed_ranges)
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(candidate_bytes)
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/build_vcn_policy_only_candidate.py",
        "stock": {"path": str(stock_path), "sha256": sha256(stock), "size": len(stock)},
        "d3b2_source": {"path": str(d3b2_path), "sha256": sha256(d3b2), "size": len(d3b2)},
        "output": {"path": str(output), "sha256": sha256(candidate_bytes), "size": len(candidate_bytes)},
        "transformation": f"restore complete stock APCB range 0x{APCB:X}..0x{APCB + apcb_size - 1:X}",
        "apcb_size": apcb_size,
        "removed_d3b2_apcb_delta_offsets": [f"0x{APCB + index:X}" for index in apcb_diff],
        "changed_byte_count_from_stock": changed_count,
        "changed_ranges_from_stock": changed_ranges,
        "checks": {
            "apcb_byte_identical_to_stock": True,
            "psp_directory_identical_to_d3b2": True,
            "policy_region_identical_to_d3b2": True,
            "signature_acceptance": "unverified; unchanged from D3-B2 risk",
        },
        "classification": "offline combined-policy candidate with stock APCB; hardware unverified",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "sha256": manifest["output"]["sha256"], "changed_bytes": changed_count, "changed_ranges": len(changed_ranges)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
