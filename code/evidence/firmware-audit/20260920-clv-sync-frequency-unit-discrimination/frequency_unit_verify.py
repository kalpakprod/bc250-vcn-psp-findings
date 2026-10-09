#!/usr/bin/env python3
"""Small host-only discriminator for MCLK/UCLK/FCLK evidence provenance."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
DRIVER=ROOT/'import/from-windows/Users/kukuruza/tmp_bc250/recon/cyan_skillfish_ppt.c'
HANDLERS=ROOT/'evidence/firmware-audit/20260919-oc-clock-provenance/clock-handlers-verification.json'
DOMAINS=ROOT/'evidence/firmware-audit/20260919-oc-clock-provenance/fabric-domains-verification.json'
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
OUT=Path(__file__).resolve().parent/'frequency-unit-result.json'
EXPECTED_ROM='ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
EXPECTED_DRIVER='9259ad3ff6f660fe97ca7ea68f9b7e5f5d185982f0d3341180bd880442f030f1'
checks=[]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def check(label,ok,details=None): checks.append({'label':label,'status':'PASS' if ok else 'FAIL','details':details})
rom_sha=sha(ROM); driver_sha=sha(DRIVER)
check('pinned-rom',rom_sha==EXPECTED_ROM,{'observed':rom_sha,'expected':EXPECTED_ROM})
check('driver-hash',driver_sha==EXPECTED_DRIVER,{'observed':driver_sha,'expected':EXPECTED_DRIVER})
text=DRIVER.read_text(errors='replace')
required={
 'metric-uclk-reads-memclk':'case METRICS_CURR_UCLK:' in text and '*value = metrics->Current.MemclkFrequency;' in text,
 'clock-fclk-mclk-select-uclk':'case SMU_FCLK:' in text and 'case SMU_MCLK:' in text and 'member_type = METRICS_CURR_UCLK;' in text,
 'gpu-average-alias':'gpu_metrics->average_uclk_frequency = metrics.Average.MemclkFrequency;' in text and 'gpu_metrics->average_fclk_frequency = metrics.Average.MemclkFrequency;' in text,
 'gpu-current-alias':'gpu_metrics->current_uclk = metrics.Current.MemclkFrequency;' in text and 'gpu_metrics->current_fclk = metrics.Current.MemclkFrequency;' in text,
 'gfx-mclk-alias':'case AMDGPU_PP_SENSOR_GFX_MCLK:' in text and 'METRICS_CURR_UCLK' in text,
}
for k,v in required.items(): check(k,v)
h=json.loads(HANDLERS.read_text()); d=json.loads(DOMAINS.read_text())
check('handler-software-state', 'software committed frequency float' in h['handler_0x2ea74']['proven_behavior'] and 'No PLL hardware sampling' in h['handler_0x2ea74']['proven_behavior'], h['handler_0x2ea74']['proven_behavior'])
check('handler-df-query-not-frequency','state index delta' in h['handler_0x1e988']['proven_behavior'] and 'NOT a frequency measurement' in h['handler_0x1e988']['proven_behavior'],h['handler_0x1e988']['proven_behavior'])
check('domain-physical-unknown',all(x.get('physical_domain_meaning')=='UNKNOWN_WITHOUT_RUNTIME_CONFIRMATION' for x in d['clock_domains']),{'domain_count':len(d['clock_domains'])})
check('uclk-divisor-unestablished','UCLK mapping/control unestablished' in h['uclk_divisor_status']['conclusion'])
passed=sum(x['status']=='PASS' for x in checks); failed=len(checks)-passed
result={
 'status':'PASS' if failed==0 else 'FAIL','evidence_class':['observed-bytes','static-analysis','emulated-or-host-tested'],
 'inputs':{'rom':str(ROM),'rom_sha256':rom_sha,'driver':str(DRIVER),'driver_sha256':driver_sha,'handlers':str(HANDLERS),'domains':str(DOMAINS)},
 'demonstrated_mapping':{
   'host_driver':{'status':'SOURCE_ALIAS_ONLY','mapping':'SMU_FCLK and SMU_MCLK select METRICS_CURR_UCLK; that metric reads Current.MemclkFrequency; gpu_metrics current/average UCLK and FCLK also copy MemclkFrequency.','not_proven':['independent physical FCLK/UCLK/MCLK','GDDR6 unit conversion','synchronous crossing']},
   'firmware_query':{'status':'SOFTWARE_STATE_ONLY','mapping':'Queue0 0x11 handler 0x2EA74 returns an internal committed-frequency float indexed through the 20-domain table; Queue0 0x13 returns a P-state index delta/count.','not_proven':['hardware PLL/clock sampling','physical domain identity for MCLK/UCLK/FCLK']},
   'domain_map':{'status':'STATIC_GROUPS_ONLY','mapping':'Existing fabric-domain evidence provides SMN apertures/group assignments but marks physical domain meaning unknown without runtime confirmation.'},
 },
 'smallest_offline_discriminating_check':{'executed':True,'method':'Exact source-fragment alias check plus retained byte-verified handler/domain-result assertions; no sysfs or live telemetry.', 'result':'PASS_STATIC_REJECTS_INDEPENDENT_METRIC_CLAIM','interpretation':'The available host metrics are aliased software values, and the available firmware clock query is software committed state. Neither supplies an independent MCLK/UCLK/FCLK physical mapping.'},
 'checks':{'passed':passed,'failed':failed,'total':len(checks)},'checks_detail':checks,
 'limits':['No new parser or dependency; no firmware/hardware/telemetry action.','This check does not resolve GDDR6 edge/data-rate conversion, actual physical domain identity, training range, or synchronization.']
}
OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':result['status'],'checks':result['checks'],'output':str(OUT.resolve())},sort_keys=True))
raise SystemExit(0 if failed else 0)
