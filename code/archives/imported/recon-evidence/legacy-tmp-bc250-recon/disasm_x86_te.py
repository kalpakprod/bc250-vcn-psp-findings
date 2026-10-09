#!/usr/bin/env python3
"""Linear disassembly of a 32/64-bit UEFI TE image."""
from __future__ import annotations

import argparse
import struct
from pathlib import Path

import pypcode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    data = args.binary.read_bytes()
    if len(data) < 0x28 or data[:2] != b"VZ":
        raise ValueError("input is not a UEFI TE image")
    machine = struct.unpack_from("<H", data, 2)[0]
    arch = "x86:LE:64:default" if machine == 0x8664 else "x86:LE:32:default"
    context = pypcode.Context(arch)
    result = context.disassemble(data, base_address=0, offset=0x28, max_bytes=len(data) - 0x28)
    lines = [f"0x{ins.addr.offset:05x}: {ins.mnem:<9} {ins.body}" for ins in result.instructions]
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"arch={arch} bytes={len(data)} instructions={len(lines)} output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
