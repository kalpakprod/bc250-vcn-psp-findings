#!/usr/bin/env python3
"""Bounded pointer/dataflow audit from AMD PEI provider table to dispatcher."""
from __future__ import annotations
import hashlib, json, re, struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
P=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers'
OUT=Path(__file__).resolve().parent
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
EXPECTED_ROM='ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
CASES={
 'AmdNbioGfxARIPei':{'wrapper':0x4DF0,'descriptor_off':0x14EE8,'provider_ptr_off':0x14F58,'descriptor_rva':0x15080,'provider_rva':0x150F0,'body_sha':'63413be2ac290e584bbbeeba5eb573a94b66b9624c4e0ecbea145ded655245b8'},
 'AmdNbioSmuV10Pei':{'wrapper':0x5740,'descriptor_off':0x158E0,'provider_ptr_off':0x15950,'descriptor_rva':0x15A70,'provider_rva':0x15AE0,'body_sha':'905b8be68afd1dce5453acef8273cbf94bdae6d41823c25438ace286348e2c80'},
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
def ptr_hits(b,v): return [m.start() for m in re.finditer(re.escape(struct.pack('<I',v)),b)]
def direct(x): return x.get('mnemonic','').startswith('call') and re.fullmatch(r'0x[0-9a-f]+',x.get('operands',''))

def main():
 c=json.loads((P/'census.json').read_text()); rows={x.get('ui',x['ffs_guid']):x for x in c['records']}; cs=[]; check(cs,'ROM sha256',sha(ROM),EXPECTED_ROM); check(cs,'ROM size',ROM.stat().st_size,0x1000000); modules={}
 for name,m in CASES.items():
  row=rows[name]; body=(P/(row['stem']+'.bin')).read_bytes(); ins=json.loads((P/(row['stem']+'.instructions.json')).read_text()); base=int(row['imagebase']); descriptor_va=base+m['descriptor_rva']; provider_va=base+m['provider_rva']; wrapper_va=base+m['wrapper']
  check(cs,name+' body sha256',sha(body),m['body_sha']); check(cs,name+' descriptor bytes',struct.unpack_from('<QQII',body,m['descriptor_off']),(0xffffffff,0,wrapper_va,0xfffffffe)); check(cs,name+' provider pointer value',struct.unpack_from('<I',body,m['provider_ptr_off'])[0],descriptor_va)
  descriptor_hits=ptr_hits(body,descriptor_va); provider_hits=ptr_hits(body,provider_va); wrapper_hits=ptr_hits(body,wrapper_va)
  check(cs,name+' descriptor pointer hit includes provider field',m['provider_ptr_off'] in descriptor_hits,True); check(cs,name+' provider pointer hit includes table field',m['provider_ptr_off'] in provider_hits,False)
  # Restrict xref claims to executable instruction operands containing the exact
  # RVA or VA; raw data pointer occurrences are retained separately.
  needles={hex(m['descriptor_rva']),hex(m['provider_rva']),hex(descriptor_va),hex(provider_va),hex(wrapper_va)}
  operand_refs=[x for x in ins if any(n in x.get('operands','') for n in needles)]
  indirect=[x for x in ins if x.get('mnemonic','').startswith('call') and not direct(x)]
  service_candidates=[x for x in indirect if any(k in x.get('operands','') for k in ('[eax+0x18]','[ecx+0x18]','[eax+0x20]','[ecx+0x20]','[eax+0x4]','[ecx+0x4]'))]
  # Byte-backed table neighborhood: descriptor and provider field, plus the
  # next 0x20 bytes around each data pointer. This is the actual registration
  # candidate, not an invoked-state claim.
  neighborhood=body[m['descriptor_off']:m['descriptor_off']+0x80].hex()
  modules[name]={'stem':row['stem'],'base':hex(base),'wrapper_va':hex(wrapper_va),'descriptor_va':hex(descriptor_va),'provider_va':hex(provider_va),'descriptor_rva':hex(m['descriptor_rva']),'provider_rva':hex(m['provider_rva']),'descriptor_body_off':hex(m['descriptor_off']),'provider_pointer_body_off':hex(m['provider_ptr_off']),'descriptor_pointer_hits':[{'body_off':hex(o),'rva':hex(rva_for_off(row,o)) if rva_for_off(row,o) is not None else None} for o in descriptor_hits],'provider_pointer_hits':[{'body_off':hex(o),'rva':hex(rva_for_off(row,o)) if rva_for_off(row,o) is not None else None} for o in provider_hits],'wrapper_pointer_hits':[{'body_off':hex(o),'rva':hex(rva_for_off(row,o)) if rva_for_off(row,o) is not None else None} for o in wrapper_hits],'executable_operand_refs':[{'rva':hex(x['rva']),'mnemonic':x['mnemonic'],'operands':x['operands'],'bytes':x['bytes']} for x in operand_refs],'indirect_call_count':len(indirect),'service_slot_candidates':[{'rva':hex(x['rva']),'operands':x['operands'],'bytes':x['bytes']} for x in service_candidates],'registration_neighborhood':neighborhood,'classification':'static descriptor/provider pointer is proven; no module-local executable operand joins to descriptor/provider/wrapper VA in this bounded exact scan; installed/invoked state unresolved'}
  check(cs,name+' executable operand join count',len(operand_refs),0)
  check(cs,name+' registration neighborhood nonempty',len(neighborhood)>0,True)
  check(cs,name+' indirect inventory retained',len(indirect)>0,True)
 result={'status':'PASS','checks':len(cs),'route':'provider-table pointer -> callback descriptor -> module-local registration/dispatcher join','evidence_class':['observed-bytes','static-analysis'],'rom_sha256':sha(ROM),'modules':modules,'fresh_result':'Both provider-table fields point exactly to wildcard/event callback descriptors for wrappers 0x4DF0/0x5740. All module-local executable operand references to the descriptor/provider/wrapper VA set were checked and none joined; indirect call/service-slot candidates remain unbound. This proves a static registration structure, not installed or invoked dispatch.','limits':'Coverage is restricted to the two exact module bodies, their decoded instruction metadata, and the pointer neighborhoods; no census-wide negative, arbitrary computed pointer, cross-module PEI service, DMA/HOB migration or hardware claim.','checks_detail':cs}
 (OUT/'provider-dispatch-result.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps({'status':result['status'],'checks':len(cs),'fresh_result':result['fresh_result'],'modules':modules},indent=2))
if __name__=='__main__': main()
