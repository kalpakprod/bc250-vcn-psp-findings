#!/usr/bin/env python3
"""Find decodable Xtensa entry instructions in a binary address range."""
from __future__ import annotations

import argparse
from pathlib import Path

import pypcode


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("start", type=lambda value: int(value, 0))
    parser.add_argument("end", type=lambda value: int(value, 0))
    args = parser.parse_args()

    data = args.binary.read_bytes()
    context = pypcode.Context("Xtensa:LE:32:default")
    for address in range(args.start, args.end):
        try:
            result = context.disassemble(
                data,
                base_address=address,
                offset=address,
                max_instructions=1,
            )
        except pypcode.BadDataError:
            continue
        if not result.instructions:
            continue
        instruction = result.instructions[0]
        if instruction.mnem.lower() == "entry":
            print(f"0x{address:05x}: {instruction.mnem} {instruction.body}")


if __name__ == "__main__":
    main()
