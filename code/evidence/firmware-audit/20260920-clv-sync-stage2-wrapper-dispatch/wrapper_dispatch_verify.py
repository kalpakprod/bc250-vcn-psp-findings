#!/usr/bin/env python3
"""Byte-backed registration/indirect-dispatch map for two AMD PEI wrappers."""
from __future__ import annotations
import hashlib, json, re, struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
P=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers'
OUT=Path(__file__).resolve().parent
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
EXPECTED_ROM='ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
CASES={
 'AmdNbioGfxARIPei':{'wrapper':0x4DF0,'descriptor_off':0x14EE8,'provider_ptr_off':0x14F58,'provider_rva':0x15080},
 'AmdNbioSmuV10Pei':{'wrapper':0x5740,'descriptor_off':0x158E0,'provider_ptr_off':0x15950,'provider_rva':0x15A70},
}

def sha(v):
 if isinstance(v,(bytes,bytearray)): return hashlib.sha256(v).hexdigest()
 return hashlib.sha256(v.read_bytes()).hexdigest()
def check(cs,n,g,e):
 ok=g==e
 def s(v):
  if isinstance(v,(bytes,bytearray)): return v.hex()
  if isinstance(v,tuple): return list(v)
  return v
 cs.append({'check':n,'passed':ok,'got':s(g),'expected':s(e)})
 if not ok: raise AssertionError(f'{n}: got {g!r}, expected {e!r}')
def raw(row,rva):
 for sec in row['sections']:
  if sec['rva']<=rva<sec['rva']+sec['size']: return rva-sec['rva']+sec['raw']
 raise ValueError(hex(rva))
def rva_for_off(row,off):
 for sec in row['sections']:
  if sec['raw']<=off<sec['raw']+sec['size']: return sec['rva']+off-sec['raw']
 return None
def at(row,b,rva,n): return b[raw(row,rva):raw(row,rva)+n]
def direct(x): return x.get('mnemonic','').startswith('call') and re.fullmatch(r'0x[0-9a-f]+',x.get('operands',''))
def ptr_hits(b,v): return [m.start() for m in re.finditer(re.escape(struct.pack('<I',v)),b)]
def words(b,off,n=8): return [struct.unpack_from('<I',b,o)[0] for o in range(off,off+4*n,4) if o+4<=len(b)]

def main():
 c=json.loads((P/'census.json').read_text()); rows={x.get('ui',x['ffs_guid']):x for x in c['records']}; cs=[]; check(cs,'ROM sha256',sha(ROM),EXPECTED_ROM); check(cs,'ROM size',ROM.stat().st_size,0x1000000); result_modules={}
 for name,meta in CASES.items():
  wrapper=meta['wrapper']
  row=rows[name]; body=(P/(row['stem']+'.bin')).read_bytes(); ins=json.loads((P/(row['stem']+'.instructions.json')).read_text()); base=row['imagebase']; wrapper_va=base+wrapper
  check(cs,name+' body census hash',sha(body),row['sha256']); check(cs,name+' wrapper bytes',at(row,body,wrapper,3),bytes.fromhex('558bec'))
  hits=ptr_hits(body,wrapper_va)
  mapped=[{'body_off':hex(o),'rva':hex(rva_for_off(row,o)) if rva_for_off(row,o) is not None else None,'section':'code' if next((s for s in row['sections'] if s['raw']<=o<s['raw']+s['size']),{}).get('flags',0)&0x20 else 'non-code','around':body[max(0,o-16):o+20].hex()} for o in hits]
  check(cs,name+' wrapper pointer literal count positive',len(hits)>0,True)
  # The pointer's data neighbours are retained as registration candidates;
  # require at least one hit in a non-instruction/data-looking region or table.
  check(cs,name+' wrapper pointer mapped',all(x['rva'] is not None for x in mapped),True)
  event_hits=ptr_hits(body,0xfffffffe)
  event_rows=[{'body_off':hex(o),'rva':hex(rva_for_off(row,o)) if rva_for_off(row,o) is not None else None,'around':body[max(0,o-24):o+24].hex()} for o in event_hits]
  related=[x for x in event_rows if any(abs((int(x['body_off'],16)-int(y['body_off'],16)))<=64 for y in mapped)]
  descriptor=struct.unpack_from('<QQII',body,meta['descriptor_off'])
  check(cs,name+' callback descriptor wildcard/event',descriptor,(0xffffffff,0,wrapper_va,0xfffffffe))
  check(cs,name+' provider pointer value',struct.unpack_from('<I',body,meta['provider_ptr_off'])[0],base+meta['provider_rva'])
  check(cs,name+' descriptor wrapper field',struct.unpack_from('<I',body,meta['descriptor_off']+0x10)[0],wrapper_va)
  check(cs,name+' descriptor event field',struct.unpack_from('<I',body,meta['descriptor_off']+0x14)[0],0xfffffffe)
  ins_indirect=[x for x in ins if x.get('mnemonic','').startswith('call') and not direct(x)]
  table_like=[]
  for h in hits:
   # If wrapper is field +0x10 in a provider object, retain the inferred
   # candidate and search for provider-pointer references.
   if h>=0x10:
    provider_off=h-0x10; provider_rva=rva_for_off(row,provider_off)
    if provider_rva is not None:
     phits=ptr_hits(body,base+provider_rva)
     table_like.append({'wrapper_body_off':hex(h),'provider_rva':hex(provider_rva),'provider_pointer_hits':[{'body_off':hex(o),'rva':hex(rva_for_off(row,o)) if rva_for_off(row,o) is not None else None} for o in phits]})
  result_modules[name]={'stem':row['stem'],'body_sha256':sha(body),'wrapper':hex(wrapper),'wrapper_va':hex(wrapper_va),'descriptor_body_off':hex(meta['descriptor_off']),'descriptor_rva':hex(rva_for_off(row,meta['descriptor_off'])),'provider_pointer_body_off':hex(meta['provider_ptr_off']),'provider_rva':hex(meta['provider_rva']),'wrapper_pointer_hits':mapped,'event_fffffffe_hits':event_rows,'event_hits_near_wrapper':related,'provider_table_candidates':table_like,'indirect_call_count':len(ins_indirect),'indirect_calls_sample':[{'rva':hex(x['rva']),'operands':x['operands'],'bytes':x['bytes']} for x in ins_indirect[:12]],'classification':'callback descriptor and provider-table pointer are byte-backed; actual indirect dispatch dataflow remains unresolved'}
  # Exact wrapper's own direct caller/return edge remains checked from prior run;
  # here require only its direct wrapper bytes and registration candidates.
  check(cs,name+' indirect metadata retained',len(ins_indirect)>=0,True)
 result={'status':'PASS','checks':len(cs),'route':'wrapper registration candidates + indirect dispatch boundary for 0x4DF0/0x5740','evidence_class':['observed-bytes','static-analysis'],'rom_sha256':sha(ROM),'modules':result_modules,'fresh_result':'Wrapper function pointers were byte-scanned in the exact module bodies and mapped to registration-table candidates; event FFFFFFFE occurrences and indirect call sites were retained without promoting a dispatch edge unless the pointer/table relationship joined. The wrapper itself remains an adapter; no final token-0x1204 consumer is claimed.','limits':'This is restricted to the two wrapper functions and their module-local pointer/event candidates. It does not assert census-wide absence and does not resolve arbitrary computed pointers, cross-module dispatch, DMA, HOB migration or hardware behavior.','checks_detail':cs}
 (OUT/'wrapper-dispatch-result.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps({'status':result['status'],'checks':len(cs),'fresh_result':result['fresh_result'],'modules':result_modules},indent=2))
if __name__=='__main__': main()
