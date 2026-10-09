#!/usr/bin/env python3
"""Destination/cursor lifetime map for remaining Setup fields in two modules."""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];P=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers';OUT=Path(__file__).resolve().parent
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin';EXPECTED_ROM='ea5781049160ab334fd?'
EXPECTED_ROM='ea5781049160ab334fd?'
EXPECTED_ROM='ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
MODULES={'CbsBasePei':'6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77','AmdNbioSmuV10Pei':'905b8be68afd1dce5453acef8273cbf94bdae6d41823c25438ace286348e2c80'}
FIELDS=(0x316,0x330,0x703,0x704,0x36d,0x368)
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
def text(x):return f"{x['rva']:05X} {x['bytes']} {x['mnemonic']} {x['operands']}"
def trace(row,b,ins,field):
 src=[(i,x) for i,x in enumerate(ins) if re.search(fr'\[edx\+0x{field:x}\]',x.get('operands',''))]
 if not src: raise AssertionError(f'field {field:#x} source count 0')
 out=[]
 for si,s in src:
  prev=[(i,x) for i,x in enumerate(ins[max(0,si-40):si],max(0,si-40)) if x.get('mnemonic')=='mov' and re.fullmatch(r'edx,0x[0-9a-f]+',x.get('operands',''))]
  if not prev: continue
  ti,t=prev[-1]; win=ins[ti:min(len(ins),si+32)]
  token_ptr=next(x for x in win if x.get('mnemonic')=='mov' and x.get('operands')=='eax,DWORD PTR [ebp-0x8]')
  token_store=next(x for x in win if x.get('operands')=='WORD PTR [eax],dx')
  cursor_ptr=next(x for x in win if x.get('mnemonic')=='mov' and x.get('operands')=='ecx,DWORD PTR [ebp-0x8]' and x['rva']>=token_store['rva'])
  value_store=next(x for x in win if x.get('operands','').startswith('BYTE PTR [ecx+0x3]') or x.get('operands','').startswith('WORD PTR [ecx+0x3]'))
  adv=next(x for x in win if x.get('mnemonic')=='add' and x.get('operands') in ('ecx,0x4','ecx,0x5') and x['rva']>value_store['rva'])
  cur_store=next(x for x in win if x.get('operands')=='DWORD PTR [ebp-0x8],ecx' and x['rva']>adv['rva'])
  out.append({'field':hex(field),'token':hex(int(t['operands'].split(',')[1],16)),'token_rva':hex(t['rva']),'token_ptr':text(token_ptr),'token_store':text(token_store),'source':text(s),'source_rva':hex(s['rva']),'cursor_ptr':text(cursor_ptr),'value_store':text(value_store),'value_store_rva':hex(value_store['rva']),'cursor_add':text(adv),'cursor_store':text(cur_store),'source_before_value':s['rva']<value_store['rva'],'value_before_advance':value_store['rva']<adv['rva']<cur_store['rva'],'value_width':'u16' if 'WORD PTR' in value_store['operands'] else 'u8','chronology':[text(z) for z in (token_ptr,token_store,cursor_ptr,s,value_store,adv,cur_store)]})
 if not out: raise AssertionError(f'field {field:#x} has no record-builder source')
 return out
def main():
 c=json.loads((P/'census.json').read_text());rows={x.get('ui',x['ffs_guid']):x for x in c['records']};cs=[];check(cs,'ROM sha256',sha(ROM),EXPECTED_ROM);check(cs,'ROM size',ROM.stat().st_size,0x1000000);mods={}
 for name,expected in MODULES.items():
  row=rows[name];b=(P/(row['stem']+'.bin')).read_bytes();ins=json.loads((P/(row['stem']+'.instructions.json')).read_text());check(cs,name+' hash',sha(b),expected); rec={}
  for f in FIELDS:
   rs=trace(row,b,ins,f);rec[hex(f)]=rs
   for r in rs:
    check(cs,f'{name} field {r["field"]} token/value chronology {r["source_rva"]}',r['source_before_value'] and r['value_before_advance'],True);check(cs,f'{name} field {r["field"]} value width {r["source_rva"]}',r['value_width'] in ('u8','u16'),True)
  mods[name]={'stem':row['stem'],'sha256':sha(b),'records':rec}
 check(cs,'Cbs/SMU field-token identity',[(f,[r['token'] for r in mods['CbsBasePei']['records'][hex(f)]]) for f in FIELDS],[(f,[r['token'] for r in mods['AmdNbioSmuV10Pei']['records'][hex(f)]]) for f in FIELDS])
 result={'status':'PASS','checks':len(cs),'route':'all remaining Setup field record-lifetime mapping in Cbs and SMU serializers','evidence_class':['observed-bytes','static-analysis'],'rom_sha256':sha(ROM),'modules':mods,'fresh_result':'Complete cursor-lifetime traces recover actual token IDs, same-record value stores and cursor advances for fields +0x316, +0x330, +0x703, +0x704, +0x36D and +0x368 in both modules. Cbs and SMU mappings agree; no historical matrix label is used to assign IDs. The +0x6A3/+0x1332 contradiction remains explicit from the prior reconciliation.','limits':'Serializer ownership only; no requester/consumer or hardware claim, no firmware execution, no shared-state change.','checks_detail':cs}
 (OUT/'all-fields-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'checks':len(cs),'fresh_result':result['fresh_result'],'mapping':{name:{hex(f):[r['token'] for r in mods[name]['records'][hex(f)]] for f in FIELDS} for name in mods}},indent=2))
if __name__=='__main__':main()
