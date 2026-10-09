#!/usr/bin/env python3
"""M5 builder: M4 + verbatim native NVRAM FV + native PEI FV.

Transplants (from pre-m0, byte-verbatim, layouts proven identical):
  R1  0x000000-0x020000  NVRAM FV (AmdSetup/Setup NVARs + VSS store)
  R2  0xE00000-0x100000  PEI FV (SEC, reset vector, PEI core, inner FV)
Keeps from M4: PSP dir + BL graft, BHD dir, APCB, DXE FV.
Conventions follow scripts/build_m2full_c0a_apcb.py.
"""
import hashlib
import struct
import sys

REPO = "/home/OWNER/orca/projects/bc250"
SRC = sys.argv[1] if len(sys.argv) > 1 else (
    REPO + "/candidates/BC250_M4_M2full_BL-native_v001.bin")
NAT = sys.argv[2] if len(sys.argv) > 2 else (
    REPO + "/evidence/programmer/reads/20260916/pre-m0-read-a.bin")
DST = sys.argv[3] if len(sys.argv) > 3 else (
    REPO + "/candidates/BC250_M5_M4_PEI-native_v001.bin")
SRC_HASH = "856af24bceb04ef06da34c82e906570147c4c207da3ee9d785233435981a47a3"
NAT_HASH = "3f836668bc194cfaef230de3ea842828e665608b96f9f50c7d3960615fbea5fd"
RANGES = [(0x0, 0x20000), (0xE00000, 0x1000000)]
FVHS = [(0x0, 0x20000), (0xE00000, 0x200000), (0xE02000, 0x1FE000)]


def check_fv(d, tag):
    for base, ln in FVHS:
        assert d[base + 0x28:base + 0x2C] == b"_FVH", f"{tag} FVH @{base:#x}"
        assert struct.unpack_from("<Q", d, base + 0x20)[0] == ln, \
            f"{tag} FV len @{base:#x}"


raw = open(SRC, "rb").read()
nat = open(NAT, "rb").read()
assert hashlib.sha256(raw).hexdigest() == SRC_HASH, "M4 hash mismatch"
assert hashlib.sha256(nat).hexdigest() == NAT_HASH, "native hash mismatch"
assert len(raw) == len(nat) == 0x1000000, "size mismatch"
check_fv(raw, "M4")
check_fv(nat, "NAT")
# NVRAM precondition: native HAS AmdSetup NVAR, M4 (C0A NVRAM) does not.
assert nat[0x4BB:0x4BB + 4] == b"NVAR", "no native AmdSetup NVAR"
assert nat[0x4C6:0x4C6 + 9] == b"AmdSetup\x00", "native AmdSetup name?"
assert raw[0x4BB:0x4BB + 4] != b"NVAR", "M4 unexpectedly has NVAR@0x4BB"

out = bytearray(raw)
for lo, hi in RANGES:
    out[lo:hi] = nat[lo:hi]

# Post-conditions: transplanted ranges == native, rest == M4.
for lo, hi in RANGES:
    assert bytes(out[lo:hi]) == nat[lo:hi], f"range {lo:#x} mismatch"
mid = bytes(out[0x20000:0xE00000])
assert mid == raw[0x20000:0xE00000], "middle region changed"
diff = [i for i in range(len(raw)) if out[i] != raw[i]]
ok = all((0x0 <= i < 0x20000) or (0xE00000 <= i < 0x1000000) for i in diff)
assert ok and diff, "diff escaped transplant ranges"
open(DST, "wb").write(bytes(out))

print("M5 built:", DST)
print("src  sha256:", SRC_HASH)
print("dst  sha256:", hashlib.sha256(bytes(out)).hexdigest())
print("ranges:", " ".join(f"{lo:#x}-{hi:#x}" for lo, hi in RANGES))
print("diff bytes vs M4:", len(diff))
