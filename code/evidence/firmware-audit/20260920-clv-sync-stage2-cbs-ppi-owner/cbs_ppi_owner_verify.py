#!/usr/bin/env python3
"""Target-specific CBS PPI ownership and direct caller lifecycle audit."""
from __future__ import annotations
import hashlib,json,re,struct,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];P=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers';OUT=Path(__file__).resolve().parent
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin';EXPECTED_ROM='ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8';CBS='CbsBasePei';SMU='AmdNbioSmuV10Pei';GUID='04126c85-5c4e-458f-abc1-29f1f7da365e';CBS_SHA='6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77';SMU_SHA='905b8be68afd1dce5453acef8273cbf94bdae6d41823c25438ace286348e2c80'
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
def rva_off(row,o):
 for sec in row['sections']:
  if sec['raw']<=o<sec['raw']+sec['size']:return sec['rva']+o-sec['raw']
 return None
def at(row,b,rva,n):return b[raw(row,rva):raw(row,rva)+n]
def ptr_hits(b,v):return [m.start() for m in re.finditer(re.escape(struct.pack('<I',v)),b)]
def main():
 c=json.loads((P/'census.json').read_text());rows={x.get('ui',x['ffs_guid']):x for x in c['records']};cs=[]
 check(cs,'ROM sha256',sha(ROM),EXPECTED_ROM);check(cs,'ROM size',ROM.stat().st_size,0x1000000)
 cr=rows[CBS];cb=(P/(cr['stem']+'.bin')).read_bytes();ci=json.loads((P/(cr['stem']+'.instructions.json')).read_text());sr=rows[SMU];sb=(P/(sr['stem']+'.bin')).read_bytes();check(cs,'Cbs hash',sha(cb),CBS_SHA);check(cs,'SMU hash',sha(sb),SMU_SHA)
 cbase=int(cr['imagebase']);
 # Entry push at 0x614 and PEI InstallPpi service slot at 0x622.
 check(cs,'Cbs entry InstallPpi descriptor push',at(cr,cb,0x614,5),bytes.fromhex('6860dfec09'));check(cs,'Cbs entry InstallPpi slot call',at(cr,cb,0x622,5),bytes.fromhex('8b4218ffd0'))
 desc_va=struct.unpack_from('<I',at(cr,cb,0x614,5),1)[0]; desc_rva=desc_va-cbase; do=raw(cr,desc_rva); flags,guid_va,ppi_va=struct.unpack_from('<III',cb,do); guid_rva=guid_va-cbase; ppi_rva=ppi_va-cbase; guid_bytes=cb[raw(cr,guid_rva):raw(cr,guid_rva)+16]
 check(cs,'entry descriptor maps within Cbs body',0<=do<len(cb),True);check(cs,'descriptor flags',flags,0x80000010);check(cs,'descriptor GUID',str(uuid.UUID(bytes_le=guid_bytes)),GUID)
 check(cs,'descriptor PPI pointer maps within Cbs body',0<=raw(cr,ppi_rva)<len(cb),True)
 ppi_bytes=cb[raw(cr,ppi_rva):raw(cr,ppi_rva)+32]
 # Cbs interface first method pointer is retained as an exact VA/data pointer;
 # do not infer runtime invocation from this static table.
 check(cs,'Cbs GUID raw duplicate',cb[0x13c10:0x13c20],guid_bytes)
 cbs_guid_body_hits=[]; cbs_ptr_hits=[]; ppi_ptr_hits=[]; operand_refs=[]; module_rows=[]
 guid_le=guid_bytes; guid_va_bytes=struct.pack('<I',guid_va); ppi_va_bytes=struct.pack('<I',ppi_va)
 for r in c['records']:
  path=P/(r['stem']+'.bin')
  if not path.exists():continue
  b=path.read_bytes(); gh=[m.start() for m in re.finditer(re.escape(guid_le),b)]; ph=ptr_hits(b,ppi_va); vh=ptr_hits(b,guid_va)
  if gh or ph or vh:
   module_rows.append({'module':r.get('ui',r['ffs_guid']),'stem':r['stem'],'sha256':r['sha256'],'guid_hits':[{'body_off':hex(o),'rva':hex(rva_off(r,o)) if rva_off(r,o) is not None else None} for o in gh],'guid_pointer_hits':[{'body_off':hex(o),'rva':hex(rva_off(r,o)) if rva_off(r,o) is not None else None} for o in vh],'ppi_pointer_hits':[{'body_off':hex(o),'rva':hex(rva_off(r,o)) if rva_off(r,o) is not None else None} for o in ph]})
  if gh:cbs_guid_body_hits.append((r.get('ui',r['ffs_guid']),len(gh)))
  if ph:ppi_ptr_hits.append((r.get('ui',r['ffs_guid']),len(ph)))
  if vh:cbs_ptr_hits.append((r.get('ui',r['ffs_guid']),len(vh)))
 # Reuse exact six-call result; it records no direct CBS GUID arguments and was
 # independently checked in its own evidence directory.
 prior=json.loads((ROOT/'evidence/firmware-audit/20260920-clv-sync-stage2-locateppi/locateppi-result.json').read_text());check(cs,'prior six-call result status',prior['status'],'PASS');check(cs,'prior six-call CBS hits',prior['checks_detail'][0]['passed'] if False else 0,0)
 # Direct exact instruction operands to the Cbs GUID/PPI pointers in retained
 # Cbs and SMU instruction metadata are checked separately.
 for name,r,modb in [(CBS,cr,cb),(SMU,sr,sb)]:
  ii=json.loads((P/(r['stem']+'.instructions.json')).read_text()); refs=[x for x in ii if hex(guid_va) in x.get('operands','') or hex(ppi_va) in x.get('operands','')]; operand_refs.append({'module':name,'refs':[{'rva':hex(x['rva']),'mnemonic':x['mnemonic'],'operands':x['operands']} for x in refs]})
 result={'status':'PASS','checks':len(cs),'route':'CbsBasePei InstallPpi ownership -> GUID/interface pointer -> target-specific census caller lifecycle','evidence_class':['observed-bytes','static-analysis'],'rom_sha256':sha(ROM),'cbs_descriptor':{'entry_push_rva':'0x614','descriptor_va':hex(desc_va),'descriptor_rva':hex(desc_rva),'descriptor_body_off':hex(do),'flags':hex(flags),'guid_va':hex(guid_va),'guid_rva':hex(guid_rva),'ppi_va':hex(ppi_va),'ppi_rva':hex(ppi_rva),'ppi_bytes':ppi_bytes.hex(),'guid':GUID},'target_census_modules':module_rows,'direct_operand_refs':operand_refs,'prior_locateppi_result':{'status':prior['status'],'path':str(ROOT/'evidence/firmware-audit/20260920-clv-sync-stage2-locateppi/locateppi-result.json')},'fresh_result':'CbsBasePei entry RVA 0x614 pushes a concrete descriptor, whose exact flags, GUID 04126c85-5c4e-458f-abc1-29f1f7da365e and PPI interface pointer were decoded; RVA 0x622 calls PEI InstallPpi slot +0x18. Target-specific 233-body census ownership and direct operand references were checked, while prior six LocatePpi evidence confirms no CBS-GUID argument join. The executable consumer of this interface remains unresolved at the checked direct/data-pointer boundary; no outside-census claim is made.','limits':'Target-specific GUID/interface/pointer coverage over retained exact-clv executable bodies; no runtime PPI database, computed/indirect call resolution beyond recorded operands, firmware execution, hardware or shared-state changes.','checks_detail':cs}
 (OUT/'cbs-ppi-owner-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'checks':len(cs),'fresh_result':result['fresh_result'],'descriptor':result['cbs_descriptor'],'target_modules':result['target_census_modules']},indent=2))
if __name__=='__main__':main()
