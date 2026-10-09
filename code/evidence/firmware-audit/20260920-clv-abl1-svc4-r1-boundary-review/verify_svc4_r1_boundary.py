#!/usr/bin/env python3
"""Independent raw-byte boundary review for exact CLV ABL1 SVC#4 R1 path."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT = Path('/home/OWNER/orca/projects/bc250')
ABL = ROOT / 'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
REPORT = ROOT / 'docs/research/20260920-clv-abl1-svc4-r1-target-xhigh.md'
RESULT = ROOT / 'evidence/firmware-audit/20260920-clv-abl1-svc4-r1-target-xhigh/svc4-r1-target-result.json'
CALLBACK_REVIEW = ROOT / 'evidence/firmware-audit/20260920-clv-abl1-context660-callback-xhigh/abl1-context660-callback-result.json'
OWN = Path(__file__).resolve().parent
EXPECTED_ABL = 'af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a'

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

b = ABL.read_bytes()
checks = []
def ck(name, observed, expected):
    ok = observed == expected
    checks.append({'name': name, 'ok': ok, 'observed': observed, 'expected': expected})
    return ok

def hx(off, n):
    return b[off:off+n].hex()

# This is independent byte extraction, not an invocation/import of the prior verifier.
ck('exact_abl_hash', sha(ABL), EXPECTED_ABL)
ck('prior_r1_report_hash', sha(REPORT), 'd32ba56c94ef3e35d89fc1e5e02765d8cc4607b0623f9ba621b5e1af082c0446')
ck('prior_r1_result_hash', sha(RESULT), '05fa26427c0d969a11d3779714089943d01421780beebbe8b62b910661eeecca')
# FCLK branch token and indirect dispatch arguments.
ck('fclk_movw_r1_61e', hx(0x107e8, 4), '40f21e61')
ck('fclk_context_passed_r0_before_indirect_dispatch', hx(0x1081e, 2), '2046')
ck('fclk_calls_dispatcher_10958', hx(0x10820, 4), '00f09af8')
ck('dispatcher_loads_callback_from_context_plus_660', hx(0x1095a, 4), 'd0f86046')
ck('dispatcher_moves_selected_value_r2_to_callback_r3', hx(0x1095e, 2), '1346')
ck('dispatcher_moves_token_r1_to_callback_r2', hx(0x10960, 2), '0a46')
ck('dispatcher_normalizes_callback_r1_to_1', hx(0x10966, 2), '0121')
ck('dispatcher_indirect_branch', hx(0x10968, 2), '6047')
# Candidate callback raw path: it dereferences a context-supplied table pointer.
ck('candidate_sets_r5_from_r0_context', hx(0x9ade, 2), '0546')
ck('candidate_copies_selected_value_r3_to_r11', hx(0x9ae2, 2), '9b46')
ck('candidate_extracts_low_12_token_bits', hx(0x9ae8, 4), 'c2f30b00')
ck('candidate_loads_table_base_from_context_plus_44', hx(0x9b18, 2), '686c')
ck('candidate_outer_slot_indexed_load', hx(0x9b1c, 4), '50f82160')
ck('candidate_nested_slot_indexed_load', hx(0x9b54, 4), '50f82160')
# Exact helper target construction: R4 is passed as actual SVC-wrapper input R1.
ck('helper_read_passes_r4_as_r1', hx(0x9c28, 2), '2146')
ck('helper_read_calls_6da4', hx(0x9c2a, 4), 'fdf7bbf8')
ck('helper_write_passes_r4_as_r1', hx(0x9d94, 2), '2146')
ck('helper_write_calls_6e70', hx(0x9d96, 4), 'fdf76bf8')
# Confirm the earlier parent initializer object and later callback context are distinct inputs.
ck('object_constructor_r5_from_argument', hx(0x737c, 2), '0546')
ck('object_constructor_r4_from_r6_plus_3c4', hx(0x73ae, 4), 'd6f8c443')
ck('object_constructor_stores_r4_child_into_r5_plus_8', hx(0x73b2, 2), 'ac60')
ck('initializer_passes_parent_r5_as_r0', hx(0x74de, 2), '2846')
ck('initializer_calls_af90', hx(0x74e0, 4), '03f056fd')
ck('later_indirect_call_uses_parent_r5_as_r0', hx(0x74e8, 2), '2846')
ck('later_indirect_call_via_r1', hx(0x74ea, 2), '8847')
ck('active_fclk_dispatch_uses_current_r4_as_r0', hx(0x1081e, 2), '2046')
# Conditional static initializer candidate: AF90 writes a constant callback pointer to +660.
ck('initializer_af90_sets_r4_from_r0', hx(0xaf94, 2), '0446')
ck('initializer_loads_static_literal_near_b168', hx(0xb0c2, 2), '2948')
ck('initializer_stores_literal_to_object_plus_660', hx(0xb0c4, 4), 'c4f86006')
ck('literal_at_b168', hx(0xb168, 4), 'd90b0600')
ck('mapped_callback_candidate_entry_bytes', hx(0x9ad8, 4), '2de9ff4f')
# Separate exact initializer routine B228 sets context+44 from a helper-returned pointer in either branch.
ck('table_initializer_r4_from_r0', hx(0xb22e, 2), '0446')
ck('table_initializer_existing_path_pointer_from_stack', hx(0xb264, 2), '0698')
ck('table_initializer_existing_path_store_context_plus_44', hx(0xb266, 2), '6064')
ck('table_initializer_fallback_path_pointer_from_stack', hx(0xb26a, 2), '0399')
ck('table_initializer_fallback_path_store_context_plus_44', hx(0xb274, 2), '6164')
ck('table_initializer_existing_helper_call_site', hx(0xb23a, 4), 'fbf79bf8')
ck('table_initializer_fallback_helper_call_site', hx(0xb252, 4), 'faf7f1ff')


# Exact descriptor arithmetic from the independent source report and raw bytes.
slot_offset = 0x61E * 4
slot_literal = int.from_bytes(b[0xC9F0:0xC9F4], 'little')
nested_index = (slot_literal >> 12) & 0xFFF
nested_offset = nested_index * 4
nested_descriptor = int.from_bytes(b[0xC9D8:0xC9DC], 'little')
ck('descriptor_slot_offset_61e', slot_offset, 0x1878)
ck('descriptor_slot_literal_raw', b[0xC9F0:0xC9F4].hex(), 'c0176d00')
ck('descriptor_slot_nested_index', nested_index, 0x6D1)
ck('descriptor_nested_offset', nested_offset, 0x1B44)
ck('descriptor_nested_literal_raw', b[0xC9D8:0xC9DC].hex(), '7c020008')
ck('descriptor_nested_kind', (nested_descriptor >> 27) & 0x7, 1)
ck('descriptor_nested_bit30', (nested_descriptor >> 30) & 1, 0)
ck('descriptor_nested_low12', nested_descriptor & 0xFFF, 0x27C)
ck('descriptor_nested_field_start', nested_descriptor & 0x3F, 0x3C)
ck('descriptor_nested_field_end', (nested_descriptor >> 6) & 0x3F, 9)
# Exact candidate kind-1 arithmetic, with dynamic context byte d=0 only as a conditional model.
kind1_d0 = (nested_descriptor & 0xFFF) | 0x50000 | ((0 >> 1) << 20) | ((0 & 1) << 13)
ck('conditional_kind1_d0_r4', kind1_d0, 0x5027C)

# Cross-check other-owned result claims without rewriting its artifacts.
owner = json.loads(CALLBACK_REVIEW.read_text())
ck('callback_owner_result_hash', sha(CALLBACK_REVIEW), 'cf16bf73c370bac1c4426f7c79e64890898a11da7743304528ddeccfe3cd7ecb')
identity = owner.get('ownership', {}).get('identity', '')
ck('callback_identity_in_existing_review_explicitly_unproven', 'not proven' in identity.lower(), True)
ck('callback_active_dispatch_not_claimed_by_owner_result', 'not asserted to be the callback actually invoked' in owner.get('claim_boundary',''), True)

result = {
    'status': 'PASS' if all(x['ok'] for x in checks) else 'FAIL',
    'checks': {'passed': sum(x['ok'] for x in checks), 'failed': sum(not x['ok'] for x in checks), 'total': len(checks)},
    'evidence_class': ['observed-bytes', 'independent fresh LLVM disassembly'],
    'inputs': {
        'abl_path': str(ABL), 'abl_sha256': sha(ABL),
        'target_report_path': str(REPORT), 'target_report_sha256': sha(REPORT),
        'target_result_path': str(RESULT), 'target_result_sha256': sha(RESULT),
        'callback_owner_result_path': str(CALLBACK_REVIEW), 'callback_owner_result_sha256': sha(CALLBACK_REVIEW),
    },
    'r1_boundary': {
        'fclk_dispatch_input_R1': '0x61E is the callback selector/token, not the SVC#4 address; dispatcher moves it to callback R2 and sets callback R1=1.',
        'candidate_callback_SVC_helper_R1': 'conditional on active binding: helper receives dynamic R4 via MOV R1,R4 at 0x9C28 / 0x9D94.',
        'candidate_R4_source': 'candidate callback selects table[0x61E], then table[(first_slot >> 12)&0xFFF], builds descriptor/context selector using descriptor kind and context bytes; numeric selector remains unknown.',
    },
    'callback_binding': {
        'active_path': 'FCLK caller passes its current R4 object to dispatcher 0x10958; dispatcher loads [current context+0x660] and branches indirectly.',
        'static_candidate': 'initializer 0xAF90 loads literal 0x00060BD9 at 0xB168 and stores it at [initializer parent+0x660]; under conditional base 0x57100 this maps to Thumb candidate 0x9AD8.',
        'binding_status': 'UNPROVEN: constructor passes parent R5 to initializer, stores a child pointer from [R6+0x3C4] in parent+0x08, then has unresolved BLX R1; later FCLK dispatch uses current R4. No byte-backed object identity connects that initialized parent+0x660 to current R4+0x660, or the B228 +0x44 owner to the active R4 object.',
    },
    'context_plus_44_table': {
        'observed': 'candidate code loads table base from context+0x44 at 0x9B18; exact ABL1 function 0xB228 initializes that field from either a lookup-result pointer or fallback allocation pointer. Caller-supplied table[0x61E] and nested descriptor bytes remain dynamic unless the exact fallback path is selected; this review does not decode table entries.',
        'static_pointer_status': 'An exact ABL1 initializer function at 0xB228 writes context+0x44 from helper-returned stack pointers on two paths: lookup-result [SP+0x18] -> STR [R4+0x44] at 0xB266, or fallback-result [SP+0x0C] -> STR [R4+0x44] at 0xB274. The base is not a static pointer literal; it is dynamically supplied by code in the module. The caller/active-context binding remains unproven.',
        'candidate_660_initializer': 'A separate static pointer literal exists for the +0x660 callback slot; it does not identify the active callback object or replace the +0x44 table pointer source.',
    },
    'report_correction': {
        'finding': 'Latest SVC4 R1 report overstates the active route by writing “callback 0x9AD8” without making its conditional binding explicit.',
        'corrected_statement': 'Exact bytes prove the FCLK branch calls dispatcher 0x10958 with token 0x61E and that a conditional initializer candidate points to a compatible 0x9AD8 routine. They do not prove that the live [context+0x660] points to 0x9AD8. Therefore the 0x9AD8 -> table+0x44 -> helper R1=R4 chain is conditional, not an established active FCLK SVC#4 path.',
        'R1_scope': 'At active FCLK caller, R1=0x61E is only the dispatch key. The eventual helper R1=R4 is exact only inside callback 0x9AD8; active path still has no numeric or function-bound helper R1.',
        'claim_scope': 'No SVC#4 physical target, SMN/MMIO register, clock effect, units, hardware execution, or MCLK=UCLK=FCLK claim follows.',
    },
    'checks_detail': checks,
}
(OWN/'boundary-review-result.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
print(json.dumps({'status': result['status'], 'checks': result['checks'], 'callback_binding': result['callback_binding']['binding_status'], 'table_pointer': result['context_plus_44_table']['static_pointer_status']}, sort_keys=True))
raise SystemExit(0 if result['status']=='PASS' else 1)
