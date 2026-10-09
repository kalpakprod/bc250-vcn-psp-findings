#!/usr/bin/env python3
"""Verify retained instruction bytes; preserve scoped DXE/hook evidence and hashes."""
from pathlib import Path
import hashlib
import json
import re
import struct
import uuid

OUT = Path(__file__).resolve().parent
SMU = Path('import/from-windows/Users/kukuruza/tmp_bc250/upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5').read_bytes()
DXE = Path('evidence/firmware-audit/20260919-clock-trace/modules/0000_AmdNbioSmuV10Dxe_pe32.bin').read_bytes()
counts = {}
for name in ['smu-table-callback.txt','smu-table-apply.txt','scaling-consumers.txt','scaling-consumers-followup.txt']:
    text = (OUT/name).read_text()
    assert text.startswith('PASS: entire loaded program memory')
    assert 'FAILED:' not in text and 'NO EXISTING FUNCTION' not in text
    count = 0
    for addr, raw in re.findall(r'^([0-9a-f]{8}) ([0-9a-f]+) ',text,re.M):
        a = int(addr,16)
        data = bytes.fromhex(raw)
        assert SMU[a:a+len(data)] == data, (name,addr)
        count += 1
    counts[name] = count
# This PE's inspected RVAs equal raw offsets, checked against section mapping in scaling-audit.py.
listing = Path('evidence/firmware-audit/20260919-clock-trace/0000_AmdNbioSmuV10Dxe_pe32.asm').read_text()
ranges = [(0x18cd,0x1b85),(0x1c54,0x1c65),(0x259b,0x25df),(0x4e58,0x4f10),(0x5870,0x58fe)]
selected = []
for line in listing.splitlines():
    m = re.match(r'\s*([0-9a-f]+):\s+((?:[0-9a-f]{2}\s+)+)',line)
    if m and any(lo <= int(m[1],16) < hi for lo,hi in ranges):
        a = int(m[1],16)
        data = bytes.fromhex(m[2])
        assert DXE[a:a+len(data)] == data, hex(a)
        selected.append(line)
(OUT/'scaling-dxe-windows.txt').write_text('\n'.join(selected)+'\n')
hook = dict(guid=str(uuid.UUID(bytes_le=DXE[0x5ca0:0x5cb0])),table_pointer=hex(struct.unpack_from('<Q',DXE,0x5ce0)[0]),first_id=hex(struct.unpack_from('<I',DXE,0x5cb0)[0]),note='Local IDS table immediately terminates; fallback protocol method receives hook ID and descriptor {0, PPTable pointer}. Provider not identified.')
# Selected literal values to corroborate 21E8C helper identities, not runtime reads.
helpers = {hex(a):hex(struct.unpack_from('<I',SMU,a)[0]) for a in [0x17290,0x17294,0x1778c,0x17790,0x17794,0x17134,0x17160,0x177bc,0x17a9c]}
result = dict(status='PASS',instruction_counts=counts,dxe_lines=len(selected),hook=hook,helper_literals=helpers)
(OUT/'scaling-verification.json').write_text(json.dumps(result,indent=2)+'\n')
files = [p for p in OUT.glob('scaling-*') if p.is_file() and p.name != 'scaling-SHA256SUMS']
(OUT/'scaling-SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p)+'\n' for p in sorted(files)))
print(json.dumps(result,indent=2))
