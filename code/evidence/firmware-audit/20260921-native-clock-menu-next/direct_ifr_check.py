#!/usr/bin/env python3
"""Independent byte-level spot check of exact-clv clock question and REF records."""
import hashlib, json, struct
from pathlib import Path
ROOT=Path('/home/OWNER/orca/projects/bc250')
EVID=ROOT/'evidence/firmware-audit/20260921-native-clock-menu-next'
MODULE=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/CbsSetupDxe-7ff717d51c9a.bin'
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
PARSER_RESULT=EVID/'menu-result.json'
EXPECTED_MODULE_SHA='7ff717d51c9a447c6954c63b633cf836f1e4396c2b01f4bf590268a60ac1d0d8'
EXPECTED_ROM_SHA='ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
EXPECTED={
 'Memory Clock Speed':(0x20f,0x702c,0x316,0x10,0x05),
 'UclkDiv1M0':(0x229,0x702f,0x330,0x10,0x05),
 'Memory P-state':(0x25e,0x7032,0x36d,0x10,0x05),
 'FCLK_DPM':(0x7045,0x703e,0x6a3,0x14,0x05),
 'DF Clock Override Control':(0x37d,0x703f,0x703,0x10,0x05),
 'DF Clock Override':(0x37e,0x703f,0x704,0x10,0x07),
}
EXPECTED_REFS=[
 (0x7007,0x7028),(0x7028,0x702a),(0x702a,0x702c),
 (0x7000,0x7008),(0x7008,0x702e),(0x702e,0x702f),
 (0x702e,0x7030),(0x7030,0x7032),
 (0x7009,0x703e),(0x7009,0x703f),
]
def sha(b):return hashlib.sha256(b).hexdigest()
rom=ROM.read_bytes(); module=MODULE.read_bytes(); report=json.loads(PARSER_RESULT.read_text())
assert len(rom)==0x1000000 and sha(rom)==EXPECTED_ROM_SHA
assert sha(module)==EXPECTED_MODULE_SHA
forms_start=int(report['forms_package_offset'],16)
forms_end=forms_start+4+report['ifr_bytes_walked']
questions={}; forms=set(); refs=[]; stack=[]; curform=None; pos=forms_start+4
while pos<forms_end:
    op=module[pos]; rawlen=module[pos+1]; ln=rawlen&0x7f; scope=rawlen>>7
    assert ln>=2 and pos+ln<=forms_end,(hex(pos),ln,forms_end)
    body=module[pos+2:pos+ln]
    conditions=tuple(s for s in stack if s in (0x0a,0x19,0x1e))
    if op==0x01:
        curform=struct.unpack_from('<H',body)[0]; forms.add(curform)
    elif op in (0x05,0x06,0x07):
        prompt,helpid,qid,vid,off,flags=struct.unpack_from('<HHHHHB',body)
        if vid==0x5000 and off in {0x316,0x330,0x36d,0x6a3,0x703,0x704}:
            questions[(vid,off)]={'qid':qid,'form':curform,'flags':flags,'op':op,'conditions':conditions,'raw':module[pos:pos+ln].hex(),'module_offset':hex(pos)}
    elif op==0x0f and len(body)>=13:
        target=struct.unpack_from('<H',body,11)[0]
        refs.append({'source':curform,'target':target,'conditions':conditions,'raw':module[pos:pos+ln].hex(),'module_offset':hex(pos)})
    if op==0x29:
        assert stack,(hex(pos),'unbalanced END')
        stack.pop()
    elif scope:
        stack.append(op)
    pos+=ln
assert pos==forms_end and not stack
checks=[]
def ck(label,ok,details):
    checks.append({'check':label,'status':'PASS' if ok else 'FAIL','details':details})
    assert ok,label
for label,(qid,form,off,flags,op) in EXPECTED.items():
    q=questions[(0x5000,off)]
    actual=(q['qid'],q['form'],q['flags'],q['op'],q['conditions'])
    wanted=(qid,form,flags,op,())
    ck('question:'+label,actual==wanted,{'expected':[hex(qid),hex(form),hex(flags),hex(op),[]],'observed':[hex(q['qid']),hex(q['form']),hex(q['flags']),hex(q['op']),list(q['conditions'])],'module_offset':q['module_offset'],'raw':q['raw']})
stored={'Memory Clock Speed':(0x316,b'\x24'),'UclkDiv1M0':(0x330,b'\x01'),
        'Memory P-state':(0x36d,b'\xff'),'FCLK_DPM':(0x6a3,b'\x0f'),
        'DF Clock Override Control':(0x703,b'\x01'),'DF Clock Override':(0x704,b'\x8c\x05')}
for label,(off,want) in stored.items():
    actual=rom[0x4cf+off:0x4cf+off+len(want)]
    ck('donor-byte:'+label,actual==want,{'body_offset':hex(off),'rom_offset':hex(0x4cf+off),'expected':want.hex(),'observed':actual.hex()})
refset={(r['source'],r['target']):r for r in refs}
for src,dst in EXPECTED_REFS:
    r=refset[(src,dst)]
    ck(f'ref:{src:#x}->{dst:#x}',r['conditions']==(),{'conditions':list(r['conditions']),'module_offset':r['module_offset'],'raw':r['raw']})
for form in (0x7007,0x7009):
    incoming=[r for r in refs if r['target']==form]
    ck(f'no-package-local-incoming-ref:{form:#x}',not incoming,{'incoming_refs':incoming})
# The exact CbsSetupDxe RouteConfig body invokes the UEFI runtime-service
# SetVariable slot at +0x58 after ConfigToBlock. This is the standard HII
# save path; it is separate from the one field carrying CALLBACK metadata.
route_config_bytes=module[0x919:0x91c].hex()
ck('RouteConfig-SetVariable-slot+0x58',route_config_bytes=='ff5058',
   {'module_offset':'0x919','expected':'ff5058','observed':route_config_bytes,
    'meaning':'indirect call through EFI_RUNTIME_SERVICES->SetVariable'})
result={'status':'PASS','rom_sha256':sha(rom),'module_sha256':sha(module),'package_span':[hex(forms_start),hex(forms_end)],'questions_checked':len(EXPECTED),'stored_fields_checked':len(stored),'refs_checked':len(EXPECTED_REFS),'checks':checks}
(EVID/'direct-ifr-check-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':result['status'],'rom_sha256':result['rom_sha256'],'module_sha256':result['module_sha256'],'questions_checked':result['questions_checked'],'stored_fields_checked':result['stored_fields_checked'],'refs_checked':result['refs_checked'],'checks_passed':len(checks)},sort_keys=True))
