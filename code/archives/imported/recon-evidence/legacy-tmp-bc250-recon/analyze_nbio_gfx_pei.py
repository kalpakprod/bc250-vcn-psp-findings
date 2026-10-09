#!/usr/bin/env python3
"""Detailed x86 disassembly and cross-reference analysis of AmdNbioGfxARIPei."""
from __future__ import annotations

import re
import struct
import sys
from pathlib import Path

import pypcode

PATH = Path(
    r"C:\Users\OWNER\tmp_bc250\recon\robin3_uefi\BIOS.bin.dump\0 61C0F511-A691-4F54-974F-B9A42172CE53\21 AmdNbioGfxARIPei\1 TE image section\body.bin"
)


def main() -> None:
    data = PATH.read_bytes()
    ctx = pypcode.Context("x86:LE:32:default")
    # disassemble from offset 0x28 (code start after TE header)
    result = ctx.disassemble(data, base_address=0, offset=0x28, max_bytes=len(data) - 0x28)
    lines = []
    for ins in result.instructions:
        line = f"0x{ins.addr.offset:04x}: {ins.mnem:<8} {ins.body}"
        lines.append(line)

    out = Path(r"C:\Users\OWNER\tmp_bc250\recon\disasm_AmdNbioGfxARIPei.txt")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out} ({len(lines)} instructions)")

    # Print instructions containing immediate constants of interest
    keywords = ["13fe", "1002", "0x240", "0x3b1", "0x1e00", "0x7800", "0x7e00", "0x170b", "0x1720"]
    for l in lines:
        if any(k in l.lower() for k in keywords):
            print(" ", l)


if __name__ == "__main__":
    main()
