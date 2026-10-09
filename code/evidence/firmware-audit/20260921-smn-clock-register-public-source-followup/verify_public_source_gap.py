#!/usr/bin/env python3
"""Verify bounded public-source reads against latest completed domain18 result.

Reads cached Jina Reader responses in /tmp (not copied into the agent workspace),
local immutable sources, and the latest completed result. It performs no network,
hardware, credential, sysfs, firmware, ROM, NVRAM, or register action.
"""
from __future__ import annotations
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path('/home/OWNER/orca/projects/bc250')
TMP=Path('/tmp/bc250-smn-public-source-20260921.kKfGwn')
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
DOMAIN18=ROOT/'evidence/firmware-audit/20260921-smu-domain18-identity/domain18-identity-result.json'
COREBOOT=ROOT/'import/from-windows/Users/kukuruza/AppData/Local/Temp/bc250-phase10-public/coreboot'
DF=COREBOOT/'src/soc/amd/cezanne/include/soc/data_fabric.h'
LEDGER=Path(__file__).resolve().parent/'public-source-retrieval-ledger.json'
OUT=Path(__file__).resolve().parent/'public-source-gap-result.json'
EXPECTED={
 'rom':'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8',
 'domain18':'f4a005400dba428ff8ba8f782d67bfa608c9e5fc714c5771075c48d6467e5cbe',
 'coreboot_header':'bd438484a85441daf8eb4bfd1a89b102c3638e16317e766dd826384f46689af3',
 'coreboot_response':'fdf8b9a6a6b45e75fd4dd8b2031708ad8baffdec96005f9885c923d830afc460',
 'linux_gc_response':'0834a1a258b52935e37d56fea479fa62ce2c845c7a76a93c8efad5c3b886e8d2',
 'linux_gfx_response':'4bd9bb4a4738817158d0a907d304bd9ac955a6631b54746a0b93d3ec904c42fb',
}

def digest(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def page_body(name:str):
 data=(TMP/name).read_bytes(); txt=data.decode('utf-8',errors='replace')
 marker='Markdown Content:\n'; body=txt.split(marker,1)[1] if marker in txt else ''
 return data,(body.rstrip('\n')+'\n' if body else '')
def addr_hit(s:str)->bool:
 return bool(re.search(r'(?i)(?<![0-9a-f])(?:0x)?0*(?:0116d150|0116d174|06d150|06d174|6d150|6d174|d150|d174)(?![0-9a-f])',s))
checks=[]
def ck(n,ok,got,want=True):checks.append({'name':n,'status':'PASS' if ok else 'FAIL','observed':got,'expected':want})

rom_sha=digest(ROM.read_bytes()); d18_sha=digest(DOMAIN18.read_bytes()); d18=json.loads(DOMAIN18.read_text()); ledger=json.loads(LEDGER.read_text())
cbdata,cbody=page_body('coreboot-data-fabric.md'); gcdata,gcbody=page_body('linux-gc-offset.md'); gfxdata,gfxbody=page_body('linux-gfx-v10.md')
commit=subprocess.check_output(['git','-C',str(COREBOOT),'rev-parse','HEAD'],text=True).strip()
remote=subprocess.check_output(['git','-C',str(COREBOOT),'remote','get-url','origin'],text=True).strip()
path=d18['confirmed_exact_robin5_static_path']; setup=d18['target']['preserved_setup_request']

ck('clv-pinned',rom_sha==EXPECTED['rom'],rom_sha,EXPECTED['rom'])
ck('domain18-result-pinned',d18_sha==EXPECTED['domain18'],d18_sha,EXPECTED['domain18'])
ck('latest-result-static-address-path',d18['verdict']=='INTERNAL_GROUP6_ONLY; PHYSICAL_CLOCK_IDENTITY_UNRESOLVED' and path['dynamic_domain_id']=='0x18' and path['internal_group']==6 and path['smn_program_address']=='0x0116D150' and path['smn_poll_address']=='0x0116D174',{'verdict':d18['verdict'],'domain':path['dynamic_domain_id'],'group':path['internal_group'],'program':path['smn_program_address'],'poll':path['smn_poll_address']})
ck('clv-request-preserved',rom_sha==EXPECTED['rom'] and setup['value']=='0x24' and setup['rom_offset']=='0x7E5',setup,{'value':'0x24','rom_offset':'0x7E5'})
ck('coreboot-commit',commit=='b7931d1afacdc6666b4812305a14ed3deb431201',commit,'b7931d1afacdc6666b4812305a14ed3deb431201')
ck('coreboot-origin',remote=='https://github.com/coreboot/coreboot.git',remote,'https://github.com/coreboot/coreboot.git')
ck('coreboot-header-hash',digest(DF.read_bytes())==EXPECTED['coreboot_header'],digest(DF.read_bytes()),EXPECTED['coreboot_header'])
ck('coreboot-jina-response-hash',digest(cbdata)==EXPECTED['coreboot_response'],digest(cbdata),EXPECTED['coreboot_response'])
ck('coreboot-pinned-public-body-equals-local-copy',cbody==DF.read_text(errors='replace'),cbody==DF.read_text(errors='replace'))
ck('coreboot-has-no-target-address-literal',not addr_hit(cbody),addr_hit(cbody),False)
ck('coreboot-has-no-physical-clock-label',not re.search(r'(?i)\b(MCLK|UCLK|FCLK|UMCCLK|DFCLK)\b',cbody),re.findall(r'(?i)\b(MCLK|UCLK|FCLK|UMCCLK|DFCLK)\b',cbody),[])
ck('linux-v6.8-offset-response-hash',digest(gcdata)==EXPECTED['linux_gc_response'],digest(gcdata),EXPECTED['linux_gc_response'])
ck('linux-v6.8-offset-source-has-no-target-literal',not addr_hit(gcbody),addr_hit(gcbody),False)
ck('linux-v6.8-gfx-response-hash',digest(gfxdata)==EXPECTED['linux_gfx_response'],digest(gfxdata),EXPECTED['linux_gfx_response'])
ck('linux-v6.8-gfx-source-has-no-target-literal',not addr_hit(gfxbody),addr_hit(gfxbody),False)
ck('source-limit-not-exceeded',len(ledger['public_sources'])<=3,len(ledger['public_sources']),'< = 3')

passed=sum(c['status']=='PASS' for c in checks); failed=len(checks)-passed
result={
 'status':'PASS' if failed==0 else 'FAIL','evidence_class':['observed-bytes','external-primary','static-analysis'],
 'scope':'bounded public-source retrieval, max 3 source files; no credentials, installs, hardware, firmware, ROM or register action',
 'inputs':{'clv_sha256':rom_sha,'latest_domain18_result_sha256':d18_sha,'coreboot_commit':commit,'coreboot_data_fabric_sha256':digest(DF.read_bytes())},
 'derived_target':{'domain_id':'0x18','group':6,'program':'0x0116D150','poll':'0x0116D174','units_or_clock_name':'unresolved'},
 'checked_source_families':[
  {'family':'coreboot/coreboot','revision':commit,'file':'src/soc/amd/cezanne/include/soc/data_fabric.h','license':'SPDX GPL-2.0-only','direct_match':False,'scope':'DF routing/config access definitions; no clock-domain name'},
  {'family':'torvalds/linux','revision':'v6.8','files':['drivers/gpu/drm/amd/include/asic_reg/gc/gc_10_1_0_offset.h','drivers/gpu/drm/amd/amdgpu/gfx_v10_0.c'],'license':'AMD permissive license notice in each source','direct_match':False,'scope':'exact target address literals only; no other clock implementation claims made'}
 ],
 'search_blockers':ledger['bounded_search_attempts'],
 'bounded_verdict':'No exact physical-clock semantics identified in the two independently retrieved source families. The new SMU domain18 trace still lacks an exact AMD/AGESA register/domain map for the program/poll pair.',
 'missing_source':'A pinned AMD Cezanne/Ariel/Cyan Skillfish SMN/PMFW register or domain dictionary naming 0x0116D150/0x0116D174 and mapping dynamic domain ID 0x18/Group 6 to a physical clock tree, register fields, and units.',
 'checks':{'passed':passed,'failed':failed,'total':len(checks)},'checks_detail':checks,
}
OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'checks':result['checks'],'latest_result':'domain18-identity-result.json','program':'0x0116D150','poll':'0x0116D174','physical_clock_identity':'unresolved','source_families':2,'source_files':3,'source_literal_hits':0,'verdict':'bounded-public-source-gap','output':str(OUT.resolve())},sort_keys=True))
raise SystemExit(0 if failed==0 else 1)
