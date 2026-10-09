#!/usr/bin/env python3
"""Compare live SMU power-domain blocks and rank domain-6-specific fields."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


def fmt(value: int | None) -> str:
    return "None" if value is None else f"{value:08x}"


def main() -> None:
    path = Path(sys.argv[1])
    data = json.loads(path.read_text(encoding="utf-8"))
    domains = data["domains"]
    rows = []
    for index in range(0x200 // 4):
        offset = index * 4
        values = [domains[str(domain)]["words"][index] for domain in range(8)]
        active = values[:6]
        common = Counter(active).most_common(1)[0]
        dom6 = values[6]
        dom7 = values[7]
        if dom6 is None:
            continue
        score = 0
        reasons = []
        if dom6 == dom7 and dom6 != common[0]:
            score += 4
            reasons.append("dom6==dom7!=active-mode")
        if dom6 not in active:
            score += 3
            reasons.append("dom6-unique-vs-0..5")
        if common[1] >= 4 and dom6 != common[0]:
            score += 2
            reasons.append(f"active-consensus={common[1]}/6")
        if dom6 != 0:
            score += 1
            reasons.append("nonzero")
        if score:
            rows.append((score, offset, values, reasons))

    rows.sort(key=lambda row: (-row[0], row[1]))
    print("domain block bases/states:")
    for domain in range(8):
        info = domains[str(domain)]
        print(
            f"  dom{domain}: block=0x{info['block_base']:06x} "
            f"state=0x{info['state']:02x}"
        )
    print("\nranked domain-6-specific offsets:")
    print("offset  d0       d1       d2       d3       d4       d5       d6       d7       reasons")
    for score, offset, values, reasons in rows[:80]:
        print(
            f"+0x{offset:03x} "
            + " ".join(fmt(value) for value in values)
            + f"  score={score} {';'.join(reasons)}"
        )


if __name__ == "__main__":
    main()
