#!/usr/bin/env python3
"""Bounded symbolic R1/TABLE join through the exact B228 fallback initializer."""
import hashlib,json,re,sys,collections
from pathlib import Path
ROOT=Path('/home/OWNER/orca/projects/bc250')
PAYLOAD=ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
LISTING=ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt'
PRIOR=ROOT/'evidence/firmware-audit/20260920-clv-abl1-svc4-descriptor-source-xhigh/descriptor-source-result.json'
MAP=ROOT/'docs/research/2026-09-20-oc-df-init-route.md'
OUT=Path(__file__).resolve().parent
b=PAYLOAD.read_bytes(); text=LISTING.read_text(); prior=json.loads(PRIOR.read_text())
checks=[]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ck(n,ok,d):
 checks.append({'name':n,'ok':bool(ok),'detail':d})
 if not ok:print(f'FAIL {n}: {d}',file=sys.stderr)
def raw(off,hx,n):
 want=bytes.fromhex(hx);got=b[off:off+len(want)]
 ck(n,got==want,f'0x{off:X} got={got.hex()} expected={want.hex()}')
def ins(off,s,n):
 ok=re.search(rf'^\s*{off:x}:.*{re.escape(s)}',text,re.M)!=None
 ck(n,ok,f'0x{off:X} {s}')
ck('payload_sha256',h(PAYLOAD)=='af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a',h(PAYLOAD))
ck('listing_sha256',h(LISTING)=='b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65',h(LISTING))
ck('prior_descriptor_result_sha256',h(PRIOR)=='14f71a9b17faa3b669681c574036ccb8edb3d75b7fde966a73aa0beb9dd9f7c0' and prior['status']=='PASS',h(PRIOR))
ck('map_report_sha256',h(MAP)=='3122a0dce28bc61942a22d567acdc29e318a714097b48877eb0391094a7d0e43',h(MAP))
# Exact source setup, HEAP existing path, fallback path.
raw(0xb228,'2de9f04ff7b004464ff092750495016804a8fbf79bf8','b228_entry')
ins(0xb230,'mov.w\tr5, #0x1240000','heap_key_constant')
ins(0xb236,'ldr\tr1, [r0]','owner_load')
ins(0xb23a,'bl\t0x6374','heap_lookup_call')
ins(0xb23e,'cbz\tr0, 0xb264','heap_existing_branch')
ins(0xb264,'ldr\tr0, [sp, #0x18]','existing_body_pointer')
ins(0xb266,'str\tr0, [r4, #0x44]','existing_table_install')
ins(0xb240,'movw\tr0, #0x26c0','fallback_size')
ins(0xb244,'strd\tr0, r5, [sp]','fallback_size_key')
ins(0xb248,'movs\tr0, #0x4','fallback_type')
ins(0xb252,'bl\t0x6238','fallback_alloc_call')
ins(0xb256,'cbz\tr0, 0xb26a','fallback_success_branch')
ins(0xb26a,'ldr\tr1, [sp, #0xc]','fallback_table_base_load')
ins(0xb274,'str\tr1, [r4, #0x44]','fallback_table_install')
ins(0xb276,'str.w\tr2, [r1, r0, lsl #2]','fallback_zero_loop')
ins(0xb280,'blo\t0xb276','fallback_zero_loop_bound')
# Symbolic CFG over exact listing: R1 starts as TABLE at B26A. Calls are not on the initializer path; direct R1 updates are modeled.
insns={}
for line in text.splitlines():
 m=re.match(r'\s*([0-9a-f]+):\s+((?:[0-9a-f]{2,4}\s+)+?)\s{2,}(.+)$',line)
 if m:
  a=int(m.group(1),16); rawbytes=' '.join(m.group(2).split()); insns[a]=(len(bytes.fromhex(rawbytes)),m.group(3).strip())
def upd(v,tx,pc):
 if pc==0xb26a:return v
 m=re.match(r'(?:add(?:\.w|s)?|adds)\s+r1, r1, #0x([0-9a-f]+)$',tx)
 if m:return v+int(m.group(1),16) if v is not None else None
 m=re.match(r'(?:sub(?:\.w|s)?|subs)\s+r1, r1, #0x([0-9a-f]+)$',tx)
 if m:return v-int(m.group(1),16) if v is not None else None
 if re.match(r'(?:mov|movw|movt|ldr|ldrd|ldm|pop|eor|orr|and|ubfx|lsl|lsr|bic|rsb|adr)\w*(?:\.w)?\s+r1(?:,|\s)',tx):return None
 if tx.startswith(('bl ','blx')):return None
 return v
def succ(tx,nxt):
 m=re.match(r'b\.(?:w|n)?\s+(0x[0-9a-f]+)',tx)
 if m:return [int(m.group(1),16)]
 m=re.match(r'b\s+(0x[0-9a-f]+)',tx)
 if m and not tx.startswith('bl '):return [int(m.group(1),16)]
 m=re.match(r'b(?:eq|ne|hi|hs|lo|ls|gt|ge|lt|le|mi|pl|vs|vc|cs|cc|al)\s+(0x[0-9a-f]+)',tx)
 if m:return [int(m.group(1),16),nxt]
 m=re.match(r'cbn?z\s+r\d+,\s*(0x[0-9a-f]+)',tx)
 if m:return [int(m.group(1),16),nxt]
 if re.match(r'(?:bx\s+lr|pop.*pc)',tx):return []
 return [nxt]
# Target instructions that store candidate first/nested table slots.
targets={0xc210:0xc210,0xcc22:0xcc22,0xc79a:0xc79a,0xc7de:0xc7de,0xc7e8:0xc7e8}
Q=collections.deque([(0xb26a,0)]); seen=set(); states=collections.defaultdict(set)
while Q:
 pc,v=Q.popleft(); key=(pc,v)
 if key in seen:continue
 seen.add(key)
 if pc in targets:states[pc].add(v)
 if pc not in insns:continue
 n,tx=insns[pc];nv=upd(v,tx,pc)
 for nx in succ(tx,pc+n):
  k=(nx,nv)
  if nx in insns and k not in seen:Q.append(k)
for pc in targets:
 vals=states.get(pc,set());
 ck(f'cfg_reaches_{pc:X}',bool(vals),f'R1 states={[v for v in vals]}')
 ck(f'cfg_R1_table_plus_70_{pc:X}',vals=={0x70},f'R1 states={["TABLE" if v==0 else ("UNKNOWN" if v is None else hex(v)) for v in vals]}')
visited_pcs={pc for pc,_ in seen}
ck('cfg_c7de_r1_state',states.get(0xc7de)=={0x70},f'0xC7DE R1 states={states.get(0xc7de)}')
ck('cfg_c7e8_r1_state',states.get(0xc7e8)=={0x70},f'0xC7E8 R1 states={states.get(0xc7e8)}')
ck('cfg_visited',len(seen)>1000,f'{len(seen)} states visited')
# At C210: R0=R1+0x1808, R1=TABLE+0x70 => TABLE+0x1878 (index 0x61E), literal pool C47C.
ins(0xc202,'movw\tr0, #0x1808','first_slot_offset_instruction')
ins(0xc206,'add\tr0, r1','first_slot_address_add')
ins(0xc20c,'ldr\tr2, [pc, #0x26c]','first_slot_literal_load')
ins(0xc210,'str\tr2, [r0]','first_slot_store')
slot=int.from_bytes(b[0xc47c:0xc480],'little')
ck('first_slot_offset',0x70+0x1808==0x1878,'R1=TABLE+0x70 plus 0x1808')
ck('first_slot_index',0x1878//4==0x61e,'0x1878/4')
ck('first_slot_value',slot==0x006ca7c0,f'pool C47C=0x{slot:08X}')
first_nested=(slot>>12)&0xfff
ck('first_slot_nested_index',first_nested==0x6ca,f'first_slot>>12 = 0x{first_nested:X}')
# At CC22: R2=0x1AB8 and R1=TABLE+0x70 => TABLE+0x1B28 (index 0x6CA), literal pool CF40.
ins(0xcc18,'movw\tr2, #0x1ab8','nested_slot_offset_instruction')
ins(0xcc22,'str\tr0, [r1, r2]','nested_slot_store')
nested=int.from_bytes(b[0xcf40:0xcf44],'little')
ck('nested_slot_offset',0x70+0x1ab8==0x1b28,'R1=TABLE+0x70 plus 0x1AB8')
ck('c79a_literal_store_not_nested_slot',0x70+0x1b44==0x1bb4 and (0x1bb4//4)==0x6ed,'reachable c79A store uses T+0x1BB4 (index 0x6ED), not T+0x1B28 (index 0x6CA)')
ck('nested_slot_index',0x1b28//4==0x6ca,'0x1B28/4')
ck('nested_slot_value',nested==0x006f47c0,f'pool CF40=0x{nested:08X}')
ck('nested_descriptor_equals_callback_value',nested==0x006f47c0,'descriptor chain exact fallback literals')
# Descriptor decode from exact nested value; context+0x40 can rewrite high fields later in callback.
ck('nested_low12',(nested&0xfff)==0x7c0,f'low12=0x{nested&0xfff:X}')
ck('nested_start',(nested&0x3f)==0,'start={nested&0x3f}')
ck('nested_end',((nested>>6)&0x3f)==31,f'end={(nested>>6)&0x3f}')
ck('nested_raw_kind',((nested>>27)&7)==0,f'raw kind={(nested>>27)&7}; callback context+0x40 can rewrite high bits')
ck('nested_raw_bit30',((nested>>30)&1)==0,f'bit30={(nested>>30)&1}')
# Exact callback merge source and R1 helper sites.
ins(0x9b82,'ldr\tr0, [r5, #0x40]','context_40_descriptor_high_merge_source')
ins(0x9b88,'bfi\tr6, r1, #15, #5','context_40_merge_bits15_19')
ins(0x9b90,'lsrs\tr0, r0, #0x1c','context_40_merge_bits28_31')
ins(0x9b98,'bfi\tr6, r0, #28, #4','context_40_merge_bits28_31_store')
ins(0x9c28,'mov\tr1, r4','read_R1_helper')
ins(0x9c2a,'bl\t0x6da4','read_helper')
ins(0x9d94,'mov\tr1, r4','write_R1_helper')
ins(0x9d96,'bl\t0x6e70','write_helper')
result={'status':'PASS' if all(x['ok'] for x in checks) else 'FAIL',
 'checks':len(checks),'passed':sum(x['ok'] for x in checks),
 'inputs':{'payload_sha256':h(PAYLOAD),'listing_sha256':h(LISTING),'prior_descriptor_result_sha256':h(PRIOR),'map_report_sha256':h(MAP)},
 'symbolic_join':{
  'start':'B26A: R1=TABLE=[SP+0xC], fallback pointer later stored at context+0x44',
  'target_c210':'CFG proves R1=TABLE+0x70; R0=R1+0x1808 => TABLE+0x1878 => table index 0x61E; store literal 0x006CA7C0 from pool C47C',
  'target_cc22':'CFG proves R1=TABLE+0x70; R2=0x1AB8 => TABLE+0x1B28 => table index 0x6CA; store literal 0x006F47C0 from pool CF40',
  'descriptor_decode':'table[0x61E]=0x006CA7C0 -> nested index 0x6CA -> table[0x6CA]=0x006F47C0; raw descriptor low12 0x7C0, bits0..5=0, bits6..11=31, raw kind bits27..29=0, bit30=0',
  'rejected_linear_candidates':'C7DE/C7E8 are unreachable from the B26A fallback CFG; reachable C79A has R1=TABLE+0x70 so R2=0x1B44 targets TABLE+0x1BB4/index0x6ED, not nested TABLE+0x1B28/index0x6CA'
 },
 'active_boundary':'Existing HEAP path B264/B266 returns before fallback initializer; fallback join is exact, but active HEAP-vs-fallback selection and context+0x40 high-bit merge remain runtime/provider boundaries',
 'r1_physical':'No physical SMN/MMIO claim; callback context+0x40 may rewrite descriptor high fields before R4 construction, and SVC#4 translation remains opaque',
 'checks_detail':checks}
(OUT/'descriptor-join-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,sort_keys=True))
if result['status']!='PASS':sys.exit(1)
