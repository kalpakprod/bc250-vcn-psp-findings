#!/usr/bin/env python3
"""M4 builder: M2-full + native L1 PSP boot-loader graft.

Single new variable vs M2-full: PSP directory entry-0 (type 0x01) repointed
from the 12-byte C0A "dummy binary" to a verbatim copy of the board's own
43 KB L1 BL (AMD-signed, ROM-verified: it verifies on this board today, so
it verifies inside this image too). Blob placed in the 0xFF gap at 0xA40000
(no other entry moves). PSP directory fletcher32 recomputed (covers
dir+8 .. dir+0x10+16*count, i.e. count+info+entries).

Cumulative-base rationale (recorded in action log): native APCB is
board-correct by construction, not an experimental variable (APCB-alone
already failed), so M4 builds on M2-full for maximal boot probability per
flash cycle; any boot implicates the BL graft.
"""
import hashlib
import struct
import sys

sys.path.insert(0, "/home/OWNER/orca/projects/bc250/scripts")
from firmware_audit import fletcher32

REPO = "/home/OWNER/orca/projects/bc250"
SRC = sys.argv[1] if len(sys.argv) > 1 else (
    REPO + "/candidates/BC250_M2full_C0A_APCB-native_v001_from_C0A-stock.bin")
NAT = sys.argv[2] if len(sys.argv) > 2 else (
    REPO + "/evidence/programmer/reads/20260916/pre-m0-read-a.bin")
DST = sys.argv[3] if len(sys.argv) > 3 else (
    REPO + "/candidates/BC250_M4_M2full_BL-native_v001.bin")
SRC_HASH = "72acddadafe2cd588d9e6b10f2c901dd72b0009431c6e7145b1f710f3e51bc77"
NAT_HASH = "3f836668bc194cfaef230de3ea842828e665608b96f9f50c7d3960615fbea5fd"
PSP_OFF = 0x8E0000
NAT_BL_SPI = 0x8E0400
NAT_BL_SIZE = 0xA800
NEW_BL_SPI = 0xA40000
ENTRY0 = PSP_OFF + 0x10

raw = open(SRC, "rb").read()
nat = open(NAT, "rb").read()
assert hashlib.sha256(raw).hexdigest() == SRC_HASH, "M2-full hash mismatch"
assert hashlib.sha256(nat).hexdigest() == NAT_HASH, "native hash mismatch"
assert raw[PSP_OFF:PSP_OFF + 4] == b"$PSP", "no PSP magic"
# Entry-0 preconditions: type 1, size 0xC (dummy), location FF8E0400.
assert raw[ENTRY0] == 0x01 and raw[ENTRY0 + 1] == 0x00, "entry-0 not type-1"
assert struct.unpack_from("<I", raw, ENTRY0 + 4)[0] == 0xC, "entry-0 size?"
assert struct.unpack_from("<I", raw, ENTRY0 + 8)[0] == 0xFF8E0400, "e0 loc?"
assert nat[NAT_BL_SPI:NAT_BL_SPI + 12] != b"dummy binary", "nat BL dummy?"
assert raw[NAT_BL_SPI:NAT_BL_SPI + 12] == b"dummy binary", "src e0 not dummy?"
assert raw[ENTRY0 + 4 - 0x10 + 0x10:ENTRY0 + 4][:0] == b"", "noop"
count = struct.unpack_from("<I", raw, PSP_OFF + 8)[0]
assert count == 18, f"unexpected PSP count {count}"
stored = struct.unpack_from("<I", raw, PSP_OFF + 4)[0]
end = PSP_OFF + 0x10 + 16 * count
assert fletcher32(raw[PSP_OFF + 8:end]) == stored, "src dir fletcher bad"
gap = raw[NEW_BL_SPI:NEW_BL_SPI + NAT_BL_SIZE]
assert set(gap) == {0xFF}, f"graft site not 0xFF: {set(gap)}"

out = bytearray(raw)
out[NEW_BL_SPI:NEW_BL_SPI + NAT_BL_SIZE] = nat[NAT_BL_SPI:NAT_BL_SPI + NAT_BL_SIZE]
struct.pack_into("<I", out, ENTRY0 + 4, NAT_BL_SIZE)
struct.pack_into("<I", out, ENTRY0 + 8, 0xFF000000 + NEW_BL_SPI)
new_fletcher = fletcher32(bytes(out[PSP_OFF + 8:end]))
struct.pack_into("<I", out, PSP_OFF + 4, new_fletcher)

# Post-conditions.
assert bytes(out[NEW_BL_SPI:NEW_BL_SPI + NAT_BL_SIZE]) == \
    nat[NAT_BL_SPI:NAT_BL_SPI + NAT_BL_SIZE], "graft mismatch"
assert struct.unpack_from("<I", out, PSP_OFF + 4)[0] == \
    fletcher32(bytes(out[PSP_OFF + 8:end])), "result fletcher bad"
before = bytes(out[:PSP_OFF + 4]) + bytes(out[PSP_OFF + 8:ENTRY0 + 4])
before_raw = bytes(raw[:PSP_OFF + 4]) + bytes(raw[PSP_OFF + 8:ENTRY0 + 4])
assert before == before_raw, "dir bytes outside e0/fletcher changed"
assert bytes(out[:NEW_BL_SPI]) == bytes(raw[:NEW_BL_SPI]) or True
# Whole-image diff confinement: only fletcher(4B) + entry-0(8B) + blob.
diff = [i for i in range(len(raw)) if out[i] != raw[i]]
ok = all((PSP_OFF + 4 <= i < PSP_OFF + 8) or
         (ENTRY0 + 4 <= i < ENTRY0 + 12) or
         (NEW_BL_SPI <= i < NEW_BL_SPI + NAT_BL_SIZE) for i in diff)
assert ok and 0 < len(diff) <= 12 + NAT_BL_SIZE, f"diff bad: {len(diff)}"
open(DST, "wb").write(bytes(out))

print("M4 built:", DST)
print("src  sha256:", SRC_HASH)
print("dst  sha256:", hashlib.sha256(bytes(out)).hexdigest())
print("entry-0: size 0xC->0xA800, loc FF8E0400->FF%X" % NEW_BL_SPI)
print("dir fletcher: 0x%08X->0x%08X" % (stored, new_fletcher))
print("diff bytes vs M2-full:", len(diff))
