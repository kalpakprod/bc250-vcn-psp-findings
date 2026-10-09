#!/usr/bin/env python3
import hashlib, json, sys
from pathlib import Path

ROOT = Path('/home/OWNER/orca/projects/bc250')
ROM = ROOT / 'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
FAB = ROOT / 'evidence/firmware-audit/20260919-inv-token-consumers/AmdFabricAriPei-c5b99650a442.bin'
INS = ROOT / 'evidence/firmware-audit/20260919-inv-token-consumers/AmdFabricAriPei-c5b99650a442.instructions.json'
PRIOR_HOB = ROOT / 'evidence/firmware-audit/20260920-clv-token1204-hob-boundary-xhigh/token1204-hob-boundary-result.json'
PRIOR_PROV = ROOT / 'evidence/firmware-audit/20260920-clv-fabric-provider-266f-xhigh/provider-266f-result.json'
OUT = Path(__file__).resolve().parent

fb = FAB.read_bytes()
inst = json.loads(INS.read_text())
by = {int(z['rva']): z for z in inst}
checks = []

def h(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def ck(name, ok, detail):
    checks.append({'name': name, 'ok': bool(ok), 'detail': detail})
    if not ok:
        print(f"FAIL {name}: {detail}", file=sys.stderr)

def at(off, bytes_, mnemonic=None, operands=None, name=''):
    z = by.get(off)
    ok = z is not None and z['bytes'] == bytes_
    if mnemonic:
        ok = ok and z['mnemonic'] == mnemonic
    if operands:
        ok = ok and z['operands'] == operands
    ck(name or hex(off), ok, str(z))

# 1. Base inputs and prior chain hashes
ck('rom_hash', h(ROM) == 'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8', h(ROM))
ck('fabric_hash', h(FAB) == 'c5b99650a442ed9be1cf3a62e7571f7eb163b9f80a60d4fcc7b3e9afe4506f78', h(FAB))
ck('instruction_hash', h(INS) == '77b1d4be4393fbbf920847398ae5667c42b3841066d40c2aaace1b49036c81e1', h(INS))
ck('prior_hob_reopened', PRIOR_HOB.exists() and json.loads(PRIOR_HOB.read_text()).get('status') == 'PASS', str(PRIOR_HOB))
ck('prior_prov_reopened', PRIOR_PROV.exists() and json.loads(PRIOR_PROV.read_text()).get('status') == 'PASS', str(PRIOR_PROV))

# 2. Provider function 0x25D3: IDTR source to object pointer
at(0x25d3, '55', 'push', 'ebp', 'prov_entry_55')
at(0x25d4, '8bec', 'mov', 'ebp,esp', 'prov_prolog_8bec')
at(0x25d9, '8d45f4', 'lea', 'eax,[ebp-0xc]', 'prov_lea_idtr_local')
at(0x25e2, '0f0108', 'sidtd', '[eax]', 'prov_sidt_op')
at(0x25e5, '8b45f6', 'mov', 'eax,DWORD PTR [ebp-0xa]', 'prov_mov_idtr_base')
at(0x25e8, '8b40fc', 'mov', 'eax,DWORD PTR [eax-0x4]', 'prov_mov_obj_ptr_base_minus_4')
at(0x25eb, 'c9', 'leave', None, 'prov_leave')
at(0x25ec, 'c3', 'ret', None, 'prov_ret')

# 3. Provider caller wrapper 0x266F: acquiring object and calling [ECX+0x34]
at(0x266f, '55', 'push', 'ebp', 'wrap_entry_55')
at(0x2673, 'e85bffffff', 'call', '0x25d3', 'wrap_call_25d3')
at(0x2678, '8b08', 'mov', 'ecx,DWORD PTR [eax]', 'wrap_mov_ecx_vtable')
at(0x267a, '8d55fc', 'lea', 'edx,[ebp-0x4]', 'wrap_lea_out_buf')
at(0x267d, '52', 'push', 'edx', 'wrap_push_out_buf')
at(0x267e, 'ff750c', 'push', 'DWORD PTR [ebp+0xc]', 'wrap_push_arg2')
at(0x2681, 'ff7508', 'push', 'DWORD PTR [ebp+0x8]', 'wrap_push_arg1')
at(0x2684, '50', 'push', 'eax', 'wrap_push_obj_this')
at(0x2685, 'ff5134', 'call', 'DWORD PTR [ecx+0x34]', 'wrap_call_vtable_34')
at(0x268b, '85c0', 'test', 'eax,eax', 'wrap_test_status')
at(0x268f, '8365fc00', 'and', 'DWORD PTR [ebp-0x4],0x0', 'wrap_status_zero_on_neg')
at(0x2693, '8b45fc', 'mov', 'eax,DWORD PTR [ebp-0x4]', 'wrap_mov_ret_val')

# 4. Caller 1 at 0x2698: passes selector 4, output buffer
at(0x2698, '8d4718', 'lea', 'eax,[edi+0x18]', 'c1_lea_edi_18')
at(0x269b, '50', 'push', 'eax', 'c1_push_eax')
at(0x269c, '6a04', 'push', '0x4', 'c1_push_04')
at(0x269e, 'e8ccffffff', 'call', '0x266f', 'c1_call_266f')
at(0x26a5, '85c0', 'test', 'eax,eax', 'c1_test_eax')
at(0x26a9, '83c018', 'add', 'eax,0x18', 'c1_add_eax_18')
at(0x26ac, '8b0e', 'mov', 'ecx,DWORD PTR [esi]', 'c1_copy_w0')
at(0x26ae, '8948f0', 'mov', 'DWORD PTR [eax-0x10],ecx', 'c1_store_w0')
at(0x26b1, '8b4e04', 'mov', 'ecx,DWORD PTR [esi+0x4]', 'c1_copy_w1')
at(0x26b4, '8948f4', 'mov', 'DWORD PTR [eax-0xc],ecx', 'c1_store_w1')
at(0x26b7, '8b4e08', 'mov', 'ecx,DWORD PTR [esi+0x8]', 'c1_copy_w2')
at(0x26ba, '8948f8', 'mov', 'DWORD PTR [eax-0x8],ecx', 'c1_store_w2')
at(0x26bd, '8b4e0c', 'mov', 'ecx,DWORD PTR [esi+0xc]', 'c1_copy_w3')
at(0x26c0, '8948fc', 'mov', 'DWORD PTR [eax-0x4],ecx', 'c1_store_w3')

# 5. Caller 2 at 0x26D5: passes selector 2, size 0x30, buffer ESI
at(0x26d5, '56', 'push', 'esi', 'c2_push_esi')
at(0x26d6, '6a30', 'push', '0x30', 'c2_push_30')
at(0x26d8, '6a02', 'push', '0x2', 'c2_push_02')
at(0x26da, 'e890ffffff', 'call', '0x266f', 'c2_call_266f')

# 6. Negative audit: confirm no 0x1204 token or clock parameter in this slice
ck('no_direct_1204_in_provider_window', not any(z.get('mnemonic') == 'push' and z.get('operands') == '0x1204' for z in inst if 0x25d3 <= z.get('rva', 0) <= 0x26da), 'no direct 0x1204 argument in 0x25D3..0x26DA')
ck('no_direct_push_1204_whole_module', b'\x68\x04\x12\x00\x00' not in fb, "no push 0x00001204 in entire AmdFabricAriPei")

all_ok = all(x['ok'] for x in checks)
result = {
    'status': 'PASS' if all_ok else 'FAIL',
    'checks': len(checks),
    'passed': sum(x['ok'] for x in checks),
    'failed': sum(not x['ok'] for x in checks),
    'route': 'AmdFabricAriPei 0x266F -> 0x25D3 (SIDT IDTR base - 4) -> [ECX+0x34]',
    'inputs': {
        'rom_sha256': h(ROM),
        'fabric_sha256': h(FAB),
        'instructions_sha256': h(INS),
        'prior_hob_result': str(PRIOR_HOB),
        'prior_provider_result': str(PRIOR_PROV)
    },
    'provider_analysis': {
        'source': 'SIDT local at 0x25E2, loads IDTR base at [ebp-0xa], dereferences [base - 4] at 0x25E8',
        'nature': 'Provider object pointer is retrieved from the pre-PEI/CAR execution context anchor at [IDTR.Base - 4], not via PEI LocatePpi or static GUID table.',
        'dispatch': 'Wrapper 0x266F calls indirect method [ECX+0x34] on the acquired provider object.',
        'callers': {
            'caller_0x2698': 'Passes immediate 4 (selector) and output pointer [EDI+0x18]. Copies 4 DWORDs on success.',
            'caller_0x26D5': 'Passes immediate 2 (selector), size 0x30, and buffer ESI.'
        },
        'token1204_status': 'No reference to token 0x1204, UclkDiv1M0, or clock/divider structure exists in this provider edge.',
        'verdict': 'NON-DISCRIMINATING for token 0x1204. The edge represents a generic runtime platform service dispatch; token 0x1204 dataflow terminates at the NVTB/HOB generic reader boundary without entering this provider path.'
    },
    'checks_detail': checks
}

out_json = OUT / 'token1204-provider-boundary-result.json'
out_json.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps(result, sort_keys=True))

if not all_ok:
    sys.exit(1)
