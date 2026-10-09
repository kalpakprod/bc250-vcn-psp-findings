#!/usr/bin/env python3
"""Build the SPI serve-map for the Pico 2 TOCTOU rig (lane V7').

Answers, for our patched candidate (91de01eb...) vs stock 5.00 CLV: which SPI
address ranges DIFFER (the rig must be able to serve either image there), and
which PSP entries the ROM anchor-check must still see ORIGINAL (key-carrying
ranges). Output: evidence JSON + the range table the Pico firmware consumes.

Read-only; evidence: evidence/firmware-audit/20260923-toctou-serve-map/.
"""

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from firmware_audit import parse_psp

ROOT = Path(__file__).resolve().parent.parent
STOCK = ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin"
CAND = ROOT / "candidates/BC250_5.00_clv_VcnUnlock_GlitchSigned_v001.bin"
EVID = ROOT / "evidence/firmware-audit/20260923-toctou-serve-map"

STOCK_SHA = "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"
CAND_SHA = "91de01eb7cb8e97014294adc8692eb8be66c3f95ce8481c234805544c0ddd517"
MERGE_GAP = 64  # bytes: gaps smaller than this merge into one served range


def diff_ranges(a: bytes, b: bytes) -> list[tuple[int, int]]:
    diffs = (i for i in range(min(len(a), len(b))) if a[i] != b[i])
    ranges: list[list[int]] = []
    for i in diffs:
        if ranges and i - ranges[-1][1] <= MERGE_GAP:
            ranges[-1][1] = i
        else:
            ranges.append([i, i])
    return [(r[0], r[1] + 1) for r in ranges]


def main() -> int:
    stock = STOCK.read_bytes()
    cand = CAND.read_bytes()
    assert hashlib.sha256(stock).hexdigest() == STOCK_SHA
    assert hashlib.sha256(cand).hexdigest() == CAND_SHA

    ranges = diff_ranges(stock, cand)

    # per-PSP-entry verdict: which entries the two images disagree on
    sp = parse_psp(stock, 0x8E0000)
    cp = parse_psp(cand, 0x8E0000)
    entries = []
    for se, ce in zip(sp["entries"], cp["entries"]):
        sb = stock[se["spi_offset"] : se["spi_offset"] + se["size"]]
        cb = cand[ce["spi_offset"] : ce["spi_offset"] + ce["size"]]
        same = sb == cb
        entries.append(
            {
                "type": hex(se["type"]),
                "spi": hex(se["spi_offset"]),
                "size": se["size"],
                "identical": same,
                # key-carrying entries: the ROM anchor covers the root key chain,
                # so the rig must serve ORIGINAL for their anchor-check reads.
                "anchor_sensitive": se["type"] in (0x09, 0x4F, 0x50, 0x51),
            }
        )

    anchor_ranges = [
        [r[0], r[1]]
        for r in ranges
        if any(
            e["anchor_sensitive"]
            and not e["identical"]
            and int(e["spi"], 16) < r[1]
            and int(e["spi"], 16) + e["size"] > r[0]
            for e in entries
        )
    ]

    out = {
        "scope": "serve-map for Pico 2 TOCTOU rig; stock vs glitch-signed candidate",
        "stock_sha256": STOCK_SHA,
        "candidate_sha256": CAND_SHA,
        "changed_ranges": [[hex(a), hex(b)] for a, b in ranges],
        "changed_total_bytes": sum(b - a for a, b in ranges),
        "psp_entries": entries,
        "anchor_check_serve_original_ranges": [
            [hex(a), hex(b)] for a, b in anchor_ranges
        ],
        "rig_semantics": [
            "default serve: PATCHED candidate",
            f"serve ORIGINAL for reads inside {len(anchor_ranges)} anchor ranges "
            "(key-carrying entries; exact window/order tuned at session time — "
            "the PT article found 'patched first' on their dump; our rig keeps "
            "both orders configurable)",
            "all other reads: either image (identical bytes)",
        ],
        "sources": ["docs/research/2026-09-23-habr-pamdora-toctou.md"],
    }
    EVID.mkdir(parents=True, exist_ok=True)
    (EVID / "serve-map.json").write_text(json.dumps(out, indent=2) + "\n")

    print(f"changed ranges: {len(ranges)}, bytes: {out['changed_total_bytes']}")
    for a, b in ranges[:12]:
        print(f"  {hex(a)}..{hex(b)}")
    print("anchor-check serve-ORIGINAL ranges:")
    for a, b in anchor_ranges:
        print(f"  {hex(a)}..{hex(b)}")
    print("entries differing stock vs candidate:")
    for e in entries:
        if not e["identical"]:
            print(f"  type {e['type']} @ {e['spi']} ({e['size']} B)")
    return 0


if __name__ == "__main__":
    main()
