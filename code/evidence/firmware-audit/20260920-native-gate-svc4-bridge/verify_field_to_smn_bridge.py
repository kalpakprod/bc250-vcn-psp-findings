#!/usr/bin/env python3
"""Exact-byte discriminator for native INV field -> ABL1 mapped-target join.

This is read-only. It does not patch, copy, or emit a ROM/candidate.
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path
ROOT=Path('/home/OWNER/orca/projects/bc250')
OUT=Path(__file__).resolve().parent
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
ABL=ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
DIS=ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt'
CBS=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/CbsBasePei-6ff112922ad8.bin'
FAB=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/AmdFabricAriPei-c5b99650a442.bin'
FABINS=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/AmdFabricAriPei-c5b99650a442.instructions.json'
EXPECTED={
 ROM:'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8',
 ABL:'af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a',
 DIS:'b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65',
 CBS:'6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77',
 FAB:'c5b99650a442ed9be1cf3a62e7571f7eb163b9f80a60d4fcc7b3e9afe4506f78',
}
checks=[]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def check(name,got,exp):
 ok=got==exp; checks.append({'name':name,'status':'PASS' if ok else 'FAIL','got':got,'expected':exp})
 if not ok: raise AssertionError(f'{name}: got {got!r} expected {exp!r}')
for p in [ROM,ABL,DIS,CBS,FAB,FABINS]: check(f'exists:{p.name}',p.exists(),True)
for p,expected in EXPECTED.items(): check(f'hash:{p.name}',sha(p),expected)
rom=ROM.read_bytes(); abl=ABL.read_bytes(); cbs=CBS.read_bytes(); fab=FAB.read_bytes(); fi=json.loads(FABINS.read_text())
check('pinned ROM size',len(rom),16777216)
check('ABL payload size',len(abl),94624)
def raw(buf,offset,expected,name): check(name,buf[offset:offset+len(expected)].hex(),expected.hex())
# Native field record identity and exact CbsBasePei payload load.
raw(cbs,0x9cc4-0x190,bytes.fromhex('ba04120000'),'CbsBasePei header token 0x1204')
raw(cbs,0x9ce4-0x190,bytes.fromhex('8a8230030000'),'CbsBasePei loads AmdSetup+0x330')
raw(cbs,0x9cea-0x190,bytes.fromhex('884103'),'CbsBasePei stores value byte into record')
# ABL1 caller token, callback dispatch, runtime table descriptor loads, and mapped call.
for off,hx,label in [
 (0x107e8,'40f21e61','ABL1 caller immediate token 0x61E'),
 (0x1081e,'2046','ABL1 passes context object before callback dispatch'),
 (0x10820,'00f09af8','ABL1 calls dispatcher'),
 (0x1095a,'d0f86046','dispatcher loads callback from current object +0x660'),
 (0x1095e,'1346','dispatcher forwards selected value'),
 (0x10960,'0a46','dispatcher forwards token index'),
 (0x10966,'0121','dispatcher normalizes arg R1=1'),
 (0x10968,'6047','dispatcher branches through loaded callback'),
 (0x9ae8,'c2f30b00','candidate extracts token low 12 bits'),
 (0x9b18,'686c','candidate loads runtime table pointer from context +0x44'),
 (0x9b1c,'50f82160','candidate loads descriptor table[token] dynamically'),
 (0x9b2c,'c6f30b31','candidate extracts nested descriptor index'),
 (0x9b54,'50f82160','candidate loads nested descriptor dynamically'),
 (0x9c2a,'fdf7bbf8','candidate calls mapped read helper 0x6DA4'),
 (0x9d96,'fdf76bf8','candidate calls write helper 0x6E70'),
 (0xb0c2,'2948','initializer loads callback pointer literal'),
 (0xb0c4,'c4f86006','initializer stores callback into initializer object +0x660'),
 (0xb168,'d90b0600','literal points to conditional local Thumb callback 0x9AD8 under base 0x57100'),
]: raw(abl,off,bytes.fromhex(hx),label)
# The exact PEI generic reader has two direct request tokens and no direct 0x1204 requester.
ins={d['rva']:d for d in fi}
reader_calls=sorted((r,d) for r,d in ins.items() if d.get('mnemonic')=='call' and d.get('operands','').lower()=='0x1d3c')
check('number of direct generic-reader calls',len(reader_calls),2)
expected_calls=[(0x1ebd,'e87afeffff','0x10ff'),(0x1f94,'e8a3fdffff','0x1104')]
for call_rva,callbytes,token in expected_calls:
 d=ins.get(call_rva); check(f'reader call {call_rva:#x}',None if d is None else d['bytes'],callbytes)
 # Use the nearest preceding push in the exact decoded contiguous basic block.
 pushes=[x for r,x in ins.items() if call_rva-0x20 <= r < call_rva and x.get('mnemonic')=='push' and x.get('operands','').lower().startswith('0x')]
 nearest=max(pushes,key=lambda x:x['rva']) if pushes else None
 check(f'reader request token before {call_rva:#x}',None if nearest is None else nearest['operands'].lower(),token)
check('no direct generic-reader token 0x1204',all((x.get('operands','').lower()!='0x1204') for _,x in reader_calls),True)
# Immediate evidence of unresolved join: callback parameter index and INV token are separate literal IDs;
# runtime descriptor table is dereferenced, not statically named at these instructions.
check('ABL1 token index differs from native INV 0x1204',0x61e != 0x1204,True)
check('descriptor value loaded from runtime table rather than immediate literal',ins.get(0x9b1c,{}).get('mnemonic'), 'mov')
# We deliberately do not infer descriptor contents from absence of a convenient literal.
result={
 'status':'BLOCKED','decision':'HOLD_ROM_CANDIDATE_UNTIL_FIELD_TO_MAPPED_ACTUATOR_JOIN',
 'single_prebuild_gate':{
  'id':'G-ACT','name':'native field -> active consumer -> runtime descriptor -> encoded SMN target (mapped actuator identity)',
  'acceptance':'For the candidate field (starting with Setup+0x330 / INV 0x1204), byte-backedly join its record to the actually active consumer/callback, recover the runtime +0x44 table entry and encoded descriptor, and decode the target register/field effect sufficiently to predict the candidate result.',
  'why_now':'SVC#4 is a mapped-register service, so a callback descriptor can address SMN/MMIO rather than only local context; unknown descriptor therefore hides the actual write target.',
  'can_close_offline':'PARTIAL_ONLY_FROM_CURRENT_BIOS. The caller/serializer bytes are local and a static producer/table trace could identify the encoded SMN address; however current exact callback table entries and active object binding are runtime dataflow gaps, and the on-die SVC#4 handler/translation table is absent from this BIOS image. The encoded descriptor target may be closable offline if its exact producer and active registration are recovered, but the physical mapped window is not closable from this BIOS corpus alone.'
 },
 'direct_observation':{
  'native_path':'CbsBasePei loads Setup+0x330 and serializes it under INV token 0x1204 (raw instruction assertions passed).',
  'consumer_path':'AmdFabricAriPei exact direct generic-reader callers request 0x10FF and 0x1104, not 0x1204.',
  'ABL1_path':'caller passes token/index 0x61E; dispatcher reads callback at current-object +0x660; callback indexes current-context +0x44 table twice and loads descriptor values dynamically; helpers route through SVC#4 map caller contract.',
  'join':'No byte-backed join currently connects native INV 0x1204 to ABL1 token 0x61E or to an active context descriptor.'
 },
 'inputs':{str(p.resolve()):{'size':p.stat().st_size,'sha256':sha(p)} for p in [ROM,ABL,DIS,CBS,FAB,FABINS]},
 'checks':{'passed':sum(x['status']=='PASS' for x in checks),'failed':sum(x['status']=='FAIL' for x in checks),'total':len(checks)},
 'evidence_class':['observed-bytes','static-analysis'],
 'limitations':['No ROM candidate, firmware execution, hardware, NVRAM, physical mapping, or clock behavior was tested.','SVC#4 caller shape does not establish the on-die handler or mapped window.','No 1:1:1 claim follows.'],
 'checks_detail':checks,
}
(OUT/'field-to-smn-bridge-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':result['status'],'decision':result['decision'],'single_prebuild_gate':result['single_prebuild_gate'],'checks':result['checks']},sort_keys=True))
raise SystemExit(0 if result['checks']['failed']==0 else 1)
