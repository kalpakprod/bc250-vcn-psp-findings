#!/usr/bin/env python3
"""Pinned, read-only DF override -> token/FCLK-request boundary check."""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import re
import subprocess
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path('/home/OWNER/orca/projects/bc250')
OUT = ROOT / 'evidence/firmware-audit/20260921-df-consumer-next'
ROM = ROOT / 'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
CBS = ROOT / 'evidence/firmware-audit/20260919-inv-token-consumers/CbsBasePei-6ff112922ad8.bin'
SMU = ROOT / 'evidence/firmware-audit/20260919-inv-token-consumers/AmdNbioSmuV10Pei-905b8be68afd.bin'
FAB = ROOT / 'evidence/firmware-audit/20260919-inv-token-consumers/AmdFabricAriPei-c5b99650a442.bin'
ABL1 = ROOT / 'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
ABL1_OBJ = ROOT / 'evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o'
MENU = ROOT / 'evidence/firmware-audit/20260920-df-init-route/menu-result.json'
ROM_SHA = 'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
EXPECTED = {
    ROM: (ROM_SHA, 16777216),
    CBS: ('6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77', 81520),
    SMU: ('905b8be68afd1dce5453acef8273cbf94bdae6d41823c25438ace286348e2c80', 90672),
    FAB: ('c5b99650a442ed9be1cf3a62e7571f7eb163b9f80a60d4fcc7b3e9afe4506f78', 96680),
    ABL1: ('af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a', 0x171A0),
    ABL1_OBJ: ('54abef3a390abb0ff745685de2eed4e0e8db5e9ba27bba1a0f245573b47ff135', 95312),
}
checks: list[dict] = []
commands: list[dict] = []

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

def record(name: str, passed: bool, detail: str) -> None:
    checks.append({'name': name, 'status': 'PASS' if passed else 'FAIL', 'detail': detail})
    if not passed:
        raise AssertionError(f'{name}: {detail}')

def run(name: str, argv: list[str]) -> subprocess.CompletedProcess[str]:
    p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, check=False)
    (OUT / f'{name}.stdout').write_text(p.stdout, encoding='utf-8')
    (OUT / f'{name}.stderr').write_text(p.stderr, encoding='utf-8')
    (OUT / f'{name}.exit').write_text(f'{p.returncode}\n', encoding='ascii')
    commands.append({'name': name, 'argv': argv, 'exit_status': p.returncode,
                     'stdout_file': f'{name}.stdout', 'stderr_file': f'{name}.stderr'})
    record(name + '_exit_and_stderr', p.returncode == 0 and p.stderr == '',
           f'exit={p.returncode}; stderr_bytes={len(p.stderr.encode())}')
    return p

def gnu_instructions(text: str):
    rows = []
    for line in text.splitlines():
        m = re.match(r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2}\s+)+)(.*?)\s*$', line)
        if not m:
            continue
        rows.append((int(m.group(1), 16), bytes.fromhex(m.group(2)), m.group(3)))
    return rows

def llvm_thumb_bytes(token: str) -> bytes:
    # LLVM prints each Thumb halfword in target-endian display order.
    assert len(token) == 4, token
    return bytes.fromhex(token[2:] + token[:2])

def llvm_instructions(text: str):
    rows = []
    for line in text.splitlines():
        m = re.match(r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{4}\s+)+)(.*?)\s*$', line)
        if not m:
            continue
        raw = b''.join(llvm_thumb_bytes(t) for t in m.group(2).split())
        rows.append((int(m.group(1), 16), raw, m.group(3)))
    return rows

def check_disassembly_bytes(name: str, text: str, data: bytes, delta: int, thumb: bool = False) -> list[tuple[int, bytes, str]]:
    rows = llvm_instructions(text) if thumb else gnu_instructions(text)
    valid = bool(rows)
    for addr, raw, _asm in rows:
        off = addr if thumb else addr - delta
        if off < 0 or data[off:off + len(raw)] != raw:
            valid = False
            break
    record(name + '_every_decoded_instruction_matches_input', valid,
           f'{len(rows)} decoded instructions checked; mapping=' + ('payload-relative' if thumb else f'RVA-minus-TE-delta 0x{delta:x}'))
    return rows

try:
    OUT.mkdir(parents=True, exist_ok=True)
    input_rows = {}
    for path, (want_sha, want_size) in EXPECTED.items():
        got_size = path.stat().st_size
        got_sha = sha(path)
        ok = got_size == want_size and got_sha == want_sha
        input_rows[str(path)] = {'size': got_size, 'sha256': got_sha, 'expected_size': want_size, 'expected_sha256': want_sha}
        record('input_' + path.name, ok, f'size={got_size}; sha256={got_sha}')
    menu_hash = sha(MENU)
    menu = json.loads(MENU.read_text(encoding='utf-8'))
    record('menu_result_parses', isinstance(menu.get('questions'), list), f'menu JSON SHA-256={menu_hash}')

    rom = ROM.read_bytes()
    setup_base = 0x4CF
    mem = rom[setup_base + 0x316]
    control = rom[setup_base + 0x703]
    value_bytes = rom[setup_base + 0x704:setup_base + 0x706]
    value = int.from_bytes(value_bytes, 'little')
    record('original_memory_request_retained', mem == 0x24,
           f'ROM+0x{setup_base+0x316:x}=0x{mem:02x}; MemoryClockSpeed enum 0x24 (menu label 1800MHz)')
    record('original_df_request_bytes', control == 0x01 and value_bytes == bytes.fromhex('8c05'),
           f'ROM+0x{setup_base+0x703:x}=0x{control:02x}; +0x704 bytes={value_bytes.hex()} LE={value}')

    fields = {q.get('offset'): q for q in menu['questions']}
    q_control = fields['0x703']
    q_value = fields['0x704']
    exact_help = 'When you try to override FCLK, please make sure FCLK > UCLK and Memory P-state is disabled.'
    record('exact_hii_df_questions',
           q_control.get('qid') == '0x37d' and q_value.get('qid') == '0x37e'
           and q_control.get('label') == 'DF Clock Override Control'
           and q_value.get('label') == 'DF Clock Override'
           and q_control.get('help') == exact_help and q_value.get('help') == exact_help
           and q_control.get('callback') is False and q_value.get('callback') is False,
           f'QID 0x37D +0x703 / QID 0x37E +0x704; help string exact; both CALLBACK=false; menu-result SHA-256={menu_hash}')
    record('hii_numeric_bounds_are_metadata', q_value.get('bounds') == [0, 2000, 0],
           f'IFR numeric bounds={q_value.get("bounds")}; bounds are UI metadata, not a found clock actuator/range')

    cbs_data, smu_data, fab_data = CBS.read_bytes(), SMU.read_bytes(), FAB.read_bytes()
    # Fixed, prior-mapped TE address corrections: CbsBasePei/AmdNbioSmuV10Pei - 0x190; Fabric - 0x198.
    for name, data, delta, expected in [
        ('cbs', cbs_data, 0x190, {0xE706:'ba73130000', 0xE726:'8a8203070000', 0xE738:'ba74130000', 0xE75B:'668b8204070000', 0xE762:'66894103'}),
        ('smu', smu_data, 0x190, {0x10786:'ba73130000', 0x107A6:'8a8203070000', 0x107B8:'ba74130000', 0x107DB:'668b8204070000', 0x107E2:'66894103'}),
        ('fabric', fab_data, 0x198, {0x11C98:'ba74130000', 0x11CBB:'668b8204070000', 0x11CC2:'66894103'}),
    ]:
        ok = all(data[addr-delta:addr-delta+len(bytes.fromhex(raw))] == bytes.fromhex(raw) for addr, raw in expected.items())
        record(name + '_raw_serializer_anchors', ok,
               '; '.join(f'RVA 0x{a:x} raw={(a-delta):#x}={raw}' for a, raw in expected.items()))

    objdump_version = subprocess.run(['objdump', '--version'], cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()[0]
    llvm_version = subprocess.run(['llvm-objdump', '--version'], cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()[0]
    disasm_specs = [
        ('cbs_1373_1374', ['objdump','-D','-z','--insn-width=16','-b','binary','-m','i386','-M','intel','--adjust-vma=0x190','--start-address=0xe706','--stop-address=0xe76f',str(CBS)], cbs_data, 0x190, False,
         ['e706:','mov    edx,0x1373','e726:','BYTE PTR [edx+0x703]','e738:','mov    edx,0x1374','e75b:','WORD PTR [edx+0x704]','e762:','WORD PTR [ecx+0x3]']),
        ('smu_1373_1374', ['objdump','-D','-z','--insn-width=16','-b','binary','-m','i386','-M','intel','--adjust-vma=0x190','--start-address=0x10786','--stop-address=0x107e5',str(SMU)], smu_data, 0x190, False,
         ['10786:','mov    edx,0x1373','107a6:','BYTE PTR [edx+0x703]','107b8:','mov    edx,0x1374','107db:','WORD PTR [edx+0x704]','107e2:','WORD PTR [ecx+0x3]']),
        ('fabric_1374', ['objdump','-D','-z','--insn-width=16','-b','binary','-m','i386','-M','intel','--adjust-vma=0x198','--start-address=0x11c98','--stop-address=0x11ccf',str(FAB)], fab_data, 0x198, False,
         ['11c98:','mov    edx,0x1374','11cbb:','WORD PTR [edx+0x704]','11cc2:','WORD PTR [ecx+0x3]']),
    ]
    all_x86_rows = {}
    for name, argv, data, delta, thumb, markers in disasm_specs:
        p = run(name, argv)
        text = p.stdout
        rows = check_disassembly_bytes(name, text, data, delta, thumb)
        all_x86_rows[name] = rows
        record(name + '_literal_instruction_chain', all(marker in text for marker in markers),
               f'checked direct listing for {len(markers)//2} address/mnemonic anchors')

    abl1_data = ABL1.read_bytes()
    fclk_label_bytes = b'\n\tOverride Fclk: %d\n\x00'
    record('exact_abl1_fclk_logger_string', abl1_data[0x469C:0x469C + len(fclk_label_bytes)] == fclk_label_bytes,
           f'payload+0x469C={fclk_label_bytes!r}')
    thumb_specs = [
        ('abl1_fclk_request_463c', ['llvm-objdump','-D','--triple=thumbv7m-none-eabi','--start-address=0x463c','--stop-address=0x4696',str(ABL1_OBJ)],
         ['4648:','cmp\tr1, #0xf','4652:','strh.w\tr0, [sp, #0x10]','465e:','strh.w\tr0, [sp, #0x12]','466a:','bl\t0x1fb4','4678:','adr\tr2, #32','467e:','ldrh.w\tr0, [sp, #0x8]','4682:','str\tr0, [r5]']),
        ('abl1_generic_reader_1fb4', ['llvm-objdump','-D','--triple=thumbv7m-none-eabi','--start-address=0x1fb4','--stop-address=0x2050',str(ABL1_OBJ)],
         ['1fb4:','push.w','1fe0:','bl\t0x4800','1fe6:','ldr\tr0, [sp, #0x8]','1fe8:','uxtb\tr0, r0','1fea:','cmp\tr0, #0x1','2016:','ldrh\tr0, [r0, #0x2]']),
        ('abl1_context_selector_107e4', ['llvm-objdump','-D','--triple=thumbv7m-none-eabi','--start-address=0x107e4','--stop-address=0x10824',str(ABL1_OBJ)],
         ['107e4:','ldrh.w\tr0, [r4, #0x78]','107ec:','cmp.w\tr0, #0x3e8','107f2:','cmp.w\tr0, #0x4b0','10820:']),
    ]
    thumb_texts = {}
    for name, argv, markers in thumb_specs:
        p = run(name, argv)
        text = p.stdout
        rows = check_disassembly_bytes(name, text, abl1_data, 0, True)
        thumb_texts[name] = (text, rows)
        record(name + '_static_window_anchors', all(m in text for m in markers),
               f'checked exact ABL1 instruction/string anchors; {len(rows)} decoded instructions byte-matched')

    fclk_rows = thumb_texts['abl1_fclk_request_463c'][1]
    fclk_cmp = [{'address': f'0x{a:x}', 'instruction': asm.strip()} for a, _raw, asm in fclk_rows if asm.strip().startswith('cmp')]
    record('fclk_branch_has_no_fclk_uclk_order_compare',
           [x['address'] for x in fclk_cmp] == ['0x4648', '0x4686'],
           f'only CMPs in bounded FCLK branch: {fclk_cmp}; first is selector r1=0xF, second caller-state check r0=r4')

    result = {
        'status': 'PASS',
        'timestamp': dt.datetime.now(ZoneInfo('Asia/Almaty')).isoformat(),
        'evidence_class': ['observed-bytes', 'static-analysis'],
        'scope': 'Pinned offline CLV DF field/token and exact ABL1 FCLK request boundary; no hardware/runtime action.',
        'inputs': input_rows,
        'menu_result': {'path': str(MENU), 'sha256': menu_hash},
        'tool_versions': {'objdump': objdump_version, 'llvm-objdump': llvm_version},
        'baseline': {'AmdSetup_body_offset': '0x4CF', 'MemoryClockSpeed_plus_0x316': {'absolute_ROM_offset':'0x7E5','raw':f'0x{mem:02X}','enum_label':'1800MHz'}, 'DfClockOverrideControl_plus_0x703': {'absolute_ROM_offset':'0xBD2','raw':f'0x{control:02X}','label':'Manual'}, 'DfClockOvrd_plus_0x704': {'absolute_ROM_offsets':['0xBD3','0xBD4'],'raw_le':value_bytes.hex(),'u16_le':value}},
        'positive_edges': {
            'Setup_plus_0x703_to_INV_0x1373': 'CbsBasePei RVA 0xE726 reads byte [Setup+0x703] after emitting ID 0x1373 at RVA 0xE706; byte copied to record+3 and record cursor advances 4 (type bits 0). AmdNbioSmuV10Pei mirrors this at 0x10786/0x107A6.',
            'Setup_plus_0x704_to_INV_0x1374': 'CbsBasePei RVA 0xE738 emits ID 0x1374, sets type bits 1, loads WORD [Setup+0x704] at 0xE75B, copies two bytes to record+3 at 0xE762 and advances 5. AmdNbioSmuV10Pei mirrors this at 0x107B8/0x107DB; AmdFabricAriPei independently emits token 0x1374 at 0x11C98/0x11CBB.',
            'separate_ABL1_FCLK_request': 'At payload 0x463C, only when R1==0x0F does the branch query descriptor halfwords 0x015F/0x0160 via generic reader 0x1FB4; its returned halfword is loaded from SP+8 and written through caller R5 at 0x4682. The adjacent string at payload 0x469C is `\\n\\tOverride Fclk: %d\\n`. This is a real static ABL1 FCLK-named request/data path, but no byte-backed join to $INV token 0x1373/0x1374 was found in this bounded trace.',
            'HII_help_and_range': {'QID_0x37D': q_control.get('help'), 'QID_0x37E': q_value.get('help'), 'QID_0x37E_bounds': q_value.get('bounds'), 'interpretation': 'Static HII help/range metadata only; neither proves a code-enforced FCLK>UCLK relation or a common unit.'},
        },
        'bounded_code_enforcement_result': {
            'result': 'NOT_OBSERVED_IN_CHECKED_PATHS; GLOBAL_ENFORCEMENT_UNRESOLVED',
            'facts': ['The DF serializer windows copy bytes/word to typed $INV/NVTB records without arithmetic conversion or an FCLK/UCLK comparison.', 'ABL1 FCLK branch compares R1 to 0x0F (selector) and R0 to saved R4 (caller-state integrity); it does not compare FCLK and UCLK or read the Memory P-state field in this bounded branch.', 'The exact help sentence is an HII string associated with QIDs 0x37D/0x37E; no action callback is set on those questions.', 'HII NUMERIC bounds [0,2000] are UI metadata, not a proven physical clock limit.'],
            'ABL1_context_branch': 'The separate payload+0x107E4 consumer reads context+0x78 and compares raw immediates 0x03E8 and 0x04B0 to select a callback code; source linkage from the FCLK request to this field, units, conversion, and callback target remain unresolved.',
        },
        'limits_and_first_unresolved_boundary': {
            'unit_conversion': 'No conversion from Setup+0x704 raw u16 (baseline 1420) to ABL1 FCLK descriptors 0x015F/0x0160 or a PMFW row/divider value is proven.',
            'actuator': 'The previously mapped PMFW DF coefficient/register path at 0x1E170/0x1E1D0/0x1E260/0x1EF18 is static and not joined to the Setup tokens in this check.',
            'first_unresolved_instruction_boundary': 'Post-serializer $INV record receiver/consumer: no selected receiver/provider instruction has been proven to consume tokens 0x1373/0x1374 as the separate ABL1 FCLK query keys 0x015F/0x0160. In the independent ABL1 route, payload+0x1FB4 calls helper 0x4800; provider/base provenance for the request value remains the next unresolved boundary.',
            'status': 'No runtime consumer, frequency unit/physical limit, divider relation, or hardware application proved.'
        },
        'checks': checks,
        'commands': commands,
    }
    (OUT / 'result.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    (OUT / 'commands.txt').write_text('\n'.join(f"{c['name']}: {' '.join(c['argv'])}\n  exit={c['exit_status']}; stdout={c['stdout_file']}; stderr={c['stderr_file']}" for c in commands) + '\n', encoding='utf-8')
    print(json.dumps({'status':'PASS','checks_passed':len(checks),'checks_failed':0,
                      'memory_request':'AmdSetup+0x316=0x24 (1800MHz label), preserved',
                      'df_serializer':'AmdSetup+0x703 u8->$INV 0x1373; +0x704 u16 LE->$INV 0x1374',
                      'fclk_path':'ABL1 0x463C -> descriptors 0x015F/0x0160 -> reader 0x1FB4 -> output [R5]',
                      'help_text_enforcement':'NOT_OBSERVED_IN_CHECKED_PATHS; GLOBAL_ENFORCEMENT_UNRESOLVED',
                      'first_unresolved':'token 0x1373/0x1374 receiver-to-ABL1 FCLK-key join; ABL1 helper/provider request data origin'}, separators=(',',':')))
except Exception as exc:
    failed = {'status':'FAIL','error':f'{type(exc).__name__}: {exc}','checks':checks,'commands':commands}
    (OUT / 'result.json').write_text(json.dumps(failed,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':'FAIL','error':str(exc),'checks_passed':sum(x['status']=='PASS' for x in checks),'checks_failed':sum(x['status']=='FAIL' for x in checks)},separators=(',',':')))
    raise
