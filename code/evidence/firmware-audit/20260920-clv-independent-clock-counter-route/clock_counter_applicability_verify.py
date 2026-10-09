#!/usr/bin/env python3
"""Bounded exact-clv applicability check for the imported RLC counter header."""
from __future__ import annotations
import hashlib,json,struct,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin';OFF=ROOT/'import/from-windows/Users/kukuruza/tmp_bc250/recon/gc_10_1_0_offset.h';MASK=ROOT/'import/from-windows/Users/kukuruza/tmp_bc250/recon/gc_10_1_0_sh_mask.h';SMU_SRC=ROOT/'import/from-windows/Users/kukuruza/tmp_bc250/recon/smu_v11_0.c';ACT=ROOT/'docs/research/oc-clock-actuator-chain.md'
checks=[]
def sha(value):
    data=value if isinstance(value,(bytes,bytearray)) else Path(value).read_bytes()
    return hashlib.sha256(data).hexdigest()
def ck(ok,label,got,exp):checks.append({'label':label,'status':'PASS' if ok else 'FAIL','got':got,'expected':exp});return ok
rom=ROM.read_bytes();ck(sha(ROM)=='ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8','rom-hash',sha(ROM),'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8');
# Exact PSP type 0x08 container/body extraction.
psp=0x8e0000; entries=[]
for i in range(19):
 e=psp+0x10+i*16; typ=rom[e]; size=int.from_bytes(rom[e+4:e+8],'little'); loc=int.from_bytes(rom[e+8:e+12],'little')&0xffffff; entries.append((typ,size,loc))
t8=next(x for x in entries if x[0]==8); blob=rom[t8[2]:t8[2]+t8[1]]; body=blob[0x100:]
ck(len(body)==0x40100,'clv-type8-body-length',len(body),0x40100);ck(sha(body)=='cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37','type8-body-hash-recorded?',sha(body),'cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37')
# Direct scalar literals in exact PMFW body; no new disassembler assumptions.
refs={}
for val in range(0x4c30,0x4c36):
 pat=struct.pack('<I',val); refs[hex(val)]=[hex(i) for i in range(len(body)-3) if body[i:i+4]==pat]
 ck(len(refs[hex(val)])==0,f'PMFW-direct-literal-{hex(val)}',refs[hex(val)],[])
# Header terminology/base-index is explicit but no CLV binding.
o=OFF.read_text();m=MASK.read_text();
for n in ['mmRLC_CLK_COUNT_GFXCLK_LSB','mmRLC_CLK_COUNT_GFXCLK_MSB','mmRLC_CLK_COUNT_REFCLK_LSB','mmRLC_CLK_COUNT_REFCLK_MSB','mmRLC_CLK_COUNT_CTRL','mmRLC_CLK_COUNT_STAT']:
 mm=re.search(rf'^#define {n}\s+0x([0-9A-Fa-f]+)',o,re.M); bi=re.search(rf'^#define {n}_BASE_IDX\s+(\d+)',o,re.M);ck(mm is not None,f'header-offset-{n}',bool(mm),True);ck(bi is not None and bi.group(1)=='1',f'header-base-index-{n}',bi.group(1) if bi else None,'1')
ck('RLC_CLK_COUNT_GFXCLK' not in SMU_SRC.read_text(),'SMU-source-no-counter-usage','no direct symbol in retained SMU source',True);ck('Does NOT sample hardware PLL counters' in ACT.read_text(),'existing-negative-SMU-query','negative semantics retained',True)
result={'status':'PASS' if all(x['status']=='PASS' for x in checks) else 'FAIL','checks':{'passed':sum(x['status']=='PASS' for x in checks),'failed':sum(x['status']=='FAIL' for x in checks),'total':len(checks)},'exact_clv':{'rom_sha256':sha(ROM),'psp_type8_container_offset':hex(t8[2]),'container_size':hex(t8[1]),'body_sha256':sha(body),'direct_literals':refs},'header':{'register_offsets':'DWORD-index declarations with BASE_IDX=1 in imported header','exact_clv_binding':'not established'},'decision':'The RLC counter block remains an external-primary/source static prototype only. No direct 0x4C30..0x4C35 literal was found in the exact CLV type-0x08 PMFW body, no retained SMU source uses the symbols, and no UMC/DF/UCLK binding exists in this bounded evidence. Do not adopt this block as an exact-board MCLK/UCLK/FCLK route until domain/register provenance is recovered.', 'limits':['A computed/indirect register route may exist outside direct scalar literal scan.','No hardware or live read.','No DWORD-index-to-byte-MMIO conversion is assumed for this board.'],'checks_detail':checks}
(OUT/'clock-counter-applicability-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'status':result['status'],'checks':result['checks'],'exact_clv':result['exact_clv'],'decision':result['decision']},sort_keys=True));raise SystemExit(0 if result['status']=='PASS' else 1)
