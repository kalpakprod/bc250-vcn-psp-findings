#!/usr/bin/env python3
"""Linear Xtensa disassembly for BC-250 SMU SRAM ranges using pypcode."""
from __future__ import annotations

import argparse
from pathlib import Path

import pypcode


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("start", type=lambda value: int(value, 0))
    parser.add_argument("--size", type=lambda value: int(value, 0), default=0x800)
    parser.add_argument("--stop-after-ret", action="store_true")
    parser.add_argument("--stop-next-entry", action="store_true")
    args = parser.parse_args()

    data = args.binary.read_bytes()
    context = pypcode.Context("Xtensa:LE:32:default")
    result = context.disassemble(
        data,
        base_address=args.start,
        offset=args.start,
        max_bytes=args.size,
    )
    seen_entry = False
    for instruction in result.instructions:
        print(
            f"0x{instruction.addr.offset:05x}: "
            f"{instruction.mnem:<10} {instruction.body}"
        )
        if instruction.mnem.lower() == "entry":
            if seen_entry and args.stop_next_entry:
                break
            seen_entry = True
        if args.stop_after_ret and instruction.mnem.lower().startswith("ret"):
            break


if __name__ == "__main__":
    main()
