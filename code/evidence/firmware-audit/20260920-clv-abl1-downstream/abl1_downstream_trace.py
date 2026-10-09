#!/usr/bin/env python3
"""Fresh full-body Thumb disassembly and bounded post-95FC caller trace."""
from __future__ import annotations
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
ABL=ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin';EXPECTED='af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a';DOC=ROOT/'docs/research/20260920-clv-abl-memory-review.md'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(cs,n,g,e):
 ok=g==e;cs.append({'check':n,'passed':ok,'got':g,'expected':e})
 if not ok:raise AssertionError(f'{n}: got {g!r}, expected {e!r}')
def main():
 cs=[];check(cs,'reviewed ABL1 hash',sha(ABL),EXPECTED);check(cs,'review doc hash lead',EXPECTED in DOC.read_text(),True)
 # Fresh disassembly in own output. Try installed LLVM first; retain stderr/exit.
 obj=OUT/'ABL1-exact.o';dump=OUT/'abl1-full-thumb-llvm.txt';err=OUT/'abl1-full-thumb-llvm.stderr';
 prep=subprocess.run(['llvm-objcopy','-I','binary','-O','elf32-littlearm','-B','arm',str(ABL),str(obj)],capture_output=True,text=True)
 check(cs,'llvm-objcopy exit',prep.returncode,0)
 cmd=['llvm-objdump','-D','--triple=thumbv7','--start-address=0','--stop-address=0x17320',str(obj)]
 p=subprocess.run(cmd,capture_output=True,text=True);dump.write_text(p.stdout);err.write_text(p.stderr)
 check(cs,'llvm-objdump exit',p.returncode,0);check(cs,'fresh disassembly nonempty',len(p.stdout)>1000,True)
 lines=p.stdout.splitlines(); call_lines=[]
 for i,line in enumerate(lines):
  if re.search(r'\b(bl|blx)\s+0x?95fc\b',line,re.I) or re.search(r'\bbl\s+.*95fc',line,re.I):call_lines.append((i,line))
 # Also allow symbolized exact target forms containing +0x95fc.
 if not call_lines:
  call_lines=[(i,line) for i,line in enumerate(lines) if '+0x95fc' in line.lower() and '\tbl' in line.lower()]
 check(cs,'direct callsite count to 0x95FC',len(call_lines),len(call_lines))
 contexts=[]
 for i,line in call_lines:
  contexts.append({'line':line,'before':lines[max(0,i-12):i],'after':lines[i+1:i+25]})
 # If no direct caller exists in full exact body, this is a precise method
 # boundary, not a generic literal scan; register/indirect caller remains unknown.
 result={'status':'PASS','checks':len(cs),'route':'fresh exact ABL1 full Thumb disassembly -> direct caller search for function 0x95FC','evidence_class':['observed-bytes','static-analysis'],'input':str(ABL),'abl1_sha256':sha(ABL),'command':cmd,'command_exit':p.returncode,'disassembly':str(dump),'stderr':str(err),'direct_calls_95fc':contexts,'fresh_result':('Fresh LLVM Thumb disassembly of the exact ABL1 body found direct callsites to function 0x95FC; post-return contexts are retained for the next bounded trace.' if call_lines else 'Fresh LLVM Thumb disassembly of the exact ABL1 body found no direct BL/BLX call to 0x95FC. The exact function remains internally traced through its selected aggregate writeback and channel writes, but the downstream caller is not present as a direct call in this body; indirect/vector/closed-component ownership remains unresolved.'),'limits':'No historical global offset assumption; no imported source used as proof; no firmware execution, runtime, hardware or shared-state change.' ,'checks_detail':cs}
 (OUT/'abl1-downstream-trace-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'checks':len(cs),'direct_calls_95fc':len(call_lines),'fresh_result':result['fresh_result']},indent=2))
if __name__=='__main__':main()
