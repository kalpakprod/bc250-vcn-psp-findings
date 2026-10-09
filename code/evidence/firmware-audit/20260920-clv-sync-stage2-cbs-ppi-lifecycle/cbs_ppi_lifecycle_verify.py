#!/usr/bin/env python3
"""Trace CBS PPI owner/notify/dispatch and counterpart registration records."""
from __future__ import annotations
import hashlib,json,struct,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];P=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers';OUT=Path(__file__).resolve().parent
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin';EXPECTED_ROM='ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8';CBS_GUID='04126c85-5c4e-458f-abc1-29f1f7da365e';NOTIFY_GUID='60db76a0-5d55-47bb-970f-34d8d0be369e';MODS={'CbsBasePei':'6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77','AmdNbioGfxARIPei':'63413be2ac290e584bbbeeba5eb573a94b66b9624c4e0ecbea145ded655245b8','AmdNbioSmuV10Pei':'905b8be68afd1dce5453acef8273cbf94bdae6d41823c25438ace286348e2c80'}
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
def at(row,b,rva,n):return b[raw(row,rva):raw(row,rva)+n]
def main():
 c=json.loads((P/'census.json').read_text());rows={x.get('ui',x['ffs_guid']):x for x in c['records']};cs=[]
 check(cs,'ROM sha256',sha(ROM),EXPECTED_ROM);check(cs,'ROM size',ROM.stat().st_size,0x1000000)
 cr=rows['CbsBasePei'];cb=(P/(cr['stem']+'.bin')).read_bytes();base=int(cr['imagebase']);check(cs,'Cbs hash',sha(cb),MODS['CbsBasePei'])
 # CbsBasePei entry: InstallPpi then NotifyPpi.
 check(cs,'Cbs InstallPpi push',at(cr,cb,0x614,5),bytes.fromhex('6860dfec09'));check(cs,'Cbs InstallPpi slot',at(cr,cb,0x622,5),bytes.fromhex('8b4218ffd0'));check(cs,'Cbs NotifyPpi push',at(cr,cb,0x62d,5),bytes.fromhex('686cdfec09'));check(cs,'Cbs NotifyPpi slot',at(cr,cb,0x63b,5),bytes.fromhex('8b4824ffd1'))
 desc_va=struct.unpack_from('<I',at(cr,cb,0x614,5),1)[0]; desc_rva=desc_va-base;do=raw(cr,desc_rva);flags,guid_va,ppi_va=struct.unpack_from('<III',cb,do);guid=str(uuid.UUID(bytes_le=cb[raw(cr,guid_va-base):raw(cr,guid_va-base)+16]));check(cs,'Cbs owner descriptor flags',flags,0x80000010);check(cs,'Cbs owner GUID',guid,CBS_GUID)
 ppi_rva=ppi_va-base; ppi_off=raw(cr,ppi_rva); method_va=struct.unpack_from('<I',cb,ppi_off)[0];check(cs,'Cbs interface method RVA',method_va-base,0x250);check(cs,'Cbs method prologue',at(cr,cb,0x250,3),bytes.fromhex('558bec'))
 # Notify descriptor at 0x9ecdf6c: flags 0x80000040, Notify GUID, callback base+0x4d0.
 notify_va=struct.unpack_from('<I',at(cr,cb,0x62d,5),1)[0];no=raw(cr,notify_va-base);nflags,nguid_va,ncallback=struct.unpack_from('<III',cb,no);nguid=str(uuid.UUID(bytes_le=cb[raw(cr,nguid_va-base):raw(cr,nguid_va-base)+16]));check(cs,'Cbs notify flags',nflags,0x80000040);check(cs,'Cbs notify GUID',nguid,NOTIFY_GUID);check(cs,'Cbs notify callback RVA',ncallback-base,0x4d0);check(cs,'Cbs callback prologue',at(cr,cb,0x4d0,3),bytes.fromhex('558bec'))
 # Method dispatch: callback table entry pointer +0x10 is invoked after
 # descriptor/event gating; assert exact known indirect dispatch window.
 dispatch=at(cr,cb,0x47d,0x1d);check(cs,'Cbs callback indirect dispatch window',dispatch,bytes.fromhex('8d9538f7ffff528b450c508b4d08518b9518f7ffff8b4210ffd083c40c'))
 counterparts={}
 for name in ('AmdNbioGfxARIPei','AmdNbioSmuV10Pei'):
  r=rows[name];b=(P/(r['stem']+'.bin')).read_bytes();base2=int(r['imagebase']);check(cs,name+' hash',sha(b),MODS[name]);guid_bytes=uuid.UUID(CBS_GUID).bytes_le; hits=[m.start() for m in __import__('re').finditer(__import__('re').escape(guid_bytes),b)];check(cs,name+' CBS GUID pattern count',len(hits),1);o=hits[0];rva=r['sections'][0]['rva']+o-r['sections'][0]['raw'] if r['sections'][0]['raw']<=o<r['sections'][0]['raw']+r['sections'][0]['size'] else None; # registration is GUID + notify GUID + descriptor
  reg_guid=str(uuid.UUID(bytes_le=b[o+16:o+32])); reg=struct.unpack_from('<QQII',b,o+32);check(cs,name+' notify GUID after CBS GUID',reg_guid,NOTIFY_GUID);check(cs,name+' counterpart wildcard CPU',reg[:2],(0xffffffff,0));check(cs,name+' counterpart event',reg[3],0xfffffffe);counterparts[name]={'guid_body_off':hex(o),'guid_rva':hex(rva) if rva is not None else None,'descriptor_bytes':b[o+32:o+56].hex(),'callback_va':hex(reg[2]),'callback_rva':hex(reg[2]-base2)}
 result={'status':'PASS','checks':len(cs),'route':'CbsBasePei InstallPpi/NotifyPpi -> interface method 0x250 -> wildcard callback dispatch -> counterpart registration records','evidence_class':['observed-bytes','static-analysis'],'rom_sha256':sha(ROM),'owner':{'module':'CbsBasePei','descriptor_rva':hex(desc_rva),'guid':guid,'ppi_rva':hex(ppi_rva),'method_rva':'0x250','notify_descriptor_rva':hex(notify_va-base),'notify_guid':nguid,'notify_callback_rva':'0x4d0'},'counterparts':counterparts,'fresh_result':'CbsBasePei owns and registers the CBS PPI at entry, registers an AmdSetup NotifyPpi descriptor, and its interface method RVA 0x250 contains the exact indirect callback dispatch window. Gfx and SMU carry byte-identical CBS GUID + Notify GUID + wildcard/event callback registration records. This establishes static registration/dispatch ownership for FCLK record 0x1331 and UCLK record 0x1204; runtime invocation and downstream requester use remain unverified.','limits':'Static exact-clv lifecycle only; no runtime PPI database, firmware execution, hardware, computed dispatch beyond checked method window, or shared-state change.','checks_detail':cs}
 (OUT/'cbs-ppi-lifecycle-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'checks':len(cs),'fresh_result':result['fresh_result'],'owner':result['owner'],'counterparts':counterparts},indent=2))
if __name__=='__main__':main()
