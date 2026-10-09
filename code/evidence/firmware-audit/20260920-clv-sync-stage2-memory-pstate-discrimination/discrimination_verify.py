#!/usr/bin/env python3
"""Narrow static distinction among Memory P-state, Phy Power Saving, FCLK_DPM."""
import hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; OUT=Path(__file__).resolve().parent
CLV=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
ULT=ROOT/'evidence/firmware-audit/20260920-clv-sync-stage1/archive-members/ultimate.rar/03_BC250_ULTIMATE_LOW_LATENCY_StockCPU.bin'
BASE_INS=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/CbsBasePei-6ff112922ad8.instructions.json'
BASE_BIN=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/CbsBasePei-6ff112922ad8.bin'
MENU_TXT=ROOT/'evidence/firmware-audit/20260920-df-init-route/menu-CbsSetupDxe.txt'
EXPECTED={'clv':('ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8',CLV),'ultimate':('578113a9c9c02f0ab98fa896cf61356664e1429f7054de3c308810bcd4770896',ULT),'cbsbase':('6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77',BASE_BIN),'menu':('f71c97ed6041a0c9a4260f651c093bd7873cc33222b124830b0728107cfb6084',MENU_TXT)}
def sha(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1<<20),b''):h.update(c)
 return h.hexdigest()
checks=[]
def ck(c,l,d=None):checks.append({'label':l,'status':'PASS' if c else 'FAIL','details':d});return c
for n,(want,p) in EXPECTED.items(): ck(sha(p)==want,'hash:'+n,{'observed':sha(p),'expected':want})
clv=CLV.read_bytes();ult=ULT.read_bytes();base=0x4cf
fields={'PhyPowerSaving':0x368,'MemoryPstate':0x36d,'FclkDpm':0x6a3}
values={k:{'body_offset':hex(o),'absolute_clv':hex(base+o),'clv':clv[base+o],'ultimate':ult[base+o]} for k,o in fields.items()}
# Explicit expected pair checks (FCLK_DPM uses Auto=0x0F, unlike UMC bytes).
expected_pairs={'PhyPowerSaving':(0xff,0),'MemoryPstate':(0xff,0),'FclkDpm':(0x0f,0)}
for k,x in values.items(): ck((x['clv'],x['ultimate'])==expected_pairs[k],f'profile-byte-pair:{k}',x)
text=MENU_TXT.read_text()
menu_lines={
 'PhyPowerSaving':["ONE_OF @form='DRAM Power Options' qid=0x259 var=AmdSetup+0x368 flags=0x10 'Phy Power Saving'","OPTION 'Auto' = 0xff","OPTION 'Enabled' = 0x1","OPTION 'Disabled' = 0x0"],
 'MemoryPstate':["ONE_OF @form='DRAM Power Options' qid=0x25e var=AmdSetup+0x36d flags=0x10 'Memory P-state'","OPTION 'Auto' = 0xff","OPTION 'Enabled' = 0x1","OPTION 'Disabled' = 0x0"],
 'FclkDpm':["ONE_OF @form='SMU Features' qid=0x7045 var=AmdSetup+0x6a3 flags=0x14 'FCLK_DPM'","OPTION 'Disabled' = 0x0","OPTION 'Enabled' = 0x1","OPTION 'Auto' = 0xf"],
}
for k,ls in menu_lines.items(): ck(all(x in text for x in ls),f'IFR-label-enum:{k}',ls)
ins={int(x['rva']):x for x in json.loads((ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/CbsBasePei-6ff112922ad8.instructions.json').read_text())}
exact={0x1d42:'c68068030000ff',0x1d74:'c6826d030000ff',0x294b:'c682a30600000f',0xa6c7:'ba37120000',0xa6e7:'8a8268030000',0xa6ed:'884103',0xa7c1:'ba3c120000',0xa7e1:'8a826d030000',0xa7e7:'884103',0xd9e0:'ba31130000',0xda00:'8a82a3060000',0xda06:'884103'}
for r,b in exact.items():ck(r in ins and ins[r]['bytes']==b,f'CbsBase-byte:{r:#x}',{'observed':ins.get(r),'expected':b})
record_map={'PhyPowerSaving':'0x1237','MemoryPstate':'0x123c','FclkDpm':'0x1331'}
result={'status':'PASS' if all(x['status']=='PASS' for x in checks) else 'FAIL','checks':{'passed':sum(x['status']=='PASS' for x in checks),'failed':sum(x['status']=='FAIL' for x in checks),'total':len(checks)},'evidence_class':['observed-bytes','static-analysis'],'profiles':values,'ifr_mapping':{'PhyPowerSaving':{'offset':'0x368','qid':'0x259','flags':'0x10','record':record_map['PhyPowerSaving']},'MemoryPstate':{'offset':'0x36d','qid':'0x25e','flags':'0x10','record':record_map['MemoryPstate']},'FclkDpm':{'offset':'0x6a3','qid':'0x7045','flags':'0x14','record':record_map['FclkDpm']}},'interpretation':['Memory P-state +0x36D is distinct from Phy Power Saving +0x368 and FCLK_DPM +0x6A3.','Historical ULTIMATE sets all three bytes to 0; filename does not identify which control satisfies DF help.','Record IDs are serializer handoff identifiers; downstream hardware/training application is unknown.','UI help is guidance, not a hardware constraint.'],'checks_detail':checks}
(OUT/'discrimination-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':result['status'],'checks':result['checks'],'profiles':values,'records':record_map},sort_keys=True));sys.exit(0 if result['status']=='PASS' else 1)
