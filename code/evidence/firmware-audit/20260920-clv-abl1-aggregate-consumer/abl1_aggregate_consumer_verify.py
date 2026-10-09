#!/usr/bin/env python3
"""Trace exact ABL1 aggregate +0x2BC load into first consumer branch/call."""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
ABL=ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin';DIS=ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt';EXPECTED='af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(cs,n,g,e):
 ok=g==e
 def s(v):
  if isinstance(v,(bytes,bytearray)):return v.hex()
  return v
 cs.append({'check':n,'passed':ok,'got':s(g),'expected':s(e)})
 if not ok:raise AssertionError(f'{n}: got {g!r}, expected {e!r}')
def main():
 b=ABL.read_bytes();d=DIS.read_text();cs=[];check(cs,'ABL1 hash',sha(ABL),EXPECTED);check(cs,'fresh disassembly exists',DIS.exists(),True);check(cs,'aggregate load listing exists','7e40:' in d and '[r0, #0x2bc]' in d,True)
 # Exact raw bytes and source provenance around consumer at 0x7E40.
 root_load=bytes.fromhex('3068');agg_load=bytes.fromhex('d0f8bc62');pass_r1=bytes.fromhex('3146');check(cs,'caller context load root',b[0x7e3e:0x7e3e+len(root_load)],root_load);check(cs,'aggregate consumer load',b[0x7e40:0x7e40+len(agg_load)],agg_load);check(cs,'aggregate passed as r1',b[0x7e52:0x7e52+len(pass_r1)],pass_r1)
 check(cs,'consumer call 0x751c listing','7e54:' in d and 'bl\t0x751c' in d,True);check(cs,'consumer result conversion',b[0x7e58:0x7e5a],bytes.fromhex('c7b2'));check(cs,'consumer result stored stack',b[0x7e5a:0x7e5c],bytes.fromhex('0096'));check(cs,'consumer next service call','7e64:' in d and 'bl\t0x130c' in d,True)
 # Function 751C exact policy branch: aggregate in r1 is matched against an
 # 8-entry halfword table and r0 selects the returned class 0/7.
 pro_class=bytes.fromhex('30b5');table_load=bytes.fromhex('084b');table_bytes=bytes.fromhex('04db06002de9f041456806462c682146');check(cs,'consumer function prologue',b[0x751c:0x751c+len(pro_class)],pro_class);check(cs,'consumer PC-relative table load',b[0x751e:0x751e+len(table_load)],table_load);check(cs,'consumer policy table bytes',b[0x7540:0x7540+len(table_bytes)],table_bytes);check(cs,'consumer aggregate compare listing','7528:' in d and 'cmp\tr5, r1' in d,True);check(cs,'consumer class branch listing','7532:' in d and 'cmp\tr0, #0x6' in d,True);class7=bytes.fromhex('072030bd');check(cs,'consumer returns class7 bytes',b[0x753a:0x753a+len(class7)],class7)
 # Struct provenance from containing function: 0x75CC receives r0 and moves it
 # into r6, which is the pointer dereferenced at 0x7E3E.
 pro=bytes.fromhex('2de9f04f');r0r6=bytes.fromhex('0646');check(cs,'containing function prologue',b[0x75cc:0x75cc+len(pro)],pro);check(cs,'containing r0->r6 provenance',b[0x75d0:0x75d0+len(r0r6)],r0r6)
 result={'status':'PASS','checks':len(cs),'route':'ABL1 aggregate +0x2BC load at 0x7E40 -> policy classifier 0x751C -> class/result service call 0x130C','evidence_class':['observed-bytes','static-analysis'],'input':str(ABL),'abl1_sha256':sha(ABL),'disassembly':str(DIS),'fresh_result':'A concrete downstream consumer is proven outside function 0x95FC: containing function 0x75CC receives a context in r0, preserves it in r6, loads root=[r6] at 0x7E3E, then loads aggregate [root+0x2BC] at 0x7E40. It passes the aggregate as r1 to classifier 0x751C, which compares against an 8-entry halfword table and returns class 0 or 7 based on r0; the result is converted/stored and passed onward through call 0x130C. This is a control-class consumer, not a MHz or 1:1 clock proof.','limits':'Exact ABL1 static path only; units, runtime base, external caller, downstream service semantics, memory clock identity, synchronization and hardware remain unknown.','checks_detail':cs}
 (OUT/'abl1-aggregate-consumer-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'checks':len(cs),'fresh_result':result['fresh_result']},indent=2))
if __name__=='__main__':main()
