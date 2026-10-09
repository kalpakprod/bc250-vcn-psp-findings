#!/usr/bin/env python3
"""Offline identity, exact literals, PPTable aliases and bounded reader leads."""
from pathlib import Path
import hashlib
import json
import struct

OUT = Path(__file__).resolve().parent
ROM = Path('evidence/donor/retroweb-20260916/BC250_5.00_clv.bin')
SMU = Path('import/from-windows/Users/kukuruza/tmp_bc250/upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5')
DXE = Path('evidence/firmware-audit/20260919-clock-trace/modules/0000_AmdNbioSmuV10Dxe_pe32.bin')
expected = ['ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8', 'cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37', 'b158f039f48db05e352b965a62c8e983a395a4858791c93c73f727285c9ac8d8']
blobs = [p.read_bytes() for p in (ROM, SMU, DXE)]
identities = []
for p, b, h in zip((ROM, SMU, DXE), blobs, expected):
    assert hashlib.sha256(b).hexdigest() == h, p
    identities.append(dict(path=str(p), size=len(b), sha256=h))
r, b, d = blobs
assert r[0x8fef00:0x8fef00+len(b)] == b
u32 = lambda a: struct.unpack_from('<I', b, a)[0]
addresses = [0x170ac,0x17118,0x1711c,0x17120,0x17124,0x17104,0x17108,0x17798,0x177bc]
literals = [dict(address=hex(a), bytes=b[a:a+4].hex(), u32=hex(u32(a)), f32=struct.unpack_from('<f',b,a)[0]) for a in addresses]
assert u32(0x17120)-u32(0x1711c) == 0x380
assert u32(0x17118)-u32(0x1711c) == 0x49c
aliases = {hex(x): hex(u32(0x17120)+x-u32(0x1711c)) for x in (0x80,0x84)}
# Only the literal pool and code span relevant to existing table/clock helpers.
# Unaligned raw instruction candidates are leads, not semantic evidence.
targets = {u32(0x17124)+x for x in (0,0x14,0x30)}
pool = {a:u32(a) for a in range(0x17000,0x18000,4) if u32(a) in targets}
leads = []
for pc in range(0x1b000,0x2b000-2):
    if b[pc]&15 != 1:
        continue
    imm = int.from_bytes(b[pc+1:pc+3],'little')
    target = ((pc+3)&~3) + (imm-65536)*4
    if target in pool:
        entries = [a for a in range(max(0x1b000,pc-0x500),pc+1) if b[a]==0x36 and b[a+2]==0 and b[a+1]&15==1]
        leads.append(dict(pc=hex(pc),literal=hex(target),value=hex(pool[target]),entry_candidate=hex(entries[-1]) if entries else None))
# PE section mapping for exact constant-table source; no guessed raw/RVA equality.
pe = struct.unpack_from('<I',d,0x3c)[0]
n, opt = struct.unpack_from('<H',d,pe+6)[0], struct.unpack_from('<H',d,pe+20)[0]
sections=[]
for i in range(n):
    off=pe+24+opt+i*40
    size,va,rawsize,raw=struct.unpack_from('<IIII',d,off+8)
    sections.append((va,rawsize,raw))
def rawoff(va):
    return next(raw+va-base for base,size,raw in sections if base<=va<base+size)
def cstring(va):
    off=rawoff(va)
    return d[off:d.index(0,off)].decode('ascii')
constants=[]
for offset,label in ((0x400,0x72a0),(0x404,0x72c0)):
    raw=rawoff(0x5d20+offset)
    constants.append(dict(pptable_offset=hex(offset),source_rva=hex(0x5d20+offset),file_offset=hex(raw),bytes=d[raw:raw+4].hex(),u32=struct.unpack_from('<I',d,raw)[0],debug_label=cstring(label)))
result=dict(identities=identities,rom_body_offset='0x8fef00',literals=literals,relative_aliases=aliases,output_addresses=['0x13488','0x134a4'],dxe_template=constants,l32r_leads=leads,coverage='literal pool [0x17000,0x18000); raw l32r candidates [0x1b000,0x2b000), not exhaustive xrefs')
(OUT/'scaling-literals.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
