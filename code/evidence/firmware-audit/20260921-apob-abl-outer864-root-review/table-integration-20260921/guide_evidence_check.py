#!/usr/bin/env python3
import hashlib, json, pathlib, sys
root=pathlib.Path('/home/OWNER/orca/projects/bc250')
mod=root/'docs/guides/bc250-clv-111-evidence-draft-corrected.md'
afst= root/'docs/research/2026-09-21-abl7378-indirect-entry.md'
afr= root/'evidence/firmware-audit/20260921-abl7378-indirect-entry/run-20260921T200924+0500/helper-contract-result-corrected.json'
item= root/'docs/research/2026-09-21-abl-item17-reachable-output.md'
checks=[]
def ck(name, ok, detail):
    checks.append({'name':name,'status':'PASS' if ok else 'FAIL','detail':detail})
    if not ok: raise SystemExit(json.dumps({'status':'FAIL','failed':name,'detail':detail}))
s=mod.read_text(); a=afst.read_text(); ir=item.read_text(); result=json.loads(afr.read_text())
for token in ['HEAP claim status: WITHDRAWN','ABL1 AF58 helper contract','Item `0x17` callback/output edge','Hardware acceptance gate','0x5CBE','0xFE60','[2,1]','0x7378','0xAF90','no frequency/unit/clock meaning established','NOT READY']:
    ck('guide-token:'+token, token in s, f'present={token in s}')
ck('af58-report-result-pass','Corrected machine result: `helper-contract-result-corrected.json`, `PASS`, `22/22`' in a,'report corrected result line present')
ck('af58-report-no-direct-clock-link','No direct clock-policy literal or clock register operation occurs in either exact helper body.' in a,'AF58 helper limit present')
ck('af58-machine-status',result.get('status')=='PASS' and result.get('checks',{}).get('total')==22, str(result.get('checks')))
ck('af58-input-hash',hashlib.sha256(afr.read_bytes()).hexdigest()=='7fa682acc22fb4fe186e529d3c63992e45bda83acdf4159d0d87e81a607267f2',hashlib.sha256(afr.read_bytes()).hexdigest())
ck('item17-conditional-boundary','conditional' in ir.lower() and 'No frequency or clock unit is assigned.' in ir, 'item17 report preserves conditional/no-unit boundary')
ck('item17-hardware-boundary','hardware' in ir.lower() and 'No ROM, firmware' in ir, 'item17 report retains no-hardware-action boundary')
obj={'status':'PASS','checks':{'passed':len(checks),'failed':0,'total':len(checks)},'guide':str(mod),'af58_report':str(afst),'af58_result':str(afr),'item17_report':str(item),'details':checks}
path=pathlib.Path(__file__).with_name('guide-evidence-result.json'); path.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':'PASS','checks':obj['checks'],'result':str(path)},sort_keys=True))
