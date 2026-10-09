#!/usr/bin/env python3
"""Independent raw-byte check of adjacent 0x1331/0x1332 serializers."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
CBS=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/CbsBasePei-6ff112922ad8.bin'
SMU=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/AmdNbioSmuV10Pei-905b8be68afd.bin'
MEM=ROOT/'memory/oc-recheck.md'
EXPECTED={ROM:'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8',CBS:'6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77',SMU:'905b8be68afd1dce5453acef8273cbf94bdae6d41823c25438ace286348e2c80',MEM:'33fc15ec83a877a5f0e73b2411467b8a619e479b2d4c44ea18ebfbd4a6436802'}
def sha(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1<<20),b''):h.update(c)
 return h.hexdigest()
checks=[]
def ck(c,l,d=None):checks.append({'label':l,'status':'PASS' if c else 'FAIL','details':d});return c
for p,w in EXPECTED.items():ck(sha(p)==w,'hash:'+str(p),{'observed':sha(p),'expected':w})
clv=ROM.read_bytes();base=0x4cf
ck(clv[base+0x6a2]==0x0f and clv[base+0x6a3]==0x0f,'clv-adjacent-body-bytes',{'0x6a2':hex(clv[base+0x6a2]),'0x6a3':hex(clv[base+0x6a3])})
# TE .text instruction RVA to raw file offset is independently known from module map: raw = RVA - 0x190.
def raw_window(p,rva,n):
 b=p.read_bytes();return b[rva-0x190:rva-0x190+n]
windows={
 'CbsBasePei':(CBS,{0xd9ce:'8a82a2060000',0xd9e0:'ba31130000',0xda00:'8a82a3060000',0xda12:'ba32130000'}),
 'AmdNbioSmuV10Pei':(SMU,{0xfa4e:'8a82a2060000',0xfa60:'ba31130000',0xfa80:'8a82a3060000',0xfa92:'ba32130000'}),
}
for name,(p,ws) in windows.items():
 for r,expected in ws.items():
  obs=raw_window(p,r,len(bytes.fromhex(expected))).hex();ck(obs==expected,f'{name}-raw-rva-{r:#x}',{'raw_offset':hex(r-0x190),'observed':obs,'expected':expected})
result={'status':'PASS' if all(x['status']=='PASS' for x in checks) else 'FAIL','checks':{'passed':sum(x['status']=='PASS' for x in checks),'failed':sum(x['status']=='FAIL' for x in checks),'total':len(checks)},'correction':{'superseded_claim':'Setup+0x6A3 -> token 0x1331','corrected_mapping':'Setup+0x6A2 -> token 0x1331; Setup+0x6A3 -> token 0x1332','sources':['CbsBasePei','AmdNbioSmuV10Pei']},'checks_detail':checks,'limitations':['Serializer record IDs are handoff identifiers; no downstream consumer or hardware behavior proven.']}
(OUT/'token-correction-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':result['status'],'checks':result['checks'],'corrected_mapping':result['correction']['corrected_mapping']},sort_keys=True));sys.exit(0 if result['status']=='PASS' else 1)
