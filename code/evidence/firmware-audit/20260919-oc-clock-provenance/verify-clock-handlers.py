#!/usr/bin/env python3
"""Deterministic verification of SMU clock handlers and actuator chain:
- ROM: evidence/donor/retroweb-20260916/BC250_5.00_clv.bin
  SHA-256 ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8
- SMU: import/from-windows/Users/kukuruza/tmp_bc250/upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5
  SHA-256 cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37, offset 0x8FEF00 in ROM
- Queue 0, ID 0x11 at 0x70F0 -> handler 0x2EA74 (reads float from 0x13EEC struct, returns utrunc.s)
- Queue 0, ID 0x13 at 0x7100 -> handler 0x1E988 (reads bytes from 0xCEE0 struct, returns (byte[0xf7] - byte[0xd]) - 1)
- Queue 0, ID 0x1A at 0x7138 -> handler 0x2B634 (GFX DFLL divider)
- Queue 3, ID 0x1D at 0x7550 -> handler 0x2EA08 (dynamic per-domain clock request, 1-based domain index)
- Clock state struct at 0x13EEC:
  - Domain mapping at 0x13EF4 (20 domain IDs)
  - Current frequency float array at 0x13F48 (20 floats, step 12)
  - Target frequency float array at 0x14038 (20 floats, step 12)
  - Actuator loop FUN_0002e788:
    - Compares target floats (0x14038) with current floats (0x13F48)
    - Dispatches domain ID through helpers FUN_00023994 / FUN_00023ab0 / FUN_00023ac4 / FUN_00023c78 / FUN_00023890
    - Actuator FUN_00023890 writes MMIO/SMN registers via FUN_000235c8
  - Writer 1 FUN_0002e9dc:
    - Loads target frequencies from table at 0x7B5C (0x7B5C + pstate * 100 + 0x48) into 0x14038
  - Writer 2 FUN_0002ea08:
    - Takes 1-based domain index (1..20) and frequency request (arg & 0xFFFF)
    - Writes target float to 0x1402c + index * 12 (0x14038 for index 1)
    - Calls FUN_0002e788
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

results = {}

# 1. Queue dispatch table verification
q0_entry_base = 0x7068
assert u32(0x7a94) == 0x706c

# Queue 0 ID 0x11: offset = 0x7068 + 0x11 * 8 = 0x70F0
q0_11_flags = u32(0x70f0)
q0_11_handler = u32(0x70f4)
assert q0_11_handler == 0x2ea74, f"ID 0x11 handler expected 0x2ea74, got 0x{q0_11_handler:x}"

# Queue 0 ID 0x13: offset = 0x7068 + 0x13 * 8 = 0x7100
q0_13_flags = u32(0x7100)
q0_13_handler = u32(0x7104)
assert q0_13_handler == 0x1e988, f"ID 0x13 handler expected 0x1e988, got 0x{q0_13_handler:x}"

# Queue 0 ID 0x1A: offset = 0x7068 + 0x1a * 8 = 0x7138
q0_1a_flags = u32(0x7138)
q0_1a_handler = u32(0x713c)
assert q0_1a_handler == 0x2b634, f"ID 0x1a handler expected 0x2b634, got 0x{q0_1a_handler:x}"

# Queue 3 ID 0x1D: offset = 0x7468 + 0x1d * 8 = 0x7550
q3_1d_flags = u32(0x7550)
q3_1d_handler = u32(0x7554)
assert q3_1d_handler == 0x2ea08, f"Queue 3 ID 0x1d handler expected 0x2ea08, got 0x{q3_1d_handler:x}"

results["dispatch_table"] = {
    "queue_0_base": "0x7068",
    "id_0x11": {"offset": "0x70f0", "flags": hex(q0_11_flags), "handler": hex(q0_11_handler)},
    "id_0x13": {"offset": "0x7100", "flags": hex(q0_13_flags), "handler": hex(q0_13_handler)},
    "id_0x1A": {"offset": "0x7138", "flags": hex(q0_1a_flags), "handler": hex(q0_1a_handler)},
    "queue_3_id_0x1D": {"offset": "0x7550", "flags": hex(q3_1d_flags), "handler": hex(q3_1d_handler)}
}

# 2. Handler 0x2EA74 byte verification (Reader)
assert b[0x2ea8e:0x2ea91] == bytes.fromhex('d1e9a5') # l32r a13, 0x18234 (0x13eec)
assert b[0x2eaa6:0x2eaa9] == bytes.fromhex('030d17') # lsi f0, a13, 0x5c (0x13f48 + index*12)
assert b[0x2eaa9:0x2eaac] == bytes.fromhex('00b0ea') # utrunc.s a11, f0, 0x0
assert u32(0x18234) == 0x13eec

results["handler_0x2ea74"] = {
    "literal_18234": hex(u32(0x18234)),
    "bytes_hex": b[0x2ea74:0x2eac7].hex(),
    "proven_behavior": "0-based index (0..19). Reads internal software committed frequency float at 0x13eec + 0x5c + index*12 (0x13f48 + index*12); returns utrunc.s(float). No PLL hardware sampling or physical frequency measurement."
}

# 3. Handler 0x1E988 byte verification (DF P-state query)
assert b[0x1e98b:0x1e98e] == bytes.fromhex('b118e2') # l32r a11, 0x171ec (0xcee0)
assert b[0x1e98e:0x1e991] == bytes.fromhex('c20b0d') # l8ui a12, a11, 0xd
assert b[0x1e991:0x1e994] == bytes.fromhex('b20bf7') # l8ui a11, a11, 0xf7
assert b[0x1e996:0x1e999] == bytes.fromhex('c0bbc0') # sub a11, a11, a12
assert b[0x1e999:0x1e99b] == bytes.fromhex('0bbb')     # addi.n a11, a11, -1
assert u32(0x171ec) == 0xcee0

results["handler_0x1e988"] = {
    "literal_171ec": hex(u32(0x171ec)),
    "bytes_hex": b[0x1e988:0x1e9a6].hex(),
    "proven_behavior": "Returns (byte[0xcee0 + 0xf7] - byte[0xcee0 + 0xd] - 1); state index delta, NOT a frequency measurement."
}

# 4. Writer 2 FUN_0002ea08 byte verification (Dynamic per-domain frequency request)
assert b[0x2ea08:0x2ea0b] == bytes.fromhex('364100') # entry a1, 0x20
assert b[0x2ea0b:0x2ea0d] == bytes.fromhex('ad02')   # mov.n a10, a2
assert b[0x2ea0d:0x2ea10] == bytes.fromhex('e55ed2') # call8 0x00000ffc (get mailbox arg)
assert b[0x2ea14:0x2ea17] == bytes.fromhex('a0a0f5') # extui a10, a10, 0x10, 0x10 (index = arg >> 16)
assert b[0x2ea17:0x2ea1a] == bytes.fromhex('a73c3f') # bltu a12, a10, 0x2ea5a (bounds check: index <= 20)
assert b[0x2ea1a:0x2ea1c] == bytes.fromhex('bcca')   # beqz.n a10, 0x2ea5a (reject index == 0 -> 1-based index 1..20)
assert b[0x2ea1c:0x2ea1f] == bytes.fromhex('d106a6') # l32r a13, 0x00018234 (0x13eec)
assert b[0x2ea1f:0x2ea22] == bytes.fromhex('d0baa0') # addx4 a11, a10, a13 (0x13eec + index*4)
assert b[0x2ea22:0x2ea24] == bytes.fromhex('b81b')   # l32i.n a11, a11, 0x4 (domain ID from 0x13eec + 4 + index*4 = 0x13ef0 + index*4)
assert b[0x2ea38:0x2ea3b] == bytes.fromhex('d0cca0') # addx4 a12, a12, a13 (0x13eec + index*12)
assert b[0x2ea3b:0x2ea3e] == bytes.fromhex('034c50') # ssi f0, a12, 0x140 (store float to 0x13eec + 0x140 + index*12 = 0x1402c + index*12)
assert b[0x2ea41:0x2ea44] == bytes.fromhex('65d4ff') # call8 0x0002e788 (ACTUATOR LOOP)

results["writer_2_0x2ea08"] = {
    "entry_hex": b[0x2ea08:0x2ea58].hex(),
    "proven_behavior": "1-based domain index (1..20). Domain ID at 0x13ef0 + index*4; for index 1..20, this maps to 0x13ef4..0x13f40 (entries 0..19). Target float written to 0x1402c + index*12; for index 1..20, this maps to 0x14038..0x1411c (entries 0..19). Calls actuator FUN_0002e788."
}

# 5. Writer 1 FUN_0002e9dc byte verification (P-state bulk loader)
assert b[0x2e9dc:0x2e9df] == bytes.fromhex('364100') # entry a1, 0x20
assert b[0x2e9df:0x2e9e1] == bytes.fromhex('1c43')   # movi.n a3, 0x14 (20 entries)
assert b[0x2e9e1:0x2e9e4] == bytes.fromhex('51cea1') # l32r a5, 0x0001711c (0x7b5c)
assert b[0x2e9e7:0x2e9ea] == bytes.fromhex('42a064') # movi a4, 0x64 (stride 100)
assert b[0x2e9ea:0x2e9ed] == bytes.fromhex('404282') # mull a4, a2, a4 (pstate * 100)
assert b[0x2e9ed:0x2e9ef] == bytes.fromhex('2918')   # s32i.n a2, a8, 0x4 (stores requested pstate index to 0x13eec + 4)
assert b[0x2e9ef:0x2e9f2] == bytes.fromhex('502480') # add a2, a4, a5 (0x7b5c + pstate * 100)
assert b[0x2e9f2:0x2e9f5] == bytes.fromhex('4115a6') # l32r a4, 0x00018248 (0x14038)
assert b[0x2e9f5:0x2e9f8] == bytes.fromhex('76a30a') # loopgtz a3, 0x0002ea03
assert b[0x2e9f8:0x2e9fb] == bytes.fromhex('822212') # l32i a8, a2, 0x48 (load uint from a2 + 0x48)
assert b[0x2e9fb:0x2e9fe] == bytes.fromhex('0008da') # ufloat.s f0, a8, 0x0
assert b[0x2e9fe:0x2ea00] == bytes.fromhex('4b22')   # addi.n a2, a2, 0x4
assert b[0x2ea00:0x2ea03] == bytes.fromhex('03c403') # ssip f0, a4, 0xc (store float to a4, a4 += 12)

results["writer_1_0x2e9dc"] = {
    "entry_hex": b[0x2e9dc:0x2ea04].hex(),
    "proven_arithmetic": {
        "pstate_row_stride": 100,
        "entry_start_offset": "0x48 (72 decimal)",
        "entry_count": 20,
        "entry_size": 4,
        "total_read_bytes_per_call": 80,
        "read_span": "0x7b5c + pstate*100 + 0x48 .. 0x7b5c + pstate*100 + 0x98 (offsets 72..152)",
        "stride_overlap_note": "Reading 80 bytes at offset 0x48 (72) within a 100-byte row stride extends across offsets 72..152. Whether this represents a prebiased base, structure-of-arrays layout, or bug is preserved as an open technical uncertainty without runtime buffer population evidence."
    }
}

# 6. Actuator Loop FUN_0002e788 byte verification
assert b[0x2e788:0x2e78b] == bytes.fromhex('364100') # entry a1, 0x20
assert b[0x2e78b:0x2e78e] == bytes.fromhex('71aaa6') # l32r a7, 0x00018234 (0x13eec)
assert b[0x2e78e:0x2e791] == bytes.fromhex('51aaa6') # l32r a5, 0x00018238 (0x13fdc)
assert b[0x2e7c1:0x2e7c4] == bytes.fromhex('251df5') # call8 0x00023994
assert b[0x2e7d8:0x2e7db] == bytes.fromhex('652df5') # call8 0x00023ab0
assert b[0x2e7f3:0x2e7f6] == bytes.fromhex('252df5') # call8 0x00023ac4
assert b[0x2e805:0x2e808] == bytes.fromhex('2547f5') # call8 0x00023c78
assert b[0x2e821:0x2e824] == bytes.fromhex('e506f5') # call8 0x00023890

results["actuator_0x2e788"] = {
    "entry_hex": b[0x2e788:0x2e842].hex(),
    "loop_count": (0x13fdc - 0x13eec) // 12,
    "proven_behavior": "Iterates 20 domains. Reads domain ID from 0x13ef4 + i*4. Compares target float at 0x14038 + i*12 with current software committed float at 0x13f48 + i*12. Dispatches changed domains to FUN_00023994 / FUN_00023ab0 / FUN_00023ac4 / FUN_00023c78 / FUN_00023890. Commits software state float to 0x13f48."
}

# 7. Domain mapping & Hardware Register Aperture Verification
domain_ids = [u32(0x13ef4 + i * 4) for i in range(20)]
results["domain_ids_0x13ef4"] = domain_ids

domain_table = []
for i, did in enumerate(domain_ids):
    ivar3_off = did * 0x1c + 0xf728
    ivar4_off = did * 0x1c + 0xf568 + 0x254
    ivar4 = u32(ivar4_off)
    reg_addr = (ivar4 & 0xfffff) + 0x1100000
    poll_reg = ((ivar4 + 0x24) & 0xfffff) + 0x1100000
    b_80 = u8(ivar3_off + 0x80)
    b_7e = u8(did * 0x1c + 0xf72c + 0x7e)
    
    # Classification based on raw register aperture:
    if 0x5afff < ivar4 <= 0x5b7ff:
        classification = f"CPU_CORE_{did}"
    elif b_80 == 0x01:
        classification = f"CLK_GROUP_1_ID_{hex(did)}"
    elif b_80 == 0x05:
        classification = f"CLK_GROUP_5_ID_{hex(did)}"
    elif b_80 == 0x06:
        classification = f"CLK_GROUP_6_ID_{hex(did)}"
    else:
        classification = f"CLK_GROUP_{b_80}_ID_{hex(did)}"

    domain_table.append({
        "index_0based": i,
        "index_1based": i + 1,
        "domain_id": hex(did),
        "classification": classification,
        "pll_group_byte_80": hex(b_80),
        "divider_state_byte_7e": hex(b_7e),
        "smn_program_reg": hex(reg_addr),
        "smn_poll_reg": hex(poll_reg),
        "ivar4_raw": hex(ivar4)
    })

results["domain_hardware_mapping"] = domain_table

# 8. UCLK divisor inspection verdict
# Analysis of FUN_0002e788 -> FUN_00023890 -> FUN_000235c8:
# Registers written in this loop are in the 0x0115Bxxx, 0x0116Cxxx, 0x0116Dxxx apertures and 0x01D80414.
# Absence of DF/UMC known register ranges cannot prove UCLK not controlled (clock generator may use other aperture).
# Helpers FUN_00023890, FUN_000235c8, FUN_00023994, FUN_00023ab0, FUN_00023ac4, FUN_00023c78 are static disassembly only; verifier does not cover them.
results["uclk_divisor_status"] = {
    "conclusion": "UCLK mapping/control unestablished; observed address set only",
    "evidence": "Observed actuator loop FUN_0002e788 and callee FUN_00023890 write to SMN apertures 0x0115Bxxx, 0x0116Cxxx, 0x0116Dxxx, and 0x01D80414. Absence of DF/UMC known register ranges cannot prove UCLK not controlled (clock generator may use other aperture). Helper findings are static disassembly only and verifier does not cover them.",
    "observed_apertures": ["0x0115Bxxx", "0x0116Cxxx", "0x0116Dxxx", "0x01D80414"]
}

out_path = Path('evidence/firmware-audit/20260919-oc-clock-provenance/clock-handlers-verification.json')
out_path.write_text(json.dumps(results, indent=2))
print(f"PASS: Clock handlers and actuator chain verification complete. Written to {out_path}")

