#!/usr/bin/env python3
"""Trace adjacent INV record ownership by destination-pointer stores, not nearest RVA."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
MODS={
 'CbsBasePei':ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/CbsBasePei-6ff112922ad8.bin',
 'AmdNbioSmuV10Pei':ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/AmdNbioSmuV10Pei-905b8be68afd.bin',
}
INS={n:ROOT/f'evidence/firmware-audit/20260919-inv-token-consumers/{p}.instructions.json' for n,p in [('CbsBasePei','CbsBasePei-6ff112922ad8'),('AmdNbioSmuV10Pei','AmdNbioSmuV10Pei-905b8be68afd')]}
OUT=Path(__file__).resolve().parent/'record-ownership-result.json'
EXPECTED_ROM='ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
EXPECTED_MOD={'CbsBasePei':'6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77','AmdNbioSmuV10Pei':'905b8be68afd1dce5453acef8273cbf94bdae6d41823c25438ace286348e2c80'}
# Each row is one destination record block: header -> source load -> dest+3 store -> pointer +4.
BLOCKS={
 'CbsBasePei':[
  {'token':0x1330,'header':0xd9ae,'source':0xd9ce,'src_off':0x6a2,'store':0xd9d4,'inc':0xd9da},
  {'token':0x1331,'header':0xd9e0,'source':0xda00,'src_off':0x6a3,'store':0xda06,'inc':0xda0c},
  {'token':0x1332,'header':0xda12,'source':0xda32,'src_off':0x6a4,'store':0xda38,'inc':0xda3e},
  {'token':0x1333,'header':0xda44,'source':0xda64,'src_off':0x6a5,'store':0xda6a,'inc':0xda70},
 ],
 'AmdNbioSmuV10Pei':[
  {'token':0x1330,'header':0xfa2e,'source':0xfa4e,'src_off':0x6a2,'store':0xfa54,'inc':0xfa5a},
  {'token':0x1331,'header':0xfa60,'source':0xfa80,'src_off':0x6a3,'store':0xfa86,'inc':0xfa8c},
  {'token':0x1332,'header':0xfa92,'source':0xfab2,'src_off':0x6a4,'store':0xfab8,'inc':0xfabe},
 ]
}
checks=[]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ck(label,ok,details=None): checks.append({'label':label,'status':'PASS' if ok else 'FAIL','details':details})
check_rom=sha(ROM); ck('rom-hash',check_rom==EXPECTED_ROM,{'observed':check_rom,'expected':EXPECTED_ROM})
allmaps={}
for name,p in MODS.items():
 b=sha(p); ck(f'{name}-hash',b==EXPECTED_MOD[name],{'observed':b,'expected':EXPECTED_MOD[name]})
 ins={x['rva']:x for x in json.loads(INS[name].read_text())}; maps=[]
 for row in BLOCKS[name]:
  h=ins.get(row['header']); s=ins.get(row['source']); st=ins.get(row['store']); inc=ins.get(row['inc'])
  exp_h=f'ba{row["token"] & 0xff:02x}{(row["token"]>>8)&0xff:02x}0000'
  exp_s='8a82'+row['src_off'].to_bytes(4,'little').hex()
  checks0=[h and h['bytes']==exp_h,s and s['bytes']==exp_s,st and st['bytes']=='884103',inc and inc['bytes']=='83c104']
  ck(f'{name}-record-{row["token"]:04x}-owned-by-source-{row["src_off"]:#x}',all(checks0),{'header':h,'source':s,'store':st,'increment':inc})
  maps.append({'token':hex(row['token']),'source_setup_offset':hex(row['src_off']),'header_rva':hex(row['header']),'source_rva':hex(row['source']),'store_rva':hex(row['store']),'increment_rva':hex(row['inc']),'ownership_basis':'same destination pointer [ebp-0x8] is used for header, flags, source+3 store; +4 increment follows store'})
 allmaps[name]=maps
# Explicit discriminating assertion.
for name,maps in allmaps.items():
 target=next(x for x in maps if x['source_setup_offset']=='0x6a3')
 ck(f'{name}-FclkDpm-token1331',target['token']=='0x1331',target)
result={'status':'PASS' if all(x['status']=='PASS' for x in checks) else 'FAIL','checks':{'passed':sum(x['status']=='PASS' for x in checks),'failed':sum(x['status']=='FAIL' for x in checks),'total':len(checks)},'ownership':allmaps,'correction':{'superseded':'nearest-RVA pairing of +0x6A3 with token 0x1332','corrected':'destination-pointer dataflow pairs +0x6A3 with token 0x1331; +0x6A4 with token 0x1332'},'limits':['Static instruction/dataflow ownership only; no downstream consumer, units, training, physical clock, or hardware behavior.'],'checks_detail':checks}
OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':result['status'],'checks':result['checks'],'fclk_dpm_token':'0x1331','output':str(OUT.resolve())},sort_keys=True))
raise SystemExit(0 if result['status']=='PASS' else 1)
