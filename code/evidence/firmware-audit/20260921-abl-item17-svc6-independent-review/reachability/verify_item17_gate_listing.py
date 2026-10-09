#!/usr/bin/env python3
"""Parse fresh ABL1 disassembly windows to adjudicate the conditional item17 SVC path."""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path
ROOT=Path('/home/OWNER/orca/projects/bc250')
BASE=Path(__file__).resolve().parent
OUT=BASE
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
ABL=ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
OBJ=BASE.parent/'ABL1-exact.o'
EXPECTED_ROM='ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
EXPECTED_ABL='af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a'
EXPECTED_OBJ='adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6'
WINDOWS={
 'gate':'callback-95fc-9658.objdump',
 'bypass':'bypass-9740-9860.objdump',
 'alt_calls':'svc-alternatives-9770-9820.objdump',
 'helper':'helper-6c20-6d24.objdump',
 'config':'reachable-config-dispatch-130c-1420.objdump',
 'single':'reachable-single-state-984e-98b0.objdump',
}
checks=[]
def add(name,observed,expected):
 ok=observed==expected; checks.append({'name':name,'passed':ok,'observed':observed,'expected':expected})
 if not ok: raise AssertionError(f'{name}: {observed!r} != {expected!r}')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def parse_window(name):
 p=BASE/WINDOWS[name]; out={}
 rx=re.compile(r'^\s*([0-9a-fA-F]+):\s+(.*)$')
 for line in p.read_text().splitlines():
  m=rx.match(line)
  if not m: continue
  addr=int(m.group(1),16); parts=m.group(2).strip().split(); i=0
  while i<len(parts) and re.fullmatch(r'[0-9a-fA-F]{4}',parts[i]): i+=1
  if i>=len(parts): continue
  mnemonic=parts[i].lower(); operands=' '.join(parts[i+1:]).split('@')[0].strip().lower()
  out[addr]=(mnemonic,operands,line.strip())
 return out
def expect(window,addr,mnemonic,operand_prefix=None):
 row=parse[window].get(addr)
 if row is None: raise AssertionError(f'missing disassembly row {window}:{addr:#x}')
 gotm, goto, line=row
 add(f'{window}:{addr:#x} mnemonic',gotm,mnemonic.lower())
 if operand_prefix is not None:
  add(f'{window}:{addr:#x} operands prefix',goto.startswith(operand_prefix.lower()),True)
 return goto

rom_hash=sha(ROM); abl_hash=sha(ABL); obj_hash=sha(OBJ)
add('exact ROM SHA-256',rom_hash,EXPECTED_ROM); add('exact ABL1 SHA-256',abl_hash,EXPECTED_ABL); add('exact ELF wrapper SHA-256',obj_hash,EXPECTED_OBJ)
parse={k:parse_window(k) for k in WINDOWS}

# Reused state is a report/result input only; do not repeat the table mapping.
prev=ROOT/'evidence/firmware-audit/20260921-item17-reachability-review/item17-reachability-result.json'
prevdoc=json.loads(prev.read_text())
add('prior item17 reachability result status',prevdoc.get('status'),'PASS')
add('prior conditional base preserved',prevdoc.get('conditional_base'),'0x57100')

# Exact local helper status -> callback guard.
expect('helper',0x6d1e,'movs','r0, #0x1')
expect('helper',0x6d20,'pop','{r4, pc}')
expect('helper',0x6c2a,'bl','0x6d10')
expect('helper',0x6c2e,'str','r0, [r4, #0x4]')
expect('gate',0x962a,'add','r0, sp, #0x160')
expect('gate',0x962c,'bl','0x6c20')
expect('gate',0x963e,'ldr','r0, [sp, #0x164]')
expect('gate',0x9644,'cmp','r0, #0x1')
expect('gate',0x9646,'bls','0x9744')
expect('bypass',0x9744,'b','0x984e')

# The selected branch skips the direct DD4/118C/10C0 call sites, but it enters
# a reachable local configuration dispatcher at 0x130c from the single-state path.
for addr,target in [(0x9780,'0xdd4'),(0x97e4,'0x118c'),(0x9800,'0x10c0')]:
 expect('alt_calls',addr,'bl',target)
expect('single',0x9850,'movs','r0, #0x4')
expect('single',0x9852,'movs','r1, #0x0')
expect('single',0x9854,'bl','0x130c')
expect('single',0x9858,'b','0x989e')
expect('single',0x988a,'bl','0x130c')
expect('single',0x98aa,'b','0x978e')
expect('bypass',0x978e,'strb.w','r10, [r4, #0x2c0]')
expect('bypass',0x9792,'b','0x9846')
expect('bypass',0x9848,'movs','r0, #0x0')
expect('bypass',0x984a,'pop.w','{r4, r5, r6, r7, r8, r9, r10, r11, pc}')

# With helper arguments r0=4,r1=0, 0x130c's two selector tests choose 0x1354.
expect('config',0x1310,'eor','r4, r0, #0x20')
expect('config',0x1314,'orrs','r4, r1')
expect('config',0x131a,'beq','0x1324')
expect('config',0x131c,'eor','r4, r0, #0x1')
expect('config',0x1320,'orrs','r4, r1')
expect('config',0x1322,'bne','0x1328')
expect('config',0x1328,'bl','0x1354')
expect('config',0x135a,'ldr','r0, [pc, #0xbc]')
expect('config',0x1366,'ldr','r0, [r0]')
expect('config',0x1376,'bl','0x1332')
expect('config',0x133c,'ldr','r0, [r1]')
expect('config',0x133e,'blx','r0')
expect('config',0x1346,'ldr.w','r1, [r6, r4, lsl #2]')
expect('config',0x134a,'cmp','r1, #0x0')
expect('config',0x134c,'bne','0x133c')

value=4; flag=0
first_zero=((value ^ 0x20) | flag)==0
second_zero=((value ^ 1) | flag)==0
indirect_provider_reached=(not first_zero) and (not second_zero)
add('input r0=4/r1=0 bypasses 0x1324 equality case',first_zero,False)
add('input r0=4/r1=0 branches to local 0x1354 dispatcher',indirect_provider_reached,True)

result={
 'status':'PASS','checks':{'passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks),'total':len(checks)},
 'inputs':{'rom_sha256':rom_hash,'abl1_sha256':abl_hash,'elf_sha256':obj_hash,'item17_result_sha256':sha(prev)},
 'selected_local_path':{
  'conditional_prior_item17_binding':'base 0x57100 reused, not rechecked; loader runtime base remains unproven',
  'helper_gate':'0x6D10 returns 1; 0x6C20 writes result to scratch +4; 0x95FC loads [SP+0x164]; 0x9646 -> 0x9744 -> 0x984E',
  'direct_alternatives_bypassed':['0x9780 -> 0x0DD4','0x97E4 -> 0x118C','0x9800 -> 0x10C0'],
  'next_reachable_local_edge':'0x984E -> 0x130C (r0=4,r1=0) -> 0x1354 -> 0x1332 -> data-dependent BLX R0 callback table; 0x130C is called again at 0x988A',
  'indirect_table_status':'dispatch code is byte-backed; table pointer/object initialization and callback targets are unresolved; no SVC6 reachability conclusion follows from this indirect edge',
  'local_return':'after the single-state loop, 0x98AA -> 0x978E -> 0x9846 -> r0=0 return'
 },
 'accepted':'The exact selected local helper branch bypasses the directly enumerated DD4 and SVC-wrapper callsites, reaches a different local indirect callback dispatcher, and returns 0 from ABL1.',
 'disallowed':'Do not claim SVC #6 is globally unreachable for item17; do not claim it is reached or is the current item17 actuator. The dynamic callback table and external SVC handler are unresolved.',
 'limits':['No item17 table/base mapping repeated.','No SVC handler/recipient semantics.','No clock-register/PLL write or physical-clock effect in this check.','No runtime, hardware, training, performance, or synchronization result.'],
 'checks_detail':checks
}
(OUT/'reachable-config-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':'PASS','checks':result['checks']['total'],'passed':result['checks']['passed'],'failed':result['checks']['failed'],'direct_svc_callsites':'BYPASSED_ON_SELECTED_STATIC_BRANCH','next_local_edge':'0x130C -> 0x1354 -> dynamic BLX table','global_svc6_reachability':'UNRESOLVED'},indent=2))
