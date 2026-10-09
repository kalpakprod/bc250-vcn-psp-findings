#!/usr/bin/env python3
"""Extract full mapping of offsets [EDX + 0x1xx] to register/ID constants in AmdNbioGfxARIPei."""
from pathlib import Path
import re

dis_path = Path(r"C:\Users\OWNER\tmp_bc250\recon\disasm_AmdNbioGfxARIPei.txt")
lines = dis_path.read_text(encoding="utf-8", errors="replace").splitlines()

# Search between lines 7900 and 8500
records = []
current_const = None

for i in range(7900, 8500):
    line = lines[i]
    m_const = re.search(r"MOV\s+(?:EDX|EAX|ECX|DX|AX|CX),(0x[0-9a-f]+|[0-9]+)", line)
    if m_const and not "ptr" in line:
        current_const = m_const.group(1)
    
    m_offset = re.search(r"MOV\s+AL,byte ptr \[EDX \+ (0x[0-9a-f]+)\]", line)
    if m_offset:
        off = m_offset.group(1)
        records.append((current_const, off, line))

print(f"Extracted {len(records)} mapping entries:")
for c, off, line in records:
    print(f"  Offset in struct: {off}  ->  ID/Param: {c}  (Disasm: {line.strip()})")
