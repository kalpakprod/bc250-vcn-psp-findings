#!/usr/bin/env python3
"""Independent exact-byte decode of the AmdMemAm4Pei APOB service pointer."""
from pathlib import Path
import hashlib
import json
import struct

ROOT = Path('/home/OWNER/orca/projects/bc250')
ROM = ROOT / 'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
CENSUS = ROOT / 'evidence/firmware-audit/20260919-inv-token-consumers/census.json'
EXPECTED_ROM = 'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
EXPECTED_MODULE = '1ef4e7b944672a9a48b6fcb16c4d35cb6d23bb8306429dc3eb10ee1d0c7bb5f8'
EXPECTED_POINTER = 0x09E3B14C
RVA = 0x08A0

census = json.loads(CENSUS.read_text())
row = next(item for item in census['records'] if item.get('ui') == 'AmdMemAm4Pei')
body = ROOT / 'evidence/firmware-audit/20260919-inv-token-consumers' / (row['stem'] + '.bin')
blob = body.read_bytes()
section = next(item for item in row['sections'] if item['rva'] <= RVA < item['rva'] + item['size'])
raw = RVA - section['rva'] + section['raw']
instruction = blob[raw:raw + 5]
pointer = struct.unpack_from('<I', instruction, 1)[0]
rom_hash = hashlib.sha256(ROM.read_bytes()).hexdigest()
module_hash = hashlib.sha256(blob).hexdigest()
checks = {
    'rom_hash_matches': rom_hash == EXPECTED_ROM,
    'module_hash_matches': module_hash == EXPECTED_MODULE,
    'opcode_is_push_imm32': instruction[:1] == b'\x68',
    'pointer_is_full_value': pointer == EXPECTED_POINTER,
    'pointer_differs_from_truncated_root_value': pointer != 0x009E3B14,
}
result = {
    'rom_sha256': rom_hash,
    'module': str(body),
    'module_sha256': module_hash,
    'imagebase': hex(row['imagebase']),
    'module_rva': hex(RVA),
    'raw_offset': hex(raw),
    'bytes': instruction.hex(),
    'decoded': f'push imm32 0x{pointer:08X}',
    'expected_full_pointer': '0x09E3B14C',
    'root_truncated_spelling': '0x9E3B14',
    'checks': checks,
    'status': 'PASS' if all(checks.values()) else 'FAIL',
}
print(json.dumps(result, indent=2))
if result['status'] != 'PASS':
    raise SystemExit(1)
