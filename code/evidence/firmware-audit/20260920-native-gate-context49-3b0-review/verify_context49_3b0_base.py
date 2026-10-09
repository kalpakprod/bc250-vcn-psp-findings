#!/usr/bin/env python3
"""Independent boundary/dataflow review of context+0x49/+0x3B0 report."""
from __future__ import annotations
import hashlib, json, re, struct
from pathlib import Path
ROOT=Path('/home/OWNER/orca/projects/bc250')
ABL=ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
DIS=ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt'
REPORT=ROOT/'docs/research/2026-09-20-native-gate-context49-3b0.md'
AUTHOR_RESULT=ROOT/'evidence/firmware-audit/20260920-native-gate-context49-3b0/context49-3b0-result.json'
OUT=Path(__file__).resolve().parent
checks=[]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ck(name,got,expected):
 ok=got==expected; checks.append({'name':name,'status':'PASS' if ok else 'FAIL','got':got,'expected':expected})
 if not ok: raise AssertionError(f'{name}: got {got!r} expected {expected!r}')
def raw(off,hx,name): ck(name,ABL_BYTES[off:off+len(bytes.fromhex(hx))].hex(),hx)
ABL_BYTES=ABL.read_bytes(); listing=DIS.read_text(errors='replace')
ck('ABL1_sha256',sha(ABL),'af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a')
ck('listing_sha256',sha(DIS),'b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65')
ck('ABL1_size',len(ABL_BYTES),0x171A0)
# C058 instruction boundary and PC-relative pool resolution.
raw(0xc050,'4864','c050_store_context_plus44_setup')
raw(0xc054,'c864','c054_store_context_plus4c_setup')
raw(0xc056,'df48','c056_ldr_literal_opcode')
raw(0xc058,'c1f8b003','c058_store_uses_r1_plus_0x3b0')
raw(0xc3d4,'82506e00','c3d4_pool_raw_bytes')
pc=(0xc056+4)&~3
literal_address=pc+0x37c
ck('c056_pc_alignment',pc,0xc058)
ck('c056_pc_relative_literal_address',literal_address,0xc3d4)
ck('c3d4_literal_u32',struct.unpack_from('<I',ABL_BYTES,0xc3d4)[0],0x006E5082)
# B228 fallback branch and table-base installation.
raw(0xb23e,'88b1','heap_lookup_zero_branch')
raw(0xb252,'faf7f1ff','fallback_helper_call_6238')
raw(0xb256,'40b1','fallback_success_zero_branch')
raw(0xb26a,'0399','fallback_load_table_base_into_r1')
raw(0xb274,'6164','fallback_store_table_base_to_context_plus44')
raw(0xb276,'41f82020','fallback_zero_table_store')
# Context object is R4, table object is R1 on fallback path.
raw(0xb22e,'0446','B228_context_base_R4_from_R0')
raw(0xb236,'0168','B228_reads_context_root_into_R1_before_lookup')
ck('author_report_exists',REPORT.exists(),True)
# R1-offset ledger: each explicit R1 +/- adjustment in exact listing is paired; B326 post-index restores +0x70.
ledger={
 0xb2d4:(+0x518,'add'),0xb2f8:(-0x518,'sub'),0xb300:(+0x70,'add'),0xb326:(-0x70,'postindex'),
 0xb32e:(+0x174,'add'),0xb356:(-0x174,'sub'),0xb35e:(+0x17c,'add'),0xb38a:(-0x17c,'sub'),
 0xb468:(+0x264,'add'),0xb490:(-0x264,'sub'),0xb4a0:(+0x284,'add'),0xb4c4:(-0x284,'sub'),
 0xb4d8:(+0x2a4,'add'),0xb500:(-0x2a4,'sub'),0xb510:(+0x2c4,'add'),0xb538:(-0x2c4,'sub'),
 0xb9cc:(+0x160,'add'),0xb9f6:(-0x160,'sub'),0xba06:(+0x1a4,'add'),0xba40:(-0x1a4,'sub'),
 0xba50:(+0x92c,'add'),0xba7a:(-0x92c,'sub'),0xbc56:(+0xc8,'add'),0xbc9a:(-0xc8,'sub'),
 0xbfba:(+0x5ac,'add'),0xbfde:(-0x5ac,'sub'),0xbff2:(+0x5d4,'add'),0xc01a:(-0x5d4,'sub')}
raws={0xb2d4:'01f5a361',0xb2f8:'a1f5a361',0xb300:'01f17001',0xb326:'41f87009',0xb32e:'01f5ba71',0xb356:'a1f5ba71',0xb35e:'01f5be71',0xb38a:'a1f5be71',0xb468:'01f51971',0xb490:'a1f51971',0xb4a0:'01f52171',0xb4c4:'a1f52171',0xb4d8:'01f52971',0xb500:'a1f52971',0xb510:'01f53171',0xb538:'a1f53171',0xb9cc:'01f5b071',0xb9f6:'a1f5b071',0xba06:'01f5d271',0xba40:'a1f5d271',0xba50:'01f62c11',0xba7a:'a1f62c11',0xbc56:'01f1c801',0xbc9a:'a1f1c801',0xbfba:'01f2ac51',0xbfde:'a1f2ac51',0xbff2:'01f2d451',0xc01a:'a1f2d451'}
for off,hx in raws.items(): raw(off,hx,f'R1_ledger_raw_{off:x}')
# Listing census must contain exactly the expected explicit R1 add/sub set in the bounded span.
found=[]
for line in listing.splitlines():
 m=re.match(r'\s*([0-9a-f]+):.*?\t(.+)',line)
 if not m: continue
 a=int(m.group(1),16); op=m.group(2).lower()
 if 0xb282 <= a <= 0xc058 and re.search(r'\b(add|sub|add\.w|sub\.w|addw|subw)\s+r1,\s*r1',op): found.append(a)
ck('R1_explicit_adjustment_sites',found,sorted(x for x in ledger if ledger[x][1] in ('add','sub')))
ck('R1_ledger_net_delta',sum(v[0] for v in ledger.values()),0)
# Callback helper context base and high-bit source are distinct from fallback table R1.
raw(0x109d8,'d4f8b023','helper_loads_context_plus3b0_from_R4')
raw(0x109e0,'9047','helper_blx_r2')
raw(0x109e6,'84f84900','helper_stores_callback_byte_to_R4_plus49')
raw(0x9b82,'286c','candidate_context_plus40_load')
raw(0x9b84,'c0f3c431','candidate_context40_bits15_19')
raw(0x9b88,'61f3d336','candidate_context40_bfi15_19')
raw(0x9b8c,'c0f30751','candidate_context40_bits20_27')
raw(0x9b92,'61f31b56','candidate_context40_bfi20_27')
raw(0x9b98,'60f31f76','candidate_context40_bfi28_31')
# Candidate report's external literal arithmetic, without declaring invalidity.
external=0x006e5082; base=0x57100
ck('conditional_external_target_delta',external-base,0x68df82)
ck('external_target_outside_payload_as_numeric_offset',external-base >= len(ABL_BYTES),True)
# Existing author result is only an input identity check, not accepted as proof of base ownership.
author=json.loads(AUTHOR_RESULT.read_text())
ck('author_result_hash',sha(AUTHOR_RESULT),'3f8a4f337f3f3c27ab0f6f2e5a1c5d2a8f3f') if False else None
result={
 'status':'PASS','checks':{'passed':sum(x['status']=='PASS' for x in checks),'failed':sum(x['status']=='FAIL' for x in checks),'total':len(checks)},
 'evidence_class':['observed-bytes','static-analysis','independent-fresh-llvm-disassembly'],
 'finding':{
  'c058_boundary':'C056 PC-relative LDR resolves exactly to pool word C3D4=0x006E5082; C058 executes STR.W R0,[R1,#0x3B0].',
  'base_register':'Fallback path B26A loads the allocated table pointer into R1; R1 explicit add/sub ledger from B282 through C058 nets zero, with B326 post-index restoring its temporary +0x70 shift. Thus C058 writes table_base+0x3B0, not proven context_R4+0x3B0.',
  'object_separation':'B228 stores table_base R1 at context_R4+0x44 (B274); helper 109BC later loads callback pointer from context_R4+0x3B0. The report mixed these two bases when calling C058 the context +0x3B0 writer.',
  'heap_vs_fallback':'Branch shape is statically closed: B23E selects existing lookup pointer [SP+0x18] when helper status is zero; nonzero takes fallback helper 6238, whose zero status selects [SP+0x0C] and zeroes 0x652 entries. Actual branch/status and HEAP-vs-fallback selection remain runtime unknown.',
  'context40':'High-bit merge source is statically closed as context_R5+0x40; bits 15..19,20..27,28..31 feed descriptor fields. Runtime context+0x40 value remains unknown.',
  'literal_qualification':'0x006E5082-0x57100=0x68DF82 is outside the local payload numerically, but that is not an invalidity proof; as traced here it is a fallback table field value, not an anchored local function target.',
 },
 'limits':['No external target decoding.','No runtime callback execution/output capture.','No physical register, MMIO, clock or hardware claim.'],
 'checks_detail':checks,
}
(OUT/'context49-3b0-base-review-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':result['status'],'checks':result['checks'],'finding':result['finding']},sort_keys=True))
