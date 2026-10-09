#!/usr/bin/env python3
"""Verify the narrow exact-CLV ABL1 memory-policy branch/override path."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ROM = ROOT / 'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
PAY = ROOT / 'evidence/firmware-audit/20260920-clv-sync-stage2-abl-memory/ABL1-clv-decompressed.bin'
PSP = ROOT / 'evidence/firmware-audit/20260920-clv-psp-abl-provenance/clv-psp-abl-inventory.json'
DIS = OUT / 'abl1-policy-95fc-989e.txt'
OBJ = OUT / 'ABL1-exact.o'
OBJDUMP_ERR = OUT / 'objdump.stderr'
EXPECTED_ROM = 'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
EXPECTED_PAY = 'af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a'
EXPECTED_OBJ = 'c4420d815773d9ee38a00923f5c8ab0b33095bdd714b4df41cb879193c581b6e'
EXPECTED_DIS = 'af1c864b86e4fdd07801f55197e4a2c0157b3033a4913bb88739a8c4c752be81'
checks: list[dict] = []

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def check(name: str, actual, expected) -> None:
    checks.append({'name': name, 'actual': actual, 'expected': expected,
                   'status': 'PASS' if actual == expected else 'FAIL'})

check('donor_sha256', sha(ROM), EXPECTED_ROM)
check('donor_size', ROM.stat().st_size, 16777216)
check('abl1_payload_sha256', sha(PAY), EXPECTED_PAY)
check('abl1_payload_size', PAY.stat().st_size, 94624)
check('fresh_objcopy_output_sha256', sha(OBJ), EXPECTED_OBJ)
check('fresh_narrow_disassembly_sha256', sha(DIS), EXPECTED_DIS)
check('objdump_stderr_empty', sha(OBJDUMP_ERR), 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')

inv = json.loads(PSP.read_text())
abl1 = next(x for x in inv['abl_payloads'] if x['payload_id'] == 'ABL1')
check('PSP_type', abl1['type'], '0x31')
check('PSP_SPI_offset', abl1['spi_offset'], '0x99FD00')
check('PS1_magic', abl1['magic'], '$PS1')
check('ABL1_container_size', abl1['container_size'], 49184)
check('ABL1_decompressed_sha256', abl1['decompressed_payload_sha256'], EXPECTED_PAY)

listing = DIS.read_text()
# Parse the freshly generated listing by address, so spacing in objdump columns
# cannot turn valid instruction evidence into a false verifier failure.
import re
rows: dict[int, tuple[str, str]] = {}
for line in listing.splitlines():
    parts = line.split("\t")
    if len(parts) < 3:
        continue
    match = re.match(r"\s*([0-9a-f]+):", parts[0])
    if not match:
        continue
    address = int(match.group(1), 16)
    mnemonic = parts[1].strip().lower()
    operands = parts[2].split("@", 1)[0].strip().lower()
    rows[address] = (mnemonic, operands)

def instruction_matches(address: int, mnemonic: str, operands_pattern: str) -> bool:
    actual = rows.get(address)
    return bool(actual and actual[0] == mnemonic and re.search(operands_pattern, actual[1]))

# (address, mnemonic, operand regex); all values are exact decoded addresses.
insns = {
    'guard_slot164_le_1': (0x9644, 'cmp', r'r0,\s*#0x1'),
    'slot164_le_1_bypasses_to_master_path': (0x9646, 'bls', r'0x9744'),
    'status_field_loaded': (0x9648, 'ldr', r'r0,\s*\[sp,\s*#0x174\]'),
    'status_zero_test': (0x964e, 'cmp', r'r0,\s*#0x0'),
    'status_zero_bypasses_to_fallback_path': (0x9650, 'beq', r'0x9746'),
    'nonzero_path_starts_after_both_guards': (0x9652, 'movs', r'r0,\s*#0x4'),
    'per_channel_speed_read': (0x9672, 'ldrh', r'r0,\s*\[r0,\s*#0x20\]'),
    'per_channel_speed_staged': (0x9674, 'str.w', r'r0,\s*\[r1,\s*#0x278\]'),
    'zero_entry_test': (0x96e4, 'cbnz', r'r0,\s*0x96e8'),
    'zero_entry_substitutes_r9': (0x96e6, 'mov', r'r0,\s*r9'),
    'normalized_entry_store': (0x96e8, 'str.w', r'r0,\s*\[r1,\s*#0x278\]'),
    'min_seed_2001': (0x9698, 'movw', r'r9,\s*#0x7d1'),
    'min_candidate_load': (0x971a, 'ldr.w', r'r2,\s*\[r2,\s*#0x278\]'),
    'min_candidate_compare': (0x971e, 'cmp', r'r2,\s*r6'),
    'larger_candidate_skips_update': (0x9720, 'bhs', r'0x9724'),
    'smaller_candidate_updates_u16_min': (0x9722, 'uxth', r'r6,\s*r2'),
    'minimum_to_context_aggregate': (0x973e, 'str.w', r'r6,\s*\[r4,\s*#0x2bc\]'),
    'multi_state_channel_writeback': (0x9758, 'strh', r'r6,\s*\[r0,\s*#0x20\]'),
    'status_zero_path': (0x9746, 'b', r'0x9794'),
    'fallback_calls_policy_helper': (0x97e4, 'bl', r'0x118c'),
    'fallback_calls_selector_helper': (0x9800, 'bl', r'0x10c0'),
    'fallback_helper_status_check': (0x9804, 'cmp', r'r0,\s*#0x9'),
    'fallback_output_to_context': (0x981e, 'str.w', r'r0,\s*\[r4,\s*#0x2bc\]'),
    'fallback_state_byte_write': (0x9822, 'strb.w', r'r6,\s*\[r4,\s*#0x2c0\]'),
    'fallback_output_to_channels': (0x983c, 'strh', r'r0,\s*\[r1,\s*#0x20\]'),
    'single_state_path_label_target': (0x984e, 'ldr', r'r2,\s*\[pc,\s*#0x1bc\]'),
    'single_state_reads_table_entry': (0x986e, 'ldrh', r'r0,\s*\[r1,\s*r5\]'),
    'single_state_updates_aggregate': (0x989a, 'str.w', r'r0,\s*\[r4,\s*#0x2bc\]'),
}
for name, (address, mnemonic, operands) in insns.items():
    check(name, instruction_matches(address, mnemonic, operands), True)

# This is a bounded negative only for the path window and exact channel field.
single_rows = [inst for addr, inst in rows.items() if 0x984e <= addr < 0x98aa]
check('single_state_window_has_no_channel_speed_store',
      any(mnemonic == 'strh' and re.search(r'\[r1,\s*#0x20\]', operands)
          for mnemonic, operands in single_rows), False)

# Read only: confirm the stored baseline requests are still the stated bytes.
rom = ROM.read_bytes()
base = 0x4CF
profile = {
    'MemoryClockSpeed': {'body_offset': 0x316, 'value': rom[base + 0x316], 'expected': 0x24},
    'UclkDiv1M0': {'body_offset': 0x330, 'value': rom[base + 0x330], 'expected': 0x01},
    'MemoryPstate': {'body_offset': 0x36D, 'value': rom[base + 0x36D], 'expected': 0xFF},
    'FclkDpm': {'body_offset': 0x6A3, 'value': rom[base + 0x6A3], 'expected': 0x0F},
    'DfClockOverrideControl': {'body_offset': 0x703, 'value': rom[base + 0x703], 'expected': 0x01},
    'DfClockOvrd': {'body_offset': 0x704, 'raw_le': rom[base + 0x704:base + 0x706].hex(),
                    'value_le': int.from_bytes(rom[base + 0x704:base + 0x706], 'little'),
                    'expected': 1420},
}
for name, row in profile.items():
    check('baseline_'+name, row.get('value', row.get('value_le')), row['expected'])

passed = sum(c['status'] == 'PASS' for c in checks)
failed = len(checks) - passed
result = {
    'status': 'PASS' if failed == 0 else 'FAIL',
    'checks': {'passed': passed, 'failed': failed, 'total': len(checks)},
    'exact_inputs': {
        'donor': {'path': str(ROM), 'size': ROM.stat().st_size, 'sha256': sha(ROM)},
        'abl1': {'psp_type': abl1['type'], 'spi_offset': abl1['spi_offset'],
                 'container_size': abl1['container_size'], 'magic': abl1['magic'],
                 'payload_path': str(PAY), 'payload_size': PAY.stat().st_size,
                 'payload_sha256': sha(PAY)},
        'disassembly': {'path': str(DIS), 'sha256': sha(DIS), 'tool': 'llvm-objdump 22.1.8',
                        'command': 'llvm-objdump -D --triple=thumbv7 --start-address=0x95fc --stop-address=0x989e evidence/firmware-audit/20260921-pstate-precedence-next/ABL1-exact.o'},
    },
    'baseline_setup_raw': profile,
    'branch_precedence': {
        'slot_164_le_1': '0x9644/0x9646 branches to 0x9744 then 0x984E system-master/table retrieval; the selected table value is stored to context+0x2BC at 0x989A. The bounded single-state window does not store a value to channel+0x20.',
        'slot_164_gt_1_and_slot_174_eq_0': '0x964E/0x9650 branches to 0x9746/0x9794; it gathers channel+0x20 values, calls helpers 0x118C and 0x10C0, then writes the output slot to context+0x2BC (0x981E) and each channel+0x20 (0x983C). Helper selection semantics are opaque.',
        'slot_164_gt_1_and_slot_174_ne_0': 'Collects per-channel+0x20 values at 0x9672/0x9674; zero slave-table entries substitute 0x7D1 at 0x96E4..0x96E8; a 0x7D1-initialized current value is lowered on smaller candidates at 0x971E..0x9722; selected value is stored to context+0x2BC at 0x973E and each channel+0x20 at 0x9758.',
    },
    'limits': [
        'The branch selects/synchronizes runtime channel-policy values, but no exact join from native AmdSetup+0x316/0x330/0x36D/0x6A3/0x703/0x704 into the ABL1 context is shown.',
        'The slot_164/slot_174 fields and callbacks are not runtime captured; the exact invocation of function 0x95FC is not established by this disassembly.',
        'The 0x7D1 sentinel is only an integer constant; no MHz/rate conversion is assigned.',
        'No UCLK ratio, FCLK_DPM effect, Memory-P-state training rule, PLL/register target, 1800 physical rate, 1:1:1 behavior, or hardware acceptance is proven.',
        'No ROM, NVRAM, register, hardware, candidate, or firmware bytes were written.',
    ],
    'checks_detail': checks,
}
(OUT / 'pstate-precedence-result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps({'status': result['status'], 'checks': result['checks'],
                  'branch_precedence': result['branch_precedence'],
                  'setup_raw': {k: (v.get('value') if 'value' in v else v['value_le']) for k, v in profile.items()}},
                 sort_keys=True))
raise SystemExit(0 if failed == 0 else 1)
