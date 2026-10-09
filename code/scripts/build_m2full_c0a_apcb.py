#!/usr/bin/env python3
"""M2-full builder: C0A-stock + verbatim native APCB (board record port).

One variable: the APCB region only (0xAB1000, 1160 -> 2928 bytes).
Source APCB comes byte-verbatim from the board's own pre-M0 capture, whose
internal checksum already verifies. C0A tail after its APCB must be 0xFF
padding (headroom proof). No BHD/PSP/UEFI change.

Conventions follow scripts/build_m2_c0a_memg.py.
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
NAT = (
    sys.argv[2]
    if len(sys.argv) > 2
    else (REPO + "/evidence/programmer/reads/20260916/pre-m0-read-a.bin")
)
DST = (
    sys.argv[3]
    if len(sys.argv) > 3
    else (REPO + "/candidates/BC250_M2full_C0A_APCB-native_v001_from_C0A-stock.bin")
)
SRC_HASH = "bb2cf51df4099a4c4a01c9959c13cfa186f5e59abd2eb04de731670febca8243"
NAT_HASH = "3f836668bc194cfaef230de3ea842828e665608b96f9f50c7d3960615fbea5fd"
APCB = 0xAB1000
APCB_REGION_END = 0xAB2000  # BHD type-96 region: 8 KB, both images

raw = open(SRC, "rb").read()
nat = open(NAT, "rb").read()
assert hashlib.sha256(raw).hexdigest() == SRC_HASH, "C0A source hash mismatch"
assert hashlib.sha256(nat).hexdigest() == NAT_HASH, "native source hash mismatch"
assert raw[APCB : APCB + 4] == b"APCB", "no APCB magic in C0A"
assert nat[APCB : APCB + 4] == b"APCB", "no APCB magic in native"
csize = struct.unpack_from("<I", raw, APCB + 8)[0]
nsize = struct.unpack_from("<I", nat, APCB + 8)[0]
assert csize == 1160, f"unexpected C0A APCB size {csize}"
assert nsize == 2928, f"unexpected native APCB size {nsize}"
assert raw[APCB + 0x10] == apcb_checksum(raw, APCB, csize) == 0x5E, (
    "C0A APCB checksum unexpected"
)
assert nat[APCB + 0x10] == apcb_checksum(nat, APCB, nsize) == 0x32, (
    "native APCB checksum unexpected"
)
tail = raw[APCB + csize : APCB_REGION_END]
assert set(tail) == {0xFF}, f"C0A APCB tail not 0xFF padding: {set(tail)}"
assert APCB + nsize <= APCB_REGION_END, "native APCB overflows BHD region"

out = bytearray(raw)
out[APCB : APCB + nsize] = nat[APCB : APCB + nsize]
# Post-conditions: verbatim port + valid checksum + nothing else touched.
assert bytes(out[APCB : APCB + nsize]) == nat[APCB : APCB + nsize], "port mismatch"
assert out[APCB + 0x10] == apcb_checksum(out, APCB, nsize), "result checksum bad"
assert bytes(out[:APCB]) == raw[:APCB], "bytes before APCB changed"
assert bytes(out[APCB + nsize :]) == raw[APCB + nsize :], "bytes after APCB changed"
open(DST, "wb").write(bytes(out))

print("M2-full built:", DST)
print("src  sha256:", SRC_HASH)
print("dst  sha256:", hashlib.sha256(bytes(out)).hexdigest())
print("changed range: 0x%X-0x%X (%d bytes)" % (APCB, APCB + nsize, nsize))
print("result APCB size/checksum: 0x%X / 0x%02X" % (nsize, out[APCB + 0x10]))
