#!/usr/bin/env python3
"""Independent deterministic byte & arithmetic verification of SMU metrics producer 0x29E34,
literal 0x17F88, table base calculation, telemetry source array 0x107FC+0x1F8,
actuator state struct 0x13474, and telemetry master pointer table 0x15380-0x153B8.
"""
import hashlib
import json
from pathlib import Path
import struct
import sys

ROM_PATH = Path('evidence/donor/retroweb-20260916/BC250_5.00_clv.bin')
SMU_PATH = Path('import/from-windows/Users/kukuruza/tmp_bc250/upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5')

r = ROM_PATH.read_bytes()
b = SMU_PATH.read_bytes()

r_hash = hashlib.sha256(r).hexdigest()
b_hash = hashlib.sha256(b).hexdigest()

assert len(r) == 16777216, f"ROM size mismatch: {len(r)}"
assert r_hash == 'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8', f"ROM hash mismatch: {r_hash}"
assert len(b) == 262400, f"SMU size mismatch: {len(b)}"
assert b_hash == 'cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37', f"SMU hash mismatch: {b_hash}"
assert r[0x8fef00:0x8fef00 + len(b)] == b, "SMU body at ROM offset 0x8fef00 does not match standalone SMU binary"

def u32(a): return struct.unpack_from('<I', b, a)[0]
def f32(a): return struct.unpack_from('<f', b, a)[0]

# 1. Literals check
lit_17f88 = u32(0x17f88)
lit_17f84 = u32(0x17f84)
lit_17f7c = u32(0x17f7c)
lit_17124 = u32(0x17124) # Actuator state struct pointer

assert lit_17f88 == 0xca68, f"Expected 0xca68 at 0x17f88, got 0x{lit_17f88:x}"
assert lit_17f84 == 0x107fc, f"Expected 0x107fc at 0x17f84, got 0x{lit_17f84:x}"
assert lit_17f7c == 0x16ee4, f"Expected 0x16ee4 at 0x17f7c, got 0x{lit_17f7c:x}"
assert f32(lit_17f7c) == 1000.0, f"Expected 1000.0f at 0x16ee4, got {f32(lit_17f7c)}"
assert lit_17124 == 0x13474, f"Expected 0x13474 at 0x17124, got 0x{lit_17124:x}"

# 2. Table base calculation in FUN_00029E34
# Instruction at 0x29e3d: l32r a4, 0x17f88 (a4 = 0xca68)
# Instruction at 0x29e46: addmi a2, a4, 0x100 (a2 = 0xca68 + 0x100 = 0xcb68)
table_wrapper_base = lit_17f88 # 0xca68
table_export_base = table_wrapper_base + 0x100 # 0xcb68
assert table_export_base == 0xcb68

# Instructions in loop at 0x29ee1-0x29f16:
# 2 iterations: a9 in [0, 1]
# Stride arithmetic:
# a15 = a9 * 4 + a2 (export destination base)
# a12 = (a9 * 4 + a9) * 4 + a13 = (5 * a9) * 4 + a13 = a9 * 20 + a13 = a9 * 0x14 + a13
# where a13 = *0x17f84 = 0x107fc
# Offset 0x1f8 -> Voltage, offset 0x1fc -> Current, offset 0x200 -> Power
# Iteration 0 (Domain 0):
#   src_voltage_0 = 0x107fc + 0 * 0x14 + 0x1f8 = 0x109f4
#   src_current_0 = 0x107fc + 0 * 0x14 + 0x1fc = 0x109f8
#   src_power_0   = 0x107fc + 0 * 0x14 + 0x200 = 0x109fc
#   dst_voltage_0 = 0xcb68 + 0 * 4 + 0x50 = 0xcbb8
#   dst_current_0 = 0xcb68 + 0 * 4 + 0x58 = 0xcbc0
#   dst_power_0   = 0xcb68 + 0 * 4 + 0x60 = 0xcbc8
# Iteration 1 (Domain 1):
#   src_voltage_1 = 0x107fc + 1 * 0x14 + 0x1f8 = 0x10a08
#   src_current_1 = 0x107fc + 1 * 0x14 + 0x1fc = 0x10a0c
#   src_power_1   = 0x107fc + 1 * 0x14 + 0x200 = 0x10a10
#   dst_voltage_1 = 0xcb68 + 1 * 4 + 0x50 = 0xcbbc
#   dst_current_1 = 0xcb68 + 1 * 4 + 0x58 = 0xcbc4
#   dst_power_1   = 0xcb68 + 1 * 4 + 0x60 = 0xcbcc

assert (0x107fc + 0x1f8) == 0x109f4
assert (0x107fc + 0x14 + 0x1f8) == 0x10a08
assert (0xcb68 + 0x50) == 0xcbb8
assert (0xcb68 + 4 + 0x50) == 0xcbbc

# 3. Exact loop byte verification in binary
loop_bytes = b[0x29ee1:0x29f16]
expected_loop_bytes = bytes.fromhex(
    '76ab31'        # loopgtz a11, 0x00029f16
    '20f9a0'        # addx4 a15, a9, a2
    '1bb9'          # addi.n a11, a9, 1
    '90c9a0'        # addx4 a12, a9, a9
    'd0cca0'        # addx4 a12, a12, a13
    'd30c7f'        # lsi f13, a12, 0x1fc
    'e30c7e'        # lsi f14, a12, 0x1f8
    'f30c80'        # lsi f15, a12, 0x200
    '00cf2a'        # mul.s f12, f15, f0
    '00be2a'        # mul.s f11, f14, f0
    '00ad2a'        # mul.s f10, f13, f0
    'b09074'        # extui a9, a11, 0, 8
    '00ecea'        # utrunc.s a14, f12, 0
    '00abea'        # utrunc.s a10, f11, 0
    '008aea'        # utrunc.s a8, f10, 0
    'a26f14'        # s32i a10, a15, 0x50
    '826f16'        # s32i a8, a15, 0x58
    'e26f18'        # s32i a14, a15, 0x60
)
assert loop_bytes == expected_loop_bytes, f"Loop byte mismatch: {loop_bytes.hex()} vs {expected_loop_bytes.hex()}"

# 4. Telemetry Master Pointer Table at 0x15380-0x153B4
# Direct memory contents in Robin-5:
table_15380 = [u32(0x15380 + i*4) for i in range(14)]
expected_15380 = [
    0x00000000,
    0x00011060,
    0x000108b0,
    0x00011360,
    0x00011070,
    0x00013474, # Actuator state struct base
    0x000109f4, # Domain 0 Voltage telemetry source
    0x000109f8, # Domain 0 Current telemetry source
    0x000109fc, # Domain 0 Power telemetry source
    0x000108a4,
    0x00010a08, # Domain 1 Voltage telemetry source
    0x00010a0c, # Domain 1 Current telemetry source
    0x00010a10, # Domain 1 Power telemetry source
    0x000112b0
]
assert table_15380 == expected_15380, f"Table 0x15380 mismatch: {[hex(x) for x in table_15380]}"

# 5. Actuator State Struct Layout comparison
# Actuator base: 0x13474
# Domain 0: voltage float target at +0x00 (0x13474), VID code uint8 at +0x04 (0x13478)
# Domain 1: voltage float target at +0x20 (0x13494), VID code uint8 at +0x24 (0x13498)
actuator_dom0_float = 0x13474 + 0x00
actuator_dom0_vid   = 0x13474 + 0x04
actuator_dom1_float = 0x13474 + 0x20
actuator_dom1_vid   = 0x13474 + 0x24

metrics_dom0_src = 0x109f4
metrics_dom1_src = 0x10a08

assert actuator_dom0_float != metrics_dom0_src
assert actuator_dom1_float != metrics_dom1_src
delta_dom0 = actuator_dom0_float - metrics_dom0_src
delta_dom1 = actuator_dom1_float - metrics_dom1_src

# 6. Negative Static Writer Proof
# Verify that no l32r instruction directly loads literals targeting 0x109f4, 0x10a08, or 0x107fc
# other than the 2 read consumers:
l32r_refs_17f84 = []
for pc in range(0, len(b)-3):
    if b[pc]&15 == 1:
        target = ((pc+3)&~3) + (int.from_bytes(b[pc+1:pc+3], 'little') - 65536)*4
        if target == 0x17f84:
            l32r_refs_17f84.append(hex(pc))

assert l32r_refs_17f84 == ['0x29c2d', '0x29ede'], f"Unexpected l32r refs to 0x17f84: {l32r_refs_17f84}"

out = {
    "status": "PASS",
    "verification": {
        "clv_rom_sha256": r_hash,
        "robin5_smu_sha256": b_hash,
        "smu_body_offset_in_rom": "0x8fef00",
        "literal_17f88": hex(lit_17f88),
        "literal_17f84": hex(lit_17f84),
        "literal_17f7c": hex(lit_17f7c),
        "table_export_base": hex(table_export_base),
        "loop_bytes_exact_match": True,
        "master_pointer_table_15380": [hex(x) for x in table_15380],
        "delta_domain0_actuator_vs_telemetry": hex(delta_dom0),
        "delta_domain1_actuator_vs_telemetry": hex(delta_dom1),
        "l32r_refs_to_telemetry_base": l32r_refs_17f84
    },
    "provenance_conclusion": {
        "telemetry_source_array": "0x107fc + 0x1f8 (0x109f4) and + 0x20c (0x10a08)",
        "telemetry_master_pointer_table": "0x15380, entries 0x15394 (actuator), 0x15398 (dom0 V), 0x153a8 (dom1 V)",
        "actuator_direct_read": False,
        "static_code_writer_status": "BOUNDED_NEGATIVE_LITERAL_SCAN: Direct l32r references to telemetry base literal 0x17f84 are read consumers (0x29c2d, 0x29ede). Scope of negative scan only literal-reference path, NOT all stores/indirect/DMA writes; does NOT establish an external hardware writer. Verified producer reads 0x109f4/0x10a08, not direct alias 0x13474; unequal addresses do not disprove actuator->telemetry copy; source writer and copied provenance unknown."
    }
}

json_path = Path('evidence/firmware-audit/20260919-voltage-producer-writer/verification-summary.json')
json_path.write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps(out, indent=2))
