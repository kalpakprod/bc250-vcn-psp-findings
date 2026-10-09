"""Pinned-byte audit of host domain selection; no hardware or image writes."""
import hashlib
import json
import struct
from pathlib import Path

rom = Path('evidence/donor/retroweb-20260916/BC250_5.00_clv.bin').read_bytes()
b = Path('import/from-windows/Users/kukuruza/tmp_bc250/upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5').read_bytes()
assert len(rom) == 16777216 and len(b) == 262400
assert hashlib.sha256(rom).hexdigest() == 'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
assert hashlib.sha256(b).hexdigest() == 'cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37'
assert rom[0x8fef00:0x8fef00+len(b)] == b

def u32(offset):
    return struct.unpack_from('<I', b, offset)[0]

checks = {
    0x2ea08: '364100ad02e55ed21c4c',
    0x2ea14: 'a0a0f5a73c3fbcca',
    0x2ea1c: 'd106a6d0baa0b81b1c38871b3ac71b37',
    0x2ea3b: '034c50',
    0x2ea41: '65d4ff',
    0x2e794: '98178807',
    0x2e79d: '979802462700',
    0x2e82d: '7302537342174b33cb22',
    0x2392e: 'a5c9ff',
}
for address, expected in checks.items():
    raw = bytes.fromhex(expected)
    assert b[address:address+len(raw)] == raw, hex(address)
assert u32(0x7554) == 0x2ea08
base = u32(0x18234)
assert base == 0x13eec
mapping = struct.unpack_from('<20I', b, base+8)
assert mapping == (13,0,1,2,3,4,5,6,7,10,24,19,20,21,22,23,11,8,9,12)
assert (u32(0x18238)-base)//12 == 20
excluded = set(range(14,19))
assert not excluded.intersection(mapping)
rows = [{'api_index': i+1, 'descriptor': hex(d), 'rejected_by_descriptor_check': d in (19,20),
         'target_address': hex(base+0x140+(i+1)*12)} for i,d in enumerate(mapping)]
print(json.dumps({'status':'PASS', 'evidence_class':'observed-bytes/static-analysis',
    'mapping':rows, 'df_descriptors_absent':[hex(d) for d in sorted(excluded)],
    'checked_windows':{hex(k):v for k,v in checks.items()},
    'limits':['Static initial mapping only; runtime mapping writes not exhaustively traced.',
              'Actuator is gated by state words at base+0 and base+4; setter invocation alone is not actuation proof.',
              'No physical clock labels, supported voltage or boot outcome established.']},indent=2))
