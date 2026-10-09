#!/usr/bin/env python3
"""Independent ABL1 descriptor-array and 0x4800 selector/provider check."""
from __future__ import annotations
import hashlib, json, struct, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ROM = ROOT / 'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
ABL = ROOT / 'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
DIS = ROOT / 'evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt'
BASE = ROOT / 'evidence/firmware-audit/20260920-clv-abl-producer-base-review/abl1-producer-base-review-result.json'
PRIOR = ROOT / 'evidence/firmware-audit/20260920-clv-abl1-apcb-reader-boundary-resume/abl1-apcb-reader-boundary-result.json'
EXPECTED = {
    'rom': 'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8',
    'abl': 'af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a',
    'dis': 'b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65',
    'base': 'ecb7953571d3b008e76798718d216362bf819a4b0ffcb3dc52da58e23e2c483b',
    'prior': '537f987266057865bd7f278939304f2f40dcc5db4e57c6048ca0905ce2dac128',
}
checks: list[dict] = []
def sha(p: Path) -> str: return hashlib.sha256(p.read_bytes()).hexdigest()
def normal(v): return 'hex:'+v.hex() if isinstance(v,bytes) else v
def check(name: str, got, expected):
    ok = got == expected
    checks.append({'check': name, 'passed': ok, 'got': normal(got), 'expected': normal(expected)})
    if not ok: raise AssertionError(f'{name}: got={got!r}; expected={expected!r}')
def hx(raw: bytes) -> str: return raw.hex()
def u16(blob: bytes, off: int) -> int: return struct.unpack_from('<H', blob, off)[0]
def u32(blob: bytes, off: int) -> int: return struct.unpack_from('<I', blob, off)[0]
def run_disasm(obj: Path, start: str, stop: str, prefix: str):
    cmd = ['llvm-objdump', '-D', '--triple=thumbv7', f'--start-address={start}', f'--stop-address={stop}', str(obj)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    (OUT / f'{prefix}.stdout').write_text(p.stdout)
    (OUT / f'{prefix}.stderr').write_text(p.stderr)
    result = {'command': cmd, 'exit_status': p.returncode, 'stdout': f'{prefix}.stdout', 'stderr': f'{prefix}.stderr'}
    check(f'{prefix} llvm-objdump exit', p.returncode, 0)
    check(f'{prefix} llvm-objdump output nonempty', len(p.stdout) > 100, True)
    return result, p.stdout

def main():
    for name, path, key in [('ROM', ROM, 'rom'), ('exact ABL1', ABL, 'abl'), ('reviewed full disassembly', DIS, 'dis'), ('conditional-base result', BASE, 'base'), ('prior reader result', PRIOR, 'prior')]:
        check(f'{name} exists', path.exists(), True)
        check(f'{name} sha256', sha(path), EXPECTED[key])
    blob = ABL.read_bytes()
    base = json.loads(BASE.read_text())
    prior = json.loads(PRIOR.read_text())
    check('base hypothesis literal', base.get('candidate_base'), '0x57100')
    check('base hypothesis has four independent code anchors', len(base.get('anchors', [])), 4)
    check('prior reader result status', prior.get('status'), 'PASS')
    check('prior reader result checks', prior.get('checks'), 42)

    # Caller descriptor arrays: exact instructions show 0x20 is the first list
    # element; only the second element changes for each UclkDiv1 query.
    check('Uclk selector initializes first candidate 0x20', blob[0x2cb6:0x2cb8], bytes.fromhex('2020'))
    check('Uclk stores first candidate in descriptor[0]', blob[0x2cf0:0x2cf4], bytes.fromhex('adf84400'))
    keys = [('M0',0x2cf4,0x21,0x2d0a), ('M1',0x2d20,0x22,0x2d32), ('M2',0x2d48,0x23,0x2d5a), ('M3',0x2d70,0x24,0x2d82)]
    for label, imm_off, token, call_off in keys:
        check(f'Uclk {label} sets alternative token immediate 0x{token:02x}', blob[imm_off:imm_off+2], bytes((token,0x20)))
        check(f'Uclk {label} stores alternative token in descriptor[1]', blob[imm_off+2:imm_off+6], bytes.fromhex('adf84600'))
        check(f'Uclk {label} passes same descriptor list to 0x1fb4', blob[call_off:call_off+6], bytes.fromhex('11a8fff752f9') if label == 'M0' else bytes.fromhex('11a8fff73ef9') if label == 'M1' else bytes.fromhex('11a8fff72af9') if label == 'M2' else bytes.fromhex('11a8fff716f9'))
    check('Uclk list terminator is zero after two IDs', blob[0x2cfc:0x2d00], bytes.fromhex('adf84880'))

    # Fclk has the same ordered-list shape, now IDs 0x015f and 0x0160.
    check('Fclk branch gates on literal selector 0x0f', blob[0x4648:0x464c], bytes.fromhex('0f291bd1'))
    check('Fclk first candidate immediate is 0x015f', blob[0x464e:0x4652], bytes.fromhex('40f25f10'))
    check('Fclk stores candidate[0]', blob[0x4652:0x4656], bytes.fromhex('adf81000'))
    check('Fclk increments to second candidate 0x0160', blob[0x4656:0x4658], bytes.fromhex('401c'))
    check('Fclk zero terminator is at descriptor[2]', blob[0x4658:0x465c], bytes.fromhex('adf81420'))
    check('Fclk stores second candidate', blob[0x465c:0x4662], bytes.fromhex('03abadf81200'))
    check('Fclk passes descriptor array to common reader 0x1fb4', blob[0x4662:0x466e], bytes.fromhex('04a80092019202aafdf7a3fc'))

    # The reader treats each nonzero halfword as a separate token query:
    # helper success goes to typed output; failure advances and stops at zero.
    check('reader initializes list index at zero', blob[0x1fbc:0x1fbe], bytes.fromhex('0024'))
    check('reader loads current descriptor halfword', blob[0x1fd8:0x1fdc], bytes.fromhex('35f81400'))
    check('reader calls helper at 0x4800', blob[0x1fe0:0x1fe4], bytes.fromhex('02f00efc'))
    check('reader helper-failure branch advances index', blob[0x200e:0x2012], bytes.fromhex('641ce4b2'))
    check('reader loads next descriptor and checks zero terminator', blob[0x2012:0x201a], bytes.fromhex('05eb440040880028'))
    check('reader continues on nonzero next token', blob[0x201a:0x201c], bytes.fromhex('dad1'))
    check('reader helper success proceeds to caller type dispatch', blob[0x1fe4:0x1fea], bytes.fromhex('68b10298c0b2'))

    # Exact helper/provider dataflow; do not assign a semantic name to 0x0f.
    check('0x4800 subtracts one from token', blob[0x4806:0x4808], bytes.fromhex('401e'))
    check('0x4800 compares token-1 to inclusive upper bound 0x160', blob[0x480a:0x480e], bytes.fromhex('b0f5b07f'))
    check('0x4800 rejects token-1 above 0x160', blob[0x480e:0x4810], bytes.fromhex('08d8'))
    check('0x4800 sets internal dispatch selector to literal 0x0f', blob[0x4810:0x4812], bytes.fromhex('0f20'))
    check('0x4800 forwards type and stack arguments', blob[0x4812:0x4816], bytes.fromhex('cde90031'))
    check('0x4800 forwards output/context/token registers', blob[0x4816:0x481c], bytes.fromhex('13462a462146'))
    check('0x4800 BL resolves to provider 0x49cc', blob[0x481c:0x4820], bytes.fromhex('00f0d6f8'))
    candidate_ids = [0x20,0x21,0x22,0x23,0x24,0x15f,0x160]
    check('all caller token candidates pass range 1..0x161', all(1 <= x <= 0x161 for x in candidate_ids), True)

    # Selector case and a conditional absolute-address mapping check.
    check('0x49cc begins at exact raw push', blob[0x49cc:0x49d0], bytes.fromhex('2de9ff4f'))
    check('0x49cc selector-specific table-copy byte count is 0x24', blob[0x49da:0x49dc], bytes.fromhex('2422'))
    check('0x49cc code literal names absolute table pointer 0x6a2d4', u32(blob,0x4dd0), 0x6a2d4)
    pointer_off = 0x6a2d4 - 0x57100
    check('0x6a2d4 maps conditionally to candidate payload offset 0x131d4', pointer_off, 0x131d4)
    check('candidate table fits in exact ABL1 payload', pointer_off + 0x24 <= len(blob), True)
    values = struct.unpack_from('<18H', blob, pointer_off)
    check('conditional table has 18 halfwords', len(values), 18)
    check('internal selector 0x0f table entry equals literal 4', values[0x0f], 4)
    check('0x49cc checks selector table index against 0x10', blob[0x4b26:0x4b2a], bytes.fromhex('1b981028'))
    check('0x49cc case 0x0f starts with literal selector 0x0f', blob[0x4b0e:0x4b10], bytes.fromhex('0f22'))
    check('case 0x0f prepares literal type-id 0x1707 in r1 before TBB', blob[0x4a1a:0x4a22], bytes.fromhex('41f6fe7041f20771'))
    check('case 0x0f saves selector and type-id pair for downstream path', blob[0x4b1a:0x4b22], bytes.fromhex('4af24e06cde90121'))

    # Re-run narrowly anchored disassembly on an owned binary wrapper, not the
    # pre-existing listing's parser/assertion logic.
    obj = OUT / 'ABL1-owned-exact.o'
    prep = subprocess.run(['llvm-objcopy','-I','binary','-O','elf32-littlearm','-B','arm',str(ABL),str(obj)],capture_output=True,text=True)
    (OUT/'llvm-objcopy.stdout').write_text(prep.stdout)
    (OUT/'llvm-objcopy.stderr').write_text(prep.stderr)
    check('owned llvm-objcopy exit', prep.returncode, 0)
    dis4800, text4800 = run_disasm(obj,'0x4800','0x4830','helper-4800-thumb-llvm')
    dis49cc, text49cc = run_disasm(obj,'0x49cc','0x4b90','provider-49cc-thumb-llvm')
    check('targeted listing confirms helper call target 0x49cc', 'bl\t0x49cc' in text4800, True)
    check('targeted listing confirms provider class 0x0f block', '0x1707' in text49cc and '49cc:' in text49cc, True)
    check('targeted provider listing contains helper 0x6374 edge', '0x6374' in text49cc, True)
    check('targeted provider listing contains helper 0x6238 edge', '0x6238' in text49cc, True)

    result = {
      'status':'PASS','checks':len(checks),'route':'independent exact-byte decode of ABL1 descriptor arrays and 0x4800 selector/provider edge',
      'evidence_class':['observed-bytes','static-analysis'],
      'inputs':{'rom':str(ROM),'abl1':str(ABL),'reviewed_full_disassembly':str(DIS),'conditional_base_review':str(BASE),'prior_reader_result':str(PRIOR)},
      'hashes':{'rom':sha(ROM),'abl1':sha(ABL),'reviewed_full_disassembly':sha(DIS),'conditional_base_review':sha(BASE),'prior_reader_result':sha(PRIOR)},
      'descriptor_decode':{
        'format':'ordered u16 token candidate array terminated by zero; reader queries each token in order, advances only when helper returns false, and returns on the first type-valid success',
        'uclk':'0x20 is candidate[0]; candidate[1] varies by M0..M3 as 0x21, 0x22, 0x23, or 0x24; zero terminates each two-token array',
        'fclk':'candidate[0]=0x015f, candidate[1]=0x0160, candidate[2]=0; caller branch has a literal selector compare 0x0f and logger text labels output Fclk',
        'not_prefix_key_pair':True
      },
      'provider_edge':{
        'reader':'0x1fb4 passes the current halfword token to helper 0x4800; the exact loop treats later halfwords as alternate candidates',
        'helper':'0x4800 accepts token IDs 1..0x161, sets internal selector 0x0f, preserves the token/context/output/type argument shape, and branches directly to 0x49cc',
        'provider_49cc':'exact selector 0x0f enters its dedicated TBB case, prepares raw selector 0x0f and literal 0x1707, and reaches exact helpers 0x6374 and 0x6238',
        'conditional_pointer':'literal 0x6a2d4 maps arithmetically to payload+0x131d4 only under candidate base 0x57100; 4 validated static anchors support address coherence, not loader/runtime-base proof',
        'conditional_table':'with that conditional base, copied 18-u16 table entry index 0x0f is 4; meaning of the entry remains unknown',
        'selector_label':'0x0f is demonstrably a dispatch selector and reused as a raw provider field; the inspected route does not name it group, priority, or source index, so those interpretations remain unsupported',
        'first_consumer':'typed value store at 0x1fb4; no frequency/divider/PLL consumer established'
      },
      'fresh_result':'The caller descriptors are token-candidate lists, not prefix/key pairs: UclkDiv1 uses [0x20, one of 0x21..0x24, 0], Fclk uses [0x015f,0x0160,0]. The reader tests each token through 0x4800 until a token succeeds or the zero terminator is reached. Helper 0x4800 forwards each valid ID through selector 0x0f to 0x49cc. The literal 0x0f is an internal dispatch selector (and raw provider field), but its semantic identity as group/priority/source index is not established. Fclk naming alone does not prove units, physical frequency, divider/PLL action, runtime behavior, or hardware clocks.',
      'commands':{'objcopy':['llvm-objcopy','-I','binary','-O','elf32-littlearm','-B','arm',str(ABL),str(obj)],'helper_disassembly':dis4800,'provider_disassembly':dis49cc},
      'limits':'Static exact-payload evidence only. Candidate base 0x57100 remains conditional; no source names, runtime execution, hardware behavior, or frequency semantics inferred.',
      'checks_detail':checks
    }
    out=OUT/'abl1-descriptor-provider-result.json'
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'checks':len(checks),'descriptor_decode':result['descriptor_decode'],'provider_edge':result['provider_edge'],'limits':result['limits']},indent=2))

if __name__ == '__main__': main()
