#!/usr/bin/env python3
"""Independent bounded review of Fabric reader values and PEI slot-0x44 provenance."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
FAB=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/AmdFabricAriPei-c5b99650a442.instructions.json'
FABBIN=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/AmdFabricAriPei-c5b99650a442.bin'
HOB=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/AmdMemoryHobInfoPeim-aad3f828ccef.instructions.json'
SLOTS=ROOT/'evidence/firmware-audit/20260920-clv-sync-stage2-memclk-consumer/edk2-PiPeiCis-service-slots.txt'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return {int(x['rva']):x for x in json.loads(p.read_text())}
def ck(c,label,got,exp):
 ok=got==exp; checks.append({'label':label,'status':'PASS' if ok else 'FAIL','got':got,'expected':exp}); return ok
checks=[]
romsha=sha(ROM); ck(checks,'clv-hash',romsha,'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'); ck(checks,'fabric-hash',sha(FABBIN),'c5b99650a442ed9be1cf3a62e7571f7eb163b9f80a60d4fcc7b3e9afe4506f78'); ck(checks,'pei-service-layout-hash',sha(SLOTS),'174ca8378bef20d86a51164b9fba55a68e0d187f429f59e5734c9be637196fbe')
fab=load(FAB); hob=load(HOB)
# Reader writes returned u32 values through caller-provided output pointer, then compares token.
for r,b in {0x1d3c:'55',0x1d3d:'8bec',0x1d3f:'83ec24',0x1e38:'8b4603',0x1e3b:'8907',0x1e3d:'8b4607',0x1e40:'894704',0x1e67:'668b06',0x1e6a:'663b4508',0x1e6e:'740c',0x1e70:'03f3',0x1eb0:'68ff100000',0x1ebd:'e87afeffff',0x1ec7:'8b4c2410',0x1ecb:'8b442414',0x1f8b:'6804110000',0x1f94:'e8a3fdffff',0x1f9e:'8b442408',0x1fa2:'0b44240c'}.items():
 ck(checks,f'Fabric:{hex(r)}',fab.get(r,{}).get('bytes'),b)
# Complete parent slices contain no direct WRMSR/in/out; transitive helper/MMIO remains unknown.
for r in [0x1ec2,0x1f99]: ck(checks,f'Fabric-parent-return:{hex(r)}',fab.get(r) is not None,True)
parent_ops=[]
for x in fab.values():
 r=int(x['rva']);
 if 0x1e8f<=r<=0x1fdd and x.get('mnemonic') in ('wrmsr','in','out'): parent_ops.append(x)
ck(checks,'Fabric-parent-direct-hardware-op-count',len(parent_ops),0)
# IDS table bytes as exact existing artifact.
raw=FABBIN.read_bytes(); ck(checks,'Fabric-IDS-table',raw[0x16bc4:0x16bc4+24].hex(),'030000200fdae10904000020eddae109ffffffffffffffff')
# AmdMemoryHobInfoPeim: ESI is PEI services pointer-to-pointer; [ESI] table, table+0x44 InstallPeiMemory.
for r,b in {0x269:'8bf0',0x26b:'8b06',0x299:'ff5044',0x2a7:'395c2420'}.items(): ck(checks,f'AmdMemoryHob:{hex(r)}',hob.get(r,{}).get('bytes'),b)
# Source layout marks InstallPeiMemory before AllocatePool.
slot_text=SLOTS.read_text(); ck(checks,'EDK2-slot-InstallPeiMemory', 'EFI_PEI_INSTALL_PEI_MEMORY' in slot_text,True); ck(checks,'EDK2-slot-AllocatePool-after', 'EFI_PEI_ALLOCATE_POOL' in slot_text,True)
result={'status':'PASS' if all(x['status']=='PASS' for x in checks) else 'FAIL','checks':{'passed':sum(x['status']=='PASS' for x in checks),'failed':sum(x['status']=='FAIL' for x in checks),'total':len(checks)},'fabric':{'reader_output':'u32 store through caller pointer at 0x1E38; parent 0x1E8F reads [esp+0x10]/[esp+0x14] after 0x10FF, parent 0x1F6D reads [esp+0x8]/[esp+0xC] after 0x1104','ids_events':{'0x20000003':'0x1E8F','0x20000004':'0x1F6D'},'direct_hardware_ops_in_slices':[]},'pei_hob':{'module':'AmdMemoryHobInfoPeim','rva_0x269':'ESI=EAX (PEI services pointer-to-pointer)','rva_0x26B':'EAX=[ESI] (service table dereference)','rva_0x299':'call [EAX+0x44] (InstallPeiMemory)', 'source_layout':'EFI_PEI_SERVICES lists InstallPeiMemory before AllocatePool'},'conclusion':'Fabric direct readers 0x10FF/0x1104 use returned stack values in AGESA/IDS handlers with no direct WRMSR/in/out in the checked parent slices. Transitive helper/MMIO effects remain unknown; corrected FCLK 0x1331/UCLK 0x1204/MemoryPstate 0x123C requester remains unresolved. AmdMemoryHobInfoPeim uses PEI services ** and slot +0x44 for InstallPeiMemory, not slot +0x4C.', 'limitations':['No firmware execution or hardware.','No absence claim outside complete checked parent slices.','No clock/training semantics inferred from IDS or PPI outputs.'],'checks_detail':checks}
(OUT/'fabric-hob-review-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps({'status':result['status'],'checks':result['checks'],'conclusion':result['conclusion']},sort_keys=True)); raise SystemExit(0 if result['status']=='PASS' else 1)
