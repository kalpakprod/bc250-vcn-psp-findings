#!/usr/bin/env python3
"""Direct-byte/table checks and explicitly synthetic host models, not firmware emulation."""
import hashlib,json,re,struct,uuid,subprocess,platform
from pathlib import Path
P=Path(__file__).resolve().parent
rows=json.loads((P/'census.json').read_text())['records']
def image(name):
 r=next(r for r in rows if r.get('ui')==name); b=(P/(name+'.bin')).read_bytes()
 return b,int(r['imagebase'],16),int(r['delta'],16)
c,cb,cd=image('CbsBasePei');f,fb,fd=image('AmdFabricAriPei')
def check(b,d,rva,h):assert b[rva-d:rva-d+len(bytes.fromhex(h))]==bytes.fromhex(h),(hex(rva),h)
checks=[('CBS InstallPpi',c,cd,0x622,'8b4218ffd0'),('CBS dispatch compare',c,cd,0x42b,'8b51143b55107567'),('CBS callback call',c,cd,0x36de,'e80d000000'),('CBS size branch',c,cd,0x3701,'39017314'),('CBS signature store',c,cd,0x3728,'c70224494e56'),('CBS size constant',c,cd,0x11883,'b8e5150000'),('Fabric signed request',f,fd,0x3728,'6afee891ffffff'),('Fabric query',f,fd,0x1d72,'e899190000'),('Fabric fill',f,fd,0x1dcc,'e83f190000'),('Fabric first reader',f,fd,0x1dfc,'813e24494e56'),('Fabric record compare',f,fd,0x1e67,'668b06663b4508'),('Fabric CreateHob',f,fd,0x2685,'ff5134'),('Fabric event request',f,fd,0x420,'6803000020'),('Fabric lookup10FF',f,fd,0x1eb0,'68ff100000'),('Fabric lookup1104',f,fd,0x1f8b,'6804110000')]
for label,b,d,a,h in checks:check(b,d,a,h)
def u32(b,o):return struct.unpack_from('<I',b,o)[0]
def raw(va,base,delta):return va-base-delta
installer=struct.unpack_from('<III',c,0x13d44)
assert installer==(0x80000010,0x9ecde2c,0x9ecdf4c)
assert u32(c,0x13d30)==cb+0x250
assert c[0x13c10:0x13c20]==uuid.UUID('04126c85-5c4e-458f-abc1-29f1f7da365e').bytes_le
assert struct.unpack_from('<QQII',c,0x13c30)==(0xffffffff,0,cb+0x36c0,0xfffffffe)
assert struct.unpack_from('<QQI',c,0x13c90)==(0xffffffff,0,0x9ecde4c)
ids=raw(0x9e328f4,fb,fd);assert f[ids:ids+8]==b'$IDS\x01\x00\x00\x00'
tab=raw(u32(f,raw(0x9e32914,fb,fd)),fb,fd)
assert struct.unpack_from('<IIIIII',f,tab)==(0x20000003,fb+0x1e8f,0x20000004,fb+0x1f6d,0xffffffff,0xffffffff)
heapguid=uuid.UUID(bytes_le=f[raw(0x9e32720,fb,fd):raw(0x9e32720,fb,fd)+16]);assert str(heapguid)=='d97d161a-16cd-4ada-b9f6-aec3f9fccc2c'
# Per-image TE delta is mandatory (Fabric 198, CBS 190).
assert (cd,fd)==(0x190,0x198)
assert c==Path('evidence/firmware-audit/20260919-clock-trace/modules/0004_CbsBasePei_te.bin').read_bytes()
# Table predicate model, with positive and negative controls from decoded rows.
outer_cpu,_,nested=struct.unpack_from('<QQI',c,0x13c90)
inner_cpu,_,handler,registered=struct.unpack_from('<QQII',c,raw(nested,cb,cd))
for cpu in (0x840f00,0x123456):
 for event in (0xfffffffe,0xffffffff,0xb000000a):
  selected=(outer_cpu in (cpu,0xffffffff) and inner_cpu in (cpu,0xffffffff) and event==registered and handler!=0)
  assert selected==(event==0xfffffffe)
ftext=(P/'AmdFabricAriPei-0.asm').read_text()
reader_calls=re.findall(r'^\s*([0-9a-f]+):[^\n]*call\s+0x1d3c\s*$',ftext,re.M)
assert reader_calls==['1ebd','1f94']
assert struct.pack('<I',fb+0x1d3c) not in f
assert sum(bool(r.get('heap_guid_offsets')) for r in rows)==42
assert struct.unpack('<i',b'\xfe\xff\xff\xff')[0]==-2
assert ((~1)&0xffffffff)==((0-2)&0xffffffff)==0xfffffffe
required=0x15e5+0x20; assert required==0x1605
# Synthetic lookup model mirrors widths/terminator; values are markers, NOT settings.
tokens=(0x11ed,0x1204,0x1331,0x1364,0x1373,0x1374)
blob=bytearray(b'$INV'+struct.pack('<I',1)+bytes(24));values={}
for i,t in enumerate(tokens):
 width=4 if t==0x1364 else 1;v=0x12345678 if width==4 else i+1;values[t]=v
 blob+=struct.pack('<HB',t,2 if width==4 else 0)+v.to_bytes(width,'little')
blob+=b'\xff\xff'
def lookup(b,t):
 o=0x20
 while int.from_bytes(b[o:o+2],'little')!=0xffff:
  width=1<<(b[o+2]&3); value=int.from_bytes(b[o+3:o+3+width],'little')
  if int.from_bytes(b[o:o+2],'little')==t:return value
  o+=3+width
 return None
for t,v in values.items():assert lookup(blob,t)==v
assert lookup(blob,0x1365) is None
# Focused windows retain the real branches, not a reconstructed pseudocode only.
w=[]
for name,ranges in [('CbsBasePei',[(0x240,0x4c8),(0x610,0x64d),(0x36c0,0x3741),(0xe3f6,0xe430),(0x11848,0x1188a)]),('AmdFabricAriPei',[(0x240,0x260),(0x3b6,0x3bb),(0x41f,0x42a),(0x1c8f,0x1fde),(0x2634,0x26d5),(0x3290,0x3434),(0x36c0,0x3736),(0x3b60,0x3bba)])]:
 lines=(P/(name+'-0.asm')).read_text().splitlines()
 for lo,hi in ranges:
  w.append(name+' RVA '+hex(lo)+'..'+hex(hi))
  for line in lines:
   m=re.match(r'\s*([0-9a-f]+):',line)
   if m and lo<=int(m[1],16)<hi:w.append(line)
(P/'lifetime-windows.txt').write_text('\n'.join(w)+'\n')
result=dict(input_sha256=json.loads((P/'census.json').read_text())['sha256'],module_hashes={r['ui']:r['sha256'] for r in rows if r['guid_offsets']},raw_checks=[x[0] for x in checks],table_tests=6,synthetic_reader_tests=7,required_size=hex(required),heap_guid=str(heapguid),hob_layout={'guid_header':hex(0x18),'heap_header':hex(0x10),'INV_offset':hex(0x28),'requested_hob_size_before_alignment':hex(required+0x68+0x10+0x18),'sentinel_INV_offset':hex(required+0x64)},model_limit='Host structural models only; no firmware execution or dynamic buffer capture.',python=platform.python_version(),objdump=subprocess.check_output(['objdump','--version'],text=True).splitlines()[0])
(P/'lifetime-tests.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS',len(checks),'raw instruction windows; provider/IDS/HOB structures; 6 dispatch + 7 synthetic lookup controls; size=0x1605')
