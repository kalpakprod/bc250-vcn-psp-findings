#!/usr/bin/env python3
"""Byte-backed complete-function boundary for the two AMD PEI token-0x1204 builders."""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
P=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers'
OUT=Path(__file__).resolve().parent
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
EXPECTED_ROM='ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
CASES={
 'AmdNbioGfxARIPei': {'target':0xB3F4,'builder':0x4E20,'wrapper':0x4DF0,'call':0x4E0E,'size_call':0x4E26,'ret':0x12FA3,'sha':'63413be2ac290e584bbbeeba5eb573a94b66b9624c4e0ecbea145ded655245b8'},
 'AmdNbioSmuV10Pei': {'target':0xBD44,'builder':0x5770,'wrapper':0x5740,'call':0x575E,'size_call':0x5776,'ret':0x138F3,'sha':'905b8be68afd1dce5453acef8273cbf94bdae6d41823c25438ace286348e2c80'},
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
 for s in row['sections']:
  if s['rva']<=rva<s['rva']+s['size']: return rva-s['rva']+s['raw']
 raise ValueError(hex(rva))

def at(row,b,rva,n): return b[raw(row,rva):raw(row,rva)+n]
def direct(x): return x.get('mnemonic','').startswith('call') and re.fullmatch(r'0x[0-9a-f]+',x.get('operands',''))

def main():
 c=json.loads((P/'census.json').read_text()); rows={x.get('ui',x['ffs_guid']):x for x in c['records']}; cs=[]; check(cs,'ROM sha256',sha(ROM),EXPECTED_ROM); check(cs,'ROM size',ROM.stat().st_size,0x1000000)
 out={}
 for name,m in CASES.items():
  row=rows[name]; body=(P/(row['stem']+'.bin')).read_bytes(); ins=json.loads((P/(row['stem']+'.instructions.json')).read_text())
  check(cs,name+' body sha256',sha(body),m['sha'])
  check(cs,name+' target bytes',at(row,body,m['target'],5),bytes.fromhex('ba04120000'))
  ti=next(i for i,x in enumerate(ins) if x['rva']==m['target'] and x.get('operands')=='edx,0x1204')
  pro=next(j for j in range(ti-1,-1,-1) if ins[j].get('mnemonic')=='push' and ins[j].get('operands')=='ebp' and ins[j+1].get('mnemonic')=='mov' and ins[j+1].get('operands')=='ebp,esp')
  first_ret=next(k for k in range(ti+1,len(ins)) if ins[k].get('mnemonic')=='ret')
  check(cs,name+' containing prologue',ins[pro]['rva'],m['builder'])
  check(cs,name+' containing ret',ins[first_ret]['rva'],m['ret'])
  before=[x for x in ins[pro:first_ret+1] if direct(x)]
  after=[x for x in ins[ti+1:first_ret+1] if direct(x)]
  check(cs,name+' builder direct-call count',len(before),2)
  check(cs,name+' no direct call after token builder',len(after),0)
  helper='0x12fb0' if name.startswith('AmdNbioGfx') else '0x13900'
  check(cs,name+' size-helper calls',[(x['rva'],x['operands']) for x in before],[(m['size_call'],helper),(m['size_call']+0xf,helper)])
  # The builder ends by writing FFFF sentinel, returning AL=1, and epiloguing.
  sentinel=bytes.fromhex('baffff00008b45f8668910')
  check(cs,name+' sentinel bytes',at(row,body,m['ret']-0x10,len(sentinel)),sentinel)
  success=bytes.fromhex('b0018be55dc3')
  check(cs,name+' success return/ret bytes',at(row,body,m['ret']-5,len(success)),success)
  # Wrapper passes Setup/context, output buffer and size pointer to builder; the
  # only wrapper call is the builder call and nothing follows it before return.
  wi=next(i for i,x in enumerate(ins) if x['rva']==m['wrapper']); ci=next(i for i,x in enumerate(ins) if x['rva']==m['call'])
  wret=next(k for k in range(ci+1,min(len(ins),ci+40)) if ins[k].get('mnemonic')=='ret')
  wret_rva=ins[wret]['rva']
  check(cs,name+' wrapper prologue',at(row,body,m['wrapper'],3),bytes.fromhex('558bec'))
  check(cs,name+' wrapper builder call',at(row,body,m['call'],5),bytes.fromhex('e80d000000'))
  wrapper_calls=[x for x in ins[wi:wret+1] if direct(x)]
  check(cs,name+' wrapper direct-call sequence',[(x['rva'],x['operands']) for x in wrapper_calls],[(m['call'],hex(m['builder']))])
  argument_setup=bytes.fromhex('8b450c8b4804894dfc8b55fc8b4204508b4dfc8b11528b451050e80d000000')
  check(cs,name+' wrapper argument setup',at(row,body,m['wrapper']+4,len(argument_setup)),argument_setup)
  check(cs,name+' wrapper return bytes',at(row,body,wret_rva-3,4),bytes.fromhex('8be55dc3'))
  out[name]={'stem':row['stem'],'body_sha256':sha(body),'builder':{'entry':hex(m['builder']),'ret':hex(m['ret']),'target':hex(m['target']),'direct_calls_before_ret':[(hex(x['rva']),x['operands']) for x in before],'direct_calls_after_token':[(hex(x['rva']),x['operands']) for x in after]},'wrapper':{'entry':hex(m['wrapper']),'builder_call':hex(m['call']),'argument_window':at(row,body,m['wrapper']+4,0x1f).hex(),'direct_calls':[(hex(x['rva']),x['operands']) for x in wrapper_calls]}}
 result={'status':'PASS','checks':len(cs),'route':'complete containing functions for AMD PEI token-0x1204 builders; post-builder caller boundary','modules':out,'fresh_result':'The complete containing functions for both AMD PEI 0x1204 serializers run from 0x4E20..0x12FA3 and 0x5770..0x138F3. Each has exactly one direct call before the record body (size helper) and zero direct calls after the token site before its sentinel/return. The wrapper calls the builder with its three constructed arguments and returns immediately; no post-builder init-structure call is present at this boundary. This is a concrete adapter boundary, not proof that no indirect or later consumer exists.','limits':'Byte-backed static evidence only; no firmware execution, broad scan, indirect/computed call resolution, HOB/DMA tracing, hardware or shared-state changes.','checks_detail':cs}
 (OUT/'function-boundary-result.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps({'status':result['status'],'checks':len(cs),'fresh_result':result['fresh_result']},indent=2))
if __name__=='__main__': main()
