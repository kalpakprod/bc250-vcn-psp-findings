#!/usr/bin/env python3
"""Independent raw-byte check of the ABL1 SVC #6 caller/wrapper ABI boundary."""
from __future__ import annotations
import hashlib
import json
import struct
from pathlib import Path

ROOT=Path('/home/OWNER/orca/projects/bc250')
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
ABL=ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
ELF=Path(__file__).resolve().parent/'ABL1-exact.o'
EXPECTED_ROM='ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
EXPECTED_ABL='af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a'
EXPECTED_ELF='adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6'
b=ABL.read_bytes()
checks=[]

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def check(name, got, expected):
    ok=got==expected
    checks.append({'name':name,'passed':ok,'got':got,'expected':expected})
    if not ok: raise AssertionError(f'{name}: {got!r} != {expected!r}')
def hx(addr,n): return b[addr:addr+n].hex()

rom_hash=sha(ROM); abl_hash=hashlib.sha256(b).hexdigest(); elf_hash=sha(ELF)
check('pinned ROM hash',rom_hash,EXPECTED_ROM)
check('pinned ABL1 hash',abl_hash,EXPECTED_ABL)
check('fresh ELF wrapper hash',elf_hash,EXPECTED_ELF)
check('ABL1 size',len(b),94624)

# SVC wrapper input preservation, helper call, output buffer write, trap and return.
check('SVC wrapper entry/push',hx(0x12ac,2),'30b5')
check('wrapper saves r2 buffer pointer as r4',hx(0x12b0,2),'1446')
check('wrapper passes local stack to metadata helper',hx(0x12b2,2),'6846')
check('wrapper metadata-helper BL',hx(0x12b4,4),'05f0b4fc')
check('wrapper sets r5=0 after helper',hx(0x12b8,2),'0025')
check('wrapper loads literal via PC',hx(0x12ba,2),'0348')
check('wrapper local buffer field store',hx(0x12bc,4),'84f84050')
check('SVC instruction #6',hx(0x12c0,2),'06df')
check('wrapper return value from zeroed r5',hx(0x12c4,2),'2846')
literal=int.from_bytes(b[0x12c8:0x12cc],'little')
check('SVC literal word',hex(literal),'0x6a41c')

# Visible callers supply a local stack buffer; wrapper store +0x40 is inside
# their 0x60-byte local frames, not a named MMIO/clock register address.
check('caller 0x10C0 frame allocation',hx(0x10c4,2),'98b0')
check('caller 0x10FA selector 0x0B',hx(0x10fa,2),'0b21')
check('caller 0x1100 r2=SP',hx(0x1100,2),'6a46')
check('caller 0x1102 r0=context',hx(0x1102,2),'4046')
check('caller 0x1104 BL SVC wrapper',hx(0x1104,4),'00f0d2f8')
check('other caller 0x118C frame allocation',hx(0x1190,2),'98b0')
check('other caller 0x11C6 r1=SP',hx(0x11c6,2),'6946')
check('other caller 0x11E2 r2=r1',hx(0x11e2,2),'0a46')
check('other caller 0x11E6 selector 0x0C',hx(0x11e6,2),'0c21')
check('other caller 0x11E8 BL SVC wrapper',hx(0x11e8,4),'00f060f8')
check('0x40 lies within 0x60 caller frame',0x40 < 0x60,True)

# The wrapper saves r4/r5/LR, but not r1-r3 across helper 0x6C20. It does
# not reload the caller selectors 0x0B/0x0C before SVC #6.
wrapper_push=int.from_bytes(b[0x12ac:0x12ae],'little')
check('wrapper push mask preserves r4/r5/lr only',hex(wrapper_push),'0xb530')
check('wrapper has no saved r1-r3 in prologue mask',wrapper_push & 0x000e,0)
check('metadata helper writes into caller stack record',hx(0x6c22,2),'0446')
check('metadata helper stores first gathered field at record+0',hx(0x6c28,2),'2060')
check('metadata helper stores second gathered field at record+4',hx(0x6c2e,2),'6060')
check('metadata helper static probe call exists',hx(0x6c24,4),'00f092f8')

# The prior item-17 result is reused only for the local gate statement, not
# rerun: its conditional 6D10==1 path bypasses the SVC-reaching alternatives.
prior_path=ROOT/'evidence/firmware-audit/20260921-abl-item17-consumer/item17-consumer-result.json'
prior=json.loads(prior_path.read_text())
check('prior item17 state remains PASS',prior.get('status'),'PASS')
check('prior item17 local checks remain 136',prior.get('checks'),136)

result={
 'status':'PASS',
 'checks':{'passed':sum(x['passed'] for x in checks),'failed':sum(not x['passed'] for x in checks),'total':len(checks)},
 'inputs':{'rom_sha256':rom_hash,'abl1_sha256':abl_hash,'elf_sha256':elf_hash,'prior_item17_result_sha256':sha(prior_path)},
 'abi_observations':{
  'callers_before_wrapper':{'selector_0x0b':{'r1':'0x0B','r2':'SP','entry':'0x1104'},'selector_0x0c':{'r1':'0x0C','r2':'SP','entry':'0x11E8'}},
  'wrapper':{'saves':'r4/r5/LR','preserves_r2_as_r4':True,'calls_helper':'0x6C20 with r0=SP','loads_r0_literal':'0x0006A41C','writes':'byte 0 to [caller-buffer+0x40]','svc':'#6','returns':'r0=0 after trap'},
  'service_abi_limit':'r1-r3 after helper 0x6C20 are not proven by the extracted wrapper; the caller selectors 0x0B/0x0C are not established as SVC input arguments.'
 },
 'write_classification':{
  'direct_known_clock_register_write_in_inspected_ABL_wrapper_callers':'NOT_OBSERVED',
  'visible_store_target':'caller-provided stack buffer +0x40 (both inspected callers reserve 0x60 bytes and pass SP)',
  'SVC_handler':'outside extracted ABL1; downstream register effects unresolved'
 },
 'item17_gate':'Prior exact result reports local helper 0x6D10=1 and path 0x9646 -> 0x9744 -> 0x984E, which bypasses the two SVC-reaching alternatives; conditional static path only.',
 'limits':['No SVC #6 handler/recipient semantics recovered.','No PLL/clock selector or known physical clock register write observed in the bounded ABL caller/wrapper.','No claim that SVC cannot cause downstream writes.','No runtime, SVC, hardware, clock, training, performance, or synchronization result.'],
 'checks_detail':checks
}
(ELF.parent/'svc6-independent-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':'PASS','checks':len(checks),'passed':result['checks']['passed'],'failed':result['checks']['failed'],'direct_clock_register_write':'NOT_OBSERVED_IN_BOUNDED_ABL_WRAPPER','SVC_handler':'UNRESOLVED'},indent=2))
