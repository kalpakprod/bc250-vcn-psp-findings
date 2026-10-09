#!/usr/bin/env python3
"""Clear only VRAM spans that this session selected as previously zero VCN staging areas."""
from __future__ import annotations

import os

VRAM = os.environ.get("BC250_VRAM", "/sys/kernel/debug/dri/1/amdgpu_vram")
SPAN = 1_077_248
OFFSETS = (0x00A00000, 0x00C00000, 0x00E00000)
CHUNK = 1024 * 1024


def main() -> None:
    zero = bytes(CHUNK)
    with open(VRAM, "r+b", buffering=0) as file:
        for base in OFFSETS:
            file.seek(base)
            remaining = SPAN
            while remaining:
                size = min(CHUNK, remaining)
                file.write(zero[:size])
                remaining -= size
            file.flush()
            file.seek(base)
            data = file.read(SPAN)
            nonzero = sum(bool(byte) for byte in data)
            print(f"offset=0x{base:08x} size={SPAN} nonzero_after={nonzero}")
            if nonzero:
                raise RuntimeError(f"VRAM clear verification failed at 0x{base:x}")


if __name__ == "__main__":
    main()
