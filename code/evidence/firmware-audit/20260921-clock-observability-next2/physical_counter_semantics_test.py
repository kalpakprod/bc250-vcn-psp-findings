#!/usr/bin/env python3
"""Offline proof of the retained amdgpu GPU-counter semantics.

Reads only imported source and the pinned CLV image.  It does not access live
hardware, sysfs, network, firmware, NVRAM, registers, or the unsafe clock
probe.  The result is a bounded source-semantic classification.
"""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path

ROOT = Path('/home/OWNER/orca/projects/bc250')
ROM = ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
GFX = ROOT/'import/from-windows/Users/kukuruza/tmp_bc250/recon/linux-kiq-diff/gfx_v10_0-final.c'
HDR = ROOT/'import/from-windows/Users/kukuruza/tmp_bc250/recon/vcn-source-context/drivers/gpu/drm/amd/amdgpu/amdgpu.h'
DISC = ROOT/'import/from-windows/Users/kukuruza/tmp_bc250/recon/vcn-source-context/drivers/gpu/drm/amd/amdgpu/amdgpu_discovery.c'
OUT = Path(__file__).resolve().parent/'physical-counter-semantics-result.json'
EXPECTED = {
    'rom': 'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8',
    'gfx': 'd08eceff9418bd1fc99ab9024b7e2e7827629a093e0754a0ecb7e92c84a09ae0',
    'hdr': '2a3c6653038867f7d66764d78fa0058278d0f151fe17750c7f0daa2522e3fe90',
}

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def check(items, name, ok, observed, expected):
    items.append({'name':name,'status':'PASS' if ok else 'FAIL','observed':observed,'expected':expected})

rom = ROM.read_bytes(); gfx = GFX.read_text(errors='replace'); hdr = HDR.read_text(errors='replace'); disc = DISC.read_text(errors='replace')
checks=[]
check(checks,'clv-size',len(rom)==0x1000000,len(rom),0x1000000)
check(checks,'clv-sha256',sha(ROM)==EXPECTED['rom'],sha(ROM),EXPECTED['rom'])
check(checks,'clv-memory-request-preserved',rom[0x7e5]==0x24,{'offset':'0x7E5','value':hex(rom[0x7e5])},{'offset':'0x7E5','value':'0x24','label':'1800MHz-request'})
check(checks,'gfx-source-sha256',sha(GFX)==EXPECTED['gfx'],sha(GFX),EXPECTED['gfx'])
check(checks,'amdgpu-header-sha256',sha(HDR)==EXPECTED['hdr'],sha(HDR),EXPECTED['hdr'])

start = gfx.index('static uint64_t gfx_v10_0_get_gpu_clock_counter(')
end = gfx.index('\nstatic void gfx_v10_0_ring_emit_gds_switch', start)
fn = gfx[start:end]
# Keep direct source evidence to the target IP branch and counter definitions.
upper = '#define mmGOLDEN_TSC_COUNT_UPPER_GC_10_3_6                0x002d'
lower = '#define mmGOLDEN_TSC_COUNT_LOWER_GC_10_3_6                0x002e'
check(checks,'ip10.3.6-counter-address-upper',upper in gfx,upper in gfx,True)
check(checks,'ip10.3.6-counter-address-lower',lower in gfx,lower in gfx,True)
check(checks,'ip10.3.6-counter-base-index',
      '#define mmGOLDEN_TSC_COUNT_UPPER_GC_10_3_6_BASE_IDX       1' in gfx and '#define mmGOLDEN_TSC_COUNT_LOWER_GC_10_3_6_BASE_IDX       1' in gfx,
      {'upper_base_idx_1':'#define mmGOLDEN_TSC_COUNT_UPPER_GC_10_3_6_BASE_IDX       1' in gfx,'lower_base_idx_1':'#define mmGOLDEN_TSC_COUNT_LOWER_GC_10_3_6_BASE_IDX       1' in gfx}, {'upper':1,'lower':1})
check(checks,'target-branch-selects-gc10.3.6', 'case IP_VERSION(10, 3, 6):' in fn and 'UPPER_GC_10_3_6' in fn and 'LOWER_GC_10_3_6' in fn,
      {'branch':'case IP_VERSION(10, 3, 6):' in fn,'upper':'UPPER_GC_10_3_6' in fn,'lower':'LOWER_GC_10_3_6' in fn},True)
check(checks,'triple-read-hi-lo-hi',
      fn.count('RREG32_SOC15_NO_KIQ(SMUIO, 0, mmGOLDEN_TSC_COUNT_UPPER_GC_10_3_6)')==2 and fn.count('RREG32_SOC15_NO_KIQ(SMUIO, 0, mmGOLDEN_TSC_COUNT_LOWER_GC_10_3_6)')==2,
      {'upper_reads':fn.count('RREG32_SOC15_NO_KIQ(SMUIO, 0, mmGOLDEN_TSC_COUNT_UPPER_GC_10_3_6)'), 'lower_reads':fn.count('RREG32_SOC15_NO_KIQ(SMUIO, 0, mmGOLDEN_TSC_COUNT_LOWER_GC_10_3_6)')}, {'upper_reads':2,'lower_reads':2})
check(checks,'tear-safe-hi-retry', 'if (hi_check != clock_hi)' in fn and 'clock_hi = hi_check;' in fn and 'clock = clock_lo | (clock_hi << 32ULL);' in fn,
      {'retry':'if (hi_check != clock_hi)' in fn,'recombine':'clock = clock_lo | (clock_hi << 32ULL);' in fn},True)
check(checks,'source-documents-100mhz-timebase', fn.count('The SMUIO TSC clock frequency is 100MHz')>=1, fn.count('The SMUIO TSC clock frequency is 100MHz'), '>=1')
check(checks,'callback-registered', '.get_gpu_clock_counter = &gfx_v10_0_get_gpu_clock_counter' in gfx, '.get_gpu_clock_counter = &gfx_v10_0_get_gpu_clock_counter' in gfx, True)
check(checks,'public-macro-dispatches-callback', 'amdgpu_asic_get_gpu_clock_counter(adev)' in hdr and 'asic_funcs->get_gpu_clock_counter' in hdr,
      {'macro':'amdgpu_asic_get_gpu_clock_counter(adev)' in hdr,'callback':'asic_funcs->get_gpu_clock_counter' in hdr},True)
check(checks,'counter-is-not-mclk-uclk-fclk', not re.search(r'(?i)MCLK|UCLK|FCLK|DF|UMC|PLL|RLC_CLK_COUNT', fn),
      {'domain_terms':sorted(set(re.findall(r'(?i)MCLK|UCLK|FCLK|DF|UMC|PLL|RLC_CLK_COUNT',fn)))},[])
check(checks,'discovery-identifies-ip10.3.6-family', 'case IP_VERSION(10, 3, 6):' in disc and 'AMDGPU_FAMILY_GC_10_3_6' in disc,
      {'ip_branch':'case IP_VERSION(10, 3, 6):' in disc,'family':'AMDGPU_FAMILY_GC_10_3_6' in disc},True)

passed=sum(x['status']=='PASS' for x in checks); failed=len(checks)-passed
result={
 'status':'PASS' if failed==0 else 'FAIL',
 'evidence_class':['observed-bytes','static-analysis'],
 'scope':'offline only; no board/sysfs/network/register/firmware/NVRAM action and no clock probe invocation',
 'inputs':{'rom':str(ROM),'rom_sha256':sha(ROM),'gfx_source':str(GFX),'gfx_source_sha256':sha(GFX),'amdgpu_header':str(HDR),'amdgpu_header_sha256':sha(HDR),'discovery_source':str(DISC),'discovery_source_sha256':sha(DISC)},
 'demonstrated_path':{
   'callback':'amdgpu_asic_get_gpu_clock_counter -> adev->asic_funcs->get_gpu_clock_counter -> gfx_v10_0_get_gpu_clock_counter',
   'target_ip_branch':'IP_VERSION(10, 3, 6) selects SMUIO GC_10_3_6 Golden TSC upper 0x002D and lower 0x002E (DWORD register indices, BASE_IDX=1)',
   'read_algorithm':'RREG32 upper, lower, upper; retry lower/high if upper changed; combine 64-bit counter',
   'source_semantics':'driver comment identifies SMUIO TSC frequency as 100MHz; this is an independent timebase counter, not a memory/fabric/GDDR6 clock counter',
 },
 'not_demonstrated':[
   'exact installed BC-250 kernel/module identity or source-revision equivalence',
   'MCLK/UMC physical counter or PLL/divider readback',
   'UCLK divider/ratio and crossing/synchronous status',
   'FCLK/DF physical counter or PLL/divider readback',
   'common reference calibration converting any domain counter to MHz/GDDR6 rate',
   'hardware readback and acceptance on BC250-01',
 ],
 'future_hardware_acceptance_procedure':None,
 'missing_hardware_inputs':'Need an exact installed-driver/firmware mapping for UMC/MCLK, UCLK divider/ratio, and DF/FCLK PLL/counter/status registers, plus a safe read-only transport and common-reference calibration. The SMUIO TSC alone cannot establish MCLK:UCLK:FCLK=1:1:1.',
 'checks':{'passed':passed,'failed':failed,'total':len(checks)},'checks_detail':checks,
}
OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':result['status'],'checks':result['checks'],'ip10.3.6_upper':'0x002D','ip10.3.6_lower':'0x002E','timebase':'100MHz SMUIO TSC','physical_mclk_uclk_fclk':False,'future_procedure':None,'output':str(OUT.resolve())},sort_keys=True))
raise SystemExit(0 if failed==0 else 1)
