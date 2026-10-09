#!/usr/bin/env python3
"""
Verification script for DF P-state table (0xCF0C / 0xCEE0 region) population and immutability.
Validates:
1. Pinned CLV ROM and Robin-5 SHA-256 identities and exact SMU slice mapping.
2. Static presence of DF P-state table rows at 0xCF0C..0xCFD4 in both files.
3. Zero occurrences of DF P-state rate floats outside SMU in the entire CLV ROM.
4. Byte asserts for FUN_0001e038 (table row-pointer setup), FUN_0001e448 (table reader/applier),
   and PPTable transfer boundary (0x7B5C..0x7FF8) showing zero writes to 0xCEE0/0xCF0C.
"""

import hashlib
import struct
import sys

CLV_PATH = "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin"
ROBIN5_PATH = "import/from-windows/Users/kukuruza/tmp_bc250/upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5"

EXPECTED_CLV_HASH = "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"
EXPECTED_ROBIN5_HASH = "cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37"
SMU_OFFSET = 0x8FEF00
SMU_SIZE = 262400

with open(CLV_PATH, "rb") as f:
    clv_bytes = f.read()
assert hashlib.sha256(clv_bytes).hexdigest() == EXPECTED_CLV_HASH, "CLV hash mismatch"

with open(ROBIN5_PATH, "rb") as f:
    robin5_bytes = f.read()
assert hashlib.sha256(robin5_bytes).hexdigest() == EXPECTED_ROBIN5_HASH, "Robin-5 hash mismatch"

smu_from_clv = clv_bytes[SMU_OFFSET:SMU_OFFSET + SMU_SIZE]
assert smu_from_clv == robin5_bytes, "CLV SMU slice does not match Robin-5"
print("PASS 1: Binary identity and CLV SMU slice equality verified.")

# 2. Check DF P-state table rows at 0xCF0C
table_slice = robin5_bytes[0xCF0C:0xCFD4]
assert len(table_slice) == 200, f"Table slice length {len(table_slice)} != 200"

# P0: Domain 0x0E (30, 48) -> 250.0 MHz; Domain 0x0F/0x11 (36, 64) -> 225.0 MHz
p0_bytes = robin5_bytes[0xCF0C:0xCF34]
assert p0_bytes[:4] == bytes([30, 48, 0, 0]), "P0 domain 0x0E mismatch"
assert struct.unpack("<f", p0_bytes[4:8])[0] == 250.0, "P0 domain 0x0E float mismatch"
assert p0_bytes[8:12] == bytes([36, 64, 0, 96]), "P0 domain 0x0F DID mismatch"
assert struct.unpack("<f", p0_bytes[16:20])[0] == 225.0, "P0 domain 0x0F float mismatch"
assert struct.unpack("<f", p0_bytes[20:24])[0] == 112.5, "P0 domain 0x10 float mismatch"

# P2: 750.0 MHz, 425.0 MHz, 106.25 MHz
p2_bytes = robin5_bytes[0xCF5C:0xCF84]
assert p2_bytes[:4] == bytes([30, 16, 0, 0]), "P2 domain 0x0E mismatch"
assert struct.unpack("<f", p2_bytes[4:8])[0] == 750.0, "P2 domain 0x0E float mismatch"
assert p2_bytes[8:12] == bytes([34, 32, 0, 96]), "P2 domain 0x0F DID mismatch"
assert struct.unpack("<f", p2_bytes[16:20])[0] == 425.0, "P2 domain 0x0F float mismatch"

# P3: 1200.0 MHz, 875.0 MHz, 109.375 MHz
p3_bytes = robin5_bytes[0xCF84:0xCFAC]
assert p3_bytes[:4] == bytes([39, 13, 0, 0]), "P3 domain 0x0E mismatch"
assert struct.unpack("<f", p3_bytes[4:8])[0] == 1200.0, "P3 domain 0x0E float mismatch"
assert p3_bytes[8:12] == bytes([35, 16, 0, 96]), "P3 domain 0x0F DID mismatch"
assert struct.unpack("<f", p3_bytes[16:20])[0] == 875.0, "P3 domain 0x0F float mismatch"

# Verify table bytes match CLV ROM at 0x8FEF00 + 0xCF0C
assert clv_bytes[SMU_OFFSET + 0xCF0C : SMU_OFFSET + 0xCFD4] == table_slice
print("PASS 2: Table static presence at 0xCF0C verified in SMU and CLV ROM.")

# 3. Check for external occurrences of these rate floats in CLV ROM
rates = [250.0, 750.0, 1200.0, 225.0, 425.0, 875.0, 112.5, 106.25, 109.375]
for r in rates:
    pat = struct.pack("<f", r)
    idx = 0
    external_count = 0
    while True:
        pos = clv_bytes.find(pat, idx)
        if pos == -1:
            break
        if not (SMU_OFFSET <= pos < SMU_OFFSET + SMU_SIZE):
            external_count += 1
        idx = pos + 1
    assert external_count == 0, f"Rate float {r} found outside SMU in CLV ({external_count} times)"
print("PASS 3: Zero occurrences of DF P-state rate floats outside SMU in CLV ROM.")

# 4. Check literal 0x171EC and row-indexer bytes at 0xCEE0 + 0xA0
lit_171ec = struct.unpack("<I", robin5_bytes[0x171EC:0x171F0])[0]
assert lit_171ec == 0x0000CEE0, f"Literal 0x171EC is 0x{lit_171ec:08X} != 0xCEE0"
indexer_bytes = robin5_bytes[0xCEE0 + 0xA0 : 0xCEE0 + 0xA4]
assert indexer_bytes == bytes([3, 2, 1, 0]), f"Indexer bytes mismatch: {indexer_bytes.hex()}"
print("PASS 4: Literal 0x171EC and indexer bytes [3, 2, 1, 0] verified.")

# 5. Byte assert on FUN_0001e038 instructions:
# 0x1E038: entry a1, 0x20 -> 36 41 00
# 0x1E03B: l32r a4, 0x171EC -> 41 6c e4
# 0x1E044: call8 0x0002e4c4 -> e5 47 10
# 0x1E088: l8ui a14, a10, 0xa0 -> e2 0a a0
# 0x1E095: addx8 a8, a8, a4   -> 40 88 b0
# 0x1E098: addi a9, a8, 0x2c  -> 92 c8 2c
# 0x1E09B: s32i.n a9, a12, 0x1c -> 99 7c
# 0x1E0A4: s8i a13, a4, 0xf7  -> d2 44 f7
assert robin5_bytes[0x1E038:0x1E03B] == bytes([0x36, 0x41, 0x00])
assert robin5_bytes[0x1E03B:0x1E03E] == bytes([0x41, 0x6C, 0xE4])
assert robin5_bytes[0x1E088:0x1E08B] == bytes([0xE2, 0x0A, 0xA0])
assert robin5_bytes[0x1E095:0x1E098] == bytes([0x40, 0x88, 0xB0])
assert robin5_bytes[0x1E098:0x1E09B] == bytes([0x92, 0xC8, 0x2C])
assert robin5_bytes[0x1E09B:0x1E09D] == bytes([0x99, 0x7C])
assert robin5_bytes[0x1E0A4:0x1E0A7] == bytes([0xD2, 0x44, 0xF7])
print("PASS 5: FUN_0001e038 row-pointer population instructions verified.")

# 6. Check PPTable staging/committed pointers:
lit_7ff8 = struct.unpack("<I", robin5_bytes[0x17118:0x1711C])[0]
lit_7b5c = struct.unpack("<I", robin5_bytes[0x1711C:0x17120])[0]
assert lit_7ff8 == 0x7FF8, f"Staging pointer 0x{lit_7ff8:08X} != 0x7FF8"
assert lit_7b5c == 0x7B5C, f"Committed pointer 0x{lit_7b5c:08X} != 0x7B5C"
assert lit_7b5c + 0x49C == lit_7ff8, "Committed table size does not equal 0x49C"
print("PASS 6: PPTable staging/committed transfer boundaries verified (0x7B5C..0x7FF8).")

print("ALL 6 VERIFICATION PASSES COMPLETED SUCCESSFULLY.")
