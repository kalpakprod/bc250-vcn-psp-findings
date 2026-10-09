#!/usr/bin/env python3
"""Bounded exact CbsBasePei $INV -> AmdFabricAriPei reader edge.

Read-only; no candidate, ROM, settings, or runtime action.
"""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path('/home/OWNER/orca/projects/bc250'); OUT=Path(__file__).resolve().parent
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
CBS=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/CbsBasePei-6ff112922ad8.bin'
CBSI=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/CbsBasePei-6ff112922ad8.instructions.json'
FAB=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/AmdFabricAriPei-c5b99650a442.bin'
FABI=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/AmdFabricAriPei-c5b99650a442.instructions.json'
EXPECTED={ROM:'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8',CBS:'6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77',FAB:'c5b99650a442ed9be1cf3a62e7571f7eb163b9f80a60d4fcc7b3e9afe4506f78',CBSI:'12d801b000aa6ae17c0eb422ac58a294833c9fc7d40065df1cbe3c30ac4a75cf',FABI:'77b1d4be4393fbbf920847398ae5667c42b3841066d40c2aaace1b49036c81e1'}
checks=[]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ck(name,got,exp):
 ok=got==exp;checks.append({'name':name,'status':'PASS' if ok else 'FAIL','got':got,'expected':exp})
 if not ok:raise AssertionError(f'{name}: got {got!r} expected {exp!r}')
for p in EXPECTED:ck('exists:'+p.name,p.exists(),True)
for p,h in EXPECTED.items():ck('hash:'+p.name,sha(p),h)
cbs=json.loads(CBSI.read_text());fab=json.loads(FABI.read_text()); cbs_map={d['rva']:d for d in cbs}; fab_map={d['rva']:d for d in fab}
# Exact token serializers: source Setup byte -> INV header -> payload store.
for r,hx,name in [(0x9cc4,'ba04120000','Cbs token 0x1204 header'),(0x9ce4,'8a8230030000','Cbs Setup+0x330 source load'),(0x9cea,'884103','Cbs 0x1204 value byte store'),(0xe738,'ba74130000','Cbs token 0x1374 header'),(0xe75b,'668b8204070000','Cbs Setup+0x704 source load'),(0xe762,'66894103','Cbs 0x1374 value u16 store')]:
 d=cbs_map.get(r);ck(name,None if d is None else d['bytes'],hx)
# Exact generic reader boundary 0x1D3C: NVTB lookup, record header compare, type decode, value extraction, token scan.
for r,hx,name in [(0x1d3c,'55','reader entry'),(0x1dfc,'813e24494e56','reader requires $INV header'),(0x1e11,'83c620','reader advances to first record payload'),(0x1e16,'0fb64602','reader reads record type byte'),(0x1e1a,'83e003','reader masks record type'),(0x1e67,'668b06','reader loads record token'),(0x1e6a,'663b4508','reader compares requested token'),(0x1e70,'03f3','reader advances by record width'),(0x1e72,'b8ffff0000','reader terminator token')]:
 d=fab_map.get(r);ck(name,None if d is None else d['bytes'],hx)
# The only exact direct calls to reader 0x1D3C in this instruction census.
reader_calls=[d for d in fab if d.get('mnemonic')=='call' and d.get('operands','').lower()=='0x1d3c']
ck('direct reader call count',len(reader_calls),2)
for r,token,callbytes in [(0x1ebd,'0x10ff','e87afeffff'),(0x1f94,'0x1104','e8a3fdffff')]:
 d=fab_map.get(r);ck(f'reader call {r:#x} bytes',None if d is None else d['bytes'],callbytes)
 # previous immediate push in same local block
 prev=[x for x in fab if r-0x20<=x['rva']<r and x.get('mnemonic')=='push' and x.get('operands','').lower()==token]
 ck(f'reader request immediate before {r:#x}',len(prev),1)
# AmdFabric contains serializer literals for these records; they are not reader request pushes.
for token,rva in [('0x1204',0xd224),('0x1374',0x11c98)]:
 hits=[d['rva'] for d in fab if token in d.get('operands','').lower()]
 ck('AmdFabric serializer literal '+token,hits,[rva])
# No exact direct callsite passes corrected token via push.
for token in ['0x1204','0x1374']:
 hits=[d['rva'] for d in fab if d.get('mnemonic')=='push' and d.get('operands','').lower()==token]
 ck('AmdFabric direct push absent '+token,hits,[])
# Ensure reader's compare uses caller-supplied [ebp+8], not a hardcoded target; this is the
# actual edge that can consume arbitrary $INV tokens if a requester exists.
ck('reader compare is dynamic requested-token arg',fab_map[0x1e6a]['operands'].lower(),'ax,word ptr [ebp+0x8]')
result={
 'status':'PARTIAL_BOUNDED_EDGE','decision':'NO_DIRECT_1204_OR_1374_REQUESTER_IN_EXACT_AMDFABRIC_CENSUS',
 'edge':{
  'producer':'CbsBasePei emits Setup+0x330 as token 0x1204 and Setup+0x704 as token 0x1374.',
  'reader':'AmdFabricAriPei 0x1D3C validates $INV header, scans records until requested token [ebp+8], decodes type/width and returns payload.',
  'direct_requesters':{'0x10FF':'RVA 0x1EBD','0x1104':'RVA 0x1F94'},
  'corrected_tokens':'No direct push/literal requester for 0x1204 or 0x1374 in this exact AmdFabric instruction census.'
 },
 'boundary':'The dynamic reader can consume arbitrary requested tokens, but this bounded module has only two direct calls; computed/indirect callers, other modules, HOB/DMA/runtime delivery remain outside this check.',
 'checks':{'passed':sum(x['status']=='PASS' for x in checks),'failed':sum(x['status']=='FAIL' for x in checks),'total':len(checks)},
 'evidence_class':['observed-bytes','static-analysis'],
 'limitations':['No firmware execution or hardware result.','No claim that indirect/computed/HOB/DMA consumers are absent.','No candidate built.'],
 'checks_detail':checks,
}
(OUT/'inv-consumer-edge-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':result['status'],'decision':result['decision'],'edge':result['edge'],'checks':result['checks']},sort_keys=True))
raise SystemExit(0 if result['checks']['failed']==0 else 1)
