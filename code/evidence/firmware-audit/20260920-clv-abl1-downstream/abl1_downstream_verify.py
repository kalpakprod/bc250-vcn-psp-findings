#!/usr/bin/env python3
"""Locate exact ABL1/function-95FC evidence and bound post-return use."""
from __future__ import annotations
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
DOC=ROOT/'docs/research/20260920-clv-abl-memory-review.md'; EXPECTED='af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(cs,n,g,e):
 ok=g==e;cs.append({'check':n,'passed':ok,'got':g,'expected':e})
 if not ok:raise AssertionError(f'{n}: got {g!r}, expected {e!r}')
def main():
 cs=[];doc=DOC.read_text();check(cs,'review doc exists',DOC.exists(),True);check(cs,'review doc carries ABL1 hash',EXPECTED in doc,True)
 # Read the reviewed report as input, then locate the exact decompressed body by
 # hash in evidence without assuming a historical global offset.
 candidates=[]
 for p in ROOT.glob('evidence/**/*'):
  if p.is_file() and p.stat().st_size>10000:
   try:
    if sha(p)==EXPECTED:candidates.append(p)
   except (OSError,PermissionError):pass
 check(cs,'exact decompressed ABL1 artifact copies',len(candidates),2);abl=ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin';check(cs,'reviewed ABL1 path exists',abl.exists(),True);check(cs,'ABL1 full hash',sha(abl),EXPECTED);check(cs,'duplicate ABL1 bytes match',sha(candidates[0])==sha(candidates[1]),True)
 # Locate existing exact 95FC evidence/report/listing references.
 refs=[]
 for p in ROOT.glob('docs/**/*'):
  if p.is_file():
   try:
    t=p.read_text(errors='ignore')
    if '95FC' in t or '95fc' in t:refs.append(str(p))
   except:pass
 check(cs,'function-95FC reviewed reference present',len(refs)>0,True)
 # Retain reviewed excerpts for the downstream report and search own corpus for
 # disassembly/listings named by the reviewed source.
 snippet='\n'.join(line for line in doc.splitlines() if any(k in line.lower() for k in ('95fc','2bc','selected speed','aggregate','abl1')))
 asm_refs=[]
 for p in ROOT.glob('evidence/**/*'):
  if p.is_file() and p.suffix in ('.asm','.txt','.json','.md','.py'):
   try:
    t=p.read_text(errors='ignore')
    if '95fc' in t.lower() and ('abl1' in t.lower() or 'memory' in t.lower()):asm_refs.append(str(p))
   except:pass
 check(cs,'downstream listing/report references found',len(asm_refs)>0,True)
 result={'status':'PASS','checks':len(cs),'input':str(abl),'abl1_sha256':sha(abl),'review_doc':str(DOC),'reviewed_excerpt':snippet,'reference_paths':refs[:50],'downstream_reference_paths':asm_refs[:100],'fresh_result':'Exact ABL1 input and reviewed function-0x95FC evidence located; downstream caller/use tracing is the next bounded operation.','limits':'No firmware/hardware/runtime claim; no historical global offset assumed.'}
 (OUT/'abl1-downstream-preflight.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'checks':len(cs),'input':str(abl),'references':asm_refs[:20]},indent=2))
if __name__=='__main__':main()
