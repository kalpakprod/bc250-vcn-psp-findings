#!/usr/bin/env python3
"""Execute the true native VCN power-up function (0x24764) inside SMU firmware."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

LIB = Path(os.environ.get("BC250_SMU_PATH", "/home/OWNER/vcn_unlock/bc250-smu-unlock"))
sys.path.insert(0, str(LIB))

from bc250_smu import Bc250Smu, SmuTimeout  # noqa: E402
from bc250_smu.primitives import alloc_page, free_page  # noqa: E402

THUNK_ADDR = 0x3FF00
HANDLER_SLOT = 0x776C  # Q3 msg 0x61

# 12-byte Xtensa thunk: call8 0x24764; retw.n
#   entry   a1, 0x20        (36 41 00)
#   call8   0x24764         (e5 27 00) -> 0x3ff03 + 8 + (0x27e5 << 2) = 0x3ff0b + 0x9f94 = 0x49ea0 WRONG offset!
# Let's calculate relative call8 offset exactly:
# Target: 0x24764. Call site: 0x3ff03. Next instruction: 0x3ff06 (aligned to 4: 0x3ff08).
# offset = (0x24764 - 0x3ff08) // 4 = -0x1b7a4 // 4 = -0x6de9 = 0xffff9217 (18-bit signed)
# Let's use pypcode to assemble or construct the instruction safely.
