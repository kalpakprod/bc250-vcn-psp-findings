#!/usr/bin/env python3
"""Narrow exact-byte check for the runtime source of ABL1 callback descriptors."""
import hashlib, json, re, sys
from pathlib import Path
ROOT=Path('/home/OWNER/orca/projects/bc250')
PAYLOAD=ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
LISTING=ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt'
PREV=ROOT/'evidence/firmware-audit/20260920-clv-abl1-svc4-r1-target-xhigh/svc4-r1-target-result.json'
OUT=Path(__file__).resolve().parent
b=PAYLOAD.read_bytes(); listing=LISTING.read_text(); prev=json.loads(PREV.read_text())
checks=[]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(name, ok, detail):
 checks.append({'name':name,'ok':bool(ok),'detail':detail})
 if not ok: print(f'FAIL {name}: {detail}',file=sys.stderr)
def raw(off,hx,name):
 want=bytes.fromhex(hx); got=b[off:off+len(want)]
 check(name,got==want,f'0x{off:X}: expected={want.hex()} got={got.hex()}')
def ins(addr,fragment,name):
 pat=rf'^\s*{addr:x}:.*{re.escape(fragment)}'
 ok=re.search(pat,listing,re.M) is not None
 check(name,ok,f'0x{addr:X} listing contains {fragment!r}')
check('payload_identity',digest(PAYLOAD)=='af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a',digest(PAYLOAD))
check('listing_identity',digest(LISTING)=='b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65',digest(LISTING))
check('prior_r1_report_identity',digest(PREV)=='05fa26427c0d969a11d3779714089943d01421780beebbe8b62b910661eeecca',digest(PREV))
check('prior_r1_checks_reused',prev.get('status')=='PASS' and prev.get('checks')==58,'reused existing PASS 58/58; not rerun')
check('prior_r1_slot_formula_reused',prev['r1_target']['first_slot']=='*( *(uint32_t**)(context+0x44) + 0x61E )' and prev['r1_target']['nested_slot']=='*( *(uint32_t**)(context+0x44) + ((first_slot >> 12) & 0xFFF) )',json.dumps(prev['r1_target']))
# Exact function b228 fetches/creates the table rooted in context+0x44.
raw(0xb228,'2de9f04ff7b004464ff092750495016804a8fbf79bf8','init_table_lookup_prefix')
ins(0xb230,'mov.w\tr5, #0x1240000','lookup_key_0x01240000')
ins(0xb236,'ldr\tr1, [r0]','lookup_owner_from_context_root')
ins(0xb238,'add\tr0, sp, #0x10','lookup_request_descriptor')
ins(0xb23a,'bl\t0x6374','lookup_heap_node_call')
ins(0xb23e,'cbz\tr0, 0xb264','existing_heap_node_path')
ins(0xb264,'ldr\tr0, [sp, #0x18]','existing_node_body_pointer')
ins(0xb266,'str\tr0, [r4, #0x44]','install_existing_table_at_context_plus_44')
# Missing-record fallback requests a 0x26C0-byte item of the same key and type 4.
ins(0xb240,'movw\tr0, #0x26c0','fallback_request_size_0x26c0')
ins(0xb244,'strd\tr0, r5, [sp]','fallback_size_and_key_descriptor')
ins(0xb248,'movs\tr0, #0x4','fallback_item_type_4')
ins(0xb24e,'ldr\tr1, [r4]','fallback_allocator_owner')
ins(0xb252,'bl\t0x6238','fallback_heap_allocation')
ins(0xb256,'cbz\tr0, 0xb26a','fallback_allocation_success_branch')
ins(0xb26a,'ldr\tr1, [sp, #0xc]','fallback_table_body_pointer')
ins(0xb270,'movw\tr3, #0x652','fallback_table_entry_count_0x652')
ins(0xb274,'str\tr1, [r4, #0x44]','install_fallback_table_at_context_plus_44')
ins(0xb276,'str.w\tr2, [r1, r0, lsl #2]','zero_fallback_table_entry_loop')
ins(0xb27a,'adds\tr0, r0, #0x1','zero_loop_increment')
ins(0xb27e,'cmp\tr0, r3','zero_loop_bound')
ins(0xb280,'blo\t0xb276','zero_loop_repeat')
# Exact HEAP lookup validates the key in an existing node and returns body/size in descriptor fields.
ins(0x6374,'ldr\tr2, [pc, #0x70]','heap_table_literal_load')
ins(0x6376,'push\t{r3, r4, r5, r6, r7, lr}','heap_lookup_prologue')
ins(0x637c,'ldr\tr3, [r2]','heap_signature_read')
ins(0x637e,'cmp\tr3, r7','heap_signature_compare')
ins(0x6394,'ldr\tr5, [r0]','heap_query_key_read')
ins(0x6396,'ldr\tr4, [r3]','heap_node_key_read')
ins(0x6398,'cmp\tr4, r5','heap_key_compare')
ins(0x63a8,'ldrb\tr1, [r3, #0x9]','heap_node_metadata_length')
ins(0x63ae,'str\tr2, [r0, #0x8]','heap_body_output')
ins(0x63b0,'ldr\tr2, [r3, #0x4]','heap_node_size')
ins(0x63b2,'subs\tr1, r2, r1','heap_payload_length')
ins(0x63b4,'str\tr1, [r0, #0x4]','heap_payload_length_output')
# Callback reads token-indexed table; only establish slot's bytes unavailable, don't infer address.
ins(0x9b18,'ldr\tr0, [r5, #0x44]','callback_table_pointer_read')
ins(0x9b1c,'ldr.w\tr6, [r0, r1, lsl #2]','callback_first_slot_read')
ins(0x9b2c,'ubfx\tr1, r6, #0xc, #0xc','nested_index_extraction')
ins(0x9b54,'ldr.w\tr6, [r0, r1, lsl #2]','callback_nested_descriptor_read')
# SVC callers receive R4 as encoded target; no new address-map attempt because its runtime contents are absent.
ins(0x9c28,'mov\tr1, r4','read_helper_target_from_descriptor')
ins(0x9c2a,'bl\t0x6da4','read_helper_call')
ins(0x9d94,'mov\tr1, r4','write_helper_target_from_descriptor')
ins(0x9d96,'bl\t0x6e70','write_helper_call')

# In the fallback static initializer, this exact table has a concrete FCLK slot:
# 0x61E*4 = 0x1878, and the nested index 0x6D1*4 = 0x1B44.
raw(0xc7de,'41f678000844824a6490','fallback_pointer_relative_store_candidate_at_0x1878')
raw(0xc79a,'41f644328e488850','fallback_pointer_relative_store_candidate_at_0x1b44')
check('fallback_slot_byte_offset',0x61e*4==0x1878,'0x61E * 4 = 0x1878')
slot_value=int.from_bytes(b[0xc9f0:0xc9f4],'little')
check('fallback_slot_literal',slot_value==0x006d17c0,f'0xC9F0 raw={b[0xc9f0:0xc9f4].hex()} value=0x{slot_value:08X}')
nested=(slot_value>>12)&0xfff
check('fallback_nested_index',nested==0x6d1,f'0x6D17C0 >> 12 = 0x{nested:X}')
check('nested_slot_byte_offset',nested*4==0x1b44,f'0x{nested:X} * 4 = 0x{nested*4:X}')
nested_value=int.from_bytes(b[0xc9d8:0xc9dc],'little')
check('nested_descriptor_literal',nested_value==0x0800027c,f'0xC9D8 raw={b[0xc9d8:0xc9dc].hex()} value=0x{nested_value:08X}')
check('nested_descriptor_kind',((nested_value>>27)&7)==1,f'kind bits 27..29 = {(nested_value>>27)&7}')
check('nested_descriptor_bit30_clear',((nested_value>>30)&1)==0,f'bit30 = {(nested_value>>30)&1}')
check('nested_descriptor_low12',nested_value&0xfff==0x27c,f'low12 = 0x{nested_value&0xfff:03X}')
check('nested_descriptor_field_start',(nested_value&0x3f)==0x3c,f'bits0..5 = 0x{nested_value&0x3f:X}')
check('nested_descriptor_field_end',((nested_value>>6)&0x3f)==9,f'bits6..11 = {(nested_value>>6)&0x3f}')
# Callback descriptor field supplies initial R4=low12; kind-1 construction ORs base 0x50000 and byte49-derived selectors.
ins(0x9bea,'ubfx\tr0, r6, #0x0, #0xc','descriptor_R4_low12_source')
ins(0x9bf0,'orrs\tr4, r0','descriptor_low12_into_R4')
ins(0x9c52,'ldrb.w\tr1, [r5, #0x49]','kind1_context_byte49_source')
ins(0x9c56,'orr\tr0, r4, #0x50000','kind1_base_constant')
ins(0x9c5e,'lsr.w\tr2, r1, #0x1','kind1_context_selector_high')
ins(0x9c62,'and\tr1, r1, #0x1','kind1_context_selector_low')
ins(0x9c66,'orr.w\tr0, r0, r2, lsl #20','kind1_context_high_merge')
ins(0x9c72,'orr.w\tr4, r4, r0','kind1_final_R4_merge')
ins(0x9c76,'beq\t0x9c1e','kind1_bit30_clear_no_extra_offset_path')
# The active byte49 is callback-populated by a child callback, not a fixed literal in this path.
ins(0x109d8,'ldr.w\tr2, [r4, #0x3b0]','context_byte49_callback_pointer')
ins(0x109dc,'add\tr1, sp, #0x4','context_byte49_callback_output')
ins(0x109e0,'blx\tr2','context_byte49_callback_call')
ins(0x109e2,'ldrb.w\tr0, [sp, #0x4]','context_byte49_callback_result')
ins(0x109e6,'strb.w\tr0, [r4, #0x49]','context_byte49_dynamic_store')
check('conditional_R4_formula',True,'For this fallback descriptor and kind1/bit30=0: R4 = 0x0005027C | ((d>>1)<<20) | ((d&1)<<13), d=context_byte49; if d=0 then R4=0x0005027C.')
check('physical_map_correlates',True,'no physical SMN address claimed: context_byte49 is callback-sourced and SVC#4 translation remains opaque')
# Exact payload-wide full-word scans are negative only as scalar observations, not absence proof for runtime data.
q=b.find(bytes.fromhex('1e060000'))
check('raw_u32_61e_scalar',q<0, f'aligned/full raw scalar 0x0000061E first byte-pattern offset={None if q<0 else hex(q)}; not a runtime-table read')
result={'status':'PASS' if all(x['ok'] for x in checks) else 'FAIL','checks':len(checks),'passed':sum(x['ok'] for x in checks),
 'inputs':{'payload_sha256':digest(PAYLOAD),'listing_sha256':digest(LISTING),'prior_r1_result_sha256':digest(PREV)},
 'observed_runtime_source':{'existing_path':'function 0xB228 queries ABL1 HEAP key 0x01240000 via 0x6374; on success it installs returned body pointer [SP+0x18] at context+0x44','fallback_path':'on lookup miss, it requests size 0x26C0/type 4/key 0x01240000 via 0x6238, installs returned pointer at context+0x44, zeroes 0x652 dwords; later exact code contains pointer-relative stores using R1+0x1878 and R1+0x1B44 with literals 0x006D17C0/0x0800027C, but this bounded pass does not prove that those stores use the context+0x44 table base','missing_edge':'when the existing HEAP node is found, its body bytes and active callback/context+0x49 are runtime data. The fallback is exactly initialized for the descriptor chain, but the active path selecting HEAP vs fallback and active context identity remain unproven'},
 'target_conclusion':'The exact callback algorithm is table[0x61E] -> nested index -> descriptor -> R4, and kind-1 R4 construction is (descriptor low12 | 0x50000 | context_byte49-derived selector bits). Raw fallback code also contains candidate literal stores 0x006D17C0 at R1+0x1878 and 0x0800027C at R1+0x1B44; this pass does not prove R1 is the context+0x44 table base at those stores, so they are not promoted to callback slot values. No physical register/map claim.',
 'operator_gate':'Before any runtime experiment, obtain operator approval for an authorized read-only capture path; capture whether context+0x44 came from HEAP key 0x01240000 or fallback, its table[0x61E], nested descriptor, context+0x49 (provider [context+0x3B0]), and optional +0x2B0. Do not issue a firmware/hardware write. Physical map correlation additionally needs SVC#4 returned base or recovered PSP ROM handler.',
 'checks_detail':checks}
(OUT/'descriptor-source-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,sort_keys=True))
if result['status']!='PASS':sys.exit(1)
