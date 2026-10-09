#!/usr/bin/env python3
"""Linear ARM32 disassembly for PSP firmware bodies."""
from __future__ import annotations

import argparse
from pathlib import Path

import pypcode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--base", type=lambda value: int(value, 0), default=0)
    parser.add_argument("--start", type=lambda value: int(value, 0), default=0)
    parser.add_argument("--size", type=lambda value: int(value, 0), default=None)
    args = parser.parse_args()

    data = args.binary.read_bytes()
    size = len(data) - args.start if args.size is None else min(args.size, len(data) - args.start)
    result = pypcode.Context("ARM:LE:32:v8").disassemble(
        data,
        base_address=args.base,
        offset=args.start,
        max_bytes=size,
    )
    lines = [f"0x{ins.addr.offset:08x}: {ins.mnem:<10} {ins.body}" for ins in result.instructions]
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"bytes={len(data)} start=0x{args.start:x} instructions={len(lines)} output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
