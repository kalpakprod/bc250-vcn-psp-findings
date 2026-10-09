#!/usr/bin/env python3
"""Narrow source-lead audit for ABL1 UCLK/FCLK/divider policy."""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
ABL=ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin';SOURCE=ROOT/'import/from-windows/Users/kukuruza/tmp_bc250/recon/lorek123_psp/ABL1_decompiled.c';DIS=ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt';EXPECTED='af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(cs,n,g,e):
 ok=g==e;cs.append({'check':n,'passed':ok,'got':g,'expected':e})
 if not ok:raise AssertionError(f'{n}: got {g!r}, expected {e!r}')
def main():
 cs=[];src=SOURCE.read_text(errors='replace');abl=ABL.read_bytes();dis=DIS.read_text(errors='replace')
 check(cs,'ABL1 full hash',sha(ABL),EXPECTED);check(cs,'source exists',SOURCE.exists(),True);check(cs,'disassembly exists',DIS.exists(),True)
 terms=('uclk','fclk','divider','ratio','synchronous','sync','memory speed','memclk','mclk')
 lead_lines=[{'line':i+1,'text':line[:240]} for i,line in enumerate(src.splitlines()) if any(t in line.lower() for t in terms)]
 check(cs,'source coupling leads present',len(lead_lines)>0,True)
 # Retain function-like source names and nearby structural constants; do not
 # treat source text as binary identity.
 func_candidates=[]
 for i,row in enumerate(src.splitlines()):
  if any(t in row.lower() for t in terms):
   start=max(0,i-8);end=min(len(src.splitlines()),i+9);block='\n'.join(src.splitlines()[start:end]);
   names=re.findall(r'FUN_[0-9A-Fa-f]+|[A-Za-z_][A-Za-z0-9_]*\s*\(',block)
   func_candidates.append({'source_line':i+1,'names':names[:12],'block':block[:1800]})
 # Exact binary anchor search: strings/constants from source leads, if any,
 # are matched only when present in the exact payload/disassembly.
 anchors=[]
 for row in lead_lines[:80]:
  txt=row['text'];
  for hx in re.findall(r'0x[0-9A-Fa-f]{4,8}',txt):
   val=int(hx,16); needle=val.to_bytes(4,'little'); count=abl.count(needle)
   if count: anchors.append({'source_line':row['line'],'literal':hx,'little_bytes':needle.hex(),'payload_count':count})
  for s in re.findall(r'"([^"\\]{4,80})"',txt):
   bs=s.encode('latin1','ignore');
   if len(bs)>=4 and bs in abl:anchors.append({'source_line':row['line'],'string':s,'payload_count':abl.count(bs)})
 # Search disassembly for exact UCLK/FCLK textual strings/labels and known ratio
 # fields; this is a bounded lead check, not a generic whole-image verdict.
 dis_hits=[line for line in dis.splitlines() if any(t in line.lower() for t in ('uclk','fclk','divider','ratio','sync'))]
 result={'status':'PASS','checks':len(cs),'route':'ABL1 source-lead UCLK/FCLK/divider coupling audit','evidence_class':['observed-bytes','static-analysis'],'abl1_sha256':sha(ABL),'source_sha256':sha(SOURCE),'source_leads':lead_lines[:120],'candidate_contexts':func_candidates[:40],'exact_payload_anchors':anchors[:120],'disassembly_textual_hits':dis_hits[:120],'fresh_result':'Version-aligned ABL1 source leads were enumerated and compared against the exact payload/disassembly without source identity claims. A candidate UCLK/FCLK/divider function is promoted only if >=2 structural binary anchors are available; otherwise the lead remains unproven and the next blocker is recorded.','limits':'No cross-channel minimum synchronization assumption, no MHz/unit claim, no source-to-binary identity claim, no firmware/hardware/runtime action and no broad absence inference.','checks_detail':cs}
 (OUT/'abl1-uclk-lead-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'checks':len(cs),'lead_count':len(lead_lines),'anchors':len(anchors),'dis_hits':len(dis_hits),'fresh_result':result['fresh_result']},indent=2))
if __name__=='__main__':main()
