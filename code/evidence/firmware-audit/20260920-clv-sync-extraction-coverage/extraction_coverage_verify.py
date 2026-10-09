#!/usr/bin/env python3
"""Read-only coverage audit over the existing exact-clv executable census."""
from __future__ import annotations
import hashlib,json,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
CENSUS=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/census.json'
COVERAGE=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/coverage.json'
OUT=Path(__file__).resolve().parent/'extraction-coverage-result.json'
EXPECTED_ROM='ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
EXPECTED_CENSUS_SHA='ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
PREMEM=['MemDetect','AmdMemAm4Pei','AmdMemoryHobInfoPeim','PlatformMemoryConfigurationPei','CbsBasePei','AmdFabricAriPei','AmdNbioSmuV10Pei','AmdNbioGfxARIPei','AmdNbioBaseARIPei','AmdNbioPcieARIPei','AmdSocBl5AriPei','GnbPei','NbPei','AmiAgesaPei']
FIELD_NEEDLES=['0x316','0x330','0x368','0x36d','0x6a2','0x6a3','0x703','0x704','0x11ed','0x1204','0x1237','0x123c','0x1331','0x1332','0x1373','0x1374']
checks=[]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def check(label,ok,details=None): checks.append({'label':label,'status':'PASS' if ok else 'FAIL','details':details})
rom_sha=sha(ROM); census=json.loads(CENSUS.read_text()); coverage=json.loads(COVERAGE.read_text()); recs=census['records']; byui={r.get('ui'):r for r in recs if r.get('ui')}
check('rom-pin',rom_sha==EXPECTED_ROM,{'observed':rom_sha,'expected':EXPECTED_ROM})
check('census-input-pin',census.get('sha256')==EXPECTED_CENSUS_SHA,{'observed':census.get('sha256'),'expected':EXPECTED_CENSUS_SHA})
check('census-record-count',len(recs)==233,len(recs))
check('coverage-module-count',len(coverage.get('modules',[]))==42,len(coverage.get('modules',[])))
check('census-body-files',all((CENSUS.parent/(r['stem']+'.bin')).exists() for r in recs),sum((CENSUS.parent/(r['stem']+'.bin')).exists() for r in recs))
# Dedup/representation and origins.
origin_class=collections.Counter('nested/guided/freeform' if any(t in r.get('origin','') for t in ['/guided@','/freeform-','/fv-image@','/compression@']) else ('security-core' if 'security-core' in r.get('origin','') else 'outer/raw') for r in recs)
type_counts=collections.Counter(r.get('type') for r in recs)
check('pe32-te-only-census',set(type_counts)<= {'PE32','TE'},dict(type_counts))
check('nested-origin-representation',origin_class['nested/guided/freeform']==178,dict(origin_class))
# Relevant pre-memory map.
pre=[]
for name in PREMEM:
 r=byui.get(name); ins=[]
 if r:
  ip=CENSUS.parent/(r['stem']+'.instructions.json')
  if ip.exists():
   for x in json.loads(ip.read_text()):
    op=x.get('operands','').lower()
    if any(n in op for n in FIELD_NEEDLES): ins.append({'rva':hex(x['rva']),'bytes':x['bytes'],'operands':x['operands']})
  pre.append({'name':name,'present':True,'type':r['type'],'size':r['size'],'origin':r['origin'],'stem':r['stem'],'sha256':r['sha256'],'field_or_token_hits':ins[:32],'field_or_token_hit_count':len(ins)})
 else: pre.append({'name':name,'present':False})
check('relevant-premem-records-present',all(x['present'] for x in pre),pre)
# Raw/non-x86 gap classification from census schema, not absence claim.
raw_gap={'x86_executable_sections':{'covered_records':len(recs),'types':dict(type_counts),'nested_records':origin_class['nested/guided/freeform'],'outer_te_records':sum(1 for r in recs if r.get('type')=='TE' and r.get('origin')=='outer'),'status':'covered-by-existing-census'},'raw_non_x86_psp_abl_smu':{'status':'not-in-233-x86-census','reason':'census records are PE32/TE executable sections; PSP/BHD/raw payload bodies are separate firmware_audit/PSP evidence'},'non_executable_sections_and_runtime_indirects':{'status':'not-exhaustively-covered','reason':'extractor saves PE32/TE executable sections and coverage explicitly leaves arbitrary runtime/computed indirect targets unresolved'}}
# Relevant map classification, no semantic promotion.
result={'status':'PASS' if all(c['status']=='PASS' for c in checks) else 'FAIL','evidence_class':['observed-bytes','static-analysis'],'inputs':{'rom':str(ROM),'rom_sha256':rom_sha,'census':str(CENSUS),'census_sha256':sha(CENSUS),'coverage':str(COVERAGE),'coverage_sha256':sha(COVERAGE),'census_extractor_sha256':census.get('extractor_sha256'),'objdump':census.get('objdump')},'coverage_summary':{'records':len(recs),'type_counts':dict(type_counts),'origin_classes':dict(origin_class),'extractor_scope':coverage.get('scope'),'raw_gap_classification':raw_gap},'relevant_pre_memory_modules':pre,'conclusion':{'x86_pei_extraction':'No coverage gap found for named exact-clv PEI/x86 modules in the 233-record census; MemDetect/AmdMemAm4Pei/AmdMemoryHobInfoPeim/PlatformMemoryConfigurationPei/CbsBasePei/AmdNbio/AmdFabric candidates are present with hashes and origins.','semantic_consumer':'No relevant module is promoted as the actual clock/training consumer by extraction coverage alone; pre-memory ownership and downstream dataflow remain separate questions.','raw_payload_gap':'PSP/ABL/SMU/raw non-x86 payloads and arbitrary non-executable/computed runtime paths are outside this x86 executable census and require their existing separate evidence paths.'},'checks':{'passed':sum(c['status']=='PASS' for c in checks),'failed':sum(c['status']=='FAIL' for c in checks),'total':len(checks)},'checks_detail':checks}
OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps({'status':result['status'],'checks':result['checks'],'output':str(OUT.resolve())},sort_keys=True)); raise SystemExit(0 if result['status']=='PASS' else 1)
