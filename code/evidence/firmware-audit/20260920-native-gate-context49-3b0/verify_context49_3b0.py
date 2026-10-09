#!/usr/bin/env python3
"""Exact ABL1 context+0x49/+0x3B0 source and width check.

Read-only; no ROM/candidate or runtime action.
"""
from __future__ import annotations
import hashlib,json,re,struct
from pathlib import Path
ROOT=Path('/home/OWNER/orca/projects/bc250')
OUT=Path(__file__).resolve().parent
ABL=ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
DIS=ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt'
EXPECTED={ABL:'af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a',DIS:'b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65'}
checks=[]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ck(name,got,expected):
 ok=got==expected; checks.append({'name':name,'status':'PASS' if ok else 'FAIL','got':got,'expected':expected})
 if not ok: raise AssertionError(f'{name}: got {got!r} expected {expected!r}')
def raw(buf,off,hx,name): ck(name,buf[off:off+len(bytes.fromhex(hx))].hex(),hx)
for p in (ABL,DIS): ck(f'exists:{p.name}',p.exists(),True)
for p,h in EXPECTED.items(): ck(f'hash:{p.name}',sha(p),h)
b=ABL.read_bytes(); t=DIS.read_text(errors='replace'); ck('ABL size',len(b),94624)
# Helper 0x109BC: input byte, optional indirect callback, output-byte write into +0x49.
for off,hx,name in [
 (0x109c4,'9df80410','helper reads caller input byte from saved R1'),
 (0x109d4,'0078','helper reads global callback gate byte'),
 (0x109d8,'d4f8b023','helper loads callback pointer from context +0x3B0'),
 (0x109dc,'01a9','helper passes SP+4 as output-byte pointer'),
 (0x109de,'2046','helper passes context as R0'),
 (0x109e0,'9047','helper BLX through +0x3B0 pointer'),
 (0x109e2,'9df80400','helper reads one byte from callback output pointer'),
 (0x109e6,'84f84900','helper stores one byte to context +0x49'),
 (0x109f4,'94f84900','helper reloads context +0x49 for subsequent index arithmetic'),
]: raw(b,off,hx,name)
# Initializer's first 109BC call explicitly proposes byte index zero.
for off,hx,name in [
 (0x74f6,'0020','initializer sets R0=0 before selection helper'),
 (0x74fc,'0146','initializer copies zero into R1 input byte'),
 (0x74fe,'2846','initializer passes context in R0'),
 (0x7500,'09f05cfa','initializer calls helper 0x109BC'),
]: raw(b,off,hx,name)
# Callback address-construction uses +0x49 as an 8-bit selector in each relevant branch.
for off,hx,name in [
 (0x9c44,'95f84900','type-branch reads +0x49 byte'),
 (0x9c52,'95f84910','type-1 address path reads +0x49 byte'),
 (0x9c8c,'95f84910','type-2 address path reads +0x49 byte'),
 (0x9cbc,'95f84910','type-3 address path reads +0x49 byte'),
 (0x9cd4,'95f84900','post-read path reads +0x49 byte'),
 (0x9d9c,'95f84910','write path type-1 reads +0x49 byte'),
 (0x9dd2,'95f84910','write path type-2 reads +0x49 byte'),
 (0x9e04,'95f84910','write path post-branch reads +0x49 byte'),
]: raw(b,off,hx,name)
# Sole direct writers in exact listing census.
plus49_stores=[ln.strip() for ln in t.splitlines() if re.search(r'\bstrb(?:\.w)?\s+r\d+,\s*\[r\d+,\s*#0x49\]',ln,re.I)]
plus3b0_stores=[ln.strip() for ln in t.splitlines() if re.search(r'\bstr(?:\.w)?\s+r\d+,\s*\[r\d+,\s*#0x3b0\]',ln,re.I)]
ck('sole direct +0x49 writer count',len(plus49_stores),1)
ck('sole direct +0x49 writer address',plus49_stores[0].split(':',1)[0],'109e6')
ck('sole direct +0x49 writer opcode', 'strb.w' in plus49_stores[0].lower() and '#0x49' in plus49_stores[0].lower(), True)
ck('sole direct +0x3B0 writer count',len(plus3b0_stores),1)
ck('sole direct +0x3B0 writer address',plus3b0_stores[0].split(':',1)[0],'c058')
ck('sole direct +0x3B0 writer opcode', 'str.w' in plus3b0_stores[0].lower() and '#0x3b0' in plus3b0_stores[0].lower(), True)
# Literal pool for the same initializer block: +0x44/+0x4C/+0x3B0/+0x3AC values.
for off,val,name in [(0xc3cc,0x6e5145,'literal for +0x44'),(0xc3d0,0x6e5104,'literal for +0x4C'),(0xc3d4,0x6e5082,'literal for +0x3B0'),(0xc3d8,0x6e5041,'literal for +0x3AC')]:
 ck(name,struct.unpack_from('<I',b,off)[0],val)
# Same-object write neighborhood.
raw(b,0xc050,'4864','same initializer writes +0x44')
raw(b,0xc054,'c864','same initializer writes +0x4C')
raw(b,0xc058,'c1f8b003','same initializer writes +0x3B0')
# Existing conditional local mapping is used only for the previously anchored +0x660 callback literal.
ck('conditional base local callback pointer',0x60bd9-0x57100,0x9ad9)
ck('conditional base local callback entry',((0x60bd9-0x57100)&~1),0x9ad8)
external_target=0x6e5082-0x57100
ck('0x3B0 literal is outside exact ABL1 payload under base 0x57100',external_target>=len(b),True)
# Listing confirms the call result register is not consumed before the output-byte load.
for needle,name in [('blx\tr2','indirect callback call exists'),('ldrb.w\tr0, [sp, #0x4]','callback output-byte load exists'),('strb.w\tr0, [r4, #0x49]','output byte stored to +0x49')]:
 ck(name,needle in t.lower(),True)
result={
 'status':'UNRESOLVED_SOURCE','decision':'DO_NOT_ASSIGN_EXACT_CONTEXT49_VALUE_OR_LOCAL_3B0_TARGET',
 'field_widths':{
   'context_plus_0x49':{'width':'u8','source':'helper 0x109BC: [SP+4] after optional BLX callback; written by STRB at 0x109E6','consumer':'callback 0x9AD8 uses LDRB and bit shifts/bit tests in address construction'},
   'context_plus_0x3B0':{'width':'u32 function-pointer field','source':'initializer store at 0xC058 from literal pool 0xC3D4=0x006E5082','consumer':'helper 0x109BC LDR.W +0x3B0 then BLX R2 at 0x109E0'},
 },
 'value_source':{
   'plus_0x49':'initializer call 0x7500 proposes input byte 0; helper 0x109BC can keep that byte if global gate at 0x6E130 is nonzero, or call the +0x3B0 callback when gate is zero; callback may overwrite the SP+4 output byte. BLX return R0 is ignored, so final +0x49 remains unknown without the callback target/runtime gate.',
   'plus_0x3B0':'exact literal is 0x006E5082; under conditional local base 0x57100 it maps to 0x68DF82, outside the 0x171A0-byte payload. It is not an anchored local ABL1 target.',
 },
 'address_use':{
   'callback_entry':'0x9AD8 (conditional anchor 0x60BD9-0x57100=0x9AD9 Thumb pointer)',
   'plus_0x49_paths':['0x9C44','0x9C52','0x9C8C','0x9CBC','0x9CD4','0x9D9C','0x9DD2','0x9E04'],
   'construction':'u8 value is shifted/tested and merged into constructed descriptor/address word; exact address remains conditional on this byte and other runtime fields.'
 },
 'inputs':{str(p.resolve()):{'size':p.stat().st_size,'sha256':sha(p)} for p in (ABL,DIS)},
 'checks':{'passed':sum(x['status']=='PASS' for x in checks),'failed':sum(x['status']=='FAIL' for x in checks),'total':len(checks)},
 'evidence_class':['observed-bytes','static-analysis'],
 'limitations':['No runtime callback execution or output-byte capture.','No context+0x44 pointer analysis; that ownership remains a separate worker scope.','No physical register, MMIO, clock, or hardware claim.'],
 'checks_detail':checks,
}
(OUT/'context49-3b0-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':result['status'],'decision':result['decision'],'checks':result['checks'],'field_widths':result['field_widths'],'value_source':result['value_source']},sort_keys=True))
raise SystemExit(0 if result['checks']['failed']==0 else 1)
