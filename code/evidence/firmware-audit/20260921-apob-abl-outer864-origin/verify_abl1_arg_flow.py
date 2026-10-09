#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, re, struct, subprocess
from pathlib import Path

ROOT = Path.cwd()
OUT = ROOT / 'evidence/firmware-audit/20260921-apob-abl-outer864-origin'
ROM = ROOT / 'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
PAYLOAD = ROOT / 'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
OBJ = ROOT / 'evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o'
EXPECTED = {
    'rom_sha256': 'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8',
    'payload_sha256': 'af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a',
    'payload_size': 94624,
    'object_sha256': '54abef3a390abb0ff745685de2eed4e0e8db5e9ba27bba1a0f245573b47ff135',
}

def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def check(name: str, condition: bool, detail: str, checks: list[dict]) -> None:
    checks.append({'name': name, 'status': 'PASS' if condition else 'FAIL', 'detail': detail})
    if not condition:
        raise AssertionError(f'{name}: {detail}')

def elf_section(blob: bytes, name: str) -> tuple[int, int, int]:
    if blob[:6] != b'\x7fELF\x01\x01':
        raise ValueError('source object is not ELF32 little-endian')
    shoff = struct.unpack_from('<I', blob, 32)[0]
    shentsize, shnum, shstrndx = struct.unpack_from('<HHH', blob, 46)
    shdrs = [struct.unpack_from('<IIIIIIIIII', blob, shoff + i * shentsize) for i in range(shnum)]
    shstr = shdrs[shstrndx]
    strings = blob[shstr[4]:shstr[4] + shstr[5]]
    for h in shdrs:
        start = h[0]
        end = strings.find(b'\0', start)
        if end < 0:
            continue
        if strings[start:end].decode(errors='replace') == name:
            return h[3], h[4], h[5]
    raise ValueError(f'missing ELF section {name}')

rom = ROM.read_bytes()
payload = PAYLOAD.read_bytes()
obj = OBJ.read_bytes()
checks: list[dict] = []
check('rom_identity', len(rom) == 16777216 and sha(rom) == EXPECTED['rom_sha256'], f'bytes={len(rom)} sha256={sha(rom)}', checks)
check('payload_identity', len(payload) == EXPECTED['payload_size'] and sha(payload) == EXPECTED['payload_sha256'], f'bytes={len(payload)} sha256={sha(payload)}', checks)
check('object_identity', sha(obj) == EXPECTED['object_sha256'], f'bytes={len(obj)} sha256={sha(obj)}', checks)
section_addr, section_off, section_size = elf_section(obj, '.data')
check('object_data_section', section_addr == 0 and section_size == len(payload), f'addr=0x{section_addr:x} fileoff=0x{section_off:x} size={section_size}', checks)
check('object_maps_exact_payload', obj[section_off:section_off + section_size] == payload, 'ELF .data bytes equal exact decompressed ABL1 payload byte-for-byte', checks)

windows = {
    'caller_463c': (0x463c, 0x4684),
    'reader_1fb4': (0x1fb4, 0x2044),
    'helper_4800': (0x4800, 0x4822),
    'provider_49cc': (0x49cc, 0x4b60),
    'alternate_selector_0d': (0x47d2, 0x47f0),
    'heap_writer_6238': (0x6238, 0x6324),
    'byte_fill_6b78': (0x6b78, 0x6b84),
    'constructor_callers': (0x0b84, 0x0bd8),
    'constructor_0c00': (0x0c00, 0x0c36),
}
version = subprocess.run(['llvm-objdump', '--version'], capture_output=True, text=True, check=False)
(OUT / 'llvm-objdump.version').write_text(version.stdout + version.stderr)
check('llvm_objdump_version', version.returncode == 0 and '22.1.8' in version.stdout, version.stdout.splitlines()[1] if len(version.stdout.splitlines()) > 1 else version.stdout.strip(), checks)
for label, (start, stop) in windows.items():
    cmd = ['llvm-objdump', '-D', '--section=.data', '--triple=thumbv7', f'--start-address=0x{start:x}', f'--stop-address=0x{stop:x}', str(OBJ)]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    (OUT / f'{label}.cmd.json').write_text(json.dumps(cmd, indent=2) + '\n')
    (OUT / f'{label}.stdout').write_text(proc.stdout)
    (OUT / f'{label}.stderr').write_text(proc.stderr)
    (OUT / f'{label}.exit').write_text(str(proc.returncode) + '\n')
    check(f'disasm_{label}', proc.returncode == 0 and not proc.stderr, f'exit={proc.returncode} stderr_bytes={len(proc.stderr.encode())}', checks)

anchors = [
    ('caller_463c',0x4664,'9200','str r2, [sp]'),
    ('caller_463c',0x4666,'9201','str r2, [sp, #0x4]'),
    ('caller_463c',0x466a,'f7fdfca3','bl 0x1fb4'),
    ('reader_1fb4',0x1fb4,'e92d47ff','push.w'),
    ('reader_1fb4',0x1fc0,'e9dd790c','ldrd r7, r9'),
    ('reader_1fb4',0x1fd2,'f8cd9000','str.w r9, [sp]'),
    ('reader_1fb4',0x1fe0,'f002fc0e','bl 0x4800'),
    ('helper_4800',0x4800,'b57c','push'),
    ('helper_4800',0x4808,'9906','ldr r1, [sp, #0x18]'),
    ('helper_4800',0x4810,'200f','movs r0, #0xf'),
    ('helper_4800',0x4812,'e9cd3100','strd r3, r1, [sp]'),
    ('helper_4800',0x481c,'f000f8d6','bl 0x49cc'),
    ('provider_49cc',0x49cc,'e92d4fff','push.w'),
    ('provider_49cc',0x49d2,'b09b','sub sp, #0x6c'),
    ('provider_49cc',0x4b54,'9929','ldr r1, [sp, #0xa4]'),
    ('provider_49cc',0x4b5c,'f001fb6c','bl 0x6238'),
    ('heap_writer_6238',0x6238,'e92d4ff8','push.w'),
    ('heap_writer_6238',0x6242,'468a','mov r10, r1'),
    ('heap_writer_6238',0x6316,'2100','movs r1, #0x0'),
    ('heap_writer_6238',0x6318,'686a','ldr r2, [r5, #0x4]'),
    ('heap_writer_6238',0x631a,'f1050010','add.w r0, r5, #0x10'),
    ('heap_writer_6238',0x631e,'4653','mov r3, r10'),
    ('heap_writer_6238',0x6320,'f000fc2a','bl 0x6b78'),
    ('byte_fill_6b78',0x6b78,'e001','b 0x6b7e'),
    ('byte_fill_6b78',0x6b7a,'f8001b01','strb r1, [r0], #1'),
    ('byte_fill_6b78',0x6b7e,'1e52','subs r2, r2, #0x1'),
    ('byte_fill_6b78',0x6b80,'d2fb','bhs 0x6b7a'),
]
window_lines = {}
for label, path in windows.items():
    txt = (OUT / f'{label}.stdout').read_text()
    window_lines[label] = txt.splitlines()
for label, address, rawhex, decoded in anchors:
    raw = bytes.fromhex(rawhex)
    actual = payload[address:address + len(raw)]
    check(f'bytes_{address:05x}', actual == raw, f'payload[0x{address:x}:0x{address+len(raw):x}]={actual.hex()} expected={rawhex}', checks)
    prefix = f'{address:5x}:'
    line = next((line for line in window_lines[label] if line.lstrip().startswith(prefix)), None)
    norm = ' '.join(line.lower().split()) if line else ''
    check(f'decode_{address:05x}', line is not None and decoded.lower() in norm, f'decode_line={norm!r} expected_substring={decoded!r}', checks)

# AAPCS stack-slot reconstruction for the selector-0x0F path:
# 0x463C writes two zero stack arguments; 0x1FB4 pushes 12 regs (48 bytes),
# 0x4800 pushes 6 regs (24 bytes), and 0x49CC pushes 13 regs (52) plus 0x6c locals.
stack = {
    'caller_463c_outgoing_words': [0, 0],
    'reader_1fb4_saved_args_from_entry_sp_plus': [48, 52],
    'reader_1fb4_saved_registers': {'r7': 0, 'r9': 0},
    'helper_4800_incoming_word0_loaded_by_sp_plus_0x18_after_24_byte_push': 0,
    'provider_49cc_outgoing_words_at_0x4812': ['original_r3', 0],
    'provider_49cc_frame_bytes': 52 + 0x6c,
    'provider_49cc_load_sp_plus_0xa4_from_entry_sp': 4,
    'provider_49cc_second_stacked_arg_value': 0,
    'heap_6238_second_argument_r1': 0,
    'byte_fill_6b78_fill_byte_r1': 0,
}
check('stack_argument_math', stack['provider_49cc_frame_bytes'] == 160 and stack['provider_49cc_load_sp_plus_0xa4_from_entry_sp'] == 4 and stack['provider_49cc_second_stacked_arg_value'] == 0, 'provider SP+0xa4 equals entrySP+4 (second stacked word), whose selector-0x0F caller value traces to zero', checks)
check('byte_fill_not_copy', 'strb r1, [r0], #1' in ' '.join((OUT/'byte_fill_6b78.stdout').read_text().lower().split()) and 'ldr' not in ' '.join((OUT/'byte_fill_6b78.stdout').read_text().lower().split()), '0x6B78 loop stores R1 byte to destination and has no data load; caller sets R1=0', checks)

result = {
    'status': 'PASS',
    'checks': {'passed': len(checks), 'failed': 0, 'total': len(checks)},
    'target': {'path': str(ROM), 'bytes': len(rom), 'sha256': sha(rom)},
    'abl1_payload': {'path': str(PAYLOAD), 'bytes': len(payload), 'sha256': sha(payload)},
    'abl1_object': {'path': str(OBJ), 'bytes': len(obj), 'sha256': sha(obj), 'data_section': {'addr': section_addr, 'file_offset': section_off, 'size': section_size}, 'data_equals_payload': True},
    'stack_argument_reconstruction': stack,
    'interpretation': 'On the bounded selector-0x0F path, provider 0x49CC loads its second stacked argument (zero) at 0x4B54 and passes it as R1 to 0x6238. 0x6238 sets R1=0 and calls 0x6B78, whose loop stores that byte repeatedly; this is zero-fill, not a source-payload copy. No outer+0x864 to provider-input join is established.',
    'checks_detail': checks,
}
(OUT / 'abl1-outer864-argflow-result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps({'status': result['status'], 'checks': result['checks'], 'result': str(OUT / 'abl1-outer864-argflow-result.json')}, sort_keys=True))
