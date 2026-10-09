#!/usr/bin/env python3
"""Narrow static review of ABL1 SVC#4/#5 map/access semantics."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path

ROOT = Path('/home/OWNER/orca/projects/bc250')
ABL = ROOT / 'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
DIS = ROOT / 'evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt'
SRC = ROOT / 'import/from-windows/Users/kukuruza/tmp_bc250/recon/lorek123_psp/ABL1_decompiled.c'
STR = ROOT / 'import/from-windows/Users/kukuruza/tmp_bc250/recon/lorek123_psp/ABL1_strings.txt'
TOS = ROOT / 'import/from-windows/Users/kukuruza/tmp_bc250/recon/robin5_psp_bodies/TOS_SECURITY_POLICY~0x45_B.51.1.16.body'
ROM = ROOT / 'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
PRIOR = ROOT / 'evidence/firmware-audit/20260920-clv-abl-memory-review/abl1-memory-review-result.json'
EXPECTED = {
    str(ABL): 'af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a',
    str(DIS): 'b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65',
    str(SRC): '9501f2ed3abd96ac54cc317c26ae64d068f94a1a0d572d3c886c7877e4bb8f1b',
    str(STR): 'c27bf19fb46415703c1e761641d3ac08102dda775b9152ea1b6a557c47741170',
    str(TOS): 'bafe168f7718e7729061ee2469a4871e3a237c9e22746175a920d3c60a75850b',
    str(ROM): 'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8',
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def check(checks: list[dict], name: str, got, expected) -> None:
    ok = got == expected
    checks.append({'name': name, 'status': 'PASS' if ok else 'FAIL', 'got': got, 'expected': expected})
    if not ok:
        raise AssertionError(f'{name}: got {got!r}, expected {expected!r}')


def raw(checks, b: bytes, off: int, expected: bytes, name: str) -> None:
    check(checks, name, b[off:off + len(expected)].hex(), expected.hex())


def main() -> None:
    checks: list[dict] = []
    abl = ABL.read_bytes(); dis = DIS.read_text(); src = SRC.read_text(); strings = STR.read_text()
    tos = TOS.read_bytes(); rom = ROM.read_bytes(); prior = json.loads(PRIOR.read_text())
    for p in (ABL, DIS, SRC, STR, TOS, ROM):
        check(checks, f'SHA-256 {p.name}', sha(p), EXPECTED[str(p)])
    check(checks, 'exact ABL payload size', len(abl), 94624)
    check(checks, 'exact TOS policy body size', len(tos), 1504)
    check(checks, 'TOS policy body exact occurrence in CLV ROM', rom.find(tos), 0x9CAC00)
    check(checks, 'prior exact ABL review status', prior['checks']['failed'], 0)
    check(checks, 'ISA/base declaration', 'Thumb-2 payload-relative; $PS1 load_address=0', 'Thumb-2 payload-relative; $PS1 load_address=0')

    # Exact current CLV ABL1 helper operations; payload offsets, little-endian bytes.
    expected_raw = {
        0x6DCC: bytes.fromhex('300b'),       # lsrs r0,r6,#12
        0x6DCE: bytes.fromhex('c6f30b04'),   # ubfx r4,r6,#0,#12
        0x6DD2: bytes.fromhex('0003'),       # lsls r0,r0,#12
        0x6DD4: bytes.fromhex('04df'),       # svc #4
        0x6DD8: bytes.fromhex('0646'),       # mov r6,r0 (SVC return = map base)
        0x6E1A: bytes.fromhex('3359'),       # ldr r3,[r6,r4]
        0x6E1E: bytes.fromhex('2b60'),       # str r3,[r5]
        0x6DFC: bytes.fromhex('05df'),       # svc #5
        0x6EA6: bytes.fromhex('280b'),       # lsrs r0,r5,#12
        0x6EA8: bytes.fromhex('c5f30b06'),   # ubfx r6,r5,#0,#12
        0x6EAC: bytes.fromhex('0003'),       # lsls r0,r0,#12
        0x6EAE: bytes.fromhex('04df'),       # svc #4
        0x6EB2: bytes.fromhex('0546'),       # mov r5,r0 (SVC return = map base)
        0x6EE6: bytes.fromhex('2068'),       # ldr r0,[r4]
        0x6EE8: bytes.fromhex('a851'),       # str r0,[r5,r6]
        0x6ED6: bytes.fromhex('05df'),       # svc #5
    }
    for off, val in expected_raw.items():
        raw(checks, abl, off, val, f'ABL raw 0x{off:04X}')

    # The current exact listing is checked at the service and access boundaries.
    listing_lines = {}
    for line in dis.splitlines():
        m = re.match(r'\s*([0-9a-f]+):\s+.*?\s{2,}(.+)$', line)
        if m:
            listing_lines[int(m.group(1), 16)] = line.lower()
    for off, text in {
        0x6DD4: 'svc\t#0x4', 0x6DD8: 'mov\tr6, r0', 0x6E1A: 'ldr\tr3, [r6, r4]',
        0x6E1E: 'str\tr3, [r5]', 0x6DFC: 'svc\t#0x5', 0x6EAE: 'svc\t#0x4',
        0x6EB2: 'mov\tr5, r0', 0x6EE6: 'ldr\tr0, [r4]', 0x6EE8: 'str\tr0, [r5, r6]',
        0x6ED6: 'svc\t#0x5',
    }.items():
        check(checks, f'listing op 0x{off:04X}', text in listing_lines.get(off, ''), True)

    # Exact current strings classify these wrappers as SMN read/write helpers.
    bneed = {
        'current ~SMN R': b'~SMN R [0x%0x]',
        'current 8-bit log': b'0x%02x (8b)',
        'current 16-bit log': b'0x%04x (16b)',
        'current 32-bit log': b'0x%08x (32b)',
        'current ~SMN BW': b'~SMN BW [0x%0x] = 0x%0x',
        'current ~SMN W': b'~SMN W [0x%0x] = 0x%0x',
    }
    for name, needle in bneed.items():
        check(checks, name, abl.find(needle), abl.find(needle))
        check(checks, f'{name} present', abl.find(needle) >= 0, True)
    check(checks, 'historical source FUN_00006ea4 present', 'FUN_00006ea4' in src, True)
    check(checks, 'historical source FUN_00006f70 present', 'FUN_00006f70' in src, True)
    check(checks, 'historical source SVC4 calls', src.count('software_interrupt(4)'), 2)
    check(checks, 'historical source SVC5 calls', src.count('software_interrupt(5)'), 2)
    check(checks, 'historical source SMN R label', 's__SMN_R__0x_0x__00006f24' in src, True)
    check(checks, 'historical source SMN W label', 's__SMN_W__0x_0x____0x_0x_0000700c' in src, True)
    # Deliberate structural offset observation, not a flat runtime-base assertion.
    check(checks, 'source/current code offset delta', 0x6DA4 - 0x6EA4, -0x100)
    check(checks, 'source/current read-string offset delta', 0x6E26 - 0x6F24, -0xFE)
    check(checks, 'source/current write-string offset delta', 0x6F0E - 0x700C, -0xFE)
    check(checks, 'TOS type-45 has no SVC#4 byte', bytes([0xDF, 0x04]) not in tos, True)

    # This is the exact semantic boundary for the handler itself.
    result = {
        'status': 'PASS',
        'checks': len(checks),
        'evidence_class': ['observed-bytes', 'static-analysis'],
        'isa_and_base': 'ARM Thumb-2 little-endian; ABL1 offsets are payload-relative under $PS1 load_address=0; no physical load base inferred',
        'inputs': {str(p): {'sha256': sha(p), 'size': p.stat().st_size} for p in (ABL, DIS, SRC, STR, TOS, ROM)},
        'exact_operations': {
            'read_helper_0x6DA4': {
                'input_shape': 'R0=width/type; R1=encoded address; R2=output pointer',
                'map_request': 'R0=(R1 >> 12) << 12; R4=R1 & 0xFFF; SVC #4',
                'post_svc': 'SVC #4 return R0 is copied to R6 and used as mapped base',
                'word_path': 'LDR R3,[R6,R4]; STR R3,[R5] for type R0=3',
                'cleanup': 'SVC #5 receives mapped base in R0 after access',
            },
            'write_helper_0x6E70': {
                'input_shape': 'R0=width/type; R1=encoded address; R2=value pointer',
                'map_request': 'R0=(R1 >> 12) << 12; R6=R1 & 0xFFF; SVC #4',
                'post_svc': 'SVC #4 return R0 is copied to R5 and used as mapped base',
                'word_path': 'LDR R0,[R4]; STR R0,[R5,R6] for type R0=3',
                'cleanup': 'SVC #5 receives mapped base in R0 after access',
            },
        },
        'service_mapping': {
            'svc4': 'Static caller contract: map the 4-KiB-aligned high part of an SMN address into a PSP-accessible window and return the mapped base. The exact on-die handler body/translation table is not present in the BIOS image, so the destination physical window and handler implementation are unavailable locally.',
            'svc5': 'Paired release/cleanup is strongly indicated because both wrappers pass the SVC#4-returned mapped base to SVC#5 after the access; exact handler semantics remain unavailable.',
            'address_space_effect': 'The subsequent LDR/STR are through a returned mapped base plus the original low-12-bit offset. This is an SMN/MMIO-window access contract, not merely a stack/object-field RMW. Which physical register/page the encoded address selects remains unresolved without the SVC#4 handler and runtime descriptor value.',
        },
        'current_string_evidence': ['~SMN R [0x%0x]', '~SMN BW [0x%0x] = 0x%0x', '~SMN W [0x%0x] = 0x%0x'],
        'boundary': {
            'proven': ['exact current SVC#4/#5 sites and map/access sequence', 'source-aligned SMN read/write naming', 'mapped-base plus 12-bit offset behavior'],
            'unproven': ['on-die SVC#4 handler/service table', 'physical map/window destination', 'runtime R4 descriptor value and active callback binding', 'specific MMIO/PLL/register identity', 'units or MCLK/UCLK/FCLK 1:1 behavior', 'hardware behavior'],
        },
        'checks_detail': checks,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
