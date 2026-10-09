#!/usr/bin/env python3
"""Bounded UclkDiv1M0/MemoryPstate semantics check."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
CBS_INS=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/CbsBasePei-6ff112922ad8.instructions.json'
CBS_BIN=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/CbsBasePei-6ff112922ad8.bin'
FAB_INS=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/AmdFabricAriPei-c5b99650a442.instructions.json'
FAB_BIN=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/AmdFabricAriPei-c5b99650a442.bin'
ABL_C=ROOT/'import/from-windows/Users/kukuruza/tmp_bc250/recon/lorek123_psp/ABL1_decompiled.c'
ABL_S=ROOT/'import/from-windows/Users/kukuruza/tmp_bc250/recon/lorek123_psp/ABL1_strings.txt'
SNIP=OUT/'ABL1-memory-sync-snippet.c'; STR=OUT/'ABL1-memory-sync-strings.txt'
EXPECTED={ROM:'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8',CBS_BIN:'6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77',FAB_BIN:'c5b99650a442ed9be1cf3a62e7571f7eb163b9f80a60d4fcc7b3e9afe4506f78',ABL_C:'9501f2ed3abd96ac54cc317c26ae64d068f94a1a0d572d3c886c7877e4bb8f1b',ABL_S:'c27bf19fb46415703c1e761641d3ac08102dda775b9152ea1b6a557c47741170',SNIP:'41906789451feb97fbc323ad84be9589e5fd521ae73feeb663f26ca02a835803',STR:'d17596e7681d383ba273ae4981c3e1d320822a726e05d4f97c9f78890ca1d87a'}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1<<20),b''):h.update(c)
 return h.hexdigest()
def ck(c,l,d=None): checks.append({'label':l,'status':'PASS' if c else 'FAIL','details':d});return c
checks=[]
for p,w in EXPECTED.items():ck(sha(p)==w,'hash:'+str(p),{'observed':sha(p),'expected':w})
cbs={int(x['rva']):x for x in json.loads(CBS_INS.read_text())}
# Exact immediate serializers for both controls.
for r,b in {0x9cc4:'ba04120000',0x9ce4:'8a8230030000',0x9cea:'884103',0xa7e1:'8a826d030000',0xa7e7:'884103',0xa7f3:'ba3d120000'}.items():
 d=cbs.get(r);ck(d is not None and d['bytes']==b,'CbsBase-byte:'+hex(r),{'observed':d,'expected':b})
# No ratio arithmetic is present in these immediate serializer windows.
window=[d for d in cbs.values() if 0x9cc4<=d['rva']<=0x9cea or 0xa7e1<=d['rva']<=0xa7fe]
ck(not any(x['mnemonic'] in ('imul','idiv','div','mul','add','sub','shl','shr') for x in window),'serializer-windows-no-ratio-arithmetic')
# AmdFabric parser census: direct literals for the two serializer records absent;
# its two confirmed direct reader call sites use 0x10FF/0x1104 instead.
fab=json.loads(FAB_INS.read_text())
for lit in ['0x1204','0x123d','0x123D']:
 hits=[d for d in fab if lit.lower() in d.get('operands','').lower()]
 ck(len(hits)==0,'AmdFabric-no-direct-literal:'+lit,hits)
for lit in ['0x10ff','0x1104']:
 hits=[d['rva'] for d in fab if lit in d.get('operands','').lower()]
 ck(len(hits)>0,'AmdFabric-confirmed-literal:'+lit,hits)
# Generic retained ABL source: concrete memory-speed synchronization structure,
# explicitly not exact clv consumer evidence.
snip=SNIP.read_text(); strings=STR.read_text()
for needle in ['Synchronize_Mem_Speed_for_each_c','param_1[3] + 0x20','local_60[0]','Sending_Synchronized_Speed_back']:
 ck(needle in snip,'generic-ABL-snippet:'+needle)
for needle in ['Memory P-state Enabled.','Memory P-state Disabled.','NumOfMemPstates','Current Memory P-state']:
 ck(needle in strings,'generic-ABL-string:'+needle)
result={'status':'PASS' if all(x['status']=='PASS' for x in checks) else 'FAIL','checks':{'passed':sum(x['status']=='PASS' for x in checks),'failed':sum(x['status']=='FAIL' for x in checks),'total':len(checks)},'exact_clv':{'uclk_field':'+0x330 -> INV record 0x1204','memory_pstate_field':'+0x36D -> INV record 0x123D'},'new_discriminant':{'immediate_serializer_preserves_bytes':True,'ratio_arithmetic_in_serializer':False,'AmdFabric_direct_reader_literals':{'0x1204':False,'0x123D':False,'0x10FF':True,'0x1104':True},'generic_abl_training_source':'Synchronize memory speed across channels / select memory-speed structures; provenance is historical generic ABL, not exact clv consumer'},'conclusion':'No exact-clv downstream code in this bounded path assigns UclkDiv1M0 a ratio relative to FCLK. The native path preserves a typed byte as INV record 0x1204, while MemoryPstate is a separate typed byte/record 0x123D. A generic ABL memory-training routine handles memory-speed synchronization and P-state structures, but is not connected here to either exact clv record.', 'limitations':['Final INV consumer/actuator remains unresolved within bounded census.','No hardware/training execution or frequency/ratio claim.'],'checks_detail':checks}
(OUT/'uclk-semantics-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':result['status'],'checks':result['checks'],'new_discriminant':result['new_discriminant'],'conclusion':result['conclusion']},sort_keys=True));sys.exit(0 if result['status']=='PASS' else 1)
