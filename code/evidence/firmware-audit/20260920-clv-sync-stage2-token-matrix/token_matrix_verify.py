#!/usr/bin/env python3
"""Compact raw-byte serializer matrix for requested AmdSetup clock fields."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
CBS=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/CbsBasePei-6ff112922ad8.bin'
SMU=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/AmdNbioSmuV10Pei-905b8be68afd.bin'
EXPECTED={ROM:'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8',CBS:'6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77',SMU:'905b8be68afd1dce5453acef8273cbf94bdae6d41823c25438ace286348e2c80'}
def sha(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1<<20),b''):h.update(c)
 return h.hexdigest()
def ck(c,l,d=None):checks.append({'label':l,'status':'PASS' if c else 'FAIL','details':d});return c
def raw(p,rva,n):
 b=p.read_bytes();return b[rva-0x190:rva-0x190+n]
checks=[]
for p,w in EXPECTED.items():ck(sha(p)==w,'hash:'+str(p),{'observed':sha(p),'expected':w})
clv=ROM.read_bytes();base=0x4cf
fields=[
 {'name':'MemoryClockSpeed','offset':'0x316','width':'u8','clv_bytes':'24','clv_value':clv[base+0x316],'record':'0x11ed','cbs':[(0x9837,'baed110000'),(0x9857,'8a8216030000')],'smu':[(0xb8b7,'baed110000'),(0xb8d7,'8a8216030000')]},
 {'name':'UclkDiv1M0','offset':'0x330','width':'u8','clv_bytes':'01','clv_value':clv[base+0x330],'record':'0x1204','cbs':[(0x9cc4,'ba04120000'),(0x9ce4,'8a8230030000')],'smu':[(0xbd44,'ba04120000'),(0xbd64,'8a8230030000')]},
 {'name':'FclkDpm','offset':'0x6a3','width':'u8','clv_bytes':'0f','clv_value':clv[base+0x6a3],'record':'0x1331','cbs':[(0xd9e0,'ba31130000'),(0xda00,'8a82a3060000'),(0xda06,'884103'),(0xda12,'ba32130000'),(0xda32,'8a82a4060000'),(0xda38,'884103')],'smu':[(0xfa60,'ba31130000'),(0xfa80,'8a82a3060000'),(0xfa86,'884103'),(0xfa92,'ba32130000'),(0xfab2,'8a82a4060000'),(0xfab8,'884103')]},
 {'name':'DfClockOverrideControl','offset':'0x703','width':'u8','clv_bytes':'01','clv_value':clv[base+0x703],'record':'0x1373','cbs':[(0xe706,'ba73130000'),(0xe726,'8a8203070000')],'smu':[(0x10786,'ba73130000'),(0x107a6,'8a8203070000')]},
 {'name':'DfClockOvrd','offset':'0x704','width':'u16','clv_bytes':'8c05','clv_value':int.from_bytes(clv[base+0x704:base+0x706],'little'),'record':'0x1374','cbs':[(0xe738,'ba74130000'),(0xe75b,'668b8204070000')],'smu':[(0x107b8,'ba74130000'),(0x107db,'668b8204070000')]},
]
for f in fields:
 off=base+int(f['offset'],16); n=len(bytes.fromhex(f['clv_bytes']))
 ck(f['clv_bytes']==clv[off:off+n].hex(),'clv-byte:'+f['offset'],f)
 ck(f['clv_value']==({'0x316':36,'0x330':1,'0x6a3':15,'0x703':1,'0x704':1420}[f['offset']]),'clv-value:'+f['offset'],f['clv_value'])
 for name,p,key in [('CbsBasePei',CBS,'cbs'),('AmdNbioSmuV10Pei',SMU,'smu')]:
  for rva,expected in f[key]:
   obs=raw(p,rva,len(bytes.fromhex(expected))).hex();ck(obs==expected,f'{name}:{f["offset"]}:rva-{rva:#x}',{'raw_offset':hex(rva-0x190),'observed':obs,'expected':expected})
# Adjacent dataflow witness: header 0x1331 is followed by +6A3 load/store;
# header 0x1332 is followed by +6A4 load/store. The preceding +6A2 value
# belongs to header 0x1330.
for name,p,rva_load,rva_id in [('CbsBasePei',CBS,0xd9ce,0xd9ae),('AmdNbioSmuV10Pei',SMU,0xfa4e,0xfa2e)]:
    ck(raw(p,rva_load,6).hex()=='8a82a2060000',name+':neighbor-6a2-load')
    ck(raw(p,rva_id,5).hex()=='ba30130000',name+':neighbor-token-1330')
result={'status':'PASS' if all(x['status']=='PASS' for x in checks) else 'FAIL','checks':{'passed':sum(x['status']=='PASS' for x in checks),'failed':sum(x['status']=='FAIL' for x in checks),'total':len(checks)},'matrix':[{k:f[k] for k in ['name','offset','width','clv_bytes','clv_value','record']} for f in fields],'serializer_provenance':{'CbsBasePei':'raw instruction windows, rva->raw rva-0x190','AmdNbioSmuV10Pei':'raw instruction windows, rva->raw rva-0x190'},'limitations':['Record IDs are serializer handoff identifiers; downstream consumers, units, training, clocks, and hardware acceptance remain unknown.'],'checks_detail':checks}
(OUT/'token-matrix-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':result['status'],'checks':result['checks'],'matrix':result['matrix']},sort_keys=True));sys.exit(0 if result['status']=='PASS' else 1)
