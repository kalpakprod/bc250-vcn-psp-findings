#!/usr/bin/env python3
"""Independent final checkpoint checks for exact CLV stage-2 reports.

This does not execute firmware. It reopens worker-owned bytes/results and adds
independent direct-byte checks for PEI double-pointer semantics, Fabric buffer
identity, and the final FCLK token ownership.
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
INV=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers'

def sha(p: Path) -> str: return hashlib.sha256(p.read_bytes()).hexdigest()
def load_ins(name): return {int(x['rva']):x for x in json.loads((INV/name).read_text())}
def check(cs,label,got,expected):
 ok=got==expected; cs.append({'label':label,'status':'PASS' if ok else 'FAIL','got':got,'expected':expected}); return ok

def main():
 cs=[]
 check(cs,'clv-hash',sha(ROM),'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8')
 # Worker report fresh results are reopened, but counted separately from direct checks.
 worker=[
  ('cbs_lifecycle','evidence/firmware-audit/20260920-clv-sync-stage2-cbs-ppi-lifecycle/cbs-ppi-lifecycle-result.json',26),
  ('memclk_consumer','evidence/firmware-audit/20260920-clv-sync-stage2-memclk-consumer/memclk-consumer-result.json',12),
  ('meminit_controlflow','evidence/firmware-audit/20260920-clv-sync-stage2-memclk-consumer/mem-init-controlflow-result.json',27),
  ('cbs_dispatch','evidence/firmware-audit/20260920-clv-sync-stage2-cbs-dispatch-selection/cbs-dispatch-result.json',21),
  ('cbs_caller_chain','evidence/firmware-audit/20260920-clv-sync-stage2-cbs-caller-chain/cbs-caller-chain-result.json',21),
 ]
 worker_summary=[]
 for label,path,want in worker:
  p=ROOT/path; d=json.loads(p.read_text())
  if isinstance(d.get('checks'),dict):
   ok=d.get('status')=='PASS' and int(d['checks'].get('failed',1))==0 and int(d['checks'].get('passed',0))==want
  else:
   ok=d.get('status')=='PASS' and int(d.get('checks',0))==want
  worker_summary.append({'label':label,'path':str(p),'hash':sha(p),'status':'PASS' if ok else 'FAIL','reported_checks':d.get('checks')})
 # AmdMemAm4Pei is PEIM entry arg PeiServices**: ESI retains pointer, [ESI] is table.
 amd=load_ins('AmdMemAm4Pei-1ef4e7b94467.instructions.json')
 for r,b in {0x240:'e831060000',0x245:'8b442408',0x30f:'8bf0',0x311:'8b06',0x316:'ff504c',0x3a0:'8b06',0x3aa:'ff504c',0x3e2:'8b06',0x3e5:'ff5018'}.items():
  check(cs,f'AmdMemAm4Pei:{hex(r)}',amd.get(r,{}).get('bytes'),b)
 # Fabric pointer identity: first 3710 receives NULL buffer + local size ptr;
 # second 3710 receives [ebp-0x17]; 1df9 loads that same local and 1dfc reads it.
 fab=load_ins('AmdFabricAriPei-c5b99650a442.instructions.json')
 for r,b in {0x1d68:'8365fc00',0x1d6c:'8d45fc',0x1d70:'6a00',0x1d72:'e899190000',0x1dc5:'8d45fc',0x1dc9:'ff75e9',0x1dcc:'e83f190000',0x1df9:'8b75e9',0x1dfc:'813e24494e56'}.items():
  check(cs,f'AmdFabricAriPei:{hex(r)}',fab.get(r,{}).get('bytes'),b)
 # Final contiguous map: FCLK +0x6A3 opens/fills token 0x1331 in both serializers.
 cbs=load_ins('CbsBasePei-6ff112922ad8.instructions.json'); smu=load_ins('AmdNbioSmuV10Pei-905b8be68afd.instructions.json')
 for name,ins,head,src,store in [('CbsBasePei',cbs,0xd9e0,0xda00,0xda06),('AmdNbioSmuV10Pei',smu,0xfa60,0xfa80,0xfa86)]:
  check(cs,f'{name}:FCLK-header',ins.get(head,{}).get('operands'),'edx,0x1331')
  check(cs,f'{name}:FCLK-source',ins.get(src,{}).get('operands'),'al,BYTE PTR [edx+0x6a3]')
  check(cs,f'{name}:FCLK-store',ins.get(store,{}).get('operands'),'BYTE PTR [ecx+0x3],al')
 # Caller-chain qualification: local pointer identity is directly byte-backed; HOB+0x28
 # is not asserted here because allocation/layout helper semantics are not fully recovered.
 result={
  'status':'PASS' if all(x['status']=='PASS' for x in cs) and all(x['status']=='PASS' for x in worker_summary) else 'FAIL',
  'direct_checks':{'passed':sum(x['status']=='PASS' for x in cs),'failed':sum(x['status']=='FAIL' for x in cs),'total':len(cs)},
  'worker_reopen':worker_summary,
  'review_findings':[
   'AmdMemAm4Pei uses a PEIM entry argument of type EFI_PEI_SERVICES**: ESI retains the pointer-to-pointer; mov eax,[esi] loads the service table before calls at table+0x4C and table+0x18. The worker report wording "ESI=EAX (PeiServices table)" is imprecise and corrected here.',
   'The Fabric chain proves local pointer identity from the second 0x3710 D.buffer argument ([ebp-0x17]) to the first returned-buffer reader (0x1df9/0x1dfc). The exact HOB+0x28 offset is not independently proven by the bounded helper decode and is not promoted.',
   'The first 0x3710 call is a size pass with D.buffer=NULL; it cannot be described as filling a buffer. The second call is the data/serialization pass using the allocated pointer.',
   'The CBS lifecycle worker output contains a stale token-0x1332 wording. Independent contiguous source/store checks in both serializer bodies establish FclkDpm +0x6A3 -> token 0x1331; token 0x1332 is the following +0x6A4 record and must be removed from that claim.',
  ],
  'limitations':[
   'No firmware execution, runtime PPI invocation, hardware, training, clock, or performance result.',
   'Selected module no-hit checks do not exclude indirect/HOB/DMA/closed AGESA/PSP consumers.',
   'Worker reports with self-comparison checks remain qualified by these direct-byte checks; no broad census claim is made.',
  ],
  'checks_detail':cs,
 }
 (OUT/'stage2-checkpoint-review-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'status':result['status'],'direct_checks':result['direct_checks'],'worker_reopen':worker_summary,'review_findings':result['review_findings']},indent=2))
 raise SystemExit(0 if result['status']=='PASS' else 1)
if __name__=='__main__': main()
