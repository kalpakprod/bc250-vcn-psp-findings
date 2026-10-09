#!/usr/bin/env python3
"""Dump BC-250 SMU SRAM only when the secure debug path is already open."""
from __future__ import annotations

import os
import sys
from pathlib import Path

LIB = Path(os.environ.get("BC250_SMU_PATH", "/home/OWNER/vcn_unlock/bc250-smu-unlock"))
sys.path.insert(0, str(LIB))

from bc250_smu import Bc250Smu  # noqa: E402


def main() -> int:
    output = sys.argv[1] if len(sys.argv) > 1 else "/home/OWNER/vcn_unlock/smu_sram.bin"
    smu = Bc250Smu(bdf="0000:00:00.0", timeout=5.0)
    try:
        if not smu.alive():
            print("SMU not alive", file=sys.stderr)
            return 2
        if not smu.secure_access_enabled():
            print("secure access closed; refusing to unlock in dump script", file=sys.stderr)
            return 3
        smu.dump_sram(output)
    finally:
        smu.close()
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
