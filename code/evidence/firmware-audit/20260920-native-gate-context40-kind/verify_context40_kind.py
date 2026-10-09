#!/usr/bin/env python3
"""Exact context+0x40 source and kind-branch capability check."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path('/home/OWNER/orca/projects/bc250');OUT=Path(__file__).resolve().parent
ABL=ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
DIS=ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt'
EXPECTED={ABL:'af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a',DIS:'b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65'}
checks=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ck(name,got,exp):
 ok=got==exp;checks.append({'name':name,'status':'PASS' if ok else 'FAIL','got':got,'expected':exp})
 if not ok:raise AssertionError(f'{name}: got {got!r} expected {exp!r}')
def raw(buf,off,hx,name):ck(name,buf[off:off+len(bytes.fromhex(hx))].hex(),hx)
for p in EXPECTED:ck('exists:'+p.name,p.exists(),True)
for p,h in EXPECTED.items():ck('hash:'+p.name,sha(p),h)
b=ABL.read_bytes();t=DIS.read_text(errors='replace');ck('ABL size',len(b),94624)
# Initializer source chain: parent R5=arg0, child R4=[arg1+0x3C4], [child+4] -> [parent+0x40].
for off,hx,name in [(0x7378,'2de9f043','initializer prologue'),(0x737c,'0546','parent R5=arg0'),(0x7384,'0e46','source R6=arg1'),(0x73ae,'d6f8c443','child R4=[R6+0x3C4]'),(0x73b2,'ac60','stores child at parent+0x8'),(0x73b6,'6068','loads child+0x4'),(0x73b8,'2864','stores value at parent+0x40')]:raw(b,off,hx,name)
# Callback consumes source and merges high fields.
for off,hx,name in [(0x9b82,'286c','callback reads context+0x40'),(0x9b88,'61f3d336','BFI context bits15..19'),(0x9b8c,'c0f30751','UBFX context bits20..27'),(0x9b90,'000f','LSRS context bits28..31'),(0x9b98,'60f31f76','BFI context bits28..31'),(0x9c00,'c6f3c260','kind extract bits27..29'),(0x9c08,'23d00228','kind1 branch'),(0x9c0a,'02283ed0','kind2 branch'),(0x9c0e,'032854d0','kind3 branch'),(0x9c12,'04285bd0','kind4 branch')]:raw(b,off,hx,name)
# Symbolic merge: raw fallback descriptor 0x006F47C0, mask from exact BFI destinations.
raw_desc=0x006f47c0;mask=0xffff8000
def merged(src):return (raw_desc & ~mask)|(src&mask)
def kind(src):return (merged(src)>>27)&7
def bit30(src):return (merged(src)>>30)&1
for src,k in [(0x08000000,1),(0x10000000,2),(0x18000000,3),(0x20000000,4)]:
 ck(f'source high bits select kind {k}',kind(src),k);ck(f'source high bits kind {k} bit30 zero',bit30(src),0);ck(f'source high bits kind {k} low12 preserved',merged(src)&0xfff,0x7c0)
ck('merge preserves low15',all(merged(src)&0x7fff==raw_desc&0x7fff for src in [0,0x08000000,0x10000000,0x18000000,0x20000000]),True)
# Same exact listing source/consumer labels used to guard address assumptions.
for needle,name in [('7378:','initializer label'),('9b82:','callback context+0x40 read'),('9c00:','kind dispatch')]:ck(name,needle in t.lower(),True)
result={
 'status':'CAPABILITY_STATIC_RUNTIME_VALUE_UNRESOLVED','decision':'CONTEXT40_CAN_SELECT_KIND1_TO_KIND4_BUT_ACTIVE_PROVIDER_AND_RUNTIME_KIND_ARE_UNPROVEN',
 'source_chain':'parent context R5=arg0; child R4=[arg1+0x3C4]; context+0x40=[child+0x4] (full u32)',
 'merge':{'mask':'0xFFFF8000','preserved':'descriptor low15 including low12','replaced':'context bits15..31 in three BFI operations'},
 'kind_capability':{'examples':{'0x08000000':'kind1','0x10000000':'kind2','0x18000000':'kind3','0x20000000':'kind4'},'low12':'0x7C0 preserved','interpretation':'structural branch capability only; no runtime source value'},
 'active_boundary':'The exact current dispatcher R0 object is not joined to the 0x7378 parent R5 object; child/provider value and runtime HEAP/fallback selection are unavailable. No mapped physical address follows.',
 'checks':{'passed':sum(x['status']=='PASS' for x in checks),'failed':sum(x['status']=='FAIL' for x in checks),'total':len(checks)},
 'evidence_class':['observed-bytes','static-analysis'],
 'limitations':['No runtime callback/provider capture.','No SVC#4 translation or hardware result.','No candidate built.'],
 'checks_detail':checks,
}
(OUT/'context40-kind-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':result['status'],'decision':result['decision'],'source_chain':result['source_chain'],'merge':result['merge'],'kind_capability':result['kind_capability'],'checks':result['checks']},sort_keys=True))
raise SystemExit(0 if result['checks']['failed']==0 else 1)
