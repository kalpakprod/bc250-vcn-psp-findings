#!/usr/bin/env python3
"""Trace ABL1 HEAP key 0xA04E population and stop at the APOB/INV bridge.

No PPI GUID or UclkDiv1M0/0x1204 proof is repeated. The test follows the
selector-case descriptor into the HEAP miss writer, then traces its source
pointer to the outer runtime object field initialized by the exact ABL1
constructor. APOB service bytes and the native 0x11ED producer are boundary
context only.
"""
from __future__ import annotations
import hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; OUT=Path(__file__).resolve().parent
ABL=ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
OBJ=ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o'
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
CENSUS=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/census.json'
AMDMEM=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/AmdMemAm4Pei-1ef4e7b94467.bin'
CBS=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/CbsBasePei-6ff112922ad8.bin'
EXP={'abl':'af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a','obj':'54abef3a390abb0ff745685de2eed4e0e8db5e9ba27bba1a0f245573b47ff135','rom':'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8','cbs':'6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77','amdmem':'1ef4e7b944672a9a48b6fcb16c4d35cb6d23bb8306429dc3eb10ee1d0c7bb5f8'}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def chk(cs,n,g,e):
 ok=g==e;cs.append({'name':n,'status':'PASS' if ok else 'FAIL','got':g,'expected':e})
 if not ok: raise AssertionError(f'{n}: {g!r} != {e!r}')
def raw(row,b,rva,n):
 for s in row['sections']:
  if s['rva']<=rva< s['rva']+s['size']:
   o=rva-s['rva']+s['raw'];return b[o:o+n]
 raise ValueError(hex(rva))
def main():
 abl=ABL.read_bytes(); obj=OBJ.read_bytes(); rom=ROM.read_bytes(); census=json.loads(CENSUS.read_text()); rows={r['ui']:r for r in census['records'] if r.get('ui')}; am=AMDMEM.read_bytes(); cbs=CBS.read_bytes(); cs=[]
 for n,p,key in [('abl',ABL,'abl'),('obj',OBJ,'obj'),('rom',ROM,'rom'),('cbs',CBS,'cbs'),('amdmem',AMDMEM,'amdmem')]: chk(cs,f'{n}-hash',sha(p),EXP[key])
 # Exact selector-case descriptor and miss writer.
 chk(cs,'provider fixed key MOVW 0xA04E',abl[0x4b1a:0x4b1e].hex(),'4af24e06')
 chk(cs,'provider lookup descriptor address SP+0x24',abl[0x4b34:0x4b36].hex(),'09a8')
 chk(cs,'provider stores key in lookup descriptor',abl[0x4b38:0x4b3a].hex(),'0996')
 chk(cs,'provider miss path builds HEAP descriptor SP+0x14',abl[0x4b4e:0x4b52].hex(),'cde90506')
 chk(cs,'provider miss sets metadata 4',abl[0x4b52:0x4b5a].hex(),'042029998df81c00')
 chk(cs,'provider miss calls HEAP producer 0x6238',abl[0x4b5a:0x4b60].hex(),'05a801f06cfb')
 # 0x6238: object descriptor +4 supplies the node key; r10 source is copied.
 chk(cs,'heap producer prologue',abl[0x6238:0x6244].hex(),'2de9f84f0446484f00208a46')
 chk(cs,'heap producer reads descriptor key +4',abl[0x6278:0x627a].hex(),'6268')
 chk(cs,'heap producer writes node key',abl[0x62fa:0x62fe].hex(),'60682860')
 chk(cs,'heap producer source register to copy helper',abl[0x631e:0x6322].hex(),'534600f0')
 chk(cs,'heap producer calls byte-copy helper 0x6B78',abl[0x6320:0x6324].hex(),'00f02afc')
 chk(cs,'byte-copy helper reads source and writes node payload',abl[0x6b7a:0x6b82].hex(),'00f8011b521efbd2')
 # HEAP base/sentinel literals adjacent to lookup/producer.
 chk(cs,'heap global pointer literal 0x73000',int.from_bytes(abl[0x6360:0x6364],'little'),0x73000)
 chk(cs,'heap signature literal HEAP',abl[0x6364:0x6368].hex(),'48454150')
 # Constructor outer object and source pointer field.
 chk(cs,'constructor caller enters 0xC00',abl[0xbd0:0xbd6].hex(),'204600f015f8')
 chk(cs,'constructor prologue and preserves R1',abl[0xc00:0xc08].hex(),'2de9fc4107468846')
 chk(cs,'constructor computes outer+0x864',abl[0xc29e:0xc2a6].hex(),'01f66400c1f86c28')
 chk(cs,'constructor stores source field pointer at SP+0xA4',abl[0xc2a8:0xc2ae].hex(),'299001f50760')
 chk(cs,'constructor stores external pointer into outer+0x864',abl[0xc2ae:0xc2b4].hex(),'c1f86428814a')
 chk(cs,'constructor literal table value 0x006CD4D0',int.from_bytes(abl[0xc4b4:0xc4b8],'little'),0x006cd4d0)
 # Native INV and APOB are only boundary context; no PPI GUID or 0x1204 checks.
 cbsrow=rows['CbsBasePei']; chk(cs,'native INV 0x11ED producer header',raw(cbsrow,cbs,0x9837,5).hex(),'baed110000');chk(cs,'native Setup+0x316 load',raw(cbsrow,cbs,0x9857,6).hex(),'8a8216030000')
 amrow=rows['AmdMemAm4Pei'];chk(cs,'APOB service pointer 0x9E3B14C',raw(amrow,am,0x8a0,5).hex(),'684cb1e309');chk(cs,'APOB service arg 0xFF',raw(amrow,am,0x8ca,5).hex(),'68ff000000');chk(cs,'APOB service message 0x61',raw(amrow,am,0x8cf,2).hex(),'6a61');chk(cs,'APOB service call 0xCD9',raw(amrow,am,0x8d1,5).hex(),'e803040000')
 chk(cs,'ABL1 has no direct $INV marker',b'$INV' not in abl,True);chk(cs,'ABL1 has no direct 0x11ED literal',b'\xed\x11\x00\x00' not in abl,True);chk(cs,'ABL1 has no direct AmdMem service pointer',b'\x4c\xb1\xe3\x09' not in abl,True)
 result={'status':'PASS','checks':{'passed':sum(x['status']=='PASS' for x in cs),'failed':sum(x['status']=='FAIL' for x in cs),'total':len(cs)},'evidence_class':['observed-bytes','static-analysis'],'inputs':{'rom':{'path':str(ROM),'sha256':sha(ROM),'size':len(rom)},'abl1':{'path':str(ABL),'sha256':sha(ABL),'size':len(abl)},'object':{'path':str(OBJ),'sha256':sha(OBJ),'size':len(obj)},'cbs':{'path':str(CBS),'sha256':sha(CBS)},'amdmem':{'path':str(AMDMEM),'sha256':sha(AMDMEM)}},'dataflow':{'selector_case':'provider 0x49CC selector 0x0F -> fixed key 0xA04E at 0x4B1A','miss_writer':'0x4B5A -> 0x6238; descriptor SP+0x14 +4 supplies key and R1 supplies source pointer','heap_node':'0x6238 reads descriptor +4, writes node key at node+0, then calls 0x6B78 to copy from R10/source into node+0x10','source_field':'constructor 0xC00 receives outer object R1 from caller 0xB84; outer+0x864 is saved at SP+0xA4 and initialized to external pointer 0x006CD4D0','heap_base':'literal 0x73000; signature HEAP'},'apob_inv_boundary':{'apob_service':'AmdMemAm4Pei 0x8A0/0x8CA/0x8CF/0x8D1 = 0x9E3B14C/0xFF/0x61/call 0xCD9','native_inv':'CbsBasePei 0x9837/0x9857 = 0x11ED from Setup+0x316','join':'none in inspected exact bytes; ABL1 source field outer+0x864 and external pointer 0x006CD4D0 are not byte-joined to APOB service output or INV payload'},'first_unresolved_boundary':{'location':'producer of the outer ABL1 object passed as R1 at 0xB84/0xBD2 and population/meaning of its +0x864 field (initialized with 0x006CD4D0) relative to AmdMem APOB service output and native INV 0x11ED','statement':'The exact HEAP node writer is now closed to a runtime field-backed source: provider key 0xA04E -> descriptor -> 0x6238 -> node key/payload. The first missing cross-stage edge is upstream of that field: no byte-backed path joins outer+0x864, APOB service 0x9E3B14C/message0x61/arg0xFF, and `$INV 0x11ED`; no training/clock/SMU actuator is claimed.'},'limits':['Static exact bytes only; no ABL1 loader/runtime execution, APOB service execution, PPI invocation, HOB capture, SMU execution, or hardware.','The no-marker checks are bounded direct-literal checks, not computed/indirect/DMA absence claims.','No PPI GUID proof and no 0x1204 serializer/HOB proof was repeated.'],'checks_detail':cs}
 out=OUT/'heap-populator-result.json';out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':'PASS','checks':len(cs),'result':str(out),'first_unresolved':result['first_unresolved_boundary']},indent=2))
if __name__=='__main__': main()
