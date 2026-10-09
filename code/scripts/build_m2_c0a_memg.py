#!/usr/bin/env python3
"""M2 builder: C0A-stock + BC250 MEMG channel bits + APCB checksum fix.

Reuses apcb_checksum() from scripts/build_apcb_dfg_candidate.py.
One variable: 4 MEMG bytes (2 per channel block, inst-7/8).
"""

import hashlib
import struct
import sys

sys.path.insert(0, "/home/OWNER/orca/projects/bc250/scripts")
from build_apcb_dfg_candidate import apcb_checksum

REPO = "/home/OWNER/orca/projects/bc250"
SRC = (
    sys.argv[1]
    if len(sys.argv) > 1
    else (
        REPO
        + "/archives/imported/firmware-workbench/legacy-tmp-bc250-firmware/4700S/C0A/C0A"
    )
)
DST = (
    sys.argv[2]
    if len(sys.argv) > 2
    else (REPO + "/candidates/BC250_M2_C0A_MEMG_BC250_v001_from_C0A-stock.bin")
)
SRC_HASH = "bb2cf51df4099a4c4a01c9959c13cfa186f5e59abd2eb04de731670febca8243"
APCB = 0xAB1000
# (absolute offset, expected old, new) — from Phase-2 byte diff
EDITS = [
    (0xAB1221, 0x00, 0x01),
    (0xAB1223, 0x00, 0x20),
    (0xAB12CD, 0x00, 0x01),
    (0xAB12CF, 0x00, 0x20),
]

raw = open(SRC, "rb").read()
assert hashlib.sha256(raw).hexdigest() == SRC_HASH, "source hash mismatch"
assert raw[APCB : APCB + 4] == b"APCB", "no APCB magic"
size = struct.unpack_from("<I", raw, APCB + 8)[0]
assert size == 1160, f"unexpected APCB size {size}"
assert raw[APCB + 0x10] == apcb_checksum(raw, APCB, size) == 0x5E, (
    "stock checksum unexpected"
)
for off, old, _ in EDITS:
    assert raw[off] == old, f"precondition failed at {off:#x}"

out = bytearray(raw)
for off, _, new in EDITS:
    out[off] = new
out[APCB + 0x10] = apcb_checksum(out, APCB, size)
open(DST, "wb").write(bytes(out))
print("M2 built:", DST)
print("sha256:", hashlib.sha256(bytes(out)).hexdigest())
print("new APCB checksum byte: 0x%02X" % out[APCB + 0x10])
