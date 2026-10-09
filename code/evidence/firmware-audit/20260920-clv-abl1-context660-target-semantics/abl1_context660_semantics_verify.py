#!/usr/bin/env python3
"""Verify possible 0x9AD8 descriptor/register semantics from exact ABL1 bytes."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path('/home/OWNER/orca/projects/bc250')
ABL = ROOT / 'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
DIS = ROOT / 'evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt'
PRIOR = ROOT / 'evidence/firmware-audit/20260920-clv-abl1-context660-callback-xhigh/abl1-context660-callback-result.json'
EXPECTED = {
    'abl': 'af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a',
    'dis': 'b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65',
}
BASE = 0x57100
POINTER = 0x60BD9


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(checks: list[dict], name: str, got, expected) -> None:
    passed = got == expected
    checks.append({'check': name, 'passed': passed, 'got': got, 'expected': expected})
    if not passed:
        raise AssertionError(f'{name}: got {got!r}, expected {expected!r}')


def raw(data: bytes, offset: int, hex_bytes: str) -> None:
    # The LLVM listing prints each 16-bit Thumb halfword in host notation;
    # normalize that notation to the direct little-endian file bytes.
    listed = bytes.fromhex(hex_bytes)
    expected = b''.join(listed[i:i + 2][::-1] for i in range(0, len(listed), 2))
    got = data[offset:offset + len(expected)]
    if got != expected:
        raise AssertionError(f'raw 0x{offset:X}: got {got.hex()}, expected {expected.hex()}')


def line_at(lines: dict[int, str], address: int) -> str:
    if address not in lines:
        raise AssertionError(f'listing address 0x{address:X} absent')
    return lines[address]


def has_op(lines: dict[int, str], address: int, text: str) -> bool:
    return text.lower() in line_at(lines, address).lower()


def main() -> None:
    checks: list[dict] = []
    abl = ABL.read_bytes()
    listing = DIS.read_text()
    lines: dict[int, str] = {}
    for line in listing.splitlines():
        m = re.match(r'\s*([0-9a-f]+):\s+', line)
        if m:
            lines[int(m.group(1), 16)] = line
    prior = json.loads(PRIOR.read_text())

    check(checks, 'ABL SHA-256', sha(ABL), EXPECTED['abl'])
    check(checks, 'Thumb listing SHA-256', sha(DIS), EXPECTED['dis'])
    check(checks, 'prior pointer result status', prior['status'], 'PASS')
    check(checks, 'prior conditional candidate base', prior['pointer_map']['candidate_base'], '0x57100 (conditional static mapping, not loader proof)')
    check(checks, 'pointer arithmetic', POINTER - BASE, 0x9AD9)
    check(checks, 'Thumb entry', ((POINTER - BASE) & ~1), 0x9AD8)

    raw_expect = {
        0x107E8: 'f240611e', # caller token load R1=0x61E
        0x1081E: '4620',       # caller R0=context before dispatcher call
        0x10820: 'f000f89a',   # call dispatcher
        0x10958: 'b430',       # dispatcher saves R4/R5
        0x1095A: 'f8d04660',   # dispatcher loads callback [R0+0x660]
        0x1095E: '4613',       # callback R3 = caller selected R2
        0x10960: '460a',       # callback R2 = caller token R1
        0x10966: '2101',       # callback R1 = 1
        0x10968: '4760',       # branch through callback pointer
        0x9AD8: 'e92d4fff',  # target prologue; R0..R3 are preserved in the frame
        0x9ADE: '4605',      # R5 = incoming R0 (context)
        0x9AE2: '469b',      # R11 = incoming R3 (selected value)
        0x9AE8: 'f3c2000b',  # R0 = low 12 bits of incoming R2 (token)
        0x9AF0: '900f',      # save token index at [SP+0x3c]
        0x9B18: '6c68',      # R0 = *(context + 0x44)
        0x9B1C: 'f8506021',  # R6 = table[token_index]
        0x9B2C: 'f3c6310b',  # descriptor nested index bits 12..23
        0x9B32: 'f3c61885',  # descriptor field end bits 6..11
        0x9B36: 'f3c60705',  # descriptor field start bits 0..5
        0x9B40: 'f3c67a80',  # descriptor wide-field flag bit 30
        0x9B54: 'f8506021',  # R6 = table[nested_index]
        0x9BFA: 'f8cdb014',  # wide-field selected value -> local output
        0x9BB8: '682b',       # R3 = context[0] before helper
        0x9BBA: '2003',       # access width/type 3
        0x9BBC: 'aa05',       # output pointer = SP+0x14
        0x9BBE: '4631',       # descriptor/address argument = R6
        0x9BC0: 'f7fdf82c',   # BL 0x6c1c
        0x9C22: '682b',       # R3 = context[0]
        0x9C24: '2003',       # access width/type 3
        0x9C26: 'aa05',       # output pointer = SP+0x14
        0x9C28: '4621',       # descriptor/address argument = R4
        0x9C2A: 'f7fdf8bb',   # BL 0x6da4
        0x9D20: 'ea0b0200',   # selected value mask from R11
        0x9D24: '40ba',       # shift selected bits to field start
        0x9D26: '430a',       # merge with read value
        0x9D28: '9205',       # local output update
        0x9D38: 'f7fcff71',   # BL 0x6c1e
        0x9D8E: '682b',       # R3 = context[0]
        0x9D90: '2003',       # access width/type 3
        0x9D92: 'aa05',       # output pointer = SP+0x14
        0x9D94: '4621',       # descriptor/address argument = R4
        0x9D96: 'f7fdf86b',   # BL 0x6e70
        0x6C1C: '4770',       # exact helper operation: BX LR (listing halfword)
        0x6C1E: '4770',       # adjacent aligned BX LR entry
        0x6DA4: 'e92d41f0',   # mapped-read helper prologue
        0x6DCC: '0b30',        # mapping selector = descriptor >> 12
        0x6DCE: 'f3c6040b',    # register offset = descriptor & 0xfff
        0x6DD2: '0300',        # selector << 12
        0x6DD4: 'df04',        # SVC #4 map
        0x6E02: '5d33',         # byte read variant
        0x6E06: '702b',         # byte store to output pointer
        0x6E0A: '5b33',         # halfword read variant
        0x6E0E: '802b',         # halfword store to output pointer
        0x6E1A: '5933',         # word read variant
        0x6E1E: '602b',         # word store to output pointer
        0x6E70: 'b5f8',          # mapped-write helper prologue
        0x6EA6: '0b28',          # mapping selector = descriptor >> 12
        0x6EA8: 'f3c5060b',      # register offset = descriptor & 0xfff
        0x6EAC: '0300',          # selector << 12
        0x6EAE: 'df04',          # SVC #4 map
        0x6EE6: '6820',          # word value load from output pointer
        0x6EE8: '51A8',          # word store to mapped register
    }
    for offset, expected in raw_expect.items():
        raw(abl, offset, expected)
        listed = bytes.fromhex(expected)
        direct = b''.join(listed[i:i + 2][::-1] for i in range(0, len(listed), 2))
        check(checks, f'raw bytes 0x{offset:X}', abl[offset:offset + len(direct)].hex(), direct.hex())

    op_expect = {
        0x107E8: 'movw\tr1, #0x61e', 0x1081E: 'mov\tr0, r4', 0x10820: 'bl\t0x10958',
        0x1095A: 'ldr.w\tr4, [r0, #0x660]', 0x1095E: 'mov\tr3, r2',
        0x10960: 'mov\tr2, r1', 0x10966: 'movs\tr1, #0x1', 0x10968: 'bx\tr12',
        0x9AD8: 'push.w', 0x9ADE: 'mov\tr5, r0', 0x9AE2: 'mov\tr11, r3',
        0x9AE8: 'ubfx\tr0, r2', 0x9B18: 'ldr\tr0, [r5, #0x44]',
        0x9B1C: 'ldr.w\tr6, [r0, r1, lsl #2]', 0x9B2C: 'ubfx\tr1, r6',
        0x9B32: 'ubfx\tr8, r6', 0x9B36: 'ubfx\tr7, r6', 0x9B40: 'ubfx\tr10, r6',
        0x9B54: 'ldr.w\tr6, [r0, r1, lsl #2]', 0x9BFA: 'str.w\tr11, [sp, #0x14]',
        0x9D20: 'and.w\tr2, r11', 0x9D28: 'str\tr2, [sp, #0x14]',
        0x6DD4: 'svc\t#0x4', 0x6E1A: 'ldr\tr3, [r6, r4]',
        0x6E1E: 'str\tr3, [r5]', 0x6EAE: 'svc\t#0x4', 0x6EE6: 'ldr\tr0, [r4]',
        0x6EE8: 'str\tr0, [r5, r6]',
    }
    for addr, expected in op_expect.items():
        check(checks, f'listing operation 0x{addr:X}', has_op(lines, addr, expected), True)

    # This is the semantic boundary: exact code classifies the candidate, but no context bytes
    # are available here to choose one descriptor or prove the live Fclk object reaches it.
    semantics = {
        'entry_arguments': {
            'incoming_R0': 'context object',
            'incoming_R1': 'dispatcher-normalized constant 1 (saved at [SP+0x38])',
            'incoming_R2': 'dispatcher token; low 12 bits index context table [R0+0x44], so 0x61E -> table[0x61E]',
            'incoming_R3': 'dispatcher-selected value; copied to R11 and inserted into the selected field',
        },
        'descriptor_shape': {
            'outer_entry': 'table[token_index] at [context+0x44]',
            'nested_index': 'outer descriptor bits 12..23',
            'field_start': 'outer descriptor bits 0..5',
            'field_end': 'outer descriptor bits 6..11',
            'wide_flag': 'outer descriptor bit 30',
            'nested_entry': 'table[nested_index]',
        },
        'possible_target_semantics': {
            'normal_field_path': 'For a non-wide descriptor with nested index below 0x671, 0x6DA4 maps descriptor>>12 via SVC #4, reads byte/halfword/word (target supplies type 3), and stores the read word to [SP+0x14]; 0x9D20..0x9D28 merges R3-selected bits into that local word.',
            'wide_or_high_index_path': 'For wide/high-index descriptors, the callback can seed [SP+0x14] from R3 and call 0x6E70; 0x6E70 maps descriptor>>12 via SVC #4 and writes the local word to the mapped address (target supplies type 3).',
            'stub_callee': '0x6C1C and 0x6C1E are BX LR stubs at exact aligned entries.',
        },
        'classification': 'generic descriptor-indexed register field read/modify/write helper; not proven to be the active Fclk callback',
        'active_binding': 'unproven: this result does not recover the live context table/descriptor bytes or dataflow-identify the current dispatcher R4 object with the initializer R5 object',
    }
    result = {
        'status': 'PASS',
        'checks': len(checks),
        'evidence_class': ['observed-bytes', 'static-analysis'],
        'inputs': {'abl': str(ABL), 'dis': str(DIS), 'prior': str(PRIOR)},
        'hashes': {'abl': sha(ABL), 'dis': sha(DIS), 'prior': sha(PRIOR)},
        'conditional_pointer_map': {'base': '0x57100', 'literal': '0x00060BD9', 'thumb_target': '0x9AD9', 'entry': '0x9AD8'},
        'verified_operations': {
            'read_helper_0x6DA4': 'SVC #4 maps descriptor>>12, masks descriptor to offset, then type-3 LDR [mapped+offset] and STR to supplied output pointer',
            'write_helper_0x6E70': 'SVC #4 maps descriptor>>12, masks descriptor to offset, then type-3 LDR from supplied value pointer and STR to mapped+offset',
            'no_op_helper': '0x6C1C/0x6C1E = BX LR',
        },
        'semantics': semantics,
        'checks_detail': checks,
    }
    print(json.dumps(result, separators=(',', ':')))


if __name__ == '__main__':
    main()
