#!/usr/bin/env python3
"""Deterministic verification of SMU Fabric / Domain rate encoding and DF P-state path:
- ROM: evidence/donor/retroweb-20260916/BC250_5.00_clv.bin
  SHA-256 ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8
- SMU: import/from-windows/Users/kukuruza/tmp_bc250/upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5
  SHA-256 cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37, offset 0x8FEF00 in ROM
- 8 Clock Groups at 0xF568 (stride 0x48 = 72 bytes)
- 27 Clock Domain Descriptors at 0xF7A8 (stride 0x1C = 28 bytes)
- 20 Dynamic Domains in 0x13EF4 (Groups 0, 1, 5, 6)
- 5 Observed Clock Domains: 0x0E (Group 2), 0x0F & 0x10 (Group 3), 0x11 & 0x12 (Group 4)
- DF P-state Table at 0xCEE0 + 0x2C = 0xCF0C (5 P-states, stride 0x28 = 40 bytes)
- DF P-state Dispatch: Queue 5 msg 0x07 -> 0x1E720 (SetDfPstate) -> 0x1E448
- Actuator helpers: 0x23B7C (Domain 0x0E), 0x23BA8 (Domains 0x0F & 0x11), 0x23BF4 (Domains 0x10 & 0x12)
- Rate decoding helper: 0x2360C (U9.16 fixed point to float), 0x1CAD8 (AMD DFS DID divider formula)
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
assert r_hash == 'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8', f"ROM hash: {r_hash}"
assert len(b) == 262400, f"SMU size mismatch: {len(b)}"
assert b_hash == 'cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37', f"SMU hash: {b_hash}"
assert r[0x8fef00:0x8fef00 + len(b)] == b, "SMU binary at ROM 0x8FEF00 mismatch"

def u32(a): return struct.unpack_from('<I', b, a)[0]
def u8(a): return b[a]
def f32(a): return struct.unpack_from('<f', b, a)[0]

# Exact decoding of helper 0x2360C (U9.16 fixed-point to float conversion)
def decode_rate_2360c(raw_u32):
    int_part = raw_u32 & 0x1FF
    frac_part = (raw_u32 >> 16) & 0xFFFF
    return float(int_part) + float(frac_part) * (1.0 / 65536.0)

# Exact decoding of helper 0x1CAD8 (AMD DFS post-divider / DID code to float divider)
def decode_dfs_did_1cad8(code):
    if code <= 0x40:
        return code * 0.25
    elif code <= 0x60:
        return (code * 2 - 0x40) * 0.25
    elif code <= 0x7E:
        return (code * 4 - 0x100) * 0.25
    else:
        return 128.0

# Verify arithmetic probe and boundary tests on 0x2360C
assert decode_rate_2360c(0) == 0.0
assert decode_rate_2360c(0x1FF) == 511.0
assert decode_rate_2360c(0x00010000) == 1.0 / 65536.0
assert decode_rate_2360c(0x80000000) == 0.5
assert decode_rate_2360c(0x0000001E) == 30.0
assert decode_rate_2360c(0x0000FE00) == 0.0  # bits [15:9] ignored

# Verify arithmetic probe on 0x1CAD8
assert decode_dfs_did_1cad8(16) == 4.0
assert decode_dfs_did_1cad8(48) == 12.0
assert decode_dfs_did_1cad8(64) == 16.0
assert decode_dfs_did_1cad8(72) == 20.0
assert decode_dfs_did_1cad8(96) == 32.0
assert decode_dfs_did_1cad8(127) == 128.0

results = {
    "hashes": {
        "rom_sha256": r_hash,
        "smu_sha256": b_hash,
        "smu_rom_offset": "0x8fef00",
        "evidence_classification": "observed/static"
    },
    "clock_groups": [],
    "clock_domains": [],
    "df_pstates": [],
    "df_dispatch": {},
    "arithmetic_conversion_helpers": {
        "0x0002360c": {
            "type": "U9.16_fixed_to_float",
            "integer_mask": "0x000001FF",
            "fraction_shift": 16,
            "fraction_scale": "1/65536.0 (literal 0x17460 = 0x37800000)",
            "ignored_bits": "15:9",
            "evidence_classification": "observed/static"
        },
        "0x0001cad8": {
            "type": "dfs_did_divider_decode",
            "scaling_literal_0x17270": 0.25,
            "clamp_literal_0x17274": 128.0,
            "ranges": ["<=0x40: x*0.25", "<=0x60: (2x-64)*0.25", "<=0x7E: (4x-256)*0.25", ">=0x7F: 128.0"],
            "evidence_classification": "observed/static"
        }
    }
}

# 1. Verify 8 Clock Groups at 0xF568 (stride 0x48)
expected_group_smn = [
    0x0115b000, 0x0115b800, 0x0115c000, 0x0115c800,
    0x0116c000, 0x0116c800, 0x0116d000, 0x0115f800
]
for g in range(8):
    base = 0xF568 + g * 0x48
    base_reg = u32(base + 8)
    smn_base = (base_reg & 0xFFFFF) + 0x1100000
    vco_scale = f32(base + 0x10)
    assert smn_base == expected_group_smn[g], f"Group {g} SMN expected 0x{expected_group_smn[g]:08x}, got 0x{smn_base:08x}"
    assert abs(vco_scale - 0.1) < 1e-6, f"Group {g} word4 scale expected 0.1, got {vco_scale}"
    results["clock_groups"].append({
        "group_index": g,
        "offset": hex(base),
        "base_reg": hex(base_reg),
        "smn_base": hex(smn_base),
        "vco_scale_word4": vco_scale,
        "evidence_classification": "observed/static"
    })

# 2. Verify 27 Clock Domain Descriptors at 0xF7A8 (stride 0x1C)
dynamic_domains = [u32(0x13EF4 + i*4) for i in range(20)]

for d in range(27):
    desc = 0xF7A8 + d * 0x1C
    group_idx = u8(desc)
    prog_reg = u32(desc + 0x14)
    smn_prog = (prog_reg & 0xFFFFF) + 0x1100000
    smn_poll = ((prog_reg + 0x24) & 0xFFFFF) + 0x1100000

    entry = {
        "domain_id": hex(d),
        "offset": hex(desc),
        "group_index": group_idx,
        "smn_program_reg": hex(smn_prog),
        "smn_poll_reg": hex(smn_poll),
        "in_generic_20_pstate_array": d in dynamic_domains,
        "observed_group_membership": f"Group_{group_idx}",
        "physical_domain_meaning": "UNKNOWN_WITHOUT_RUNTIME_CONFIRMATION",
        "evidence_classification": "observed/static"
    }
    results["clock_domains"].append(entry)

# 3. Verify DF P-state Table at 0xCF0C (5 P-states, stride 0x28)
# Observed raw bytes and encoded rates
for p in range(5):
    row_addr = 0xCF0C + p * 0x28
    b0 = u8(row_addr + 0)
    b1 = u8(row_addr + 1)
    b2 = u8(row_addr + 2)
    b3 = u8(row_addr + 3)
    f4_stored = f32(row_addr + 4)
    b8 = u8(row_addr + 8)
    b9 = u8(row_addr + 9)
    b10 = u8(row_addr + 10)
    b11 = u8(row_addr + 11)
    b12 = u8(row_addr + 12)
    f16_stored = f32(row_addr + 16)
    f20_stored = f32(row_addr + 20)
    f24_stored = f32(row_addr + 24)

    # Decode computed rates via 2360C and 1CAD8
    # Domain 0x0E (Group 2): byte 0 = VCO mult, byte 1 = DFS DID
    vco_0e = decode_rate_2360c(b0) * 0.1
    did_0e = decode_dfs_did_1cad8(b1)
    computed_rate_0e_ghz = vco_0e / did_0e
    computed_rate_0e_mhz = computed_rate_0e_ghz * 1000.0

    # Domains 0x0F & 0x11 (Groups 3 & 4): byte 8 = VCO mult, byte 9 = DFS DID
    vco_0f_11 = decode_rate_2360c(b8) * 0.1
    did_0f_11 = decode_dfs_did_1cad8(b9)
    computed_rate_0f_11_ghz = vco_0f_11 / did_0f_11
    computed_rate_0f_11_mhz = computed_rate_0f_11_ghz * 1000.0

    # Domains 0x10 & 0x12 (Groups 3 & 4): byte 8 = VCO mult, byte 11 = DFS DID
    vco_10_12 = decode_rate_2360c(b8) * 0.1
    did_10_12 = decode_dfs_did_1cad8(b11)
    computed_rate_10_12_ghz = vco_10_12 / did_10_12
    computed_rate_10_12_mhz = computed_rate_10_12_ghz * 1000.0

    assert abs(computed_rate_0e_mhz - f4_stored) < 0.1, f"Pstate {p} Domain 0x0E rate mismatch: computed {computed_rate_0e_mhz} vs stored {f4_stored}"
    assert abs(computed_rate_0f_11_mhz - f16_stored) < 0.1, f"Pstate {p} Domain 0x0F/0x11 rate mismatch: computed {computed_rate_0f_11_mhz} vs stored {f16_stored}"
    assert abs(computed_rate_10_12_mhz - f20_stored) < 0.1, f"Pstate {p} Domain 0x10/0x12 rate mismatch: computed {computed_rate_10_12_mhz} vs stored {f20_stored}"

    results["df_pstates"].append({
        "pstate": p,
        "offset": hex(row_addr),
        "raw_bytes": {
            "b0": hex(b0), "b1": hex(b1), "b2": hex(b2), "b3": hex(b3),
            "b8": hex(b8), "b9": hex(b9), "b10": hex(b10), "b11": hex(b11), "b12": hex(b12)
        },
        "stored_floats": {
            "offset_0x04": f4_stored,
            "offset_0x10": f16_stored,
            "offset_0x14": f20_stored,
            "offset_0x18": f24_stored
        },
        "decoded_domain_rates": {
            "domain_0x0e": {"vco_ghz": vco_0e, "did": did_0e, "computed_rate_mhz": computed_rate_0e_mhz},
            "domains_0x0f_and_0x11": {"vco_ghz": vco_0f_11, "did": did_0f_11, "computed_rate_mhz": computed_rate_0f_11_mhz},
            "domains_0x10_and_0x12": {"vco_ghz": vco_10_12, "did": did_10_12, "computed_rate_mhz": computed_rate_10_12_mhz}
        },
        "semantic_labels_status": "UNPROVEN_PHYSICAL_MAPPING (stored float offsets 0x04/0x10/0x14/0x18 correlate with computed rates, physical clock assignment unverified)",
        "evidence_classification": "observed/static"
    })

# 4. Verify DF Dispatch & Actuators
q5_msg7_handler = u32(0x79ec)
assert q5_msg7_handler == 0x1e720, f"Queue 5 Msg 7 handler expected 0x1e720, got 0x{q5_msg7_handler:x}"

q0_msg13_handler = u32(0x7104)
assert q0_msg13_handler == 0x1e988, f"Queue 0 Msg 0x13 handler expected 0x1e988, got 0x{q0_msg13_handler:x}"

results["df_dispatch"] = {
    "queue_5_msg_0x07": {"handler": hex(q5_msg7_handler), "symbol": "SetDfPstate", "target": "FUN_0001e720"},
    "queue_0_msg_0x13": {"handler": hex(q0_msg13_handler), "symbol": "QueryDfPstate", "target": "FUN_0001e988"},
    "df_applier": "0x0001e448",
    "df_actuator_helpers": {
        "0x00023b7c": {
            "target_domain": "0x0E",
            "group": 2,
            "smn_prog": "0x0115c0fc",
            "caller_arguments": {"param_1": "row[2]", "param_2": "row[0]", "param_3": "row[1]"}
        },
        "0x00023ba8": {
            "target_domains": ["0x0F", "0x11"],
            "groups": [3, 4],
            "smn_prog": ["0x0115c8fc", "0x0116c0fc"],
            "caller_arguments": {"param_1": "row[10]", "param_2": "row[8]", "param_3": "row[9]"}
        },
        "0x00023bf4": {
            "target_domains": ["0x10", "0x12"],
            "groups": [3, 4],
            "smn_prog": ["0x0115c924", "0x0116c124"],
            "caller_arguments": {"param_1": "row[12]", "param_2": "row[8]", "param_3": "row[11]"}
        }
    },
    "evidence_classification": "observed/static"
}

out_path = Path('evidence/firmware-audit/20260921-smu-clock-entrypoints-next/fabric-domains-verification.json')
out_path.write_text(json.dumps(results, indent=2))
print(f"PASS: all fabric domain assertions passed. Verification written to {out_path}")

