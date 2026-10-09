#!/usr/bin/env python3
import hashlib, json, re, sys
from pathlib import Path

ROOT = Path('/home/OWNER/orca/projects/bc250')
PAYLOAD = ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
LISTING = ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt'
SOURCE = ROOT/'import/from-windows/Users/kukuruza/tmp_bc250/recon/lorek123_psp/ABL1_decompiled.c'
OUT = Path(__file__).resolve().parent
checks=[]

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for x in iter(lambda:f.read(1<<20), b''): h.update(x)
    return h.hexdigest()

def check(name, ok, detail):
    checks.append({'name':name,'ok':bool(ok),'detail':detail})
    if not ok: print(f'FAIL {name}: {detail}', file=sys.stderr)

b=PAYLOAD.read_bytes(); listing=LISTING.read_text(); source=SOURCE.read_text()
check('payload_hash', sha(PAYLOAD)=='af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a', sha(PAYLOAD))
check('listing_hash', sha(LISTING)=='b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65', sha(LISTING))
check('source_hash', sha(SOURCE)=='9501f2ed3abd96ac54cc317c26ae64d068f94a1a0d572d3c886c7877e4bb8f1b', sha(SOURCE))

def raw(off, hx, name):
    got=b[off:off+len(bytes.fromhex(hx))].hex()
    check(name, got==hx, f'offset=0x{off:X} expected={hx} got={got}')

def has(addr, needle, name):
    # Address-form line and operation text must both remain present in the exact listing.
    pat = rf'^\s*{addr:x}:.*{re.escape(needle)}'
    ok = re.search(pat, listing, re.M) is not None
    check(name, ok, f'listing address 0x{addr:X} operation {needle!r}')

# FCLK context branch: exact dispatcher input and convergent call.
raw(0x1081e, '204600f09af8012240f20521204600f094f8002240f2f711204600f08ef818', 'fclk_dispatch_first_call_bytes')
has(0x1081e, 'mov\tr0, r4', 'fclk_dispatch_R0_context')
has(0x10820, 'bl\t0x10958', 'fclk_dispatch_call_10958')
# Dispatcher receives incoming R1=0x61E and selected value in R2; it presents R2=0x61E, R3=value, R1=1.
raw(0x10958, '30b4d0f8604613460a46a44630bc01216047', 'dispatcher_exact_bytes')
has(0x1095a, 'ldr.w\tr4, [r0, #0x660]', 'dispatcher_loads_callback_slot')
has(0x1095e, 'mov\tr3, r2', 'dispatcher_value_to_R3')
has(0x10960, 'mov\tr2, r1', 'dispatcher_token_to_R2')
has(0x10966, 'movs\tr1, #0x1', 'dispatcher_sets_R1_1')
has(0x10968, 'bx\tr12', 'dispatcher_indirect_callback')
# Candidate callback table selection: low 12 bits of incoming R2 = 0x61E; table pointer + index*4.
raw(0x9ae8, 'c2f30b00b0f51b6f0f9002d3df48fcf7e7fc95f8200318b10020cde9080004e000210220cde9080101200021cde90601686c0f9950f82160002e7dd040f25262', 'callback_index_and_table_prefix')
has(0x9ae8, 'ubfx\tr0, r2, #0x0, #0xc', 'callback_R2_low12_index')
has(0x9b18, 'ldr\tr0, [r5, #0x44]', 'callback_table_pointer')
has(0x9b1c, 'ldr.w\tr6, [r0, r1, lsl #2]', 'callback_table_slot_R6')
has(0x9b24, 'movw\tr2, #0x652', 'callback_table_limit')
has(0x9b2c, 'ubfx\tr1, r6, #0xc, #0xc', 'descriptor_nested_index')
has(0x9b54, 'ldr.w\tr6, [r0, r1, lsl #2]', 'nested_descriptor_load')
# The FCLK token is 0x61E; exact construction is a field target, not an asserted numeric runtime value.
check('fclk_token_constant', '40f21e61' in b[0x107e0:0x107f0].hex(), 'raw search for movw r1,#0x61E in FCLK context slice')
check('fclk_descriptor_target', True, 'R1 target is table[0x61E], then table[(table[0x61E]>>12)&0xFFF]; runtime slot value is not in the bounded static bytes')
# Normal mapped-read path: R4 is assembled from descriptor/context bits and passed as R1 to 0x6DA4.
raw(0x9c22, '2b68032005aa2146fdf7bbf8', 'mapped_read_callsite_bytes')
has(0x9c22, 'ldr\tr3, [r5]', 'mapped_read_root_load')
has(0x9c24, 'movs\tr0, #0x3', 'mapped_read_width_word')
has(0x9c28, 'mov\tr1, r4', 'mapped_read_R1_R4')
has(0x9c2a, 'bl\t0x6da4', 'mapped_read_helper_call')
# Write path: same constructed R4 reaches SVC#4 wrapper 0x6E70 as R1.
raw(0x9d8a, '002000902b68032005aa2146fdf76bf858e095f8', 'mapped_write_callsite_bytes')
has(0x9d90, 'movs\tr0, #0x3', 'mapped_write_width_word')
has(0x9d94, 'mov\tr1, r4', 'mapped_write_R1_R4')
has(0x9d96, 'bl\t0x6e70', 'mapped_write_helper_call')
# Exact R4 construction: selector bits 27..29 and the four branch formulas are raw-byte backed.
raw(0x9c00, 'c6f3c2600090012823d002283ed0032854d004285bd0', 'read_descriptor_kind_dispatch')
has(0x9c00, 'ubfx\tr0, r6, #0x1b, #0x3', 'descriptor_kind_bits')
has(0x9c56, 'orr\tr0, r4, #0x50000', 'read_kind1_base')
has(0x9c8c, 'ldrb.w\tr1, [r5, #0x49]', 'read_kind2_context_byte')
has(0x9cc0, 'orr\tr0, r4, #0x53000', 'read_kind3_base')
has(0x9cce, 'orr\tr4, r4, #0x1c000', 'read_kind4_base')
has(0x9c78, 'ldr.w\tr1, [r5, #0x2b0]', 'read_kind1_optional_offset')
has(0x9cae, 'ldr.w\tr0, [r5, #0x2b0]', 'read_kind2_optional_offset')
raw(0x9d70, 'c260012812d002282bd0032842d0042848d06048', 'write_descriptor_kind_dispatch')
has(0x9d9c, 'ldrb.w\tr1, [r5, #0x49]', 'write_kind1_context_byte')
has(0x9dd2, 'ldrb.w\tr1, [r5, #0x49]', 'write_kind2_context_byte')
has(0x9e04, 'ldrb.w\tr1, [r5, #0x49]', 'write_kind3_context_byte')
has(0x9e14, 'orr\tr4, r4, #0x1c000', 'write_kind4_base')
# SVC wrappers: caller's high/low split and returned R0 -> mapped base are exact.
has(0x6dcc, 'lsrs\tr0, r6, #0xc', 'read_wrapper_high_split')
has(0x6dce, 'ubfx\tr4, r6, #0x0, #0xc', 'read_wrapper_low12_split')
has(0x6dd2, 'lsls\tr0, r0, #0xc', 'read_wrapper_page_align')
has(0x6dd4, 'svc\t#0x4', 'read_wrapper_svc4')
has(0x6dd8, 'mov\tr6, r0', 'read_wrapper_returned_base')
has(0x6e1a, 'ldr\tr3, [r6, r4]', 'read_wrapper_mapped_access')
has(0x6dfc, 'svc\t#0x5', 'read_wrapper_svc5')
has(0x6ea6, 'lsrs\tr0, r5, #0xc', 'write_wrapper_high_split')
has(0x6ea8, 'ubfx\tr6, r5, #0x0, #0xc', 'write_wrapper_low12_split')
has(0x6eac, 'lsls\tr0, r0, #0xc', 'write_wrapper_page_align')
has(0x6eae, 'svc\t#0x4', 'write_wrapper_svc4')
has(0x6eb2, 'mov\tr5, r0', 'write_wrapper_returned_base')
has(0x6ee8, 'str\tr0, [r5, r6]', 'write_wrapper_mapped_access')
has(0x6ed6, 'svc\t#0x5', 'write_wrapper_svc5')
# Historical source is only a structural cross-check: it contains the same table[0x11] and SVC wrappers, but no source-to-binary identity claim.
check('source_structural_table', 'param_1[0x11] + local_2c * 4' in source and 'software_interrupt(4)' in source and 'software_interrupt(5)' in source, 'historical table/SVC structural cross-check')
# Build machine result.
status='PASS' if all(c['ok'] for c in checks) else 'FAIL'
result={
 'status':status,
 'checks':len(checks),
 'passed':sum(c['ok'] for c in checks),
 'inputs':{'payload':str(PAYLOAD),'payload_sha256':sha(PAYLOAD),'listing':str(LISTING),'listing_sha256':sha(LISTING),'source':str(SOURCE),'source_sha256':sha(SOURCE)},
 'fclk_dispatch':{'context_field':'context+0x78','dispatcher':'0x10958','incoming_token':'0x61E','callback_arg_R2':'0x61E','callback_arg_R3':'branch-selected value','callback_arg_R1':'1'},
 'r1_target':{'first_slot':'*( *(uint32_t**)(context+0x44) + 0x61E )','nested_slot':'*( *(uint32_t**)(context+0x44) + ((first_slot >> 12) & 0xFFF) )','descriptor_bits':'start=bits0..5,end=bits6..11,nested=bits12..23,wide=bit30','constructed_R1':'R4 built from descriptor low bits plus context+0x49 and optional context+0x2B0 according to kind bits27..29','read_call':'R1=R4 at 0x9C28; BL 0x6DA4 at 0x9C2A','write_call':'R1=R4 at 0x9D94; BL 0x6E70 at 0x9D96','numeric_value':'not recovered: exact table slot contents/runtime context are unavailable in this bounded static slice'},
 'hardware_boundary':'SVC#4 handler/translation, runtime table contents, loader base, physical SMN/MMIO destination, clock/PLL effect, and hardware execution remain unknown/unrun.',
 'checks_detail':checks,
}
(OUT/'svc4-r1-target-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,sort_keys=True))
if status!='PASS': sys.exit(1)
