#!/usr/bin/env python3
"""Analyze functions in AmdNbioGfxARIPei around offsets 0x23f0, 0x7340, 0x11900."""
from pathlib import Path
import re

dis_path = Path(r"C:\Users\OWNER\tmp_bc250\recon\disasm_AmdNbioGfxARIPei.txt")
lines = dis_path.read_text(encoding="utf-8", errors="replace").splitlines()

ranges = [
    ("Init Config Struct (0x23d0 - 0x2450)", 2990, 3040),
    ("Table serialization 1 (0x7320 - 0x73a0)", 8060, 8120),
    ("Device ID / PCI check (0x118e0 - 0x11960)", 20770, 20830),
]

for label, start, end in ranges:
    print(f"================== {label} ==================")
    for i in range(max(0, start), min(len(lines), end)):
        print(f"L{i:5d}: {lines[i]}")
