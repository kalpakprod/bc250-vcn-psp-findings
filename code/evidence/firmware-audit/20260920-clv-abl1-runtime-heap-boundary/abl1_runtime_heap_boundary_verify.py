#!/usr/bin/env python3
"""Bounded exact ABL1 runtime-heap lookup for UCLK descriptor token 0x20."""
from __future__ import annotations
import hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from scripts.apcb_detail import parse_apcb
OUT=Path(__file__).resolve().parent
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'; ABL=ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'; PREV=ROOT/'evidence/firmware-audit/20260920-clv-abl1-apcb-consumer-resume/abl1-apcb-consumer-result.json'; APCBREPORT=ROOT/'evidence/firmware-audit/20260920-clv-apcb-abl-apob-interface/apcb-detail.json'
EXP={'rom':'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8','abl':'af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a','prev':'3950e5136254db2aa9c96c91caba4d48da4a11c369b38a36703c9f54cef45ee9','apcbreport':'503e4f525f4372903b23ea9320c77f7b0b39250f310d80a1b7565eb98b39f394'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def j(v):return 'hex:'+bytes(v).hex() if isinstance(v,(bytes,bytearray)) else v
def check(cs,n,g,e):
 ok=g==e; cs.append({'check':n,'passed':ok,'got':j(g),'expected':j(e)})
 if not ok: raise AssertionError(f'{n}: got {g!r}, expected {e!r}')
def main():
 cs=[]
 for n,p,k in [('ROM',ROM,'rom'),('ABL1',ABL,'abl'),('prior provider result',PREV,'prev'),('prior APCB report',APCBREPORT,'apcbreport')]:
  check(cs,n+' exists',p.exists(),True); check(cs,n+' sha256',sha(p),EXP[k])
 b=ABL.read_bytes(); prev=json.loads(PREV.read_text()); apcb=json.loads(APCBREPORT.read_text())
 check(cs,'prior provider result PASS',prev['status'],'PASS'); check(cs,'prior provider checks',prev['checks'],36)
 # Provider case-15 construction: internal type selector 0x0f, runtime table key 0xa04e, and descriptor address sp+0x24.
 check(cs,'case 0x0f selector immediate',b[0x4b0e:0x4b12],bytes.fromhex('0f2240f2'))
 check(cs,'case 0x0f runtime key immediate 0xa04e',b[0x4b1a:0x4b1e],bytes.fromhex('4af24e06'))
 check(cs,'provider stores runtime key to descriptor sp+0x24',b[0x4b34:0x4b3c],bytes.fromhex('09a82999099601f0'))
 # Exact 0x6374 linked-list/table lookup: literals 0x73000 and HEAP; input key [r0] compared to entries; match returns pointer/length.
 check(cs,'0x6374 global runtime-table literal 0x73000',b[0x63e8:0x63ec],bytes.fromhex('00300700'))
 check(cs,'0x6374 runtime-table sentinel HEAP',b[0x63ec:0x63f0],b'HEAP')
 check(cs,'0x6374 loads runtime table head and compares sentinel',b[0x6374:0x6382],bytes.fromhex('1c4af8b51c4f01261368bb4204d0'))
 check(cs,'0x6374 compares input key against table entry',b[0x6394:0x63a2],bytes.fromhex('05681c68ac4204d0db685c1c0bd0'))
 check(cs,'0x6374 returns body pointer and length on match',b[0x63a6:0x63b8],bytes.fromhex('46b1597a5a18103282605a68511a41600020'))
 # Exact 0x6238 is the runtime heap/table allocator boundary, with literal heap base 0x3000 and HEAP tag.
 check(cs,'0x6238 prologue and descriptor input',b[0x6238:0x6248],bytes.fromhex('2de9f84f0446484f00208a46e0602068'))
 check(cs,'0x6238 runtime table pointer literal 0x73000',b[0x6360:0x6364],bytes.fromhex('00300700'))
 check(cs,'0x6238 heap sentinel HEAP',b[0x6364:0x6368],b'HEAP')
 check(cs,'0x6238 loads heap signature and compares',b[0x6256:0x625a],bytes.fromhex('38688842'))
 check(cs,'0x6238 branches to existing heap on match',b[0x625a:0x625c],bytes.fromhex('05d0'))
 check(cs,'0x6238 loads global heap head state',b[0x6268:0x626e],bytes.fromhex('b86807f11008'))
 check(cs,'0x6238 enters entry scan',b[0x627c:0x6284],bytes.fromhex('d8f80030934203d1'))
 # Exact pinned APCB raw contrast; no claim of schema decoding.
 rom=ROM.read_bytes(); ar=apcb['images'][0]['apcb']; check(cs,'APCB parser checksum match',ar['checksum_match'],True); check(cs,'APCB parser offset',ar['offset'],'0xAB1000'); check(cs,'APCB parser size',ar['size'],2972)
 cbs=[g for g in ar['groups'] if g['gid']=='0x1707'][0]; check(cs,'CBSG group id present',cbs['gid'],'0x1707'); check(cs,'CBSG subgroup count',len(cbs['subgroups']),2)
 # Existing parser reports subgroup bodies; raw ROM candidates with value halfword 0x20/0x21 are recorded, not semantically named.
 candidates=[]
 body_start=0xAB1494; body=rom[body_start:body_start+1800]
 for off in range(0,len(body)-3,4):
  a=int.from_bytes(body[off:off+2],'little'); v=int.from_bytes(body[off+2:off+4],'little')
  if v in (0x20,0x21): candidates.append({'absolute':hex(body_start+off),'raw':body[off:off+4].hex(),'u16_0':hex(a),'u16_1':hex(v)})
 check(cs,'raw CBSG candidate rows with second u16 0x20/0x21',candidates,[{'absolute':'0xab14d8','raw':'01302000','u16_0':'0x3001','u16_1':'0x20'},{'absolute':'0xab14e8','raw':'01422000','u16_0':'0x4201','u16_1':'0x20'},{'absolute':'0xab1500','raw':'01782000','u16_0':'0x7801','u16_1':'0x20'},{'absolute':'0xab185c','raw':'01602100','u16_0':'0x6001','u16_1':'0x21'}])
 # Runtime key A04E is absent from the pinned ROM as aligned little-endian scalar; this is the storage-indirection boundary.
 hits=[]
 for off in range(0,len(rom)-3,2):
  if rom[off:off+4]==(0xa04e).to_bytes(4,'little'): hits.append(off)
 check(cs,'aligned ROM literal 0x0000a04e absent',len(hits),0)
 result={'status':'PASS','checks':len(cs),'route':'exact ABL1 runtime heap table boundary for UCLK descriptor 0x20','evidence_class':['observed-bytes','static-analysis'],'inputs':{'rom':str(ROM),'abl1':str(ABL),'prior_provider_result':str(PREV),'apcb_report':str(APCBREPORT)},'hashes':{'rom':sha(ROM),'abl1':sha(ABL),'prior_provider_result':sha(PREV),'apcb_report':sha(APCBREPORT)},'chain':{'descriptor':'first ordered UCLK descriptor entry 0x20 -> helper 0x4800','provider_selector':'0x0f','runtime_record_key':'0xa04e','lookup':'0x6374 uses runtime table pointer literal 0x73000 and HEAP sentinel; matches [input] key and returns body pointer/length','heap_helper':'0x6238 uses runtime table pointer literal 0x73000 and HEAP sentinel','apcb_contrast':'CBSG raw rows observed at 0xAB14D8/0xAB14E8/0xAB1500/0xAB185C; schema not decoded','direct_rom_key_match':'0xA04E absent as aligned little-endian scalar'},'fresh_result':'For the exact first UCLK descriptor 0x20, provider case 0x0f constructs runtime key 0xA04E and writes it into the descriptor passed to 0x6374. Exact 0x6374 is a HEAP-linked-list lookup at runtime table pointer 0x73000, returning body pointer/length on key match; 0x6238 is a second runtime HEAP allocator/block boundary with HEAP tag and the same runtime table pointer literal 0x73000. The key 0xA04E is absent from the pinned ROM, so no direct APCB flash row can be assigned as its backing record. Raw CBSG rows with 0x20/0x21 values are recorded without schema claims.', 'unresolved_edge':'Runtime population of the HEAP records keyed by 0xA04E and the conversion from raw CBSG/APCB records to that runtime table remain unresolved. No frequency/enum/voltage/pointer semantic assignment or MCLK=UCLK=FCLK proof follows.','checks_detail':cs}
 (OUT/'abl1-runtime-heap-boundary-result.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps({'status':result['status'],'checks':len(cs),'chain':result['chain'],'unresolved_edge':result['unresolved_edge']},indent=2))
if __name__=='__main__':main()
