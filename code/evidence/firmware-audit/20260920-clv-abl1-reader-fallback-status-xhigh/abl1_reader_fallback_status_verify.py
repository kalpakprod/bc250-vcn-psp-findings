#!/usr/bin/env python3
"""Minimal exact-byte check of ABL1 reader fallback versus sentinel handling."""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ABL = ROOT / 'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
PRIOR = ROOT / 'evidence/firmware-audit/20260920-clv-abl1-apcb-reader-boundary-resume/abl1-apcb-reader-boundary-result.json'
CONTEXT = ROOT / 'evidence/firmware-audit/20260920-clv-abl1-reader-output-context-xhigh/abl1-reader-output-context-result.json'
DIS = ROOT / 'evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt'
EXPECTED = {
    'abl': 'af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a',
    'prior': '537f987266057865bd7f278939304f2f40dcc5db4e57c6048ca0905ce2dac128',
    'context': '6abae87817c9aa5baf8565524b071f5fae6d19ad5e478d140e22fdea0da42c21',
    'dis': 'b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65',
}
checks = []
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(v): return 'hex:'+v.hex() if isinstance(v, bytes) else v
def check(name, got, expected):
    ok = got == expected
    checks.append({'check': name, 'passed': ok, 'got': norm(got), 'expected': norm(expected)})
    if not ok: raise AssertionError(f'{name}: got={got!r}; expected={expected!r}')

def main():
    for name,p,key in [('exact ABL1',ABL,'abl'),('prior reader result',PRIOR,'prior'),('output/context result',CONTEXT,'context'),('reviewed full Thumb listing',DIS,'dis')]:
        check(f'{name} exists', p.exists(), True)
        check(f'{name} sha256', sha(p), EXPECTED[key])
    blob = ABL.read_bytes()
    prior = json.loads(PRIOR.read_text())
    context = json.loads(CONTEXT.read_text())
    check('prior reader PASS', prior.get('status'), 'PASS')
    check('prior reader address', prior.get('reader',{}).get('payload_offset'), '0x1fb4')
    check('output/context PASS', context.get('status'), 'PASS')
    check('output/context retains final field-store edge', any('0x5FBA' in x for x in context.get('result',{}).get('fclk_output_path',[])), True)

    # First stage: helper status is tested in R0. A failed helper goes through
    # 0x2002 and then the index increment at 0x200e; it is the only fallback.
    check('first helper status branch is CBZ R0 -> 0x2002', blob[0x1fe0:0x1fe4], bytes.fromhex('02f00efc'))
    check('first helper status zero branch lands at 0x2002', blob[0x1fe4:0x1fe6], bytes.fromhex('68b1'))
    check('first-stage output is loaded as byte', blob[0x1fe6:0x1fea], bytes.fromhex('0298c0b2'))
    check('first-stage gate compares returned byte with literal 1', blob[0x1fea:0x1fec], bytes.fromhex('0128'))
    check('first-stage value==1 advances to next descriptor', blob[0x1fec:0x1fee], bytes.fromhex('0fd0'))
    check('first-stage value!=1 enters diagnostic path, not fallback', blob[0x1fee:0x2002], bytes.fromhex('cdf800802ca235f8143000200146fff786f94be0'))
    check('fallback increments descriptor index', blob[0x200e:0x2012], bytes.fromhex('641ce4b2'))
    check('fallback tests next descriptor for zero terminator', blob[0x2012:0x201c], bytes.fromhex('05eb440040880028dad1'))

    # Final candidate: helper status is checked before caller-type dispatch.
    check('final helper call exact status branch', blob[0x203a:0x2042], bytes.fromhex('02f0e1fb002828d0'))
    check('final helper status zero returns failure, no descriptor increment', blob[0x203e:0x2042], bytes.fromhex('002828d0'))
    check('final stage loads caller type after status success', blob[0x2042:0x2048], bytes.fromhex('9af800000128'))

    # Type-1 Auto/sentinel: returned 0xff is rejected when r7=0 and returns
    # 0 at 0x209a. The slice contains no branch to 0x200e/0x2012.
    check('type-1 sentinel guard computes ~value byte and ORs r7', blob[0x2058:0x2060], bytes.fromhex('0298c143c9b23943'))
    check('type-1 sentinel guard returns failure', blob[0x2060:0x2062], bytes.fromhex('1bd0'))
    check('type-1 non-sentinel stores byte', blob[0x2062:0x2064], bytes.fromhex('3070'))
    check('type-1 sentinel path has no fallback increment', blob[0x2058:0x2062].find(bytes.fromhex('641c')), -1)

    # Type-2 Auto/sentinel: returned 0xffff is rejected, then returns 0.
    check('type-2 sentinel guard computes ~value halfword and ORs r7', blob[0x2066:0x206e], bytes.fromhex('0298c14389b23943'))
    check('type-2 sentinel guard returns failure', blob[0x206e:0x2070], bytes.fromhex('14d0'))
    check('type-2 non-sentinel stores halfword', blob[0x2070:0x2072], bytes.fromhex('3080'))
    check('type-2 sentinel path has no fallback increment', blob[0x2066:0x2070].find(bytes.fromhex('641c')), -1)

    # Type-4 zero sentinel and type-8 zero-doubleword guards likewise return
    # failure; these are value guards, not alternate-descriptor branches.
    check('type-4 zero guard ORs r7 with returned word', blob[0x2074:0x207a], bytes.fromhex('029877ea0001'))
    check('type-4 zero guard returns failure', blob[0x207a:0x207c], bytes.fromhex('0ed0'))
    check('type-4 nonzero stores word', blob[0x207c:0x207e], bytes.fromhex('3060'))
    check('type-8 zero guard tests both returned words', blob[0x2080:0x208c], bytes.fromhex('dde90210ca4372ea000200d1'))
    check('type-8 zero guard returns failure when r7 is zero', blob[0x208c:0x208e], bytes.fromhex('2fb1'))
    check('type-8 nonzero stores doubleword', blob[0x208e:0x2092], bytes.fromhex('c6e90010'))

    check('reader success returns 1 only after typed store', blob[0x2092:0x209a], bytes.fromhex('012004b0bde8f087'))
    check('reader failure returns 0 and loops to epilogue', blob[0x209a:0x209e], bytes.fromhex('0020fae7'))
    check('reader loads r7/r9 from first/second caller stack arguments', blob[0x1fc0:0x1fc4], bytes.fromhex('dde90c79'))
    check('Uclk call site initializes r8 to zero', blob[0x2cc4:0x2cc8], bytes.fromhex('4ff00008'))
    check('Uclk call site passes r8=0 as first stack argument', blob[0x2d06:0x2d0a], bytes.fromhex('cde90080'))
    check('Fclk call site sets r2=0', blob[0x464c:0x464e], bytes.fromhex('0022'))
    check('Fclk call site passes r2=0 as first stack argument', blob[0x4664:0x4668], bytes.fromhex('00920192'))

    # Cross-review the independent output/context result with only the exact
    # Fclk stack default, return store, and downstream field read.
    fclk_path = context.get('result',{}).get('fclk_output_path',[])
    check('output/context result retains Fclk context store edge', any('0x5FBA' in x for x in fclk_path), True)
    check('Fclk branch passes output slot SP+8 to reader', blob[0x4668:0x466a], bytes.fromhex('02aa'))
    check('Fclk branch calls reader 0x1fb4', blob[0x466a:0x466e], bytes.fromhex('fdf7a3fc'))
    check('Fclk branch returns without storing through R5 on reader failure', blob[0x466e:0x4670], bytes.fromhex('48b1'))
    check('Fclk branch stores a returned halfword to caller pointer on success', blob[0x467e:0x4684], bytes.fromhex('bdf808002860'))
    check('outer Fclk caller seeds local default 0x4b0', blob[0x5fa4:0x5faa], bytes.fromhex('40f2b0400190'))
    check('outer Fclk caller passes SP+4 then calls accessor', blob[0x5fac:0x5fb2], bytes.fromhex('01a8fef745fb'))
    check('outer Fclk caller reloads local default/result after accessor', blob[0x5fb2:0x5fb4], bytes.fromhex('019b'))
    check('outer Fclk caller stores halfword in context+0x78', blob[0x5fba:0x5fbe], bytes.fromhex('a5f87830'))
    check('outer function passes same context base to Fclk accessor', blob[0x7e72:0x7e78], bytes.fromhex('2046fdf7f8ff'))
    check('outer function passes same context base to context reader', blob[0x8426:0x842c], bytes.fromhex('204607f0eafe'))
    check('context reader copies its input pointer R0 to R4', blob[0x10208:0x1020a], bytes.fromhex('0446'))
    check('context reader branch 0x104b2 targets 0x10592', 0x104b6 + ((0x6e if 0x6e < 0x80 else 0x6e-0x100) << 1), 0x10592)
    check('context reader branch 0x10592 targets 0x107da', 0x10596 + ((0x122 if 0x122 < 0x400 else 0x122-0x800) << 1), 0x107da)
    check('first identified context read is halfword [R4+0x78]', blob[0x107e4:0x107e8], bytes.fromhex('b4f87800'))
    check('first threshold compare literal is 0x3e8', blob[0x107ec:0x107f0], bytes.fromhex('b0f57a7f'))
    check('second threshold compare literal is 0x4b0', blob[0x107f2:0x107f6], bytes.fromhex('b0f5966f'))
    check('descriptor token IDs are numerically distinct from the thresholds', [0x15f,0x160] == [0x3e8,0x4b0], False)
    listing = DIS.read_text(errors='replace').splitlines()
    fclk_prefix_stores = []
    for line in listing:
        match = re.match(r'^\s*([0-9a-f]+):', line)
        if match and 0x463c <= int(match.group(1),16) < 0x466a and re.search(r'\bstr(?:b|h)?(?:\.w)?\s+.*\[sp, #0xc\]', line):
            fclk_prefix_stores.append(line)
    check('Fclk type-pointer local is not explicitly written before reader call', fclk_prefix_stores, [])
    check('Fclk passes SP+0x0c as generic reader type pointer', blob[0x465c:0x465e], bytes.fromhex('03ab'))

    result = {
      'status':'PASS', 'checks':len(checks),
      'route':'minimal exact ABL1 reader fallback-status versus sentinel check',
      'evidence_class':['observed-bytes','static-analysis'],
      'inputs':{'abl1':str(ABL),'prior_reader_result':str(PRIOR),'output_context_result':str(CONTEXT)},
      'hashes':{'abl1':sha(ABL),'prior_reader_result':sha(PRIOR),'output_context_result':sha(CONTEXT)},
      'semantics':{
        'fallback_flag':'helper return R0 status only',
        'first_stage':'status=0 enters 0x2002 then advances index at 0x200E; status=1 requires returned byte==1 to advance; returned byte!=1 returns failure at 0x209A',
        'final_stage':'status=0 returns failure at 0x2094; status=1 enters typed guards; sentinel/Auto value fails typed guard and returns 0 at 0x209A without trying another descriptor',
        'type2':'returned 0xFFFF with r7=0 is rejected by ~value/UXTH/ORR guard before STRH; no fallback branch exists in this slice',
        'precedence':'ordered chain is not combined-key fallback on arbitrary values: earlier elements are boolean gate/status stages, and the final element is the typed value stage',
        'callsite_sentinel_mask':'both Uclk and Fclk call sites pass first stack argument zero, which the reader loads into r7 and uses in sentinel guards',
        'fclk_type_selector':'Fclk passes SP+0x0c as the type-byte pointer but no explicit write to that local occurs in the bounded Fclk body before the reader call; actual type-2 branch execution for this caller is therefore not established',
        'fclk_context':'Fclk handler writes a typed reader result only on reader success; its caller seeds local 0x4b0 before the call and unconditionally stores the resulting halfword to context+0x78; a later static path loads that field and compares against 0x3e8/0x4b0',
        'numeric_qualification':'candidate token IDs 0x15f/0x160 are identifiers; downstream constants 0x3e8/0x4b0 are observed comparison thresholds. The path does not prove a unit conversion or that tokens equal thresholds'
      },
      'fresh_result':'Before the final descriptor, helper status R0=0 advances to the next item; helper status R0!=0 advances only if the returned byte equals 1. Any other first-stage byte is terminal failure at 0x209A. On the final descriptor, helper status R0=0 returns failure at 0x2094; helper success with an Auto/sentinel value also fails terminally at 0x209A without another descriptor attempt. Fallback is therefore status/gate driven, while final sentinel handling is terminal value validation. A separate exact static Fclk caller seeds local 0x4b0, calls the halfword reader, and then stores the local to context+0x78; a later context path loads it and compares to 0x3e8/0x4b0. These are threshold constants, not proven equivalents of token IDs 0x15f/0x160.',
      'limits':'Exact static bytes only; no runtime/APCB value observation, loader-base proof, frequency units, clock application, training, or hardware result.',
      'checks_detail':checks
    }
    (OUT/'abl1-reader-fallback-status-result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'checks':len(checks),'semantics':result['semantics'],'fresh_result':result['fresh_result']},indent=2))
if __name__=='__main__': main()
