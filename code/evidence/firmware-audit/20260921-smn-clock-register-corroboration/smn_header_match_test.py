#!/usr/bin/env python3
"""Corroborate selector-result SMN addresses against existing local headers.

This is a bounded literal/name lookup only. It does not re-run or reproduce
Ghidra disassembly, infer physical clock identity, or access hardware.
"""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path

ROOT=Path('/home/OWNER/orca/projects/bc250')
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
SELECTOR=ROOT/'evidence/firmware-audit/20260921-smu-domain-selector/selector-result.json'
HEADERS=[
 ROOT/'import/from-windows/Users/kukuruza/tmp_bc250/recon/gc_10_1_0_offset.h',
 ROOT/'import/from-windows/Users/kukuruza/tmp_bc250/recon/gc_10_1_0_sh_mask.h',
 ROOT/'import/from-windows/Users/kukuruza/tmp_bc250/recon/gmc_10_0_0_offset.h',
 ROOT/'import/from-windows/Users/kukuruza/tmp_bc250/recon/gmc_10_0_0_sh_mask.h',
 ROOT/'import/from-windows/Users/kukuruza/tmp_bc250/recon/smu_v11_8_pmfw.h',
]
OUT=Path(__file__).resolve().parent/'smn-header-match-result.json'
EXPECTED_ROM='ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
EXPECTED_SELECTOR={'selector_index':11,'domain_id':'0x18','internal_group':6,'smu_window_program':'0x116d150','smu_window_poll':'0x116d174'}

def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def norm_hex(s:str)->str: return s.lower().removeprefix('0x').lstrip('0') or '0'

rom=ROM.read_bytes(); selector=json.loads(SELECTOR.read_text())
example=selector['queue3_0x1d']['accepted_example']
checks=[]
def ck(name,ok,observed,expected): checks.append({'name':name,'status':'PASS' if ok else 'FAIL','observed':observed,'expected':expected})
ck('selector-report-completed-pass',selector.get('status')=='PASS',selector.get('status'), 'PASS')
ck('accepted-example-addresses-match-bound-evidence',all(example.get(k)==v for k,v in EXPECTED_SELECTOR.items()),
   {k:example.get(k) for k in EXPECTED_SELECTOR},EXPECTED_SELECTOR)
rom_sha=sha(ROM)
ck('exact-clv-identity',len(rom)==0x1000000 and rom_sha==EXPECTED_ROM,{'size':len(rom),'sha256':rom_sha},{'size':0x1000000,'sha256':EXPECTED_ROM})
request=rom[0x7E5]
ck('preserve-clv-1800-request',request==0x24,{'offset':'0x7E5','byte':f'0x{request:02X}'},{'byte':'0x24','label':'1800MHz'})

# A bounded header set taken from the local register-header inventory. Search
# full addresses and natural base-stripped/low-word variants as literal tokens.
forms={
 'program':['0116D150','116D150','06D150','6D150','D150'],
 'poll':['0116D174','116D174','06D174','6D174','D174'],
}
header_inventory=[]; matches=[]
for h in HEADERS:
 text=h.read_text(errors='replace')
 header_inventory.append({'path':str(h),'sha256':sha(h),'size':h.stat().st_size})
 lines=text.splitlines()
 for kind,variants in forms.items():
  for i,line in enumerate(lines,1):
   for variant in variants:
    pat=re.compile(rf'(?i)(?<![0-9a-f])(?:0x)?0*{variant}(?![0-9a-f])')
    if pat.search(line):
     matches.append({'kind':kind,'header':str(h),'line':i,'text':line.strip(),'matched_form':variant})

# In the same header set, separately enumerate explicit clock-domain symbols;
# these are clues only, not a semantic mapping for a calculated SMN address.
symbols=[]
for h in HEADERS:
 for i,line in enumerate(h.read_text(errors='replace').splitlines(),1):
  if re.search(r'(?i)(MCLK|UCLK|FCLK|DFCLK|UMC.*CLK|CLK.*UMC)',line):
   symbols.append({'header':str(h),'line':i,'text':line.strip()})

passed=sum(c['status']=='PASS' for c in checks); failed=len(checks)-passed
result={
 'status':'PASS' if failed==0 else 'FAIL',
 'evidence_class':['observed-bytes','static-analysis'],
 'scope':'bounded literal/name comparison only; no disassembly rerun, hardware, network, sysfs, or writes',
 'inputs':{'rom':str(ROM),'rom_size':len(rom),'rom_sha256':rom_sha,'selector_result':str(SELECTOR),'selector_result_sha256':sha(SELECTOR)},
 'selector_example':example,
 'address_interpretation_from_completed_result':{
   'program_smn_address':'0x0116D150',
   'poll_smn_address':'0x0116D174',
   'selector_index':11,'array_entry':10,'domain_id':'0x18','internal_group':6,
   'target_slot':'0x140B0','raw_program_offset':'0x6D150',
 },
 'local_register_headers':header_inventory,
 'literal_address_matches':matches,
 'explicit_clock_domain_symbol_lines':symbols,
 'verdict':'NO_DIRECT_HEADER_MATCH' if not matches else 'HEADER_LITERAL_MATCH_REQUIRES_SEMANTIC_REVIEW',
 'semantic_limit':'A miss is only a bounded literal absence. The source set does not independently map Group 6/domain 0x18 or SMN 0x0116D150/0x0116D174 to MCLK, UCLK, FCLK, DF, UMC, a divider, or a crossing selector.',
 'checks':{'passed':passed,'failed':failed,'total':len(checks)},'checks_detail':checks,
}
OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':result['status'],'checks':result['checks'],'program':'0x0116D150','poll':'0x0116D174','domain_id':'0x18','header_count':len(HEADERS),'literal_matches':len(matches),'domain_symbols':len(symbols),'verdict':result['verdict'],'output':str(OUT.resolve())},sort_keys=True))
raise SystemExit(0 if failed==0 else 1)
