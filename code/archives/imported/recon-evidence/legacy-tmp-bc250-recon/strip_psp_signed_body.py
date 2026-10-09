#!/usr/bin/env python3
"""Strip a PSP $PS1 header and trailing signature, preserving the signed body."""
from __future__ import annotations

import struct
import sys
from pathlib import Path


def main() -> int:
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    data = source.read_bytes()
    if len(data) < 0x100 or data[0x10:0x14] != b"$PS1":
        raise ValueError("input is not a PSP $PS1 container")
    signature_type = struct.unpack_from("<I", data, 0x34)[0]
    signature_size = 0x100 if signature_type == 0 else 0x200 if signature_type == 2 else 0
    rom_size = struct.unpack_from("<I", data, 0x6C)[0] or len(data)
    if rom_size > len(data) or rom_size < 0x100 + signature_size:
        raise ValueError(f"invalid ROM size 0x{rom_size:x} for {len(data)}-byte input")
    body = data[0x100 : rom_size - signature_size]
    output.write_bytes(body)
    print(
        f"input={len(data)} rom=0x{rom_size:x} signature=0x{signature_size:x} "
        f"body={len(body)} output={output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
