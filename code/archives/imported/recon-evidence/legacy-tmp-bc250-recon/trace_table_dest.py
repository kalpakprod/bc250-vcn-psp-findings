#!/usr/bin/env python3
"""Trace caller and destination of table serialization in AmdNbioGfxARIPei."""
from pathlib import Path

dis_path = Path(r"C:\Users\OWNER\tmp_bc250\recon\disasm_AmdNbioGfxARIPei.txt")
lines = dis_path.read_text(encoding="utf-8", errors="replace").splitlines()

# Search for calls to 0x7340 area, or function boundaries around 0x7000-0x8000
print("=== Function prologue/epilogue around 0x7000 - 0x7600 ===")
for i, line in enumerate(lines):
    if any(addr in line for addr in ["0x72a", "0x72b", "0x72c", "0x72d", "0x72e", "0x72f", "0x74a", "0x74b", "0x74c", "0x74d", "0x74e", "0x74f"]):
        print(f"L{i:5d}: {line}")
