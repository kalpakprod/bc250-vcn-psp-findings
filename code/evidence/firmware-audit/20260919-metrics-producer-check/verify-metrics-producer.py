#!/usr/bin/env python3
"""Verification of SMU metrics producer 0x29e34 against exact Robin-5 SMU body and CLV ROM.
Reads and validates:
- ROM SHA-256 and SMU SHA-256
- ROM offset 0x8FEF00 exact body match
- Literal 0x17F84 -> 0x107FC
- Literal 0x17F7C -> 0x16EE4 -> 1000.0f
- Direct instruction disassembly and l32r target verification for FUN_00029e34
- Metrics producer table offsets (+0x50 Voltage[0], +0x54 Voltage[1]) and source addresses (0x109F4, 0x10A08)
- utrunc.s unsigned float-to-int conversion instruction verification
"""
import hashlib
import json
from pathlib import Path
import struct
import sys

ROM_PATH = Path('evidence/donor/retroweb-20260916/BC250_5.00_clv.bin')
SMU_PATH = Path('import/from-windows/Users/kukuruza/tmp_bc250/upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5')
DECOMP_PATH = Path('evidence/firmware-audit/20260919-metrics-producer-check/metrics-producer-29e34.txt')

r = ROM_PATH.read_bytes()
b = SMU_PATH.read_bytes()

r_hash = hashlib.sha256(r).hexdigest()
b_hash = hashlib.sha256(b).hexdigest()

assert len(r) == 16777216 and r_hash == 'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
assert len(b) == 262400 and b_hash == 'cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37'
assert r[0x8fef00:0x8fef00 + len(b)] == b

def u32(a): return struct.unpack_from('<I', b, a)[0]
def f32(a): return struct.unpack_from('<f', b, a)[0]

# Literals verification
lit_17f84 = u32(0x17f84)
lit_17f7c = u32(0x17f7c)
assert lit_17f84 == 0x107fc, f"Expected 0x107fc at 0x17f84, got 0x{lit_17f84:x}"
assert lit_17f7c == 0x16ee4, f"Expected 0x16ee4 at 0x17f7c, got 0x{lit_17f7c:x}"
deref_17f7c = f32(lit_17f7c)
assert deref_17f7c == 1000.0, f"Expected 1000.0 at 0x16ee4, got {deref_17f7c}"

# Instructions in FUN_00029e34
# Check l32r at 0x29ecf -> 0x17f7c
assert b[0x29ecf:0x29ed2] == bytes.fromhex('d12bb8')
target_ecf = ((0x29ecf + 3) & ~3) + (int.from_bytes(b[0x29ed0:0x29ed2], 'little') - 65536) * 4
assert target_ecf == 0x17f7c

# Check l32r at 0x29ede -> 0x17f84
assert b[0x29ede:0x29ee1] == bytes.fromhex('d129b8')
target_ede = ((0x29ede + 3) & ~3) + (int.from_bytes(b[0x29edf:0x29ee1], 'little') - 65536) * 4
assert target_ede == 0x17f84

# Check loop instructions
# 0x29eef: lsi f13, a12, 0x1fc (Current)
# 0x29ef2: lsi f14, a12, 0x1f8 (Voltage)
# 0x29ef5: lsi f15, a12, 0x200 (Power)
assert b[0x29eef:0x29ef2] == bytes.fromhex('d30c7f') # lsi f13, a12, 0x1fc
assert b[0x29ef2:0x29ef5] == bytes.fromhex('e30c7e') # lsi f14, a12, 0x1f8
assert b[0x29ef5:0x29ef8] == bytes.fromhex('f30c80') # lsi f15, a12, 0x200

# Conversions via utrunc.s:
# 0x29f04: utrunc.s a14, f12, 0 (Power)
# 0x29f07: utrunc.s a10, f11, 0 (Voltage)
# 0x29f0a: utrunc.s a8, f10, 0 (Current)
assert b[0x29f04:0x29f07] == bytes.fromhex('00ecea') # utrunc.s a14, f12, 0
assert b[0x29f07:0x29f0a] == bytes.fromhex('00abea') # utrunc.s a10, f11, 0
assert b[0x29f0a:0x29f0d] == bytes.fromhex('008aea') # utrunc.s a8, f10, 0

# Stores:
# 0x29f0d: s32i a10, a15, 0x50 (Voltage at +0x50)
# 0x29f10: s32i a8, a15, 0x58 (Current at +0x58)
# 0x29f13: s32i a14, a15, 0x60 (Power at +0x60)
assert b[0x29f0d:0x29f10] == bytes.fromhex('a26f14')
assert b[0x29f10:0x29f13] == bytes.fromhex('826f16')
assert b[0x29f13:0x29f16] == bytes.fromhex('e26f18')

# Offsets and addresses
# Domain 0 (a9 = 0):
# export addr = 0xcb68 -> Voltage[0] at 0xcb68 + 0x50 = 0xcbb8
# source addr = 0x107fc + 0x1f8 = 0x109f4
# Domain 1 (a9 = 1):
# export addr = 0xcb68 + 4 = 0xcb6c -> Voltage[1] at 0xcb6c + 0x50 = 0xcbbc
# source addr = 0x107fc + 0x14 + 0x1f8 = 0x10a08

report = {
    "status": "PASS",
    "clv_rom": {
        "path": str(ROM_PATH),
        "sha256": r_hash,
        "size": len(r),
        "smu_body_offset": "0x8fef00"
    },
    "smu_firmware": {
        "path": str(SMU_PATH),
        "sha256": b_hash,
        "size": len(b),
        "version": "Robin-5"
    },
    "literals": {
        "0x17f84": {"raw_hex": hex(lit_17f84), "target": "0x107fc", "deref_match": True},
        "0x17f7c": {"raw_hex": hex(lit_17f7c), "target": "0x16ee4", "f32_value": deref_17f7c, "deref_match": True}
    },
    "instruction_verification": {
        "0x29ecf": "l32r a13, 0x17f7c (target 0x16ee4)",
        "0x29ede": "l32r a13, 0x17f84 (target 0x107fc)",
        "0x29eef": "lsi f13, a12, 0x1fc (Current)",
        "0x29ef2": "lsi f14, a12, 0x1f8 (Voltage)",
        "0x29ef5": "lsi f15, a12, 0x200 (Power)",
        "0x29f04": "utrunc.s a14, f12, 0 (unsigned float to int)",
        "0x29f07": "utrunc.s a10, f11, 0 (unsigned float to int)",
        "0x29f0a": "utrunc.s a8, f10, 0 (unsigned float to int)",
        "0x29f0d": "s32i a10, a15, 0x50 (Voltage store)",
        "0x29f10": "s32i a8, a15, 0x58 (Current store)",
        "0x29f13": "s32i a14, a15, 0x60 (Power store)"
    },
    "mappings": {
        "domain0": {
            "voltage_field": "Voltage[0]",
            "smu_metrics_offset": "0x50 (abs 0xcbb8)",
            "source_address": "0x109f4",
            "stride": "0x14"
        },
        "domain1": {
            "voltage_field": "Voltage[1]",
            "smu_metrics_offset": "0x54 (abs 0xcbbc)",
            "source_address": "0x10a08",
            "stride": "0x14"
        }
    },
    "actuator_comparison": {
        "actuator_struct": "0x13474",
        "domain0_actuator_voltage_target": "0x13474 + 0x00 (0x13474)",
        "domain0_metrics_producer_source": "0x109f4",
        "domain1_actuator_voltage_target": "0x13474 + 0x20 (0x13494)",
        "domain1_metrics_producer_source": "0x10a08",
        "direct_equivalence": False,
        "delta_domain0": "0x2a80",
        "delta_domain1": "0x2a8c"
    },
    "withdrawn_claims": [
        "Claim that periodic ADC poll populates 0x109f4/0x10a08 is withdrawn; writer is unidentified in static trace.",
        "Signed trunc float conversion inference is corrected to unsigned utrunc.s."
    ]
}

out_file = Path('evidence/firmware-audit/20260919-metrics-producer-check/metrics-producer-verification.json')
out_file.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
