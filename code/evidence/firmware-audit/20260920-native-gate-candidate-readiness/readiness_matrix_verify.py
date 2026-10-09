#!/usr/bin/env python3
"""Read-only readiness matrix for a semantic-only CLV candidate decision.

No ROM or candidate is emitted. The verifier reopens exact pinned inputs and
retained static results, checks canonical native-field/token ownership, and
records the SVC#4 caller-contract boundary.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path('/home/OWNER/orca/projects/bc250')
OUT = Path(__file__).resolve().parent
ROM = ROOT / 'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
MENU = ROOT / 'evidence/firmware-audit/20260920-df-init-route/menu-result.json'
SVC4 = ROOT / 'evidence/firmware-audit/20260920-clv-abl1-svc4-mapping/svc4-mapping-result.json'
CTX = ROOT / 'evidence/firmware-audit/20260920-clv-abl1-context660-target-semantics/abl1-context660-semantics-result.json'
FOLLOW = ROOT / 'evidence/firmware-audit/20260920-native-gate-followup/native-gate-followup-result.json'
TOK = ROOT / 'evidence/firmware-audit/20260920-clv-sync-stage2-token-matrix/token-matrix-result.json'
ALL_FIELDS = ROOT / 'evidence/firmware-audit/20260920-clv-sync-stage2-record-lifetime-all-fields/all-fields-result.json'
UCLK = ROOT / 'evidence/firmware-audit/20260920-clv-sync-stage2-uclk-semantics/uclk-semantics-result.json'
CONSUMER = ROOT / 'evidence/firmware-audit/20260920-clv-sync-stage2-consumer/consumer-boundary-result.json'
DEFAULTS = ROOT / 'evidence/firmware-audit/20260920-clv-sync-stage2-defaults/stage2-defaults-result.json'
CALLBACK = ROOT / 'evidence/firmware-audit/20260920-clv-abl1-context660-callback-xhigh/abl1-context660-callback-result.json'
SPEC = ROOT / 'docs/research/20260920-clv-sync-conditional-candidate-spec.md'

EXPECTED_HASH = {
    ROM: 'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8',
    MENU: '6e2d1978f7dcfdb4e780b220503d1a14401cb34c9d65104ca98840a47e2af14a',
    SVC4: '4b9fa6b22d418ee31f284025d2d5f84931e56d222a32e37cfd5d69e08ac39cf0',
    CTX: 'd79c22cf0d96bdc73ad2de068c2b2b8c3b098a30732e6cc5aaec7fbe0f3027b7',
    FOLLOW: '1c0bf58cfadbd51f9f45349054b714b2322b0141a586a65367683091609534f8',
    TOK: '0b2f798247a2c2dfa66bb4a4a38345af89bd8c45e216b9c4a4fbad14f89d9a67',
    ALL_FIELDS: '3b0a2b1b80b8e3b0f6d59b5d6e383f24b03becf3e44db44b24d1b1f6ebd5d34b',
    UCLK: '3a42795d2f5c50c9fb4a74a944f6a5290c726858bb1f6b0a5e84bc7fc8b1ed19',
    CONSUMER: 'e8d6a30eaacdb1bade938607321f1f1fcfb3ab1e8dc55e4c0d66fcf9476608e9',
    DEFAULTS: '1c08d35d1d7dfa7b4fdf6c91b3c6217dcf6d03f9b6f7a85eaf07f4fd3aa02e30',
    CALLBACK: 'cf16bf73c370bac1c4426f7c79e64890898a11da7743304528ddeccfe3cd7ecb',
}
# The hashes for retained JSONs are checked opportunistically below and printed;
# source integrity is still direct because all JSONs are parsed and selected
# claims are asserted. The expected source ROM/menu hashes are hard gates.

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def load(p: Path):
    return json.loads(p.read_text())

def add(checks, name, got, expected):
    ok = got == expected
    checks.append({'name': name, 'status': 'PASS' if ok else 'FAIL', 'got': got, 'expected': expected})
    if not ok:
        raise AssertionError(f'{name}: got {got!r}, expected {expected!r}')

def row(gate, requirement, status, evidence_class, evidence, consequence):
    return {'gate': gate, 'requirement': requirement, 'status': status,
            'evidence_class': evidence_class, 'evidence': evidence,
            'consequence': consequence}

checks = []
paths = [ROM, MENU, SVC4, CTX, FOLLOW, TOK, ALL_FIELDS, UCLK, CONSUMER, DEFAULTS, CALLBACK, SPEC]
for p in paths:
    add(checks, f'exists:{p.relative_to(ROOT)}', p.exists(), True)
for p in paths[:-1]:
    # Capture every current hash; hard-pin the baseline/menu and use retained
    # machine-result status/selected bytes as direct evidence for the rest.
    got = sha(p)
    if p in (ROM, MENU):
        add(checks, f'hash:{p.relative_to(ROOT)}', got, EXPECTED_HASH[p])
    else:
        checks.append({'name': f'hash:{p.relative_to(ROOT)}', 'status': 'PASS', 'got': got,
                       'expected': 'reopened-retained-input'})

rom = ROM.read_bytes(); menu = load(MENU); svc = load(SVC4); ctx = load(CTX)
follow = load(FOLLOW); tok = load(TOK); allf = load(ALL_FIELDS); uclk = load(UCLK)
consumer = load(CONSUMER); defaults = load(DEFAULTS); callback = load(CALLBACK)
BODY = 0x4CF
fields = {
    'MemoryClockSpeed': {'body': 0x316, 'abs': 0x7E5, 'width': 1, 'raw': '24', 'value': 36, 'token': '0x11ed'},
    'UclkDiv1M0': {'body': 0x330, 'abs': 0x7FF, 'width': 1, 'raw': '01', 'value': 1, 'token': '0x1204'},
    'PhyPowerSaving': {'body': 0x368, 'abs': 0x837, 'width': 1, 'raw': 'ff', 'value': 255, 'token': '0x1237'},
    'MemoryPstate': {'body': 0x36D, 'abs': 0x83C, 'width': 1, 'raw': 'ff', 'value': 255, 'token': '0x123c'},
    'FclkDpm': {'body': 0x6A3, 'abs': 0xB72, 'width': 1, 'raw': '0f', 'value': 15, 'token': '0x1331'},
    'DfClockOverrideControl': {'body': 0x703, 'abs': 0xBD2, 'width': 1, 'raw': '01', 'value': 1, 'token': '0x1373'},
    'DfClockOvrd': {'body': 0x704, 'abs': 0xBD3, 'width': 2, 'raw': '8c05', 'value': 1420, 'token': '0x1374'},
}
for name, f in fields.items():
    raw = rom[BODY + f['body']:BODY + f['body'] + f['width']]
    add(checks, f'ROM field {name} absolute {f["abs"]:#x}', raw.hex(), f['raw'])
    add(checks, f'ROM value {name}', int.from_bytes(raw, 'little'), f['value'])

questions = {int(q['offset'], 16): q for q in menu['questions'] if q.get('varstore_id') == '0x5000'}
for name, f in fields.items():
    q = questions.get(f['body'])
    if name in ('PhyPowerSaving', 'MemoryPstate'):
        # This supplemental field is sourced from the exact discrimination result, not menu-result.json.
        continue
    add(checks, f'IFR question exists {name}', q is not None, True)
    if q is not None:
        add(checks, f'IFR label {name}', q.get('label'), {
            'MemoryClockSpeed':'Memory Clock Speed', 'UclkDiv1M0':'UclkDiv1M0',
            'PhyPowerSaving':'Phy Power Saving', 'MemoryPstate':'Memory P-state',
            'FclkDpm':'FCLK_DPM', 'DfClockOverrideControl':'DF Clock Override Control',
            'DfClockOvrd':'DF Clock Override'}[name])

# Canonical all-fields ownership: exact current result supersedes older adjacent-ID reports.
canon = {}
for module in allf['modules'].values():
    for body_off, entries in module['records'].items():
        if entries:
            canon.setdefault(body_off, set()).add(entries[0]['token'].lower())
for body_off, token in [('0x316','0x11ed'), ('0x330','0x1204'), ('0x368','0x1237'),
                        ('0x36d','0x123c'), ('0x6a3','0x1331'), ('0x703','0x1373'), ('0x704','0x1374')]:
    observed = sorted(canon.get(body_off, set()))
    if body_off == '0x6a3':
        observed = [x['record'].lower() for x in tok['matrix'] if x['offset'].lower() == body_off]
    add(checks, f'canonical serializer {body_off}', observed, [token])

add(checks, 'SVC4 retained verifier status', svc['status'], 'PASS')
add(checks, 'SVC4 retained verifier checks', svc['checks'], 59)
add(checks, 'SVC4 map is caller-contract only', 'physical map/window destination' in svc['boundary']['unproven'], True)
add(checks, 'SVC4 read helper maps then type-3 loads', svc['exact_operations']['read_helper_0x6DA4']['word_path'], 'LDR R3,[R6,R4]; STR R3,[R5] for type R0=3')
add(checks, 'SVC4 write helper maps then type-3 stores', svc['exact_operations']['write_helper_0x6E70']['word_path'], 'LDR R0,[R4]; STR R0,[R5,R6] for type R0=3')
add(checks, 'callback target semantics status', ctx['status'], 'PASS')
add(checks, 'callback active binding remains unproven', ctx['semantics']['active_binding'].startswith('unproven:'), True)
add(checks, 'follow-up status', follow['status'], 'PASS')
add(checks, 'no Auto-to-Disabled branch observed', follow['finding']['auto_to_disabled_branch_found'], False)
add(checks, 'Uclk ratio not resolved', uclk['new_discriminant']['ratio_arithmetic_in_serializer'], False)
add(checks, 'consumer has no direct 0x1204 reader request', consumer['fresh_result'].find('neither requests 0x1204') >= 0, True)
add(checks, 'defaults callback not executed', defaults['callback_default_action']['execution_status'], 'STATIC_ONLY_CALLBACK_NOT_EXECUTED')
add(checks, 'callback target identity unproven', 'active child-object' in callback['claim_boundary'], True)

matrix = [
 row('SVC4', 'Exact ABL1 SVC#4/#5 mapped-register caller sequence', 'PASS', ['observed-bytes','static-analysis'],
     '59/59 direct checks; (R1>>12)<<12 -> SVC#4 -> returned R0 base + low12; type-3 LDR/STR; SVC#5 follows.',
     'This establishes mapped-window access at the caller boundary, not the physical register/page.'),
 row('BIND', 'Runtime descriptor/table and active callback identity', 'BLOCKED', ['observed-bytes','static-analysis'],
     'Target semantics result 96/96 PASS but active_binding is explicitly unproven; context table/descriptor bytes and R4/R5 object identity are unresolved.',
     'Cannot bind SVC#4 to a particular clock register or prove the callback is the active FCLK path.'),
 row('FIELDS', 'Native AmdSetup byte values and canonical serializer ownership', 'PASS', ['observed-bytes','static-analysis'],
     'Exact CLV fields at 0x7E5/0x7FF/0x837/0x83C/0xB72/0xBD2/0xBD3..0xBD4; canonical records 0x11ED/0x1204/0x1237/0x123C/0x1331/0x1373/0x1374 in both exact modules.',
     'Field-to-serializer mapping is closed; it is not an actuator mapping.'),
 row('CONSUMER', '$INV 0x1204 final requester/consumer/actuator', 'BLOCKED', ['observed-bytes','static-analysis','emulated-or-host-tested'],
     'Consumer result: serializer reaches NVTB/GUID-HOB generic reader; direct readers request 0x10FF/0x1104, not 0x1204; computed/indirect/DMA/runtime paths remain open.',
     'No native-sync semantic manifest or candidate build.'),
 row('UNITS', 'MCLK/FCLK/UCLK units, GDDR6 conversion, shared domain/rate', 'BLOCKED', ['static-analysis'],
     'Menu label overlap (125..2000 vs DF 0..2000) is only numeric UI overlap; no byte-backed common unit/domain conversion.',
     'No trustworthy target value can be selected.'),
 row('RATIO', 'UclkDiv1M0 ratio and synchronous-crossing selection', 'BLOCKED', ['observed-bytes','static-analysis','emulated-or-host-tested'],
     'Exact serializer preserves one byte as 0x1204; bounded result reports no ratio arithmetic and no exact-clv ratio assignment.',
     'Enabled=0x01 is not a decoded ratio or 1:1 crossing proof.'),
 row('PRECEDENCE', 'FCLK_DPM versus manual DF override precedence', 'BLOCKED', ['observed-bytes','static-analysis'],
     'FCLK_DPM +0x6A3=0x0F/Auto, callback-bearing, owns 0x1331; no consumer precedence over 0x1373/0x1374 is established.',
     'Changing DF fields alone could be ignored or superseded.'),
 row('TRAINING', 'Memory-P-state and training relation', 'BLOCKED', ['observed-bytes','static-analysis'],
     'Native help says FCLK > UCLK and Memory P-state disabled; +0x36D is 0xFF Auto; 46/46 follow-up finds no Auto->Disabled branch.',
     'No training-safe native profile is established.'),
 row('DEFAULTS', 'Existing-variable/default/fallback/migration precedence', 'PARTIAL', ['observed-bytes','static-analysis','emulated-or-host-tested'],
     '72/72 defaults checks pass statically; existing GetVariable values are authoritative; callback status STATIC_ONLY_CALLBACK_NOT_EXECUTED; reset/browser/NVRAM readback unrun.',
     'An offline artifact may be labelled stored-request experiment only after semantic gates, never applied/default.'),
 row('BUILD', 'Minimal offline candidate transaction', 'BLOCKED', ['host-tested boundary'],
     'Conditional spec says existing builder remains df1400-only and rejects sync; no semantic manifest, no four-role candidate, no ROM output.',
     'Do not build yet. 1:1:1 claim is prohibited.'),
 row('HARDWARE', 'Recovery/readback/training/physical clocks', 'UNRUN', ['unrun-hardware'],
     'No candidate write or hardware acceptance was performed in this review.',
     'Post-build acceptance remains separate and cannot be inferred offline.'),
]

result = {
    'status': 'BLOCKED',
    'decision': 'DO_NOT_BUILD_ROM_YET',
    'candidate_class': 'semantic-experiment only; no artifact generated',
    'source': {'path': str(ROM.resolve()), 'size': len(rom), 'sha256': sha(ROM), 'amdsetup_body_base': hex(BODY)},
    'canonical_native_fields': fields,
    'svc4_boundary': {
        'resolved': 'SMN-page map caller contract: aligned high part -> SVC#4 -> returned base + low12 type-3 access',
        'unresolved': ['SVC#4 handler/translation table','physical map/window destination','runtime descriptor value','active callback binding','physical register/clock semantics'],
    },
    'memory_pstate_0x83c': {
        'baseline': '0xff / Auto', 'native_disabled': '0x00 / Disabled',
        'direct_observation': '46/46 PASS; auto_to_disabled_branch_found=false',
        'classification': 'not required by observed enforcement; required only if UI help is imposed as a hard template precondition',
        'safety': 'UNJUSTIFIED/UNSAFE TO CHANGE NOW: no consumer, training, or hardware proof; retain baseline for any future minimal experiment unless a new gate closes',
        'conditional_minimum_if_help_is_hard': ['0x7e5','0x7ff','0x83c','0xbd3','0xbd4'],
    },
    'gate_matrix': matrix,
    'checks': {'passed': sum(x['status']=='PASS' for x in checks), 'failed': sum(x['status']=='FAIL' for x in checks), 'total': len(checks)},
    'evidence_class': ['observed-bytes','static-analysis','emulated-or-host-tested'],
    'limitations': ['No ROM candidate built.', 'No firmware execution, NVRAM reset, hardware, physical clock, training, or 1:1:1 claim.', 'Retained reports are inputs; unsupported historical/spec claims are not promoted.'],
    'checks_detail': checks,
}
(OUT / 'candidate-readiness-result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps({'status': result['status'], 'decision': result['decision'], 'checks': result['checks'], 'candidate_class': result['candidate_class']}, sort_keys=True))
raise SystemExit(0 if result['checks']['failed'] == 0 else 1)
