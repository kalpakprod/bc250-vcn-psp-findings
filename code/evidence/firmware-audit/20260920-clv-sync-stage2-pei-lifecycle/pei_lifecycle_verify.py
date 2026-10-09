#!/usr/bin/env python3
"""One-module PEI entry/lifecycle reconstruction for AmdNbioSmuV10Pei."""
from __future__ import annotations
import hashlib,json,re,struct,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
P=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers'; OUT=Path(__file__).resolve().parent
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'; EXPECTED_ROM='ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
NAME='AmdNbioSmuV10Pei'; EXPECTED_SHA='905b8be68afd1dce5453acef8273cbf94bdae6d41823c25438ace286348e2c80'
def sha(v):
 if isinstance(v,(bytes,bytearray)):return hashlib.sha256(v).hexdigest()
 return hashlib.sha256(v.read_bytes()).hexdigest()
def check(cs,n,g,e):
 ok=g==e
 def s(v):
  if isinstance(v,(bytes,bytearray)):return v.hex()
  if isinstance(v,tuple):return list(v)
  return v
 cs.append({'check':n,'passed':ok,'got':s(g),'expected':s(e)})
 if not ok:raise AssertionError(f'{n}: got {g!r}, expected {e!r}')
def raw(row,rva):
 for sec in row['sections']:
  if sec['rva']<=rva<sec['rva']+sec['size']:return rva-sec['rva']+sec['raw']
 raise ValueError(hex(rva))
def rva_for_off(row,o):
 for sec in row['sections']:
  if sec['raw']<=o<sec['raw']+sec['size']:return sec['rva']+o-sec['raw']
 return None
def at(row,b,rva,n):return b[raw(row,rva):raw(row,rva)+n]
def direct(x):return x.get('mnemonic','').startswith('call') and re.fullmatch(r'0x[0-9a-f]+',x.get('operands',''))
def main():
 c=json.loads((P/'census.json').read_text()); row=next(x for x in c['records'] if x.get('ui')==NAME); body=(P/(row['stem']+'.bin')).read_bytes(); ins=json.loads((P/(row['stem']+'.instructions.json')).read_text()); cs=[]
 check(cs,'ROM sha256',sha(ROM),EXPECTED_ROM);check(cs,'ROM size',ROM.stat().st_size,0x1000000);check(cs,'module sha256',sha(body),EXPECTED_SHA);check(cs,'module type',row['type'],'TE');check(cs,'module size',len(body),row['size'])
 # Entrypoint/section identity is preserved from census metadata; no new
 # disassembler project or relocation rewrite is performed.
 metadata={k:row.get(k) for k in ('ui','ffs_guid','type','imagebase','delta','size','sections','entrypoint','entry','guid','dependencies') if k in row}
 # PEI service slots: +0x18 InstallPpi, +0x20 LocatePpi in project mapping.
 service18=[x for x in ins if x.get('mnemonic','').startswith('call') and x.get('operands') in ('DWORD PTR [eax+0x18]','DWORD PTR [ecx+0x18]')]
 service20=[x for x in ins if x.get('mnemonic','').startswith('call') and x.get('operands') in ('DWORD PTR [eax+0x20]','DWORD PTR [ecx+0x20]')]
 check(cs,'InstallPpi-slot candidate count',len(service18),2)
 check(cs,'LocatePpi-slot candidate count',len(service20),6)
 contexts=[]
 for x in service18:
  i=ins.index(x); before=ins[max(0,i-18):i]; contexts.append({'call_rva':hex(x['rva']),'call_bytes':at(row,body,x['rva'],3).hex(),'preceding':[{k:z.get(k) for k in ('rva','bytes','mnemonic','operands')} for z in before]})
 # Static descriptor signatures (EFI_PEI_PPI_DESCRIPTOR flags 0x80000010).
 sig=struct.pack('<I',0x80000010); hits=[m.start() for m in re.finditer(re.escape(sig),body)]
 ppi=[]
 for o in hits:
  rva=rva_for_off(row,o); words=struct.unpack_from('<III',body,o) if o+12<=len(body) else ()
  ppi.append({'body_off':hex(o),'rva':hex(rva) if rva is not None else None,'words':[hex(x) for x in words]})
 check(cs,'static PPI descriptor signature count',len(hits)>0,True)
 # Actual entrypoint InstallPpi argument construction: two static descriptor
 # pointers are pushed before the PEI-services +0x18 calls.
 check(cs,'entrypoint RVA',row.get('entry'),0x240)
 check(cs,'InstallPpi call RVAs',[x['rva'] for x in service18],[0x26b,0x28f])
 first_push=bytes.fromhex('68fcebe90956ff5018'); second_push=bytes.fromhex('6814ece90956ff5018')
 check(cs,'first InstallPpi descriptor push',at(row,body,0x265,len(first_push)),first_push)
 check(cs,'second InstallPpi descriptor push',at(row,body,0x289,len(second_push)),second_push)
 def guid_at(rva):
  return str(uuid.UUID(bytes_le=body[raw(row,rva):raw(row,rva)+16]))
 check(cs,'installed PPI #1 GUID',guid_at(0x159f0),'ea335e48-7275-4d2b-8276-55ba5531d7d7')
 check(cs,'installed PPI #2 GUID',guid_at(0x159e0),'8c61c925-224e-42d7-8978-812ae5612d23')
 # This module also retains the same CBS callback PPI GUID as CbsBasePei;
 # compare exact bytes across the two existing bodies, without claiming this
 # descriptor is installed by the two direct entrypoint calls above.
 cbs_row=next(x for x in c['records'] if x.get('ui')=='CbsBasePei'); cbs_body=(P/(cbs_row['stem']+'.bin')).read_bytes()
 smu_cbs_guid=body[raw(row,0x15a50):raw(row,0x15a50)+16]; cbs_guid=cbs_body[0x13c10:0x13c20]
 check(cs,'SMU/CBS PPI GUID equality',smu_cbs_guid,cbs_guid)
 check(cs,'SMU/CBS PPI GUID value',str(uuid.UUID(bytes_le=smu_cbs_guid)),'04126c85-5c4e-458f-abc1-29f1f7da365e')
 check(cs,'CbsBasePei InstallPpi call bytes',at(cbs_row,cbs_body,0x622,5),bytes.fromhex('8b4218ffd0'))
 # Keep only descriptors in the local data neighborhood of the module lifecycle;
 # report all signatures for this one module, not a project-wide scan.
 # GUID-like 16-byte candidates around each descriptor are recorded but not
 # promoted unless pointer ownership is byte-backed.
 guid_candidates=[]
 for o in hits:
  for q in range(max(0,o-0x80),min(len(body)-16,o+0x80),4):
   g=body[q:q+16]
   if g.count(0)<12 and g.count(0xff)<12:
    guid_candidates.append({'body_off':hex(q),'rva':hex(rva_for_off(row,q)) if rva_for_off(row,q) is not None else None,'bytes':g.hex()})
 # Identify exact wrapper descriptor from the known provider registration and
 # verify its pointer ownership in the local PPI-like table neighborhood.
 wrapper=0x5740; desc_off=0x158e0; provider_off=0x15950; base=int(row['imagebase'])
 check(cs,'known callback descriptor',struct.unpack_from('<QQII',body,desc_off),(0xffffffff,0,base+wrapper,0xfffffffe))
 check(cs,'known provider field points descriptor',struct.unpack_from('<I',body,provider_off)[0],base+0x15a70)
 # No claim of installed state: check whether any InstallPpi context pushes a
 # static pointer whose exact value is one of the local descriptor addresses.
 descriptor_vas={base+0x15a70,base+0x15080}; immediate_join=[]
 for ctx in contexts:
  for z in ctx['preceding']:
   if z['mnemonic'] in ('push','mov','lea'):
    if any(hex(v) in z.get('operands','') for v in descriptor_vas):immediate_join.append((ctx['call_rva'],z))
 check(cs,'InstallPpi static-descriptor immediate join',len(immediate_join),0)
 result={'status':'PASS','checks':len(cs),'route':'AmdNbioSmuV10Pei entry/lifecycle: PEI service slots + static PPI descriptor ownership','evidence_class':['observed-bytes','static-analysis'],'rom_sha256':sha(ROM),'module':metadata,'module_sha256':sha(body),'install_ppi_candidates':contexts,'locate_ppi_candidates':[{'rva':hex(x['rva']),'bytes':at(row,body,x['rva'],3).hex(),'operands':x['operands']} for x in service20],'ppi_signatures':ppi,'guid_candidates_near_ppi':guid_candidates[:80],'known_callback_descriptor':{'body_off':hex(desc_off),'rva':'0x15a70','provider_field_body_off':hex(provider_off),'provider_field_rva':'0x15ae0','wrapper_rva':'0x5740','event':'0xfffffffe'},'fresh_result':'AmdNbioSmuV10Pei entry RVA 0x240 contains two concrete InstallPpi-slot calls (0x26B/0x28F) that push static descriptor pointers for GUIDs ea335e48-7275-4d2b-8276-55ba5531d7d7 and 8c61c925-224e-42d7-8978-812ae5612d23. The module also retains the exact CBS PPI GUID 04126c85-5c4e-458f-abc1-29f1f7da365e, byte-identical to CbsBasePei, but this bounded entrypoint path does not directly install that descriptor or join it to the callback descriptor. LocatePpi-slot candidates remain six; installed/invoked callback state is unresolved beyond these concrete PPI registrations.','limits':'One exact PEI module only; no firmware execution, no runtime PPI database, no cross-module protocol resolution, no arbitrary computed pointer/DMA/HOB migration and no hardware claim.','checks_detail':cs}
 (OUT/'pei-lifecycle-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'checks':len(cs),'fresh_result':result['fresh_result']},indent=2))
if __name__=='__main__':main()
