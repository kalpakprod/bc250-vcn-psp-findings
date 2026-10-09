#!/usr/bin/env python3
"""Read the guarded VCN MMIO liveness ladder without staging VRAM."""
from __future__ import annotations

import os
import sys
from pathlib import Path

SOURCE = Path(
    os.environ.get(
        "BC250_VCN_SOURCE",
        "/home/OWNER/vcn_unlock/daveconde-bc250-vcn-enable",
    )
)
sys.path.insert(0, str(SOURCE))

import enable_vcn  # noqa: E402

LADDER = (
    ("UVD_PGFSM_CONFIG", 0x0000, 1),
    ("UVD_PGFSM_STATUS", 0x0001, 1),
    ("UVD_POWER_STATUS", 0x0004, 1),
    ("CC_UVD_HARVESTING", 0x0007, 1),
    ("UVD_JPEG_POWER_STATUS", 0x000A, 1),
    ("UVD_MASTINT_EN", 0x0200, 1),
    ("UVD_STATUS", 0x026F, 1),
    ("UVD_VERSION", 0x05C9, 1),
    ("UVD_NO_OP", 0x05BF, 1),
    ("UVD_JPEG_CNTL", 0x0080, 0),
    ("UVD_JRBC_STATUS", 0x0109, 0),
)


def main() -> int:
    direct = enable_vcn.VcnDirect()
    try:
        values = {}
        for name, offset, segment in LADDER:
            mmio = (
                (enable_vcn.VCN_SEG1_DW if segment else enable_vcn.VCN_SEG0_DW)
                + offset
            ) * 4
            value = direct.rd(mmio)
            values[name] = value
            print(f"{name} mmio=0x{mmio:05x} value=0x{value:08x}", flush=True)
        all_ones = all(value == 0xFFFFFFFF for value in values.values())
        print(f"uniform_all_ones={str(all_ones).lower()}", flush=True)
        return 2 if all_ones else 0
    finally:
        direct.rf.close()
        os.close(direct.vram_fd)


if __name__ == "__main__":
    raise SystemExit(main())
