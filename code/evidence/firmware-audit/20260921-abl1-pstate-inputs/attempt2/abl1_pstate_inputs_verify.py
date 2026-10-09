#!/usr/bin/env python3
"""Verify exact ABL1 local status-field and channel-pointer dataflow."""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; OUT=Path(__file__).resolve().parent
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
PAY=ROOT/'evidence/firmware-audit/20260920-clv-sync-stage2-abl-memory/ABL1-clv-decompressed.bin'
OBJ=ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o'
WINDOWS={
 'caller': OUT/'caller-962a-9652.stdout',
 'initializer': OUT/'initializer-6c20-6d24.stdout',
 'getter14': OUT/'getter-6ca0-6cb2.stdout',
 'getter0c': OUT/'getter-6cd8-6cea.stdout',
 'returner': OUT/'returner-6d10-6d22.stdout',
 'channel': OUT/'channel-pointer-109bc-10a2c.stdout',
}
EXPECTED={'rom':'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8',
'payload':'af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a',
'obj':'54abef3a390abb0ff745685de2eed4e0e8db5e9ba27bba1a0f245573b47ff135'}
checks=[]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ck(name, actual, expected): checks.append({'name':name,'actual':actual,'expected':expected,'status':'PASS' if actual==expected else 'FAIL'})
ck('ROM_SHA256',sha(ROM),EXPECTED['rom']); ck('ROM_size',ROM.stat().st_size,16777216)
ck('ABL1_payload_SHA256',sha(PAY),EXPECTED['payload']); ck('ABL1_payload_size',PAY.stat().st_size,94624)
ck('exact_object_SHA256',sha(OBJ),EXPECTED['obj'])
for k,p in WINDOWS.items(): ck(f'{k}_stderr_empty', (OUT/(p.name.replace('.stdout','.stderr'))).read_bytes(), b'')
# Parse each objdump output by instruction address, mnemonic, and operands.
rows={}
for name,p in WINDOWS.items():
 text=p.read_text()
 d={}
 for line in text.splitlines():
  parts=line.split('\t')
  if len(parts)<3: continue
  m=re.match(r'\s*([0-9a-f]+):',parts[0])
  if m: d[int(m.group(1),16)]=(parts[1].strip().lower(),parts[2].split('@',1)[0].strip().lower())
 rows[name]=d

def ins(name, addr, mnemonic, operands=''):
 actual=rows[name].get(addr)
 good=bool(actual and actual[0]==mnemonic and (not operands or re.search(operands,actual[1])))
 ck(f'{name}:{addr:#x}',good,True)
# 0x95FC passes SP+0x160 to 0x6C20, then tests output block +0x4.
for args in [('caller',0x962a,'add',r'r0,\s*sp,\s*#0x160'),('caller',0x962c,'bl',r'0x6c20'),('caller',0x963e,'ldr',r'r0,\s*\[sp,\s*#0x164\]'),('caller',0x9644,'cmp',r'r0,\s*#0x1'),('caller',0x9646,'bls',r'0x9744'),('caller',0x9648,'ldr',r'r0,\s*\[sp,\s*#0x174\]'),('caller',0x964e,'cmp',r'r0,\s*#0x0'),('caller',0x9650,'beq',r'0x9746')]: ins(*args)
# 0x6C20 output block fields +4 and +0x14 are locally written.
for args in [('initializer',0x6c22,'mov',r'r4,\s*r0'),('initializer',0x6c2a,'bl',r'0x6d10'),('initializer',0x6c2e,'str',r'r0,\s*\[r4,\s*#0x4\]'),('initializer',0x6c36,'bl',r'0x6cd8'),('initializer',0x6c3a,'str',r'r0,\s*\[r4,\s*#0xc\]'),('initializer',0x6c3c,'bl',r'0x6ca0'),('initializer',0x6c40,'str',r'r0,\s*\[r4,\s*#0x10\]'),('initializer',0x6c42,'cbnz',r'r0,\s*0x6c48'),('initializer',0x6c44,'ldr',r'r1,\s*\[r4,\s*#0xc\]'),('initializer',0x6c46,'cbz',r'r1,\s*0x6c54'),('initializer',0x6c54,'movs',r'r1,\s*#0x1'),('initializer',0x6c56,'b',r'0x6c4a'),('initializer',0x6c4a,'str',r'r1,\s*\[r4,\s*#0x14\]')]: ins(*args)
# Helper return values are direct constants: 0x6D10 returns 1; 0x6CA0 and 0x6CD8 return 0.
for args in [('returner',0x6d1e,'movs',r'r0,\s*#0x1'),('returner',0x6d20,'pop',r'\{r4,\s*pc\}'),('getter14',0x6cae,'movs',r'r0,\s*#0x0'),('getter0c',0x6ce6,'movs',r'r0,\s*#0x0')]: ins(*args)
# 0x109BC normalizes index and derives outer context +0x0C from context+0x8 +0x70.
for args in [('channel',0x109c0,'ldrb.w',r'r0,\s*\[r0,\s*#0x4b\]'),('channel',0x109c4,'ldrb.w',r'r1,\s*\[sp,\s*#0x4\]'),('channel',0x109d6,'cbnz',r'r0,\s*0x109e2'),('channel',0x109d8,'ldr.w',r'r2,\s*\[r4,\s*#0x3b0\]'),('channel',0x109e0,'blx',r'r2'),('channel',0x109e2,'ldrb.w',r'r0,\s*\[sp,\s*#0x4\]'),('channel',0x109e6,'strb.w',r'r0,\s*\[r4,\s*#0x49\]'),('channel',0x109f0,'ldr',r'r0,\s*\[r4,\s*#0x8\]'),('channel',0x109f2,'ldr',r'r1,\s*\[r0,\s*#0x70\]'),('channel',0x109f8,'rsb',r'r2,\s*r0,\s*r0,\s*lsl\s*#0x3'),('channel',0x109fc,'add.w',r'r2,\s*r2,\s*r0,\s*lsl\s*#0x4'),('channel',0x10a00,'add.w',r'r1,\s*r1,\s*r2,\s*lsl\s*#0x4'),('channel',0x10a04,'str',r'r1,\s*\[r4,\s*#0xc\]'),('channel',0x10a28,'bl',r'0x10994')]: ins(*args)
# Re-read unchanged native baseline bytes; only preserve the 1800-labelled request.
b=ROM.read_bytes(); base=0x4cf
ck('baseline_MemoryClockSpeed_1800_label_byte',b[base+0x316],0x24)
ck('baseline_UclkDiv1M0',b[base+0x330],0x01)
ck('baseline_MemoryPstate',b[base+0x36d],0xff)
ck('baseline_FclkDpm',b[base+0x6a3],0x0f)
passed=sum(x['status']=='PASS' for x in checks); failed=len(checks)-passed
result={'status':'PASS' if failed==0 else 'FAIL','checks':{'passed':passed,'failed':failed,'total':len(checks)},
 'exact_inputs':{'rom':str(ROM),'rom_sha256':sha(ROM),'payload':str(PAY),'payload_sha256':sha(PAY),'object':str(OBJ),'object_sha256':sha(OBJ)},
 'new_edges':{
  'stack_164':{'producer':'0x95FC caller allocates SP+0x160 at 0x962A; BL 0x6C20 at 0x962C; 0x6C20 stores return of 0x6D10 at block+0x4 (0x6C2A/0x6C2E); 0x6D10 returns constant 1 at 0x6D1E/0x6D20','consequence':'if this direct call returns, [SP+0x164] == 1, so BLS at 0x9646 is taken; multi-channel branch is not entered on this local helper path'},
  'stack_174':{'producer':'0x6C20 stores helper 0x6CA0 output at block+0x10 (0x6C3C/0x6C40); 0x6CA0 returns 0 (0x6CAE); with block+0xC from 0x6CD8 also 0 (0x6C36/0x6C3A, 0x6CE6), CBZ at 0x6C46 reaches 0x6C54 and stores 1 at block+0x14 (0x6C54..0x6C4A)','consequence':'[SP+0x174] is locally prepared as 1, but the first [SP+0x164] gate prevents reaching its consumer on this direct path'},
  'channel_pointer':{'producer':'0x109BC reads/normalizes index, writes context+0x49 and derives context+0x0C at 0x109F0..0x10A04','formula':'context+0x0C = *(context+0x8+0x70) + (23*normalized_index << 4) = *(context+0x8+0x70) + 0x170*index','consumer':'0x95FC uses [context+0x0C]+0x20 at 0x9672/0x9758/0x983C'},
 },
 'limits':['0x6D4C/0x6C5C outputs, 0x6C20 caller context, and 0x109BC callback gate/object source remain unresolved.','No direct join from these ABL1 local fields to AmdSetup+0x36D or +0x6A3; do not label them MemoryPstate/FclkDpm.','No loader/runtime invocation, units, training, physical clocks, 1800 application, 1:1:1, or hardware result.']}
(OUT/'abl1-pstate-inputs-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':result['status'],'checks':result['checks'],'new_edges':result['new_edges']},sort_keys=True))
raise SystemExit(0 if failed==0 else 1)
