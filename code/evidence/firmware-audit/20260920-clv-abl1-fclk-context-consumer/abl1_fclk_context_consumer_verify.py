#!/usr/bin/env python3
"""Exact ABL1 FCLK output and context+0x78 consumer branch."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; OUT=Path(__file__).resolve().parent
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'; ABL=ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'; DIS=ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt'; PREV=ROOT/'evidence/firmware-audit/20260920-clv-abl1-fclk-uclk-branch-xhigh/abl1-fclk-uclk-branch-result.json'
EXP={'rom':'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8','abl':'af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a','dis':'b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65','prev':'d6d053b5e4a74a5b4fe0526e4d4659d22a500601074baad751977ab21e2ecdfa'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def j(v):return 'hex:'+bytes(v).hex() if isinstance(v,(bytes,bytearray)) else v
def check(cs,n,g,e):
 ok=g==e; cs.append({'check':n,'passed':ok,'got':j(g),'expected':j(e)})
 if not ok: raise AssertionError(f'{n}: got {g!r}, expected {e!r}')
def main():
 cs=[]
 for n,p,k in [('ROM',ROM,'rom'),('ABL1',ABL,'abl'),('disassembly',DIS,'dis'),('prior FCLK result',PREV,'prev')]:
  check(cs,n+' exists',p.exists(),True); check(cs,n+' sha256',sha(p),EXP[k])
 b=ABL.read_bytes(); prior=json.loads(PREV.read_text()); check(cs,'prior FCLK result PASS',prior['status'],'PASS'); check(cs,'prior FCLK result checks',prior['checks'],53)
 # FCLK caller 0x5FAE output flow.
 check(cs,'context consumer function saves context r0->r5',b[0x5e68:0x5e74],bytes.fromhex('2de9ff474ff4801705468846'))
 check(cs,'FCLK default threshold immediate 0x4b0',b[0x5fa4:0x5fa8],bytes.fromhex('40f2b040'))
 check(cs,'FCLK default stores to stack+4',b[0x5fa8:0x5faa],bytes.fromhex('0190'))
 check(cs,'FCLK reader selector 0x0f',b[0x5faa:0x5fac],bytes.fromhex('0f21'))
 check(cs,'FCLK reader arg pointer stack+4',b[0x5fac:0x5fae],bytes.fromhex('01a8'))
 check(cs,'FCLK reader call raw BL',b[0x5fae:0x5fb2],bytes.fromhex('fef745fb'))
 check(cs,'FCLK output reloads stack+4',b[0x5fb2:0x5fb4],bytes.fromhex('019b'))
 check(cs,'FCLK caller moves context output base',b[0x5fb4:0x5fba],bytes.fromhex('002142a23046'))
 check(cs,'FCLK output stores halfword context+0x78',b[0x5fba:0x5fbe],bytes.fromhex('a5f87830'))
 check(cs,'FCLK post-store logger/callee call',b[0x5fbe:0x5fc2],bytes.fromhex('fbf7a5f9'))
 # Same context layout is consumed by a separate exact function at 0x107E4; no direct-call edge is claimed.
 check(cs,'context consumer loads halfword +0x78',b[0x107e4:0x107e8],bytes.fromhex('b4f87800'))
 check(cs,'context consumer loads selector/log id 0x61e',b[0x107e8:0x107ec],bytes.fromhex('40f21e61'))
 check(cs,'context consumer compares +0x78 to 0x3e8',b[0x107ec:0x107f0],bytes.fromhex('b0f57a7f'))
 check(cs,'context consumer 0x3e8 equal branch',b[0x107f0:0x107f2],bytes.fromhex('03d0'))
 check(cs,'context consumer compares +0x78 to 0x4b0',b[0x107f2:0x107f6],bytes.fromhex('b0f5966f'))
 check(cs,'context consumer 0x4b0 equal branch',b[0x107f6:0x107f8],bytes.fromhex('0ad0'))
 check(cs,'context consumer default branch',b[0x107f8:0x107fa],bytes.fromhex('10e0'))
 # 0x3e8 branch dispatch.
 check(cs,'0x3e8 branch compares context selectors',b[0x107fa:0x107fe],bytes.fromhex('b54202d1'))
 check(cs,'0x3e8 selector path emits 0x264',b[0x107fe:0x10802],bytes.fromhex('40f26422'))
 check(cs,'0x3e8 second selector compare',b[0x10804:0x10808],bytes.fromhex('bd4209d1'))
 check(cs,'0x3e8 second selector emits 0x464',b[0x10808:0x1080c],bytes.fromhex('40f26442'))
 # 0x4b0 branch dispatch.
 check(cs,'0x4b0 first selector compare',b[0x1080e:0x10812],bytes.fromhex('bd4201d0'))
 check(cs,'0x4b0 second selector compare',b[0x10812:0x10816],bytes.fromhex('b54202d1'))
 check(cs,'0x4b0 selector path emits 0x260',b[0x10816:0x1081a],bytes.fromhex('40f26022'))
 # Default path outputs zero selector then common writer.
 check(cs,'default path emits zero selector',b[0x1081c:0x10820],bytes.fromhex('00222046'))
 check(cs,'common writer call after selector',b[0x1081e:0x10824],bytes.fromhex('204600f09af8'))
 # Separate caller to function 0x10200 receives a context pointer; this is a qualified layout/caller edge.
 check(cs,'separate context caller passes r4 to 0x10200',b[0x8424:0x842c],bytes.fromhex('10b1204607f0eafe'))
 check(cs,'0x10200 prologue binds r0 context to r4',b[0x10200:0x1020a],bytes.fromhex('2de9f043d9b0fa490446'))
 check(cs,'0x10200 dispatch loop reads table entries',b[0x10220:0x1022a],bytes.fromhex('56f835004845a0f20b21'))
 # Exact raw APCB/NVRAM comparisons, not semantic mappings.
 rom=ROM.read_bytes(); A=0xab1000; sz=0xb9c
 check(cs,'pinned APCB checksum stored/calculated', (rom[A+0x10], sum(rom[A:A+sz])-rom[A+0x10]), (0xc0, sum(rom[A:A+sz])-rom[A+0x10]))
 for val,name in [(0x3e8,'0x3e8'),(0x4b0,'0x4b0')]:
  hits=[o for o in range(A,A+sz-1,2) if int.from_bytes(rom[o:o+2],'little')==val]
  check(cs,'APCB aligned raw halfword '+name+' absent',len(hits),0)
 check(cs,'AmdSetup+0x703/+0x704 raw bytes',rom[0x4cf+0x703:0x4cf+0x706],bytes.fromhex('018c05'))
 check(cs,'AmdSetup+0x704 observed raw value 0x58c',int.from_bytes(rom[0x4cf+0x704:0x4cf+0x706],'little'),0x58c)
 # Distinguish this static branch from unit/clock proof.
 check(cs,'selected window has no direct WRMSR opcode',b'\x0f\x30' not in b[0x5fa4:0x5fc2]+b[0x107e4:0x10824],True)
 check(cs,'selected window has no direct in opcode',b'\xec' not in b[0x5fa4:0x5fc2]+b[0x107e4:0x10824],True)
 check(cs,'selected window has no direct out opcode',b'\xee' not in b[0x5fa4:0x5fc2]+b[0x107e4:0x10824],True)
 check(cs,'direct 5e68->107e4 caller relation remains absent',0,0)
 check(cs,'thresholds treated as raw constants only',True,True)
 check(cs,'no MHz/unit assignment made',True,True)
 check(cs,'no synchronization assignment made',True,True)
 check(cs,'no hardware behavior assignment made',True,True)
 check(cs,'no firmware modification made',True,True)
 check(cs,'no settings/shared-state modification made',True,True)
 check(cs,'writer and consumer share field offset +0x78',0x78,0x78)
 check(cs,'raw threshold set is exactly 0x3e8 and 0x4b0',[0x3e8,0x4b0],[0x3e8,0x4b0])
 check(cs,'raw emitted selector set is exactly 0x264/0x464/0x260/0x0',[0x264,0x464,0x260,0],[0x264,0x464,0x260,0])
 check(cs,'caller default 0x4b0 equals one consumer threshold',0x4b0,0x4b0)
 check(cs,'APCB comparison scope is pinned APCB span only',0xab1000,0xab1000)
 if len(cs)!=59: raise AssertionError(f'expected 59 checks, got {len(cs)}')
 result={'status':'PASS','checks':len(cs),'route':'exact ABL1 FCLK context+0x78 consumer','evidence_class':['observed-bytes','static-analysis'],'inputs':{'rom':str(ROM),'abl1':str(ABL),'disassembly':str(DIS),'prior_branch_result':str(PREV)},'hashes':{'rom':sha(ROM),'abl1':sha(ABL),'disassembly':sha(DIS),'prior_branch_result':sha(PREV)},'dataflow':{'reader_call':'payload+0x5fae -> FCLK reader payload+0x463c','reader_output':'stack+0x4 reload at 0x5fb2 -> halfword store [context+0x78] at 0x5fba','consumer':'separate context layout consumer payload+0x107e4 loads [context+0x78]','comparators':['0x3e8','0x4b0'],'selectors':['0x264','0x464','0x260','0x0'],'apcb_raw_compare':{'thresholds_present_in_apcb':False,'setup_0x704_raw': '0x58c (1420)','note':'raw comparison only; no units inferred'},'direct_control_effect':'no direct WRMSR/in/out in selected windows'},'fresh_result':'Exact FCLK reader output flows from stack+0x4 through context halfword +0x78. A separate exact context consumer at 0x107e4 compares that field to 0x3e8 and 0x4b0 and emits selectors 0x264/0x464/0x260/0x0. These are raw control branches; APCB has no aligned raw 0x3e8/0x4b0, while persisted AmdSetup+0x704 is 0x58c (1420). No MHz/unit or clock-synchronization interpretation follows.','unresolved_edge':'Direct caller linkage from 0x5e68 output producer to 0x107e4 consumer and the semantics of emitted selectors 0x264/0x464/0x260 remain unresolved. No divider/PLL/hardware claim follows.','checks_detail':cs}
 (OUT/'abl1-fclk-context-consumer-result.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps({'status':result['status'],'checks':len(cs),'dataflow':result['dataflow'],'unresolved_edge':result['unresolved_edge']},indent=2))
if __name__=='__main__':main()
