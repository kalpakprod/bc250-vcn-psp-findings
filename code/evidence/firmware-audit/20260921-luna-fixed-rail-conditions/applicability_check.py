#!/usr/bin/env python3
"""Read-only direct CLV PEI FFS/depex and existing-decoding applicability check."""
import hashlib
import json
import re
import uuid
from pathlib import Path

ROOT = Path('/home/OWNER/orca/projects/bc250')
DONOR = ROOT / 'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
UEFI_ROOT = ROOT / 'evidence/firmware-audit/20260920-clv-uefitool-native-run/BC250_5.00_clv.bin.dump'
MODULES = {
    'ISL69247': {'guid': '6E6D2018-28D0-4AD3-BEB3-B48E4981707D', 'ffs_offset': 0xED2C30,
                 'main_start': 0x249, 'main_ret': 0x43B,
                 'disasm': 'evidence/firmware-audit/20260920-fixed-voltage-independent-decode/ISL69247.disasm.txt',
                 'tecopy': 'evidence/firmware-audit/20260920-fixed-voltage-independent-decode/extracted/ISL69247.te.bin'},
    'ISL95712': {'guid': '02544BE0-2CB9-4B75-8111-CD8CDC07B837', 'ffs_offset': 0xED3D48,
                 'main_start': 0x249, 'main_ret': 0x312,
                 'disasm': 'evidence/firmware-audit/20260920-fixed-voltage-independent-decode/ISL95712.disasm.txt',
                 'tecopy': 'evidence/firmware-audit/20260920-fixed-voltage-independent-decode/extracted/ISL95712.te.bin'},
}

def sha256(data):
    return hashlib.sha256(data).hexdigest()

buf = DONOR.read_bytes()
result = {
    'status': 'PASS',
    'scope': 'read-only PEI depex and entry-branch applicability; no token 0x1364 scan, no hardware/register/ROM change',
    'donor': {'path': str(DONOR), 'size': len(buf), 'sha256': sha256(buf)},
    'modules': {},
}
for name, module in MODULES.items():
    offset = module['ffs_offset']
    guid = str(uuid.UUID(bytes_le=buf[offset:offset + 16])).upper()
    ffs_type = buf[offset + 0x12]
    attributes = buf[offset + 0x13]
    ffs_size = int.from_bytes(buf[offset + 0x14:offset + 0x17], 'little')
    state = buf[offset + 0x17]
    assert guid == module['guid'] and ffs_type == 6 and state == 0xF8

    depex_offset = offset + 24
    depex_size = int.from_bytes(buf[depex_offset:depex_offset + 3], 'little')
    depex_type = buf[depex_offset + 3]
    depex_body = buf[depex_offset + 4:depex_offset + depex_size]
    assert depex_type == 0x1B and depex_size == 0x28 and len(depex_body) == 0x24

    pos = 0
    parsed = []
    while pos < len(depex_body):
        opcode = depex_body[pos]
        pos += 1
        if opcode == 0x02:
            ppi_guid = str(uuid.UUID(bytes_le=depex_body[pos:pos + 16])).upper()
            pos += 16
            parsed.append({'op': 'PUSH', 'guid': ppi_guid})
        elif opcode in (0x03, 0x08):
            parsed.append({'op': {0x03: 'AND', 0x08: 'END'}[opcode]})
        else:
            raise AssertionError(f'unexpected depex opcode 0x{opcode:02x} at {pos - 1}')
    assert pos == len(depex_body) and [item['op'] for item in parsed] == ['PUSH', 'PUSH', 'AND', 'END']

    te_section_offset = depex_offset + depex_size
    te_section_size = int.from_bytes(buf[te_section_offset:te_section_offset + 3], 'little')
    te_section_type = buf[te_section_offset + 3]
    te_data_offset = te_section_offset + 4
    te_bytes = buf[te_data_offset:te_section_offset + te_section_size]
    assert te_section_type == 0x12 and len(te_bytes) == te_section_size - 4
    extracted_te = (ROOT / module['tecopy']).read_bytes()
    assert te_bytes == extracted_te

    matching_depex = [path for path in UEFI_ROOT.rglob('body.bin')
                      if path.parent.name == '0 PEI dependency section'
                      and any(part.endswith(name) for part in path.parts)]
    assert len(matching_depex) == 1
    uefitool_depex = matching_depex[0].read_bytes()
    assert uefitool_depex == depex_body
    uefitool_info = (matching_depex[0].parent / 'info.txt').read_text()

    disassembly = (ROOT / module['disasm']).read_text().splitlines()
    conditional_jumps = []
    for line in disassembly:
        match = re.match(r'^\s*([0-9a-f]+):\s+[0-9a-f ]+\s+(.+)$', line)
        if not match:
            continue
        address = int(match.group(1), 16)
        instruction = match.group(2).strip()
        opcode = instruction.split()[0]
        if module['main_start'] <= address <= module['main_ret'] and opcode.startswith('j') and opcode != 'jmp':
            conditional_jumps.append({'rva': hex(address), 'instruction': instruction})

    result['modules'][name] = {
        'ffs_guid': guid,
        'ffs_offset': hex(offset),
        'ffs_type': hex(ffs_type),
        'ffs_state': hex(state),
        'ffs_attributes': hex(attributes),
        'ffs_size': hex(ffs_size),
        'depex_section_offset': hex(depex_offset),
        'depex_section_header': buf[depex_offset:depex_offset + 4].hex(' '),
        'depex_body_hex': depex_body.hex(' '),
        'depex_body_sha256': sha256(depex_body),
        'depex_expression': parsed,
        'uefitool_extracted_depex_matches_rom': uefitool_depex == depex_body,
        'uefitool_parsed_expression': uefitool_info.split('Parsed expression:', 1)[1].strip(),
        'te_section_header_offset': hex(te_section_offset),
        'te_data_offset': hex(te_data_offset),
        'te_data_size': len(te_bytes),
        'te_sha256': sha256(te_bytes),
        'te_equals_prior_extracted_copy': te_bytes == extracted_te,
        'main_entry_review_window': {
            'start': hex(module['main_start']),
            'return': hex(module['main_ret']),
            'conditional_jumps': conditional_jumps,
        },
    }

print(json.dumps(result, indent=2, sort_keys=True))
