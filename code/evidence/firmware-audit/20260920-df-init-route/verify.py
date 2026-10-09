"""Bounded byte audit and static data derivation; never executes SMU code."""
import hashlib
import json
import re
import struct
from pathlib import Path

out = Path(__file__).resolve().parent
rom_path = Path('evidence/donor/retroweb-20260916/BC250_5.00_clv.bin')
smu_path = Path('import/from-windows/Users/kukuruza/tmp_bc250/upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5')
rom, b = rom_path.read_bytes(), smu_path.read_bytes()
assert len(rom) == 16777216 and len(b) == 262400
assert hashlib.sha256(rom).hexdigest() == 'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
assert hashlib.sha256(b).hexdigest() == 'cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37'
assert rom[0x8fef00:0x8fef00+len(b)] == b

def word(a):
    return struct.unpack_from('<I', b, a)[0]

counts = {}
for name in ('df-init.txt', 'df-init-side.txt'):
    listing = (out / name).read_text()
    rows = re.findall(r'^([0-9a-f]{8}) ([0-9a-f]+) (.+)$', listing, re.M)
    assert rows, name
    for address, raw, instruction in rows:
        a, data = int(address, 16), bytes.fromhex(raw)
        assert b[a:a+len(data)] == data, (name, address)
    counts[name] = len(rows)

# Literal values and decisive instruction windows are checked, not inferred from labels.
assert word(0x171ec) == 0xcee0
assert word(0x17194) == 0x1105c
assert word(0x170b0) == 0x15774 and word(0x15778) == 8
assert word(0x79fc) == 0x1c3b0
for a, raw in {
    0x1c3b8: 'a0c105', 0x1c3be: 'a0e005', 0x1c3c3: 'b0b074',
    0x1c3cc: 'a0a875', 0x1c3cf: 'a5c601',
    0x1e03e: '224411324412', 0x1e085: '76ae1b',
    0x1e088: 'e20aa0', 0x1e092: 'e08ea04088b092c82c997c',
    0x1e05a: '76a81a', 0x1e05d: 'e20af0',
    0x1e44e: '8203f7', 0x1e45d: '9876',
    0x1e1dc: '8265e8', 0x1e1ee: '6265e9', 0x1e1f7: '4265ea',
}.items():
    data = bytes.fromhex(raw)
    assert b[a:a+len(data)] == data, hex(a)

branches = []
for name, vector, base in (('config != 7', 0xcf80, 0xcf0c), ('config == 7', 0xcfd0, 0xcfac)):
    indices = list(b[vector:vector+4])
    pointers = [base + i*40 if i != 255 else None for i in indices]
    branches.append({'branch':name, 'indices':indices, 'row_pointers':[hex(p) if p is not None else None for p in pointers]})
assert branches[0]['row_pointers'] == ['0xcf84','0xcf5c','0xcf34','0xcf0c']
assert branches[1]['row_pointers'] == ['0xcfac',None,None,None]
mask, aperture = word(0x17134), word(0x17160) + 0x200
assert mask == 0xfffff and aperture == 0x1100000
registers = [hex((word(a)&mask)+aperture) for a in range(0x15130,0x15150,4)]
assert registers == ['0x115c9a0','0x115c9a4','0x115c9a8','0x115c9ac','0x116c1a0','0x116c1a4','0x116c1a8','0x116c1ac']
print(json.dumps({'status':'PASS','evidence_class':'observed-bytes/static-analysis',
    'instruction_byte_checks':counts, 'branches':branches,
    'mailbox_argument_fields':{'31:24':'CEE0+11; bitmask used by 1EF18','7:0':'CEE0+12','16':'1105C+2A','17':'1105C+2B'},
    '1e1d0_store_addresses':[hex(word(0x17218)+x) for x in (0x3a0,0x3a4,0x3a8)],
    '1e260_store_addresses':registers,
    'limitations':['No CPU emulation or board execution.', 'Initial config word 8 is not a live readback.',
        'Instruction byte equality does not validate all decompiler semantics; loopgtz interpreted from assembly.',
        'Indirect/runtime writers and full transitive side callees are not exhausted.',
        'Queue5 naming inherited; handler pointer checked, BIOS sender not located.']},indent=2))
