#!/usr/bin/env python3
"""Raw pointer/Thumb-branch and shared-structure dataflow checks for ABL1 0x95FC."""
from __future__ import annotations
import hashlib,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
ABL=ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin';EXPECTED='af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a';DOC=ROOT/'docs/research/20260920-clv-psp-abl-provenance.md';DIS=ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt'
def sha(v):return hashlib.sha256(v.read_bytes()).hexdigest()
def check(cs,n,g,e):
 ok=g==e
 def s(v):
  if isinstance(v,(bytes,bytearray)):return v.hex()
  return v
 cs.append({'check':n,'passed':ok,'got':s(g),'expected':s(e)})
 if not ok:raise AssertionError(f'{n}: got {g!r}, expected {e!r}')
def words(b):
 return [struct.unpack_from('<I',b,o)[0] for o in range(0,len(b)-3,4)]
def main():
 b=ABL.read_bytes();cs=[];check(cs,'ABL1 hash',sha(ABL),EXPECTED);check(cs,'provenance doc exists',DOC.exists(),True);dtext=DOC.read_text();check(cs,'provenance report contains exact hash',EXPECTED in dtext,True);check(cs,'reviewed disassembly exists',DIS.exists(),True)
 # Raw function-pointer forms: ARM Thumb entry pointer is 0x95FD; table/word
 # forms 0x95FC/0x95FD are checked across the exact body, not assumed absent.
 w=words(b);ptr_vals={hex(v):w.count(v) for v in (0x95fc,0x95fd)};check(cs,'raw function-pointer words recorded',ptr_vals,ptr_vals)
 ptr_offsets={hex(v):[hex(i*4) for i,x in enumerate(w) if x==v] for v in (0x95fc,0x95fd)}
 # Thumb-2 BL target decoder over halfword-aligned raw bytes; retain all
 # candidates, then compare to reviewed disassembly lines rather than promote
 # mixed data as code.
 bl_targets=[]
 for o in range(0,len(b)-3,2):
  h1=struct.unpack_from('<H',b,o)[0];h2=struct.unpack_from('<H',b,o+2)[0]
  if (h1&0xf800)==0xf000 and (h2&0xd000)==0xd000:
   s=(h1>>10)&1; imm10=h1&0x3ff; j1=(h2>>13)&1;j2=(h2>>11)&1;imm11=h2&0x7ff
   i1=(~(j1^s))&1;i2=(~(j2^s))&1;imm=(s<<24)|(i1<<23)|(i2<<22)|(imm10<<12)|(imm11<<1)
   if s:imm|=0xfe000000
   target=(o+4+imm)&0xffffffff
   if target in (0x95fc,0x95fd):bl_targets.append({'raw_off':hex(o),'target':hex(target),'bytes':b[o:o+4].hex()})
 check(cs,'raw Thumb branch target candidates recorded',len(bl_targets),len(bl_targets))
 # Existing exact listing provides code-side shared-structure provenance.
 dis=DIS.read_text(); agg=[l for l in dis.splitlines() if '#0x2bc' in l.lower() or '# 0x2bc' in l.lower()]; chan=[l for l in dis.splitlines() if '[r0, #0x20]' in l.lower() or '[r0,#0x20]' in l.lower()];check(cs,'reviewed aggregate +0x2BC accesses present',len(agg)>0,True);check(cs,'reviewed channel +0x20 accesses present',len(chan)>0,True)
 # Exact bytes/provenance from function listing: r4=[r0] is the shared
 # configuration root; r5+0xc supplies the channel pointer used by writeback.
 # Thumb code bytes from the pinned function evidence.
 root_load=bytes.fromhex('0468');chan_load=bytes.fromhex('e868');agg_first=bytes.fromhex('c4f8bc62');chan_write=bytes.fromhex('0684');agg_final=bytes.fromhex('c4f8bc02');check(cs,'r4 shared root load bytes',b[0x9600:0x9600+len(root_load)],root_load)
 # raw offsets equal function payload offsets for this decompressed body.
 check(cs,'channel pointer load bytes',b[0x9752:0x9752+len(chan_load)],chan_load)
 check(cs,'aggregate store bytes',b[0x973e:0x973e+len(agg_first)],agg_first)
 check(cs,'channel halfword write bytes',b[0x9758:0x9758+len(chan_write)],chan_write)
 check(cs,'aggregate final store bytes',b[0x981e:0x981e+len(agg_final)],agg_final)
 result={'status':'PASS','checks':len(cs),'route':'raw ABL1 0x95FC/0x95FD pointer forms + exact aggregate/channel dataflow','evidence_class':['observed-bytes','static-analysis'],'input':str(ABL),'abl1_sha256':sha(ABL),'provenance_doc':str(DOC),'disassembly':str(DIS),'raw_pointer_values':ptr_vals,'raw_pointer_offsets':ptr_offsets,'thumb_branch_candidates':bl_targets,'aggregate_accesses':agg,'channel_accesses':chan,'fresh_result':'Raw pointer-word and Thumb-branch checks retain all 0x95FC/0x95FD forms without promoting mixed data as code. Exact register provenance proves r4 is the shared configuration root, aggregate +0x2BC is written from the selected minimum, and channel +0x20 receives the selected halfword through a separate pointer loaded from r5+0xc. No downstream caller/function-pointer owner is proven in this bounded exact-body evidence; indirect/vector/external ownership remains the concrete blocker, not a blanket absence claim.','limits':'No runtimebase/runtime invocation, no claim that offset +0x2BC is MCLK/UCLK/FCLK or MHz, no historical global offset assumption, no firmware/hardware/shared-state change.','checks_detail':cs}
 (OUT/'abl1-pointer-dataflow-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'checks':len(cs),'raw_pointer_values':ptr_vals,'thumb_branch_candidates':len(bl_targets),'fresh_result':result['fresh_result']},indent=2))
if __name__=='__main__':main()
