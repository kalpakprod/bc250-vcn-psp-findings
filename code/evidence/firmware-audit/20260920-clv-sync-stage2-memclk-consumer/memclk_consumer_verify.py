#!/usr/bin/env python3
"""Bounded MemoryClockSpeed token consumer check."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
CBS_INS=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/CbsBasePei-6ff112922ad8.instructions.json'
CBS_BIN=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/CbsBasePei-6ff112922ad8.bin'
MODULES={
 'AmdMemAm4Pei':(ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/AmdMemAm4Pei-1ef4e7b94467.bin',ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/AmdMemAm4Pei-1ef4e7b94467.instructions.json','1ef4e7b944672a9a48b6fcb16c4d35cb6d23bb8306429dc3eb10ee1d0c7bb5f8'),
 'PlatformMemoryConfigurationPei':(ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/PlatformMemoryConfigurationPei-6a1ab7fe72ad.bin',ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/PlatformMemoryConfigurationPei-6a1ab7fe72ad.instructions.json','6a1ab7fe72ad3ee0e8f9238e2ba2d166c97e44812761e6d16a725525e1817085'),
 'AmdMemoryHobInfoPeim':(ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/AmdMemoryHobInfoPeim-aad3f828ccef.bin',ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/AmdMemoryHobInfoPeim-aad3f828ccef.instructions.json','aad3f828ccef4cf8878cad8c9ee1e47743748f652a1ef54af04de759983b4619')}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1<<20),b''):h.update(c)
 return h.hexdigest()
def ck(c,l,d=None):checks.append({'label':l,'status':'PASS' if c else 'FAIL','details':d});return c
checks=[]
ck(sha(ROM)=='ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8','clv-hash',sha(ROM)); ck(sha(CBS_BIN)=='6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77','cbs-hash',sha(CBS_BIN))
rom=ROM.read_bytes();base=0x4cf;ck(rom[base+0x316]==0x24,'clv-memoryclock-byte',{'absolute':hex(base+0x316),'raw':rom[base+0x316]})
cbs={int(x['rva']):x for x in json.loads(CBS_INS.read_text())}
for r,b in {0x9837:'baed110000',0x9857:'8a8216030000',0x985d:'884103'}.items():
 d=cbs.get(r);ck(d is not None and d['bytes']==b,'cbs-memclk-serializer:'+hex(r),{'observed':d,'expected':b})
module_results={}
for name,(binp,insp,want) in MODULES.items():
 a=json.loads(insp.read_text()); direct=[x for x in a if '0x11ed' in x.get('operands','').lower() or '+0x316' in x.get('operands','').lower()]
 # The selected memory-init bodies are tested only for direct reader literals/Setup offsets.
 ck(sha(binp)==want,name+'-hash',sha(binp)); ck(len(direct)==0,name+'-no-direct-11ed-or-setup316',direct)
 module_results[name]={'sha256':sha(binp),'instruction_count':len(a),'direct_11ed_or_setup316_hits':direct}
result={'status':'PASS' if all(x['status']=='PASS' for x in checks) else 'FAIL','checks':{'passed':sum(x['status']=='PASS' for x in checks),'failed':sum(x['status']=='FAIL' for x in checks),'total':len(checks)},'exact_clv_serializer':{'field':'AmdSetup+0x316','record':'0x11ED','source_rva':'0x9857','store_rva':'0x985D'},'memory_init_modules':module_results,'conclusion':'The exact native memory-init modules in this bounded set contain no direct 0x11ED literal or Setup+0x316 source load. Existing evidence therefore ends at the CBS INV serializer; the missing edge is the AGESA/PSP/APOB memory-init consumer or a HOB/config structure populated after INV handoff. No MHz decode or accepted-range claim is established.','limitations':['No firmware execution or training/hardware result.','A no-hit in selected memory-init module bodies does not exclude indirect protocol/HOB consumers or closed PSP/AGESA code.'],'checks_detail':checks}
(OUT/'memclk-consumer-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':result['status'],'checks':result['checks'],'modules':module_results,'conclusion':result['conclusion']},sort_keys=True));sys.exit(0 if result['status']=='PASS' else 1)
