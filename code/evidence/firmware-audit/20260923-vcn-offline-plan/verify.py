"""Offline address/provenance checks. Never imports or invokes board tools."""
import ast
import hashlib
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sources = {}

def read(rel):
    p = ROOT / rel
    b = p.read_bytes()
    sources[str(p)] = hashlib.sha256(b).hexdigest()
    return b

image = read('evidence/donor/retroweb-20260916/BC250_5.00_clv.bin')
assert hashlib.sha256(image).hexdigest() == 'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
base = 'import/from-windows/Users/kukuruza/tmp_bc250/'
source = read(base+'upstream/daveconde-bc250-vcn-enable/enable_vcn.py').decode()
tree = ast.parse(source)
fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_uvd')
# Compile only the isolated pure arithmetic function, never the hardware script.
assert len(fn.body) == 1 and isinstance(fn.body[0], ast.Return)
ns = {'VCN_SEG1_DW': 0x7e00, '__builtins__': {}}
exec(compile(ast.Module(body=[fn], type_ignores=[]), '<isolated _uvd>', 'exec'), ns)
header = Path('/home/OWNER/orca/projects/projector/firmware-analysis/forum-1117702-2026-09-20/runs/kernel_patch_research_20260920T193000Z/linux-v5.10/drivers/gpu/drm/amd/include/asic_reg/vcn/vcn_2_0_0_offset.h')
h = read(str(header)).decode()
rows = []
for name in ['UVD_VERSION','UVD_POWER_STATUS','UVD_CGC_CTRL']:
    offset = int(re.search(r'#define mm'+name+r'\s+(0x[0-9a-fA-F]+)',h)[1],16)
    idx = int(re.search(r'#define mm'+name+r'_BASE_IDX\s+(\d+)',h)[1])
    assert idx == 1
    got = ns['_uvd'](offset)
    assert got == (0x7e00+offset)*4
    rows.append(dict(name=name,segment_index=idx,offset=hex(offset),dword_index=hex(0x7e00+offset),mmio_byte_offset=hex(got)))
assert ns['_uvd'](0x1ec) == 0x1ffb0
# Exercise exact PCI transport method against fake OS calls, no file descriptor opened.
tr = ast.parse(read(base+'upstream/bc250-smu-unlock/bc250_smu/transport.py').decode())
cls = next(n for n in tr.body if isinstance(n,ast.ClassDef))
method = next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='read_smu_reg')
class FakeOS:
    def __init__(self): self.calls=[]
    def pwrite(self,fd,data,offset): self.calls.append(['pwrite',fd,data.hex(),hex(offset)]); return len(data)
    def pread(self,fd,size,offset): self.calls.append(['pread',fd,size,hex(offset)]); return struct.pack('<I',0x12345678)
class FakeSelf:
    _fd=123
    def _lock(self): pass
    def _unlock(self): pass
fake=FakeOS(); env={'os':fake,'struct':struct}
exec(compile(ast.Module(body=[method],type_ignores=[]),'<mock transport>', 'exec'),env)
transport=[]
for address in [0x20f24,0x7fec,0x02402c00,0x02403000]:
    fake.calls=[]
    assert env['read_smu_reg'](FakeSelf(),address)==0x12345678
    assert fake.calls[0][2] == struct.pack('<I',address).hex()
    transport.append(dict(input=hex(address),calls=list(fake.calls)))
record=json.loads(read('evidence/runtime/20260914-board-retrieval/stage2b_writefirst_20260912_052757.json'))
first=record['writes'][0]
assert (int(first['a'],16),int(first['v'],16)) == (0x3e810,6)
assert record['write_count']==59 and record['alive_final'] is True
old=read(base+'recon/robin3_psp_bodies/SMU_OFFCHIP_FW~0x8_0.58.6.0.body')
new=read(base+'upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5')
assert image[0x8fef00:0x93f000] == new
u32=lambda b,o: struct.unpack_from('<I',b,o)[0]
old_literals={hex(a):hex(u32(old,a)) for a in [0x1711c,0x1713c,0x17390]}
new_literals={hex(a):hex(u32(new,a)) for a in [0x1711c,0x1713c,0x17390]}
assert tuple(u32(old,a) for a in [0x1711c,0x1713c,0x17390]) == (0xfffff,0xfffe00,0x150b0)
assert old_literals != new_literals
old_code=old[0x1dd74:0x1dd9b]
assert new.find(old_code) == -1
old_table=[u32(old,0x150b0+i*4) for i in range(29)]
new_table=[u32(new,0x150b0+i*4) for i in range(29)]
assert old_table==new_table and old_table[4]==0x0900c230
assert 0xfffe00+(old_table[4]&0xfffff)+0x200==0x0100c230
# Check branch and global in exact CLV bytes, not copied report text.
t28=image[0x985000:0x99f000]
assert t28[0x121d8:0x121da] == bytes.fromhex('b4b1')
assert u32(t28,0x1220c)==0xe18b70 and u32(t28,0x12214)==0x80000203
branch=struct.unpack_from('<H',t28,0x121d8)[0]
target=0x121d8+4+((branch>>9&1)<<6)+((branch>>3&31)<<1)
assert target==0x12208
pointer=struct.pack('<I',0xe18b70)
pointer_locations=[hex(i) for i in range(len(t28)-3) if t28[i:i+4]==pointer]
result={'classification':'offline source execution with mock transport + byte checks, NOT hardware',
 'p1':{'addresses':rows,'pci_mock':transport,'smn_mmio_alias':'UNPROVEN',
       'gc_control':'0x02402c00 is a retained fabric slice anchor, not established mirror of a named GC MMIO register',
       '0x7fec':'dword index of CGC_CTRL with supplied base, NOT its MMIO byte offset',
       '0x3e810_write_already_recorded':first,'historical_readback_0x3e810':'not present, only C234 commit readback'},
 'p2':{'gate_zero_branch_body_target':hex(target),'gate_pointer_literals_body':pointer_locations,
       'permitted_alternative_request_path':'NOT ESTABLISHED in bounded check',
       'warning':'nonzero gate also requires +0x10/+0x14 fields, not just flag; producer and service semantics unresolved'},
 'p3':{'old_literals':old_literals,'clv_same_offset_literals':new_literals,
       'tables_equal':old_table==new_table,'exact_old_function_occurrences_in_clv':0,
       'old_function_local_store_example':'0x0100c230 <- 0',
       'clv_function_identity':'UNRESOLVED; old 1dd74 disassembly cannot be transferred by address'},
 'sources':sources}
# Verify that all evidence inputs stayed identical throughout this run.
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==v for p,v in sources.items())
(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS: header/_uvd agreement for 3 registers; PCI transport 4 mocked inputs')
print('PASS: historical 0x3e810=6 write confirmed in 59-write evidence')
print('PASS: CLV gate-zero branch targets 0x12208, error literal 0x80000203')
print('PASS: 29 table entries identical, but old SMU function and literals DO NOT match CLV')
print('P1 route selector unresolved; P2 alternative request unresolved; P3 CLV consumer unresolved')
print('All evidence source hashes unchanged; hardware IO=0')
