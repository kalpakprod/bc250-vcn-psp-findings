import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
CORPUS = ROOT / 'evidence/firmware-audit/20260919-inv-token-consumers'
STEM = 'AmdNbioSmuV10Pei-905b8be68afd'
b = (CORPUS / (STEM + '.bin')).read_bytes()
assert hashlib.sha256(b).hexdigest() == '905b8be68afd1dce5453acef8273cbf94bdae6d41823c25438ace286348e2c80'
assert b[:2] == b'VZ'
delta = struct.unpack_from('<H', b, 6)[0] - 40
rows = json.loads((CORPUS / (STEM + '.instructions.json')).read_text())
windows = [(0x1880,0x18e9),(0x2190,0x2263)]
checked=[]
for r in rows:
    if any(lo <= r['rva'] <= hi for lo,hi in windows):
        expected = bytes.fromhex(r['bytes'])
        off = r['rva'] - delta
        assert b[off:off+len(expected)] == expected, hex(r['rva'])
        checked.append(r)
anchors={0x18a5:'c745f419a00000',0x18b7:'8d55f4',0x18ba:'52',0x18bb:'e850090000',
         0x2214:'8b4508',0x2217:'8b08',0x2219:'51',0x221a:'e871ffffff',
         0x21b8:'8b5104',0x21bb:'3b5508',0x18d0:'8139cc9910db'}
# Verify explicit byte anchors independently of the instruction-row labels.
for rva,h in anchors.items():
    expected=bytes.fromhex(h)
    assert b[rva-delta:rva-delta+len(expected)]==expected, hex(rva)
edges={}
for target in [0x2190,0x2210]:
    found=[r['rva'] for r in rows if r['mnemonic'] in ('call','jmp') and r['operands']==hex(target)]
    edges[hex(target)]=[hex(x) for x in found]
assert edges=={'0x2190':['0x221a'],'0x2210':['0x18bb']}
result={'status':'PASS','module':STEM,'module_sha256':hashlib.sha256(b).hexdigest(),
        'rva_to_raw_delta':delta,'verified_instruction_rows':len(checked),'direct_edges':edges,
        'handle':'0xa019','not_nvtb':'0x4254564e',
        'finding':'Direct lookup uses structure handle A019; returned payload is checked for DB1099CC. This direct path is not an NVTB voltage-token lookup.',
        'limits':'Direct entry edges and two windows only. Computed calls, interior entries, pointer escapes and alternate parser paths unresolved.',
        'rows':checked}
(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS SMU PEI direct heap argument A019; '+str(len(checked))+' instruction rows byte-matched')
