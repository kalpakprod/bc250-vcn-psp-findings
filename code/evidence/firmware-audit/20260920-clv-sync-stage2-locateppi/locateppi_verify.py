#!/usr/bin/env python3
"""Resolve six exact LocatePpi candidate arguments and immediate use."""
from __future__ import annotations
import hashlib,json,re,struct,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; P=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers'; OUT=Path(__file__).resolve().parent
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'; EXPECTED_ROM='ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'; NAME='AmdNbioSmuV10Pei'; EXPECTED_SHA='905b8be68afd1dce5453acef8273cbf94bdae6d41823c25438ace286348e2c80'; CBS_GUID='04126c85-5c4e-458f-abc1-29f1f7da365e'; CANDIDATES=[0x372,0x410,0x51c,0xb26,0xc22,0x1583]
def sha(v):
 if isinstance(v,(bytes,bytearray)):return hashlib.sha256(v).hexdigest()
 return hashlib.sha256(v.read_bytes()).hexdigest()
def check(cs,n,g,e):
 ok=g==e
 def s(v):
  if isinstance(v,(bytes,bytearray)):return v.hex()
  if isinstance(v,tuple):return list(v)
  return v
 cs.append({'check':n,'passed':ok,'got':s(g),'expected':s(e)})
 if not ok:raise AssertionError(f'{n}: got {g!r}, expected {e!r}')
def raw(row,rva):
 for sec in row['sections']:
  if sec['rva']<=rva<sec['rva']+sec['size']:return rva-sec['rva']+sec['raw']
 raise ValueError(hex(rva))
def rva_for_off(row,o):
 for sec in row['sections']:
  if sec['raw']<=o<sec['raw']+sec['size']:return sec['rva']+o-sec['raw']
 return None
def at(row,b,rva,n):return b[raw(row,rva):raw(row,rva)+n]
def direct_call(x):return x.get('mnemonic','').startswith('call') and x.get('operands') in ('DWORD PTR [eax+0x20]','DWORD PTR [ecx+0x20]')
def parse_ptr(v,row,b,base):
 if not (base<=v<base+0x20000):return {'value':hex(v),'rva':None,'guid':None,'bytes':None}
 rva=v-base
 try:o=raw(row,rva)
 except ValueError:return {'value':hex(v),'rva':hex(rva),'guid':None,'bytes':None}
 data=b[o:o+16]; g=None
 if len(data)==16:
  try:g=str(uuid.UUID(bytes_le=data))
  except ValueError:pass
 return {'value':hex(v),'rva':hex(rva),'guid':g,'bytes':data.hex()}
def main():
 c=json.loads((P/'census.json').read_text()); row=next(x for x in c['records'] if x.get('ui')==NAME); b=(P/(row['stem']+'.bin')).read_bytes(); ins=json.loads((P/(row['stem']+'.instructions.json')).read_text()); base=int(row['imagebase']); cs=[]
 check(cs,'ROM sha256',sha(ROM),EXPECTED_ROM);check(cs,'ROM size',ROM.stat().st_size,0x1000000);check(cs,'module sha256',sha(b),EXPECTED_SHA)
 calls=[x for x in ins if x.get('rva') in CANDIDATES and direct_call(x)];check(cs,'all six LocatePpi call RVAs',sorted(x['rva'] for x in calls),sorted(CANDIDATES));check(cs,'all six call bytes',[at(row,b,x['rva'],3).hex() for x in calls],['ff5020','ff5120','ff5120','ff5120','ff5120','ff5120'])
 records=[]; cbs_hits=[]
 for x in sorted(calls,key=lambda z:z['rva']):
  i=ins.index(x); before=ins[max(0,i-28):i]; after=ins[i+1:min(len(ins),i+18)]
  pushes=[]
  for z in before:
   if z.get('mnemonic')=='push' and re.fullmatch(r'0x[0-9a-f]+',z.get('operands','')):
    pushes.append(parse_ptr(int(z['operands'],16),row,b,base))
  guid_args=[p for p in pushes if p['guid'] is not None]
  cbs=[p for p in guid_args if p['guid']==CBS_GUID]; cbs_hits.extend(cbs)
  use=[{'rva':hex(z['rva']),'bytes':z['bytes'],'mnemonic':z['mnemonic'],'operands':z['operands']} for z in after[:12]]
  records.append({'call_rva':hex(x['rva']),'call_bytes':at(row,b,x['rva'],3).hex(),'push_immediates':pushes,'resolved_guid_arguments':guid_args,'immediate_after_call':use,'returns_eax_use':any('eax' in z.get('operands','') and z.get('mnemonic') not in ('add','pop') for z in after[:12])})
 check(cs,'six candidate records emitted',len(records),6);check(cs,'CBS GUID direct LocatePpi arguments',len(cbs_hits),0)
 common_guid='5af9cd51-36ee-4bab-b414-aaa0541c5b38'; common_records=[x for x in records if x['call_rva']!='0x1583']
 check(cs,'five direct candidates resolve common GUID',len([x for x in common_records if any(p.get('guid')==common_guid for p in x['resolved_guid_arguments'])]),5)
 # RVA 0x1583 is a helper's LocatePpi call. Reconstruct its direct helper
 # callers and their GUID pointer arguments instead of treating the helper
 # callsite as if it had an immediate GUID.
 helper_callers=[]
 for x in ins:
  if x.get('mnemonic','').startswith('call') and x.get('operands')=='0x156f':
   i=ins.index(x); ps=[]
   for z in ins[max(0,i-16):i]:
    if z.get('mnemonic')=='push' and re.fullmatch(r'0x[0-9a-f]+',z.get('operands','')):
     ps.append(parse_ptr(int(z['operands'],16),row,b,base))
   helper_callers.append({'call_rva':hex(x['rva']),'push_immediates':ps})
 check(cs,'helper 0x156f direct caller count',len(helper_callers),3)
 check(cs,'helper callers have no CBS GUID',sum(any(p.get('guid')==CBS_GUID for p in x['push_immediates']) for x in helper_callers),0)
 check(cs,'first returned interface use',at(row,b,0x396,3),bytes.fromhex('ff5004'))
 # The known CBS GUID pointer is static data at RVA 0x15A50; no candidate
 # push should materialize it in these six immediate argument slices.
 cbs_ptr=base+0x15a50; cbs_operands=[z for x in ins if x.get('rva')<0x1700 for z in [x] if hex(cbs_ptr) in z.get('operands','')]
 check(cs,'CBS GUID pointer immediate materializations',len(cbs_operands),0)
 result={'status':'PASS','checks':len(cs),'route':'six LocatePpi argument/interface slices in AmdNbioSmuV10Pei','evidence_class':['observed-bytes','static-analysis'],'rom_sha256':sha(ROM),'module_sha256':sha(b),'module':{'name':NAME,'base':hex(base),'entry_rva':hex(row.get('entry'))},'candidates':records,'helper_0x156f_callers':helper_callers,'cbs_guid':CBS_GUID,'common_guid':common_guid,'fresh_result':'Five direct LocatePpi calls (0x372,0x410,0x51C,0xB26,0xC22) resolve the same non-CBS GUID 5af9cd51-36ee-4bab-b414-aaa0541c5b38; the returned interface is immediately used, with a concrete method call [eax+0x4] at 0x396 on the 0x372 path. The sixth call 0x1583 is a helper path; its three direct helper callers push GUID pointers at 0x33F/0x1597/0x1552A, none resolving to the CBS GUID 04126c85-5c4e-458f-abc1-29f1f7da365e. Full six-call coverage therefore yields a real non-CBS PPI handoff and a bounded CBS no-join.','limits':'Only the six exact calls, helper callers and bounded argument/use slices; no broad absence claim, arbitrary computed GUID resolution beyond these callers, runtime PPI database, firmware execution, hardware or shared-state change.','checks_detail':cs}
 (OUT/'locateppi-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'checks':len(cs),'cbs_guid_hits':len(cbs_hits),'fresh_result':result['fresh_result']},indent=2))
if __name__=='__main__':main()
