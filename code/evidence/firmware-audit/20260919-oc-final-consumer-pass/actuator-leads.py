#!/usr/bin/env python3
"""Raw Xtensa literal leads only; candidates require decoded validation."""
from pathlib import Path
import struct, json, hashlib
E = Path(__file__).resolve().parent
b = Path('import/from-windows/Users/kukuruza/tmp_bc250/upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5').read_bytes()
assert hashlib.sha256(b).hexdigest() == 'cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37'
u32 = lambda a: struct.unpack_from('<I', b, a)[0]
# Include interior state aliases; no INV scans or security-field decoding.
pool = {a:u32(a) for a in range(0x17000,0x19000,4) if 0x13474 <= u32(a) <= 0x134dc or u32(a) in [0xee7c,0xf0cc,0x14070,0x1424c]}
leads=[]
for pc in range(0x1b000,0x39000-2):
    if b[pc]&15 != 1: continue
    target=((pc+3)&~3)+(int.from_bytes(b[pc+1:pc+3],'little')-65536)*4
    if target not in pool: continue
    entries=[a for a in range(max(0x1b000,pc-0x1800),pc+1) if b[a]==0x36 and b[a+1]&15==1 and b[a+2]<4]
    leads.append(dict(pc=hex(pc),literal=hex(target),value=hex(pool[target]),entry_candidate=hex(entries[-1]) if entries else None))
result=dict(scope='Raw unaligned l32r candidates, literal pool [17000,19000), code [1b000,39000); entry heuristic only, not xref completeness',pool={hex(k):hex(v) for k,v in pool.items()},leads=leads)
with (E/'actuator-leads.json').open('x') as f: json.dump(result,f,indent=2); f.write('\n')
print(json.dumps(result,indent=2))
