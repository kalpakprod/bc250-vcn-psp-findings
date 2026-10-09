#!/usr/bin/env python3
"""Control-flow pivot for exact native memory-init modules."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
AMDBIN=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/AmdMemAm4Pei-1ef4e7b94467.bin'; AMDINS=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/AmdMemAm4Pei-1ef4e7b94467.instructions.json'
PLATBIN=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/PlatformMemoryConfigurationPei-6a1ab7fe72ad.bin'; PLATINS=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/PlatformMemoryConfigurationPei-6a1ab7fe72ad.instructions.json'
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
EXPECTED={AMDBIN:'1ef4e7b944672a9a48b6fcb16c4d35cb6d23bb8306429dc3eb10ee1d0c7bb5f8',PLATBIN:'6a1ab7fe72ad3ee0e8f9238e2ba2d166c97e44812761e6d16a725525e1817085',ROM:'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'}
def sha(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1<<20),b''):h.update(c)
 return h.hexdigest()
def ck(c,l,d=None):checks.append({'label':l,'status':'PASS' if c else 'FAIL','details':d});return c
checks=[]
for p,w in EXPECTED.items():ck(sha(p)==w,'hash:'+str(p),{'observed':sha(p),'expected':w})
amd={int(x['rva']):x for x in json.loads(AMDINS.read_text())};plat={int(x['rva']):x for x in json.loads(PLATINS.read_text())}
# PlatformMemoryConfigurationPei is a pure zero-return stub in its entire 15-record body.
check_plat={480:'33c0',482:'c3'}
for r,b in check_plat.items():ck(plat.get(r,{}).get('bytes')==b,'PlatformMemoryConfigurationPei-byte:'+hex(r),plat.get(r))
ck(len(plat)==17,'PlatformMemoryConfigurationPei-instruction-count',len(plat));ck(not any(x['mnemonic']=='call' for x in plat.values()),'PlatformMemoryConfigurationPei-no-calls')
# AmdMemAm4Pei entry delegates into helper 0x876 then main 0x2f6.
for r,b in {0x240:'e831060000',0x245:'8b442408',0x249:'e9a8000000',0x876:'55',0x882:'e857050000',0x893:'e859fdffff',0x8a0:'684cb1e309',0x8ad:'56',0x8ae:'e856020000',0x8ca:'68ff000000',0x8cf:'6a61',0x8d1:'e803040000',0x8fc:'813b41504f42',0xc73:'813e24505350',0xc96:'813f24424844',0xc8e:'e836ffffff',0xca4:'e839ffffff',0x2f6:'55',0x316:'ff504c',0x3aa:'ff504c'}.items():
 ck(amd.get(r,{}).get('bytes')==b,'AmdMemAm4Pei-byte:'+hex(r),{'observed':amd.get(r),'expected':b})
result={'status':'PASS' if all(x['status']=='PASS' for x in checks) else 'FAIL','checks':{'passed':sum(x['status']=='PASS' for x in checks),'failed':sum(x['status']=='FAIL' for x in checks),'total':len(checks)},'platform_memory_configuration':{'role':'zero-return stub','entry_rva':'0x1e0 / instruction RVA 0x1e0?','observed':'xor eax,eax; ret; no calls'},'amd_mem_am4_pei':{'entry':'0x240 -> call 0x876 -> jmp 0x2f6','helper_0x876':{'calls':['0xdde','0x5f1','0xb09','0xcd9'],'service_argument_literals':['0x9e3b14c','0x80000000','0x61','0xff']},'handoff_checks':['0x424f5041 (APOB)','0x50535024 ($PSP)','0x44484224 ($BHD)'],'checksum_helpers':['0xbc9','0xbe2'],'main_protocol_method_offsets':['+0x4c','+0x18']},'conclusion':'AmdMemAm4Pei is a PSP/APOB/BHD validation and protocol handoff wrapper; PlatformMemoryConfigurationPei is a zero-return stub. Neither exposes a direct MemoryClockSpeed enum/training write. The missing edge is the opaque service/AGESA/PSP memory-init consumer reached through AmdMem protocol methods and/or APOB structures.', 'limitations':['No service GUID names recovered from this bounded window; literals are preserved exactly.','No exact clv Setup+0x316-to-APOB field edge proven.','No firmware execution, memory training, hardware, clock, voltage, or settings action.'],'checks_detail':checks}
(OUT/'mem-init-controlflow-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':result['status'],'checks':result['checks'],'platform_role':result['platform_memory_configuration']['role'],'amd_role':result['amd_mem_am4_pei']['role'] if 'role' in result['amd_mem_am4_pei'] else 'PSP/APOB/BHD handoff wrapper','conclusion':result['conclusion']},sort_keys=True));sys.exit(0 if result['status']=='PASS' else 1)
