#!/usr/bin/env python3
"""Find decodable Xtensa direct-call instructions targeting selected addresses."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pypcode

CALL_RE = re.compile(r"^0x([0-9a-fA-F]+)$")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("targets", nargs="+", type=lambda value: int(value, 0))
    parser.add_argument("--start", type=lambda value: int(value, 0), default=0)
    parser.add_argument("--end", type=lambda value: int(value, 0), default=None)
    args = parser.parse_args()

    data = args.binary.read_bytes()
    end = len(data) if args.end is None else min(args.end, len(data))
    targets = set(args.targets)
    context = pypcode.Context("Xtensa:LE:32:default")
    for address in range(args.start, end):
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
        if not instruction.mnem.lower().startswith("call"):
            continue
        match = CALL_RE.match(instruction.body.strip())
        if not match:
            continue
        target = int(match.group(1), 16)
        if target in targets:
            print(
                f"0x{address:05x}: {instruction.mnem} 0x{target:05x} "
                f"bytes={data[address:address + instruction.length].hex()}"
            )


if __name__ == "__main__":
    main()
