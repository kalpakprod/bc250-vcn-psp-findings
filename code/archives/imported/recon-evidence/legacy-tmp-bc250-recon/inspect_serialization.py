#!/usr/bin/env python3
"""Detailed look at table emission around 0x7300-0x7400 in AmdNbioGfxARIPei."""
from pathlib import Path

dis_path = Path(r"C:\Users\OWNER\tmp_bc250\recon\disasm_AmdNbioGfxARIPei.txt")
lines = dis_path.read_text(encoding="utf-8", errors="replace").splitlines()

# Search for the IDs loaded around line 8050 - 8150
print("=== Table serialization window (lines 8050 to 8150) ===")
for i in range(8050, min(len(lines), 8150)):
    print(f"L{i:5d}: {lines[i]}")
