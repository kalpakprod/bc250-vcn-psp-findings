#!/usr/bin/env python3
"""Correlate only the conditional raw-ABL R4 base with the retained exact static SMN map."""
import hashlib,json,re,sys
from pathlib import Path
ROOT=Path('/home/OWNER/orca/projects/bc250')
PAYLOAD=ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
LISTING=ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt'
MAP=ROOT/'docs/research/2026-09-20-oc-df-init-route.md'
BASE_RESULT=ROOT/'evidence/firmware-audit/20260920-clv-abl1-svc4-r1-target-xhigh/svc4-r1-target-result.json'
OUT=Path(__file__).resolve().parent
b=PAYLOAD.read_bytes(); t=LISTING.read_text(); m=MAP.read_text(); base=json.loads(BASE_RESULT.read_text())
checks=[]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ck(n,ok,d):
 checks.append({'name':n,'ok':bool(ok),'detail':d})
 if not ok:print(f'FAIL {n}: {d}',file=sys.stderr)
def raw(off,hx,n):
 want=bytes.fromhex(hx); got=b[off:off+len(want)]
 ck(n,got==want,f'0x{off:X} {got.hex()} expected {want.hex()}')
def ins(off,s,n):
 ok=re.search(rf'^\s*{off:x}:.*{re.escape(s)}',t,re.M)!=None
 ck(n,ok,f'0x{off:X} {s}')
ck('payload_sha256',h(PAYLOAD)=='af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a',h(PAYLOAD))
ck('listing_sha256',h(LISTING)=='b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65',h(LISTING))
ck('exact_map_report_sha256',h(MAP)=='3122a0dce28bc61942a22d567acdc29e318a714097b48877eb0391094a7d0e43',h(MAP))
ck('prior_r1_result_sha256',h(BASE_RESULT)=='05fa26427c0d969a11d3779714089943d01421780beebbe8b62b910661eeecca' and base.get('status')=='PASS',h(BASE_RESULT))
ck('map_anchor_5027c', '`0x5027C`' in m and 'row+0x20' in m, 'existing exact-clv static map report maps row+0x20 to 0x5027C')
ck('map_anchor_offset_formula','slot*0x100 + mask_bit*0x100000' in m,'exact report also records slot/mask derived offsets; no identity to ABL context byte is asserted')
# Raw fallback constants are candidates unless the current R1 base and active HEAP/fallback object are captured.
raw(0xc7de,'41f678000844824a6490','candidate_store_sequence_R1_plus_0x1878')
ck('candidate_literal_slot_61e',int.from_bytes(b[0xc9f0:0xc9f4],'little')==0x006d17c0, f'pool 0xC9F0={b[0xc9f0:0xc9f4].hex()} value=0x{int.from_bytes(b[0xc9f0:0xc9f4],"little"):08X}')
raw(0xc79a,'41f644328e488850','candidate_store_sequence_R1_plus_0x1b44')
ck('candidate_nested_literal',int.from_bytes(b[0xc9d8:0xc9dc],'little')==0x0800027c, f'pool 0xC9D8={b[0xc9d8:0xc9dc].hex()} value=0x{int.from_bytes(b[0xc9d8:0xc9dc],"little"):08X}')
# Prove static derivation formula ingredients and dynamic byte producer.
ins(0x9bea,'ubfx\tr0, r6, #0x0, #0xc','callback_descriptor_low12')
ins(0x9c56,'orr\tr0, r4, #0x50000','kind1_0x50000_base')
ins(0x9c5e,'lsr.w\tr2, r1, #0x1','kind1_byte49_high_bits')
ins(0x9c62,'and\tr1, r1, #0x1','kind1_byte49_low_bit')
ins(0x109d8,'ldr.w\tr2, [r4, #0x3b0]','byte49_provider_pointer')
ins(0x109e0,'blx\tr2','byte49_provider_call')
ins(0x109e6,'strb.w\tr0, [r4, #0x49]','byte49_dynamic_store')
# For the conditional fallback descriptor only, the base if byte49=0 coincides with the exact map anchor.
value=0x0800027c; d=0
r4=((value&0xfff)|0x50000)|((d>>1)<<20)|((d&1)<<13)
ck('conditional_example_base',r4==0x0005027c,f'descriptor=0x{value:08X}, d={d}, formula R4=0x{r4:08X}')
result={'status':'PASS' if all(x['ok'] for x in checks) else 'FAIL','checks':len(checks),'passed':sum(x['ok'] for x in checks),'inputs':{'payload_sha256':h(PAYLOAD),'listing_sha256':h(LISTING),'map_report_sha256':h(MAP),'prior_r1_result_sha256':h(BASE_RESULT)},'conditional_correlation':{'candidate_descriptor':'0x0800027C, not proven to be active table entry','context_byte49':'runtime callback-sourced at 0x109D8..0x109E6','if_byte49_zero_R4':'0x0005027C','exact_static_map_hit':'row+0x20 writes use SMN address base 0x5027C in docs/research/2026-09-20-oc-df-init-route.md','boundary':'static concordance only; active table-base binding, byte49 value, SVC#4 translation and hardware effect are unproven'},'checks_detail':checks}
(OUT/'map-candidate-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,sort_keys=True))
if result['status']!='PASS':sys.exit(1)
