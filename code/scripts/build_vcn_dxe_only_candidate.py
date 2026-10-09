#!/usr/bin/env python3
"""Build a BC-250 DXE-region-only VCN unlock candidate (no PSP/APCB touch)."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

IMAGE_SIZE = 0x1000000
STOCK_SHA256 = "83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0"
PSP_START, PSP_END = 0x8E0000, 0x9E0000
APCB_START, APCB_END = 0xAB1000, 0xAB1B70

# Import injection logic from build_vcn_bios
sys.path.insert(
    0,
    str(
        Path(
            "archives/imported/historical-bios-repo/legacy-bc250-bios/tools/patch-build"
        ).resolve()
    ),
)
import build_vcn_bios


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
            result.append(
                {
                    "start": f"0x{start:X}",
                    "end": f"0x{previous:X}",
                    "length": previous - start + 1,
                }
            )
            start = position
        previous = position
    result.append(
        {
            "start": f"0x{start:X}",
            "end": f"0x{previous:X}",
            "length": previous - start + 1,
        }
    )
    return result


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stock", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--verification", type=Path, required=True)
    args = parser.parse_args()

    stock_path = args.stock.resolve()
    output_path = args.output.resolve()
    manifest_path = args.manifest.resolve()
    verification_path = args.verification.resolve()

    require(stock_path.exists(), f"stock image not found: {stock_path}")
    require(not output_path.exists(), f"refusing to overwrite output: {output_path}")

    stock_data = stock_path.read_bytes()
    require(len(stock_data) == IMAGE_SIZE, "image size mismatch")
    require(
        sha256(stock_data) == STOCK_SHA256,
        f"stock SHA-256 mismatch: expected {STOCK_SHA256}, got {sha256(stock_data)}",
    )

    rom_data = bytearray(stock_data)

    # Inject VcnUnlockDxe into DXE FV WITHOUT touching APCB or PSP
    require(build_vcn_bios.inject_vcn_dxe_into_fv(rom_data), "DXE injection failed")

    candidate_bytes = bytes(rom_data)

    # Validate PSP and APCB are strictly byte-identical
    require(
        candidate_bytes[PSP_START:PSP_END] == stock_data[PSP_START:PSP_END],
        "PSP region modified",
    )
    require(
        candidate_bytes[APCB_START:APCB_END] == stock_data[APCB_START:APCB_END],
        "APCB region modified",
    )

    changed_ranges = ranges(stock_data, candidate_bytes)
    changed_count = sum(int(item["length"]) for item in changed_ranges)

    # Ensure all changes are strictly within DXE region (>= 0xAE0000)
    for item in changed_ranges:
        start_addr = int(str(item["start"]), 16)
        require(
            start_addr >= 0xAE0000, f"change outside DXE region at 0x{start_addr:X}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    verification_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_bytes(candidate_bytes)

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/build_vcn_dxe_only_candidate.py",
        "source": {
            "path": str(stock_path),
            "sha256": sha256(stock_data),
            "size": len(stock_data),
        },
        "output": {
            "path": str(output_path),
            "sha256": sha256(candidate_bytes),
            "size": len(candidate_bytes),
        },
        "transformation": "DXE-region-only VCN unlock (inject VcnUnlockDxe FFS before BDS, no APCB/PSP touch)",
        "changed_byte_count": changed_count,
        "changed_ranges": changed_ranges,
        "checks": {
            "psp_byte_identical_to_stock": True,
            "apcb_byte_identical_to_stock": True,
            "changes_confined_to_dxe": True,
        },
        "classification": "offline DXE-only VCN unlock candidate; hardware unverified",
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    verification = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tool": "scripts/build_vcn_dxe_only_candidate.py [verification]",
        "source_sha256": sha256(stock_data),
        "output_sha256": sha256(candidate_bytes),
        "changed_ranges": changed_ranges,
        "verdict": "PASS",
        "notes": "PSP and APCB byte-identical. Changes strictly confined to DXE region (>= 0xAE0000).",
    }
    verification_path.write_text(
        json.dumps(verification, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(
        json.dumps(
            {
                "output": str(output_path),
                "sha256": sha256(candidate_bytes),
                "changed_bytes": changed_count,
                "changed_ranges_count": len(changed_ranges),
                "verdict": "PASS",
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
