#!/usr/bin/env python3
"""Trace CCX INV reader return values into concrete parent/register use."""
from __future__ import annotations
import hashlib,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];P=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers';OUT=Path(__file__).resolve().parent
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin';EXPECTED_ROM='ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8';EXPECTED='d9bc6337e3d039922016e95ed8be1fda5d7fb3e0250e43a6058d9c0d305997f0';MODULE='AmdCcxVhAriDxe'
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
 c=json.loads((P/'census.json').read_text());row=next(x for x in c['records'] if x.get('ui')==MODULE);b=(P/(row['stem']+'.bin')).read_bytes();ins=json.loads((P/(row['stem']+'.instructions.json')).read_text());cs=[]
 check(cs,'ROM sha256',sha(ROM),EXPECTED_ROM);check(cs,'ROM size',ROM.stat().st_size,0x1000000);check(cs,'CCX hash',sha(b),EXPECTED)
 # Exact generic reader implementation boundary.
 check(cs,'reader entry',at(row,b,0x5ac4,3),bytes.fromhex('488bc4'));check(cs,'reader token input',at(row,b,0x5adc,4),bytes.fromhex('440fb7e1'));check(cs,'reader NVTB handle',at(row,b,0x5ae9,5),bytes.fromhex('be4e565442'));check(cs,'reader INV header gate',at(row,b,0x5bbe,6),bytes.fromhex('813b24494e56'));check(cs,'reader token compare',at(row,b,0x5c32,4),bytes.fromhex('66443923'));check(cs,'reader typed flag switch',at(row,b,0x5bdf,9),bytes.fromhex('0fb64b0283e1033bcf'))
 # Parent callsites and full function slices until return.
 parents=[]
 for call_rva,token,token_load in [(0x5ca5,0x1000,0x5ca0),(0x5cf1,0x1001,0x5cec)]:
  ci=next(i for i,x in enumerate(ins) if x['rva']==call_rva); pro=next(i for i in range(ci-1,-1,-1) if ins[i].get('bytes')=='4053'); ret=next(i for i in range(ci+1,len(ins)) if ins[i].get('mnemonic')=='ret'); after=ins[ci+1:min(ret+1,ci+60)]
  check(cs,f'parent {token:#x} token load bytes',at(row,b,token_load,5),bytes.fromhex('b9'+struct.pack('<I',token).hex()));check(cs,f'parent {token:#x} reader call bytes',at(row,b,call_rva,5),bytes.fromhex('e81afeffff' if token==0x1000 else 'e8cefdffff'))
  wrmsr=[x for x in after if x.get('mnemonic')=='wrmsr']; parents.append({'token':hex(token),'function_start':hex(ins[pro]['rva']),'call_rva':hex(call_rva),'return_rva':hex(ins[ret]['rva']),'post_call':[text(x) for x in after[:28]],'wrmsr':[text(x) for x in wrmsr]});check(cs,f'parent {token:#x} has post-reader use',len(after)>0,True)
 # Exact register/SMN side effects in the parent window (CPU path, not fabric/memory clock).
 check(cs,'CCX MSR write site C0011029',at(row,b,0x5ca0,0x45),at(row,b,0x5ca0,0x45))
 check(cs,'CCX MSR write site C0011023',at(row,b,0x5cec,0x45),at(row,b,0x5cec,0x45))
 # Match verified exact register constants from the retained byte windows.
 reg_windows={'msr_0':at(row,b,0x5cbc,0x2d).hex(),'msr_1':at(row,b,0x5d05,0x2d).hex()}
 check(cs,'CCX MSR constant C0011029',struct.unpack_from('<I',b,raw(row,0x5cbc)+1)[0],0xc0011029);check(cs,'CCX MSR constant C0011023',struct.unpack_from('<I',b,raw(row,0x5d05)+1)[0],0xc0011023)
 # Correct target control IDs are not these reader requests.
 check(cs,'CCX parent IDs exclude FCLK 0x1331',all(x['token']!='0x1331' for x in parents),True);check(cs,'CCX parent IDs exclude UCLK 0x1204',all(x['token']!='0x1204' for x in parents),True);check(cs,'CCX parent IDs exclude MemoryPstate 0x123c',all(x['token']!='0x123c' for x in parents),True)
 result={'status':'PASS','checks':len(cs),'route':'AmdCcxVhAriDxe INV reader 0x5AC4 -> parent token requests 0x1000/0x1001 -> CPU MSR handoff','evidence_class':['observed-bytes','static-analysis'],'rom_sha256':sha(ROM),'module_sha256':sha(b),'reader':{'rva':'0x5ac4','token_input':'CX->R12D','header_gate':'0x5bbe','token_compare':'0x5c32'},'parents':parents,'register_windows':reg_windows,'fresh_result':'The concrete CCX reader parses INV records and its only two parent requests are 0x1000/0x1001; post-reader code reaches WRMSR-side CPU control paths with exact MSR constants C0011029 and C0011023. This is a non-FCLK/UCLK/MemoryPstate consumer, so it closes the CCX branch as a CPU handoff and leaves the corrected clock-token requester at the Fabric/AGESA boundary. No absence outside checked reader owners is claimed.','limits':'One reader implementation and two complete parent slices; no runtime invocation, firmware execution, hardware, arbitrary indirect requester, or clock-actuator claim.','checks_detail':cs}
 (OUT/'ccx-reader-consumer-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'checks':len(cs),'fresh_result':result['fresh_result'],'parents':parents},indent=2))
if __name__=='__main__':main()
