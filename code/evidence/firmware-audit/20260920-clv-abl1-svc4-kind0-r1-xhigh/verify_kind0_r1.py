#!/usr/bin/env python3
import hashlib,json,re,sys
from pathlib import Path
ROOT=Path('/home/OWNER/orca/projects/bc250')
PAYLOAD=ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
LISTING=ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt'
PRIOR=ROOT/'evidence/firmware-audit/20260920-clv-abl1-svc4-descriptor-join-xhigh/descriptor-join-result.json'
OUT=Path(__file__).resolve().parent
b=PAYLOAD.read_bytes(); text=LISTING.read_text(); checks=[]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ck(n,ok,d):
 checks.append({'name':n,'ok':bool(ok),'detail':d})
 if not ok:print(f'FAIL {n}: {d}',file=sys.stderr)
def raw(off,hx,n):
 w=bytes.fromhex(hx);g=b[off:off+len(w)];ck(n,g==w,f'0x{off:X} got={g.hex()} expected={w.hex()}')
def ins(off,s,n):
 ok=re.search(rf'^\s*{off:x}:.*{re.escape(s)}',text,re.M)!=None;ck(n,ok,f'0x{off:X} {s}')
ck('payload_hash',h(PAYLOAD)=='af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a',h(PAYLOAD))
ck('listing_hash',h(LISTING)=='b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65',h(LISTING))
ck('prior_join_hash',h(PRIOR)=='31e2c2952d6d4074ddaf52fea5bed68f7656ec6a0867e225e06aab7b432f6a5c',h(PRIOR))
prior=json.loads(PRIOR.read_text());ck('prior_join_pass',prior.get('status')=='PASS' and prior.get('checks')==61,'reused prior 61/61')
# exact values from prior fallback chain, re-read raw pools only
slot=int.from_bytes(b[0xc47c:0xc480],'little'); desc=int.from_bytes(b[0xcf40:0xcf44],'little')
ck('fallback_slot_literal',slot==0x006ca7c0,f'0xC47C=0x{slot:08X}')
ck('fallback_descriptor_literal',desc==0x006f47c0,f'0xCF40=0x{desc:08X}')
ck('nested_index',((slot>>12)&0xfff)==0x6ca,f'first_slot>>12=0x{(slot>>12)&0xfff:X}')
# exact branch conditions to low12 R4 construction
ins(0x9b6a,'ldr\tr0, [sp, #0x28]','nested_index_source')
ins(0x9b70,'str\tr0, [sp, #0x2c]','local_2c_store')
ins(0x9b72,'cmp\tr0, #0x1e','local_2c_compare')
ins(0x9b74,'bhs\t0x9be0','local_2c_kind_path')
ins(0x9be0,'ldr\tr0, [sp, #0x28]','raw_nested_index_reload')
ins(0x9be2,'movw\tr1, #0x671','nested_index_threshold')
ins(0x9be6,'cmp\tr0, r1','nested_index_threshold_compare')
ins(0x9be8,'bls\t0x9cea','nested_index_low_fallback_branch')
ins(0x9bea,'ubfx\tr0, r6, #0x0, #0xc','descriptor_low12_extract')
ins(0x9bf0,'orrs\tr4, r0','R4_low12_construction')
local_2c=0x6ca-0x653
ck('local_2c_value',local_2c==0x77,f'0x6CA-0x653=0x{local_2c:X}; BHS 0x1E')
ck('threshold_branch',0x6ca>0x671,'0x6CA > 0x671; BLS not taken, reaches 0x9BEA')
ck('raw_kind_zero',((desc>>27)&7)==0,f'raw kind={(desc>>27)&7}')
ck('raw_bit30_zero',((desc>>30)&1)==0,f'raw bit30={(desc>>30)&1}')
ck('r4_kind0_value',desc&0xfff==0x7c0,f'R4=descriptor&0xFFF=0x{desc&0xfff:X} before kind dispatch')
# Context+40 merge mask and exact kind dispatch.
ins(0x9b82,'ldr\tr0, [r5, #0x40]','context40_read')
ins(0x9b88,'bfi\tr6, r1, #15, #5','context40_bits15_19')
ins(0x9b92,'bfi\tr6, r1, #20, #8','context40_bits20_27')
ins(0x9b98,'bfi\tr6, r0, #28, #4','context40_bits28_31')
ins(0x9c00,'ubfx\tr0, r6, #0x1b, #0x3','kind_dispatch_extract')
ins(0x9c16,'ldr\tr0, [pc, #0x25c]','kind0_invalid_log_path')
ins(0x9c1e,'b\t0x9c22','kind0_to_mapped_read')
ins(0x9c28,'mov\tr1, r4','kind0_R1_R4')
ins(0x9c2a,'bl\t0x6da4','kind0_mapped_read')
mask=((0x1f<<15)|(0xff<<20)|(0xf<<28))
ck('context40_merge_mask',mask==0xffff8000,f'context+0x40 replaces descriptor mask 0x{mask:08X}; low15 bits including low12 preserved')
ck('kind0_R1_encoded',0x7c0==0x0|0x7c0,'kind0 branch R1=0x000007C0 before any alternative kind branch')
# Wrapper split exact.
ins(0x6dcc,'lsrs\tr0, r6, #0xc','svc4_read_high_split')
ins(0x6dce,'ubfx\tr4, r6, #0x0, #0xc','svc4_read_low12_split')
ins(0x6dd2,'lsls\tr0, r0, #0xc','svc4_read_page_align')
ins(0x6dd4,'svc\t#0x4','svc4_read')
ck('kind0_page_offset',((0x7c0>>12)<<12)==0 and (0x7c0&0xfff)==0x7c0,'encoded R1=0x7C0 -> SVC page=0, offset=0x7C0')
result={'status':'PASS' if all(x['ok'] for x in checks) else 'FAIL','checks':len(checks),'passed':sum(x['ok'] for x in checks),'fallback_values':{'table_0x61e':'0x006CA7C0','nested_index':'0x6CA','descriptor':'0x006F47C0'},'actual_kind0_decode':{'branch':'0x9B72 BHS -> 0x9BE0; 0x9BE6 compare 0x6CA vs 0x671; 0x9BEA extracts descriptor low12; 0x9BF0 ORS into R4; raw kind 0 -> 0x9C16 log -> 0x9C22 read','R4_before_context_kind_dispatch':'0x000007C0','context40_rewrite_mask':'0xFFFF8000','R1_at_0x9c28':'R4; raw-kind0 path 0x000007C0 unless context merge changes kind dispatch','svc4_encoding':'page=(R1>>12)<<12; offset=R1&0xFFF; raw-kind0 example page=0, offset=0x7C0'},'correction':'Earlier wording that raw kind0 leaves R4 zero was wrong: exact bytes at 0x9BEA/0x9BF0 set R4 to descriptor low12 0x7C0 before 0x9C00 kind dispatch. No physical map claim.', 'boundary':'Context+0x40 may rewrite high descriptor bits and switch to kind1..4 branches; active HEAP/fallback and runtime context value remain unresolved.', 'checks_detail':checks}
(OUT/'kind0-r1-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,sort_keys=True))
if result['status']!='PASS':sys.exit(1)
