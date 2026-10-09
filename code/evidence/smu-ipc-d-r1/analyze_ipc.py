#!/usr/bin/env python3
"""Bounded, read-only Xtensa scan for the D-R1 IPC call/pointer surface."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pypcode

CALL_TARGETS = {0x10D0, 0x1B514, 0x233E8, 0x246F4}
POINTER_MARKERS = ("0x400000ba8", "0x400000bac", "0x400000bb0")
CALL_RE = re.compile(r"^0x([0-9a-fA-F]+)$")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("binary", type=Path)
    ap.add_argument("--start", type=lambda x: int(x, 0), default=0)
    ap.add_argument("--end", type=lambda x: int(x, 0), default=None)
    args = ap.parse_args()
    data = args.binary.read_bytes()
    end = min(len(data), args.end if args.end is not None else len(data))
    ctx = pypcode.Context("Xtensa:LE:32:default")
    print("# scanner_class=every-byte direct-instruction candidates; not CFG coverage")
    print(f"# scope=0x{args.start:x}..0x{end:x}; omitted=0x{end:x}..0x{len(data):x}; indirect_edges=unresolved")
    print("address\tkind\ttarget_or_marker\tmnemonic\tbody\tbytes")
    for address in range(args.start, end):
        try:
            result = ctx.disassemble(
                data, base_address=address, offset=address, max_instructions=1
            )
        except pypcode.BadDataError:
            continue
        if not result.instructions:
            continue
        ins = result.instructions[0]
        body = ins.body.strip()
        match = CALL_RE.match(body)
        if ins.mnem.lower().startswith("call") and match:
            target = int(match.group(1), 16)
            if target in CALL_TARGETS:
                print(
                    f"0x{address:05x}\tcall\t0x{target:05x}\t{ins.mnem}\t"
                    f"{body}\t{data[address:address + ins.length].hex()}"
                )
        for marker in POINTER_MARKERS:
            if marker in body.lower():
                print(
                    f"0x{address:05x}\tdata-pointer\t{marker}\t{ins.mnem}\t"
                    f"{body}\t{data[address:address + ins.length].hex()}"
                )


if __name__ == "__main__":
    main()
