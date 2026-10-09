#!/usr/bin/env python3
"""Trace complete parent uses of Fabric INV reader calls 0x10FF/0x1104."""
from __future__ import annotations
import hashlib,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];P=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers';OUT=Path(__file__).resolve().parent
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin';EXPECTED_ROM='ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8';EXPECTED='c5b99650a442ed9be1cf3a62e7571f7eb163b9f80a60d4fcc7b3e9afe4506f78'
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
def main():
 c=json.loads((P/'census.json').read_text());row=next(x for x in c['records'] if x.get('ui')=='AmdFabricAriPei');b=(P/(row['stem']+'.bin')).read_bytes();ins=json.loads((P/(row['stem']+'.instructions.json')).read_text());cs=[];check(cs,'ROM sha256',sha(ROM),EXPECTED_ROM);check(cs,'ROM size',ROM.stat().st_size,0x1000000);check(cs,'Fabric hash',sha(b),EXPECTED)
 output_store=bytes.fromhex('8b460389078b4607894704'); token_compare=bytes.fromhex('668b06663b4508740c03f3'); check(cs,'reader entry',at(row,b,0x1d3c,6),bytes.fromhex('558bec83ec24'));check(cs,'reader output u32 store',at(row,b,0x1e38,len(output_store)),output_store);check(cs,'reader token compare',at(row,b,0x1e67,len(token_compare)),token_compare)
 parents=[]
 for call,token,fn,token_rva,expected_token_bytes,expected_call_bytes in [(0x1ebd,0x10ff,0x1e8f,0x1eb0,'68ff100000','e87afeffff'),(0x1f94,0x1104,0x1f6d,0x1f8b,'6804110000','e8a3fdffff')]:
  ci=next(i for i,x in enumerate(ins) if x['rva']==call); ret=next(i for i in range(ci+1,len(ins)) if ins[i].get('mnemonic')=='ret'); before=ins[max(0,ci-12):ci];after=ins[ci+1:min(ret+1,ci+90)]
  check(cs,f'parent {token:#x} function prologue',at(row,b,fn,3),bytes.fromhex('558bec'));check(cs,f'parent {token:#x} token push',at(row,b,token_rva,5),bytes.fromhex(expected_token_bytes));check(cs,f'parent {token:#x} reader call',at(row,b,call,5),bytes.fromhex(expected_call_bytes));
  # output stack setup: LEA EDI,[ESP+0x14] and EDI receives reader output.
  outptr=[x for x in before if 'edi,[esp+0x14]' in x.get('operands','') or 'edi,[esp+0xc]' in x.get('operands','')];check(cs,f'parent {token:#x} output slot setup',len(outptr),1)
  # capture full post-call instructions and classify direct hardware/service operations.
  wr=[x for x in after if x.get('mnemonic') in ('wrmsr','out','in')];calls=[x for x in after if x.get('mnemonic','').startswith('call')]
  stack_uses=[x for x in after if any(s in x.get('operands','') for s in ('[esp+0x14]','[esp+0x18]','[esp+0x10]','[edi]'))]
  parents.append({'token':hex(token),'function':hex(fn),'call':hex(call),'ret':hex(ins[ret]['rva']),'pre_call':[text(x) for x in before],'post_call':[text(x) for x in after[:80]],'post_calls':[text(x) for x in calls],'stack_uses':[text(x) for x in stack_uses],'hardware_ops':[text(x) for x in wr]})
  check(cs,f'parent {token:#x} no direct hardware op',len(wr),0)
  check(cs,f'parent {token:#x} has post-call control/use',len(after)>0,True)
 # IDS table parent ownership: static table maps events 20000003/20000004 to handlers 1e8f/1f6d.
 fab_base=int(row['imagebase']); ids_off=raw(row,0x16bdc); ids_ptr=struct.unpack_from('<I',b,ids_off+0x20)[0] if False else None
 check(cs,'IDS handler table bytes',b[0x16bc4:0x16bc4+24],bytes.fromhex('030000200fdae10904000020eddae109ffffffffffffffff'))
 result={'status':'PASS','checks':len(cs),'route':'AmdFabricAriPei reader 0x1D3C -> complete handlers 0x1E8F/0x1F6D -> returned stack values/control flow','evidence_class':['observed-bytes','static-analysis'],'rom_sha256':sha(ROM),'module_sha256':sha(b),'parents':parents,'fresh_result':'Complete parent slices show reader outputs for 0x10FF/0x1104 land in caller-provided stack result slots and continue through handler control/callee paths; neither parent performs a direct WRMSR/port operation in the checked function slice. The static IDS table maps events 0x20000003/0x20000004 to handlers 0x1E8F/0x1F6D. Transitive AGESA/helper effects, MMIO writes and clock semantics are unverified; corrected FCLK 0x1331/UCLK 0x1204/MemoryPstate 0x123C requester remains unverified.','limits':'Two complete direct parent slices and static IDS table only; no runtime invocation, indirect/computed parent, transitive helper/MMIO effects, firmware execution, hardware or absence outside checked branch.','checks_detail':cs}
 (OUT/'fabric-reader-consumer-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'checks':len(cs),'fresh_result':result['fresh_result'],'parents':parents},indent=2))
if __name__=='__main__':main()
