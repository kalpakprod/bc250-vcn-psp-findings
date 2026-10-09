#!/usr/bin/env python3
"""Targeted extraction of AmdNbioGfxARIPei disasm around key functions."""
from pathlib import Path
import re

dis_path = Path(r"C:\Users\OWNER\tmp_bc250\recon\disasm_AmdNbioGfxARIPei.txt")
if not dis_path.exists():
    print("Disasm not found")
    raise SystemExit(1)

lines = dis_path.read_text(encoding="utf-8", errors="replace").splitlines()
print(f"Total lines: {len(lines)}")

keywords = ["13fe", "vcn", "0x2403000", "0x240", "gasket", "harvest", "isolate", "enable"]

hits = {}
for i, line in enumerate(lines):
    lower = line.lower()
    for kw in ["13fe", "0x2403000", "0x02403000", "0x7800", "0x7e00", "0x1e0", "0x1e1"]:
        if kw in lower:
            hits.setdefault(kw, []).append((i, line))

for kw, items in hits.items():
    print(f"\n=== KEYWORD: {kw} (count={len(items)}) ===")
    for idx, text in items[:10]:
        print(f"  L{idx:5d}: {text}")
        # Print window around it
        start = max(0, idx - 4)
        end = min(len(lines), idx + 6)
        for j in range(start, end):
            prefix = ">>>" if j == idx else "   "
            print(f"    {prefix} L{j:5d}: {lines[j]}")
