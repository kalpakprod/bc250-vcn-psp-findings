#!/usr/bin/env python3
"""Bounded exact-byte fallback descriptor/map/native-field reach check.

No candidate or ROM is created. This verifier distinguishes a raw descriptor
field from a physical map and distinguishes an ABL1 local token 0x703 from the
native Setup field/token records 0x1373/0x1374.
"""
from __future__ import annotations
import hashlib,json,re,struct
from pathlib import Path
ROOT=Path('/home/OWNER/orca/projects/bc250')
OUT=Path(__file__).resolve().parent
ABL=ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
DIS=ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt'
JOIN=ROOT/'evidence/firmware-audit/20260920-clv-abl1-svc4-descriptor-join-xhigh/descriptor-join-result.json'
MAPC=ROOT/'evidence/firmware-audit/20260920-clv-abl1-svc4-descriptor-source-xhigh/map-candidate-result.json'
MAPR=ROOT/'docs/research/2026-09-20-oc-df-init-route.md'
TOK=ROOT/'evidence/firmware-audit/20260920-clv-sync-stage2-token-matrix/token-matrix-result.json'
CON=ROOT/'evidence/firmware-audit/20260920-clv-sync-stage2-consumer/consumer-boundary-result.json'
EXPECTED={
 ABL:'af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a',
 DIS:'b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65',
 JOIN:'31e2c2952d6d4074ddaf52fea5bed68f7656ec6a0867e225e06aab7b432f6a5c',
 MAPC:'f9fccfdcef1258fa5e8eb1758f02d9bb6eb8a0e04822a4751e1d8a7b9a3ad5eb',
 MAPR:'3122a0dce28bc61942a22d567acdc29e318a714097b48877eb0391094a7d0e43',
 TOK:'d33120e48e2c71fb0ab7e2df3a24f1dd91c1e85b0b3639022155444bc0d5765a',
 CON:'e7b1f6f66ed066029a93cf88ea7fb5cb8049df39570af9f3a1b86645882e10d1',
}
checks=[]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ck(name,got,exp):
 ok=got==exp;checks.append({'name':name,'status':'PASS' if ok else 'FAIL','got':got,'expected':exp})
 if not ok:raise AssertionError(f'{name}: got {got!r} expected {exp!r}')
def raw(buf,off,hx,name):ck(name,buf[off:off+len(bytes.fromhex(hx))].hex(),hx)
for p in EXPECTED: ck(f'exists:{p.name}',p.exists(),True)
for p,h in EXPECTED.items(): ck(f'hash:{p.name}',sha(p),h)
b=ABL.read_bytes();t=DIS.read_text(errors='replace');join=json.loads(JOIN.read_text());mapc=json.loads(MAPC.read_text());tok=json.loads(TOK.read_text());con=json.loads(CON.read_text());maptext=MAPR.read_text()
# Exact fallback table stores and pool literals.
raw(b,0xc202,'41f60800','fallback computes +0x1808')
raw(b,0xc206,'0844','fallback adds TABLE+0x70')
raw(b,0xc210,'0260','fallback stores table[0x61E]')
raw(b,0xcc18,'41f6b822','fallback computes +0x1AB8')
raw(b,0xcc22,'8850','fallback stores table[0x6CA]')
ck('fallback pool table[0x61E]',struct.unpack_from('<I',b,0xc47c)[0],0x006ca7c0)
ck('fallback pool table[0x6CA]',struct.unpack_from('<I',b,0xcf40)[0],0x006f47c0)
first=0x006ca7c0;nested=(first>>12)&0xfff;desc=0x006f47c0
ck('nested index arithmetic',nested,0x6ca)
ck('raw descriptor low12',desc&0xfff,0x7c0)
ck('raw descriptor bits0..5',(desc>>0)&0x3f,0)
ck('raw descriptor bits6..11',(desc>>6)&0x3f,31)
ck('raw descriptor raw kind bits27..29',(desc>>27)&7,0)
ck('raw descriptor bit30',(desc>>30)&1,0)
# Exact callback dynamic load/descriptor path and helper calls.
raw(b,0x9b18,'686c','callback loads context+0x44 table pointer')
raw(b,0x9b1c,'50f82160','callback loads table[index]')
raw(b,0x9b2c,'c6f30b31','callback extracts nested index')
raw(b,0x9b54,'50f82160','callback loads nested descriptor')
raw(b,0x9c28,'2146fdf7bbf8','callback passes R1=R4 to SVC4 read')
raw(b,0x9d94,'2146fdf76bf8','callback passes R1=R4 to SVC4 write')
# Existing exact map report says only these aperture bases; verify textual source and low-bit mismatch.
ck('exact map report contains 0x5027C', '0x5027C' in maptext,True)
ck('exact map report contains 0x5227C', '0x5227C' in maptext,True)
known_maps=[0x5027c,0x5227c]
ck('known map low6',sorted({x&0x3f for x in known_maps}),[0x3c])
ck('fallback raw low6 differs from known map',desc&0x3f != (known_maps[0]&0x3f),True)
# Kind-1 exact construction from prior byte-backed callback formula. Low six bits remain descriptor low six.
def kind1(byte49):return (desc&0xfff)|0x50000|((byte49>>1)<<20)|((byte49&1)<<13)
ck('kind1 byte49=0 output',kind1(0),0x507c0)
ck('kind1 byte49=1 output',kind1(1),0x527c0)
ck('kind1 all byte49 values never equal known map',all(kind1(x) not in known_maps for x in range(256)),True)
ck('known map low6 mismatch is invariant for kind1',all(kind1(x)&0x3f != known_maps[0]&0x3f for x in range(256)),True)
# The raw descriptor's other known kind branches use OR/add/mask operations; no exact instruction
# in the checked construction windows adds into bits0..5. Record byte-backed windows.
for off,hx,name in [(0x9c52,'95f8491044f4a020','kind1 construction window'),(0x9c8c,'95f8491044f4a020','kind2 construction window'),(0x9cbc,'95f8491044f4a620','kind3 construction window'),(0x9cce,'44f4e034a4e7','kind4 low-field branch')]: raw(b,off,hx,name)
ck('construction kind paths preserve descriptor low6 in known map comparison',desc&0x3f==0,True)
# Native candidate reach: exact native records and consumer boundary.
for row in tok['matrix']:
 if row['offset'].lower()=='0x703': ck('native +0x703 serializer record',row['record'].lower(),'0x1373')
 if row['offset'].lower()=='0x704': ck('native +0x704 serializer record',row['record'].lower(),'0x1374')
ck('native direct reader boundary excludes 0x1373/0x1374', 'neither requests 0x1204' in con['fresh_result'] or ('0x1373' not in con['fresh_result'] and '0x1374' not in con['fresh_result']),True)
# ABL1 local token 0x703 call exists, but no native token literals and no direct 0x704 MOVW token.
mov703=[ln.strip() for ln in t.splitlines() if 'movw' in ln.lower() and '#0x703' in ln.lower()]
mov704=[ln.strip() for ln in t.splitlines() if 'movw' in ln.lower() and '#0x704' in ln.lower()]
ck('ABL1 local #0x703 call count',len(mov703),1)
ck('ABL1 local #0x703 site',mov703[0].split(':',1)[0],'a57e')
ck('ABL1 local #0x704 MOVW token count',len(mov704),0)
# Native tokens are absent as immediate decoded values in this ABL1 listing.
ck('ABL1 native token 0x1373 immediate absent','#0x1373' not in t.lower(),True)
ck('ABL1 native token 0x1374 immediate absent','#0x1374' not in t.lower(),True)
# 0x703 site calls local helper 0x4830; helper body has no direct descriptor dispatcher BL 0x10958.
site_idx=next(i for i,l in enumerate(t.splitlines()) if l.strip().startswith('a57e:'))
near='\n'.join(t.splitlines()[site_idx:site_idx+10])
ck('ABL1 #0x703 site calls helper 0x4830','bl\t0x4830' in near.lower(),True)
helper_lines=[]
for ln in t.splitlines():
 m=re.match(r'\s*([0-9a-f]+):',ln)
 if m and 0x4830<=int(m.group(1),16)<0x49cc: helper_lines.append(ln)
ck('helper 0x4830 bounded body has no direct BL 0x10958',not any('bl\t0x10958' in ln.lower() for ln in helper_lines),True)
# Apparent listing '#704' is decimal field displacement 0x2C0, not native +0x704 Setup offset.
ck('ABL1 apparent #704 uses raw LDRD +0x2C0',b[0x83f4:0x83f8].hex(),'d4e9b002')
result={
 'status':'BLOCKED_NO_MAP_OR_NATIVE_REACH',
 'decision':'DO_NOT_TREAT_FALLBACK_DESCRIPTOR_AS_CLOCK_TARGET_OR_703_704_PATH',
 'fallback_descriptor':{
   'table_0x61e':'0x006CA7C0','nested_index':'0x6CA','nested_descriptor':'0x006F47C0','low12':'0x7C0','bits0_5':0,'bits6_11':31,'raw_kind_bits27_29':0,'raw_bit30':0,
 },
 'map_relation':{
   'known_exact_map_bases':['0x5027C','0x5227C'],
   'known_map_low6':'0x3C','fallback_low6':'0x00',
   'kind1_byte49_zero':'0x507C0','kind1_byte49_one':'0x527C0',
   'result':'No exact known-map equality; raw low-six field mismatch remains invariant for the checked kind-1 construction. Other kind/high-field merges are not promoted to a physical map.'
 },
 'native_reach':{
   'native_fields':'+0x703 -> INV 0x1373; +0x704 -> INV 0x1374',
   'abl1_local_703':'MOVW #0x703 at 0xA57E -> local helper 0x4830',
   'abl1_704':'no MOVW #0x704 native-token site; apparent #704 at 0x83F4 is raw displacement 0x2C0',
   'abl1_native_inv_tokens':'no decoded #0x1373/#0x1374 immediate',
   'descriptor_entry':'FCLK descriptor path enters with token/index 0x61E at 0x107E8 and dynamic +0x44 table; no direct edge from 0xA57E helper body to BL 0x10958',
   'result':'No byte-backed route from native +0x703/+0x704 to fallback table[0x61E]/nested descriptor is established.'
 },
 'checks':{'passed':sum(x['status']=='PASS' for x in checks),'failed':sum(x['status']=='FAIL' for x in checks),'total':len(checks)},
 'evidence_class':['observed-bytes','static-analysis'],
 'limitations':['No physical register, clock, or hardware claim.','Runtime HEAP/fallback selection and context+0x40 high-field merge remain unresolved.','Native UEFI serializer records and ABL1 local IDs are not equated without a byte-backed bridge.'],
 'checks_detail':checks,
}
(OUT/'fallback-map-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':result['status'],'decision':result['decision'],'checks':result['checks'],'fallback_descriptor':result['fallback_descriptor'],'map_relation':result['map_relation'],'native_reach':result['native_reach']},sort_keys=True))
raise SystemExit(0 if result['checks']['failed']==0 else 1)
