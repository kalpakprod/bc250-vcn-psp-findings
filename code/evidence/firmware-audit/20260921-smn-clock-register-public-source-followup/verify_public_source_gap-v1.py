#!/usr/bin/env python3
"""Offline verification of bounded Jina retrievals and the pinned source gap.

The public Jina responses are in /tmp only (Agent Reach workspace rule); this
script reads those already-retrieved pages and local immutable evidence. It
makes no network request and performs no hardware or credential operation.
"""
from __future__ import annotations
import hashlib, json, re, subprocess
from pathlib import Path
ROOT=Path('/home/OWNER/orca/projects/bc250')
TMP=Path('/tmp/bc250-smn-public-source-20260921.kKfGwn')
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
SELECTOR=ROOT/'evidence/firmware-audit/20260921-smu-domain-selector/selector-result.json'
COREBOOT=ROOT/'import/from-windows/Users/kukuruza/AppData/Local/Temp/bc250-phase10-public/coreboot'
DF=COREBOOT/'src/soc/amd/cezanne/include/soc/data_fabric.h'
LOCAL_GC=ROOT/'import/from-windows/Users/kukuruza/tmp_bc250/recon/gc_10_1_0_offset.h'
LEDGER=ROOT/'evidence/firmware-audit/20260921-smn-clock-register-public-source-followup/public-source-retrieval-ledger.json'
OUT=Path(__file__).resolve().parent/'public-source-gap-result.json'
EXPECTED={
 'rom':'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8',
 'selector':'81755d70ce15276265fdf3c31393293baae4d5782e09fa717e2d35c87d276a49',
 'coreboot_header':'bd438484a85441daf8eb4bfd1a89b102c3638e16317e766dd826384f46689af3',
 'coreboot_response':'fdf8b9a6a6b45e75fd4dd8b2031708ad8baffdec96005f9885c923d830afc460',
 'linux_gc_response':'0834a1a258b52935e37d56fea479fa62ce2c845c7a76a93c8efad5c3b886e8d2',
 'linux_gfx_response':'4bd9bb4a4738817158d0a907d304bd9ac955a6631b54746a0b93d3ec904c42fb',
}

def digest(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def jina(name:str)->tuple[bytes,str,str]:
 data=(TMP/name).read_bytes(); txt=data.decode('utf-8',errors='replace')
 marker='Markdown Content:\n'
 body=txt.split(marker,1)[1] if marker in txt else ''
 body=(body.rstrip('\n')+'\n') if body else ''
 return data,body.encode(),txt

def has_addr(text:str)->bool:
 return bool(re.search(r'(?i)(?<![0-9a-f])(?:0x)?0*(?:0116d150|0116d174|06d150|06d174|6d150|6d174|d150|d174)(?![0-9a-f])',text))

checks=[]
def ck(name,ok,observed,expected=True):
 checks.append({'name':name,'status':'PASS' if ok else 'FAIL','observed':observed,'expected':expected})
rom_sha=digest(ROM.read_bytes()); selector_sha=digest(SELECTOR.read_bytes()); df_sha=digest(DF.read_bytes())
selector=json.loads(SELECTOR.read_text()); ledger=json.loads(LEDGER.read_text())
ex=selector['queue3_0x1d']['accepted_example']
cb_data,cb_body,cb_txt=jina('coreboot-data-fabric.md')
gc_data,gc_body,gc_txt=jina('linux-gc-offset.md')
gfx_data,gfx_body,gfx_txt=jina('linux-gfx-v10.md')
head=subprocess.check_output(['git','-C',str(COREBOOT),'rev-parse','HEAD'],text=True).strip()
remote=subprocess.check_output(['git','-C',str(COREBOOT),'remote','get-url','origin'],text=True).strip()

ck('pinned-clv',rom_sha==EXPECTED['rom'],rom_sha,EXPECTED['rom'])
ck('selector-result-pinned',selector_sha==EXPECTED['selector'],selector_sha,EXPECTED['selector'])
ck('selector-target-addresses',selector.get('status')=='PASS' and ex.get('domain_id')=='0x18' and ex.get('smu_window_program')=='0x116d150' and ex.get('smu_window_poll')=='0x116d174',{'domain':ex.get('domain_id'),'program':ex.get('smu_window_program'),'poll':ex.get('smu_window_poll')})
ck('coreboot-commit',head=='b7931d1afacdc6666b4812305a14ed3deb431201',head,'b7931d1afacdc6666b4812305a14ed3deb431201')
ck('coreboot-origin',remote=='https://github.com/coreboot/coreboot.git',remote,'https://github.com/coreboot/coreboot.git')
ck('coreboot-file-hash',df_sha==EXPECTED['coreboot_header'],df_sha,EXPECTED['coreboot_header'])
ck('coreboot-jina-response-hash',digest(cb_data)==EXPECTED['coreboot_response'],digest(cb_data),EXPECTED['coreboot_response'])
ck('coreboot-jina-body-matches-pinned-local-copy',cb_body.decode(errors='replace')==DF.read_text(errors='replace'),cb_body.decode(errors='replace')==DF.read_text(errors='replace'))
ck('coreboot-source-no-target-literal',not has_addr(cb_body.decode(errors='replace')),has_addr(cb_body.decode(errors='replace')),False)
ck('coreboot-source-no-clock-domain-label',not re.search(r'(?i)\b(MCLK|UCLK|FCLK|UMCCLK|DFCLK)\b',cb_body.decode(errors='replace')),re.findall(r'(?i)\b(MCLK|UCLK|FCLK|UMCCLK|DFCLK)\b',cb_body.decode(errors='replace')),[])
ck('linux-gc-v6.8-jina-response-hash',digest(gc_data)==EXPECTED['linux_gc_response'],digest(gc_data),EXPECTED['linux_gc_response'])
ck('linux-gc-v6.8-no-target-literal',not has_addr(gc_body.decode(errors='replace')),has_addr(gc_body.decode(errors='replace')),False)
ck('linux-gfx-v6.8-jina-response-hash',digest(gfx_data)==EXPECTED['linux_gfx_response'],digest(gfx_data),EXPECTED['linux_gfx_response'])
ck('linux-gfx-v6.8-no-target-literal',not has_addr(gfx_body.decode(errors='replace')),has_addr(gfx_body.decode(errors='replace')),False)
ck('retrieval-ledger-bounded-source-count',len(ledger['public_sources'])<=3,len(ledger['public_sources']),'< = 3')
ck('clv-1800-request-preserved',ROM.read_bytes()[0x7e5]==0x24,hex(ROM.read_bytes()[0x7e5]),'0x24')

passed=sum(c['status']=='PASS' for c in checks); failed=len(checks)-passed
result={
 'status':'PASS' if failed==0 else 'FAIL',
 'evidence_class':['observed-bytes','external-primary','static-analysis'],
 'scope':'three or fewer primary source files; exact-address/clock-generator terms only; no credentials, install, hardware, ROM/NVRAM/register writes',
 'inputs':{'rom_sha256':rom_sha,'selector_result_sha256':selector_sha,'coreboot_commit':head,'coreboot_origin':remote,'coreboot_data_fabric_sha256':df_sha},
 'target':{'domain_id':'0x18','internal_group':6,'program_smn':'0x0116D150','poll_smn':'0x0116D174','raw_program_offset':'0x6D150','raw_poll_offset':'0x6D174'},
 'sources':[
  {'family':'coreboot/coreboot','revision':head,'file':'src/soc/amd/cezanne/include/soc/data_fabric.h','license':'GPL-2.0-only','external_retrieval_sha256':digest(cb_data),'normalized_body_matches_local':True,'exact_target_literal_matches':0,'semantic_result':'DF routing/config offsets only; no target clock-domain name'},
  {'family':'torvalds/linux','revision':'v6.8','file':'drivers/gpu/drm/amd/include/asic_reg/gc/gc_10_1_0_offset.h','license':'AMD permissive header notice','external_retrieval_sha256':digest(gc_data),'exact_target_literal_matches':0,'semantic_result':'generic GC MMIO offset header; no mapping for derived SMN pair'},
  {'family':'torvalds/linux','revision':'v6.8','file':'drivers/gpu/drm/amd/amdgpu/gfx_v10_0.c','license':'AMD permissive header notice','external_retrieval_sha256':digest(gfx_data),'exact_target_literal_matches':0,'semantic_result':'no exact target-address literal; no other semantics reused in this task'}
 ],
 'public_search_attempts':ledger['bounded_search_attempts'],
 'verdict':'BOUNDED_PUBLIC_SOURCE_GAP',
 'missing_source':'Need an AMD Cezanne/Ariel/Cyan Skillfish SMN/PMFW register reference that maps Group 6/domain 0x18 and 0x0116D150/0x0116D174 to an identified clock generator/register fields, including the physical clock tree, divider, units and crossing/status semantics.',
 'checks':{'passed':passed,'failed':failed,'total':len(checks)},'checks_detail':checks,
}
OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'checks':result['checks'],'domain_id':'0x18','program_smn':'0x0116D150','poll_smn':'0x0116D174','coreboot_body_matches_local':result['sources'][0]['normalized_body_matches_local'],'exact_public_source_hits':0,'independent_repo_families':2,'source_files':len(result['sources']),'verdict':result['verdict'],'output':str(OUT.resolve())},sort_keys=True))
raise SystemExit(0 if failed==0 else 1)
