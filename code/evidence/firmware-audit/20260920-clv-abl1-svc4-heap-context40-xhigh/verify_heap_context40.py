#!/usr/bin/env python3
"""Bounded exact-byte HEAP/fallback branch polarity and context+0x40 producer."""
import hashlib,json,re,sys
from pathlib import Path
ROOT=Path('/home/OWNER/orca/projects/bc250')
PAYLOAD=ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
LISTING=ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt'
PRIOR_JOIN=ROOT/'evidence/firmware-audit/20260920-clv-abl1-svc4-descriptor-join-xhigh/descriptor-join-result.json'
PRIOR_CB=ROOT/'evidence/firmware-audit/20260920-clv-abl1-context660-callback-xhigh/abl1-context660-callback-result.json'
OUT=Path(__file__).resolve().parent
b=PAYLOAD.read_bytes();text=LISTING.read_text()
checks=[]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ck(n,ok,d):
 checks.append({'name':n,'ok':bool(ok),'detail':d})
 if not ok:print(f'FAIL {n}: {d}',file=sys.stderr)
def raw(off,hx,n):
 want=bytes.fromhex(hx);got=b[off:off+len(want)];ck(n,got==want,f'0x{off:X} got={got.hex()} expected={want.hex()}')
def ins(off,s,n):
 ok=re.search(rf'^\s*{off:x}:.*{re.escape(s)}',text,re.M)!=None;ck(n,ok,f'0x{off:X} {s}')
ck('payload_hash',h(PAYLOAD)=='af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a',h(PAYLOAD))
ck('listing_hash',h(LISTING)=='b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65',h(LISTING))
ck('prior_join_hash',h(PRIOR_JOIN)=='31e2c2952d6d4074ddaf52fea5bed68f7656ec6a0867e225e06aab7b432f6a5c',h(PRIOR_JOIN))
ck('prior_callback_hash',h(PRIOR_CB)=='cf16bf73c370bac1c4426f7c79e64890898a11da7743304528ddeccfe3cd7ecb',h(PRIOR_CB))
# Exact heap helper return polarity.
ins(0x6374,'ldr\tr2, [pc, #0x70]','heap_lookup_table_literal')
ins(0x63a6,'cbz\tr6, 0x63ba','heap_match_success_guard')
ins(0x63ae,'str\tr2, [r0, #0x8]','heap_match_body_return')
ins(0x63b0,'ldr\tr2, [r3, #0x4]','heap_match_size_read')
ins(0x63b4,'str\tr1, [r0, #0x4]','heap_match_length_return')
ins(0x63b6,'movs\tr0, #0x0','heap_match_status_zero')
ins(0x63b8,'pop\t{r3, r4, r5, r6, r7, pc}','heap_match_return')
ins(0x63e2,'movs\tr0, #0x2','heap_notfound_status_two')
ins(0x63e4,'pop\t{r3, r4, r5, r6, r7, pc}','heap_notfound_return')
# B228 branch polarity and storage.
ins(0xb23a,'bl\t0x6374','B228_heap_lookup')
ins(0xb23e,'cbz\tr0, 0xb264','B228_zero_status_existing_path')
ins(0xb264,'ldr\tr0, [sp, #0x18]','B264_heap_payload_pointer')
ins(0xb266,'str\tr0, [r4, #0x44]','B266_existing_context44_install')
ins(0xb268,'b\t0xb25e','B268_existing_early_return')
ins(0xb240,'movw\tr0, #0x26c0','B240_fallback_size')
ins(0xb244,'strd\tr0, r5, [sp]','B244_fallback_key')
ins(0xb248,'movs\tr0, #0x4','B248_fallback_type4')
ins(0xb252,'bl\t0x6238','B252_fallback_allocator')
ins(0xb26a,'ldr\tr1, [sp, #0xc]','B26A_fallback_pointer')
ins(0xb274,'str\tr1, [r4, #0x44]','B274_fallback_context44_install')
# Function 7378 context object producer: R5=arg0, R6=arg1; child=[R6+3C4]; context+40=child+4.
ins(0x7378,'push.w\t{r4, r5, r6, r7, r8, r9, lr}','context_producer_entry')
ins(0x737c,'mov\tr5, r0','context_parent_R5')
ins(0x7384,'mov\tr6, r1','context_source_arg_R6')
ins(0x739e,'str\tr6, [r5]','context_root_store')
ins(0x73ae,'ldr.w\tr4, [r6, #0x3c4]','context_child_pointer_load')
ins(0x73b2,'str\tr4, [r5, #0x8]','context_child_pointer_store')
ins(0x73b6,'ldr\tr0, [r4, #0x4]','context40_source_field_load')
ins(0x73b8,'str\tr0, [r5, #0x40]','context40_store')
# Callback merge reads this field and merges high descriptor bits.
ins(0x9b82,'ldr\tr0, [r5, #0x40]','callback_context40_read')
ins(0x9b88,'bfi\tr6, r1, #15, #5','callback_context40_midfield_merge')
ins(0x9b98,'bfi\tr6, r0, #28, #4','callback_context40_highfield_merge')
# Keep active dispatch object boundary explicit.
ins(0x1095a,'ldr.w\tr4, [r0, #0x660]','active_dispatch_slot_load')
ck('active_dispatch_not_joined',True,'0x10958 current R0 object is not statically joined here to the 0x7378 R5 initializer object')
result={'status':'PASS' if all(x['ok'] for x in checks) else 'FAIL','checks':len(checks),'passed':sum(x['ok'] for x in checks),'inputs':{'payload_sha256':h(PAYLOAD),'listing_sha256':h(LISTING),'prior_join_sha256':h(PRIOR_JOIN),'prior_callback_sha256':h(PRIOR_CB)},'branch':{'heap_helper_status0':'match found: 0x63B6 returns R0=0, B23E CBZ takes B264/B266 existing-body install and B268 early return','heap_helper_status2':'no matching node: 0x63E2 returns R0=2, B23E falls through B240/B252 allocation then B26A/B274 fallback install','status7':'invalid HEAP signature path returns nonzero and does not take B264; exact downstream behavior is outside this bounded branch'},'context40':{'producer_function':'0x7378','parent_context':'R5=R0 at 0x737C','source_argument':'R6=R1 at 0x7384','child_pointer':'R4=[R6+0x3C4] at 0x73AE and [R5+0x8] at 0x73B2','stored_value':'context+0x40 <- [R4+0x4] at 0x73B6/0x73B8','consumer':'callback reads [R5+0x40] at 0x9B82 and BFI-merges bits15..19 and28..31 into descriptor'},'boundary':'The branch polarity and nearest context+0x40 producer are exact static facts; active dispatcher object identity, runtime HEAP contents, runtime context bytes, SVC#4 translation, physical register and hardware effect remain unresolved. No firmware/hardware write.', 'checks_detail':checks}
(OUT/'heap-context40-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,sort_keys=True))
if result['status']!='PASS':sys.exit(1)
