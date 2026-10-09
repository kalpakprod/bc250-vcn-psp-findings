#!/usr/bin/env python3
"""M6 builder: pre-m0 + verbatim M4 PSP region (definitive C0A-PSP test).

Transplant (from M4, byte-verbatim): 0x8E0000-0xAB1000 (PSP directory +
all bodies incl. the BL graft at 0xA40000 + BHD directory). Everything
else stays the board's own pre-m0 bytes (native PEI/DXE/NVRAM/APCB).
If M6 boots, the C0A PSP stack runs on BC250. If silent, it is dead
with a fully-native rest as witness.
"""
import hashlib
import sys

REPO = "/home/OWNER/orca/projects/bc250"
SRC = sys.argv[1] if len(sys.argv) > 1 else (
    REPO + "/evidence/programmer/reads/20260916/pre-m0-read-a.bin")
M4 = sys.argv[2] if len(sys.argv) > 2 else (
    REPO + "/candidates/BC250_M4_M2full_BL-native_v001.bin")
DST = sys.argv[3] if len(sys.argv) > 3 else (
    REPO + "/candidates/BC250_M6_native_M4PSP_v001.bin")
SRC_HASH = "3f836668bc194cfaef230de3ea842828e665608b96f9f50c7d3960615fbea5fd"
M4_HASH = "856af24bceb04ef06da34c82e906570147c4c207da3ee9d785233435981a47a3"
LO, HI = 0x8E0000, 0xAB1000

raw = open(SRC, "rb").read()
m4 = open(M4, "rb").read()
assert hashlib.sha256(raw).hexdigest() == SRC_HASH, "pre-m0 hash mismatch"
assert hashlib.sha256(m4).hexdigest() == M4_HASH, "M4 hash mismatch"
assert len(raw) == len(m4) == 0x1000000, "size mismatch"
assert raw[0x8E0000:0x8E0004] == b"$PSP", "no PSP magic in base"
assert m4[0x8E0000:0x8E0004] == b"$PSP", "no PSP magic in M4"
assert raw[0xAB0000:0xAB0004] == b"$BHD", "no BHD magic in base"
assert m4[0xAB0000:0xAB0004] == b"$BHD", "no BHD magic in M4"

out = bytearray(raw)
out[LO:HI] = m4[LO:HI]

assert bytes(out[LO:HI]) == m4[LO:HI], "transplant mismatch"
assert bytes(out[:LO]) == raw[:LO], "bytes before range changed"
assert bytes(out[HI:]) == raw[HI:], "bytes after range changed"
diff = [i for i in range(len(raw)) if out[i] != raw[i]]
assert diff and all(LO <= i < HI for i in diff), "diff escaped range"
open(DST, "wb").write(bytes(out))

print("M6 built:", DST)
print("src  sha256:", SRC_HASH)
print("dst  sha256:", hashlib.sha256(bytes(out)).hexdigest())
print("range: %#x-%#x" % (LO, HI))
print("diff bytes vs pre-m0:", len(diff))
