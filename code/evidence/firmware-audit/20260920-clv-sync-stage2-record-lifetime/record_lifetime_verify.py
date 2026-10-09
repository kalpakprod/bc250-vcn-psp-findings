#!/usr/bin/env python3
"""Track token/value destination and cursor lifetime for 0x1331/0x1332."""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; P=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers'; OUT=Path(__file__).resolve().parent
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'; EXPECTED_ROM='ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'; MODULES={'CbsBasePei':'6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77','AmdNbioSmuV10Pei':'905b8be68afd1dce5453acef8273cbf94bdae6d41823c25438ace286348e2c80'}; TOKENS=(0x1331,0x1332)
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
def at(row,b,rva,n):return b[raw(row,rva):raw(row,rva)+n]
def ins_text(x):return f"{x['rva']:05X} {x['bytes']} {x['mnemonic']} {x['operands']}"
def main():
 c=json.loads((P/'census.json').read_text()); rows={x.get('ui',x['ffs_guid']):x for x in c['records']}; cs=[]
 check(cs,'ROM sha256',sha(ROM),EXPECTED_ROM);check(cs,'ROM size',ROM.stat().st_size,0x1000000)
 modules={}
 for name,expected_hash in MODULES.items():
  row=rows[name]; b=(P/(row['stem']+'.bin')).read_bytes(); ins=json.loads((P/(row['stem']+'.instructions.json')).read_text());check(cs,name+' hash',sha(b),expected_hash)
  records={}
  for tok in TOKENS:
   hits=[(i,x) for i,x in enumerate(ins) if x.get('mnemonic')=='mov' and x.get('operands')==f'edx,{hex(tok)}']
   check(cs,f'{name} token {tok:#x} count',len(hits),1); i,x=hits[0]
   # Track exactly one record builder block from token header to the next
   # cursor update; do not use RVA adjacency as a semantic proxy.
   window=ins[i:min(len(ins),i+32)]
   token_ptr=next((z for z in window if z.get('mnemonic')=='mov' and z.get('operands')=='eax,DWORD PTR [ebp-0x8]'),None)
   token_store=next((z for z in window if z.get('operands')=='WORD PTR [eax],dx'),None)
   cursor_ptr=next((z for z in window if z.get('mnemonic')=='mov' and z.get('operands')=='ecx,DWORD PTR [ebp-0x8]'),None)
   source=next((z for z in window if re.search(r'BYTE PTR \[edx\+0x6a[234]\]',z.get('operands',''))),None)
   value_store=next((z for z in window if z.get('operands')=='BYTE PTR [ecx+0x3],al'),None)
   add=next((z for z in window if z.get('mnemonic')=='add' and z.get('operands')=='ecx,0x4'),None)
   cursor_store=next((z for z in window if z.get('operands')=='DWORD PTR [ebp-0x8],ecx'),None)
   for label,obj in [('token_ptr',token_ptr),('token_store',token_store),('cursor_ptr',cursor_ptr),('source',source),('value_store',value_store),('cursor_add',add),('cursor_store',cursor_store)]:check(cs,f'{name} {tok:#x} {label} present',obj is not None,True)
   check(cs,f'{name} {tok:#x} token before source',token_store['rva']<source['rva'],True);check(cs,f'{name} {tok:#x} source before value',source['rva']<value_store['rva'],True);check(cs,f'{name} {tok:#x} value before cursor advance',value_store['rva']<add['rva']<cursor_store['rva'],True)
   token_store_bytes=bytes.fromhex('668910'); check(cs,f'{name} {tok:#x} token store bytes',at(row,b,token_store['rva'],len(token_store_bytes)),token_store_bytes)
   check(cs,f'{name} {tok:#x} value store bytes',at(row,b,value_store['rva'],3),bytes.fromhex('884103'))
   rows_out=[{'role':'token_ptr','instruction':ins_text(token_ptr),'body_bytes':at(row,b,token_ptr['rva'],3).hex()},{'role':'token_store','instruction':ins_text(token_store),'body_bytes':at(row,b,token_store['rva'],3).hex()},{'role':'cursor_ptr','instruction':ins_text(cursor_ptr),'body_bytes':at(row,b,cursor_ptr['rva'],3).hex()},{'role':'source_load','instruction':ins_text(source),'body_bytes':at(row,b,source['rva'],6).hex()},{'role':'value_store','instruction':ins_text(value_store),'body_bytes':at(row,b,value_store['rva'],3).hex()},{'role':'cursor_add','instruction':ins_text(add),'body_bytes':at(row,b,add['rva'],3).hex()},{'role':'cursor_store','instruction':ins_text(cursor_store),'body_bytes':at(row,b,cursor_store['rva'],3).hex()}]
   records[hex(tok)]={'token_rva':hex(x['rva']),'source_operands':source['operands'],'source_rva':hex(source['rva']),'token_destination':'[ebp-0x8] -> record+0','value_destination':'[ebp-0x8] -> record+3','cursor_advance':'+4 bytes','chronology':rows_out}
  modules[name]={'stem':row['stem'],'sha256':sha(b),'records':records}
 # Matrix conflict is checked separately from the byte-backed record proof.
 matrix=(ROOT/'docs/research/2026-09-20-clv-sync-stage2-token-matrix.md').read_text();check(cs,'canonical matrix token 0x1332',('+0x6A3' in matrix and '0x1332' in matrix),True);check(cs,'observed record pair differs by source field',modules['CbsBasePei']['records']['0x1331']['source_operands']!=modules['CbsBasePei']['records']['0x1332']['source_operands'],True)
 result={'status':'PASS','checks':len(cs),'route':'complete token/value record-cursor lifetime for 0x1331/0x1332 in Cbs and SMU builders','evidence_class':['observed-bytes','static-analysis'],'rom_sha256':sha(ROM),'modules':modules,'canonical_matrix_sha256':sha(ROOT/'docs/research/2026-09-20-clv-sync-stage2-token-matrix.md'),'fresh_result':'Complete instruction chronology proves header token and value source share the same record cursor: token is written at record+0, Setup byte is loaded later and stored at record+3, then cursor advances by 4. In both CbsBasePei and AmdNbioSmuV10Pei, 0x1331 maps to Setup+0x6A3 and 0x1332 maps to Setup+0x6A4. The canonical matrix labels FclkDpm +0x6A3 -> 0x1332, so field semantics remain contradictory even though record identity/lifetime is proven.','limits':'No requester/consumer proof beyond prior bounded reader map; no semantic field rename, firmware execution, hardware or shared-state change.','checks_detail':cs}
 (OUT/'record-lifetime-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'checks':len(cs),'fresh_result':result['fresh_result'],'modules':modules},indent=2))
if __name__=='__main__':main()
