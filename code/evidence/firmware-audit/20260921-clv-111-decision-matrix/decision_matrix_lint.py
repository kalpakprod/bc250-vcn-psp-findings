#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, re, sys
root=Path('/home/OWNER/orca/projects/bc250')
out=root/'docs/guides/bc250-clv-111-decision-matrix.md'
checks=[]
def ck(name,ok,detail):
    checks.append({'name':name,'status':'PASS' if ok else 'FAIL','detail':detail})
    if not ok: raise SystemExit(json.dumps({'status':'FAIL','failed':name,'detail':detail}))
s=out.read_text()
raw=out.read_bytes()
ck('utf8-lf-no-trailing-whitespace', b'\r' not in raw and all(not line.endswith((' ', '\t')) for line in s.splitlines()), 'LF and no trailing whitespace')
section_numbers=[int(x) for x in re.findall(r'^## ([0-9]+)\.',s,re.M)]
ck('section-numbers-consecutive-unique',section_numbers==list(range(1,11)),str(section_numbers))
for token in ['DRAFT','NOT READY','NO-GO','UNRUN','Exact native menu map','Candidate-setting decisions','Required operator readbacks','Rollback and stop conditions','Evidence ledger','0x20F','0x229','0x25E','0x7045','0x37D','0x37E','0x5CBE','0xFE60','0x7E3A','0x5FBA','Hardware acceptance']:
    ck('required:'+token, token in s, f'present={token in s}')
for forbidden in ['PHYSICAL_1TO1TO1_PASS','SoC 1.15 V is safe','1.15 V recommended','1:1:1 PASS']:
    ck('no-unqualified:'+forbidden, forbidden not in s, f'absent={forbidden not in s}')
# Hash-pinned source ledger check.
sources={
'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin':'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8',
'docs/research/2026-09-20-clv-native-menu-1to1-guide.md':'03a7239adf248a32558ea8fc0bea801325cb010035a41198df888350aa8236e6',
'docs/research/2026-09-20-clv-sync-configuration-domain-matrix.md':'6441b5c1cc7f5e19d478be690a0136a608e83ab4f1ac770fde8a8b5d74973841',
'docs/research/2026-09-21-hardware-baseline-consolidated.md':'7c9b494697581339beb3f4af3423f7852bf4eee6e50ef1964f959c2e1a11812c',
'docs/research/2026-09-21-baseline-nvram-ledger.md':'d130ba9663cdfa3cdf67b07ba11f33fcf3b1c483cc33d815f82b7abcaeb4d7d7',
'docs/research/2026-09-21-manual-voltage-safety-matrix.md':'e43bb1d0108bb58ab8a81bb87bb5768e76ccf42d1b958424540c111a9926cb9d',
'docs/research/2026-09-21-voltage-evidence-integration.md':'9dda181dc478400d8e06313296674572fdb00bebb50dfedc4d2bee8703b91d36',
'docs/research/2026-09-21-latency-protocol-reviewed.md':'11d15b3a2158c71290e917ee0339bfc000bf2a74655b94fe0e4979f7d75ebcfb',
'docs/research/2026-09-21-abl7378-indirect-entry.md':'c15b43356e66dcdad621e0cf2f89a61af43dc00d84b32d8a8b15fc1bb79952c8',
'docs/research/2026-09-21-abl-item17-reachable-output.md':'6c3c528cc2b8669d48a7a98067b3241c0adb9daf983b9dca539f80f06d597122',
'docs/research/2026-09-21-apob-abl-outer864-root-verification.md':'13f9575b8ffcd6cb275cf19e87d714334d81ca749327fe3b4988aafbbb2821d2',
}
for rel,expected in sources.items():
    p=root/rel
    ck('source:'+rel, p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==expected, f'expected={expected} actual={hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else "MISSING"}')
ck('original-guide-unchanged', hashlib.sha256((root/'docs/guides/bc250-clv-111-evidence-draft.md').read_bytes()).hexdigest()=='334d6b879156bb2ba773c2d2d766ddc54cbacd37e33e3eab3bab949d2fe8e065','original guide hash stable')
obj={'status':'PASS','checks':{'passed':len(checks),'failed':0,'total':len(checks)},'output':str(out),'output_sha256':hashlib.sha256(raw).hexdigest(),'details':checks}
res=Path(__file__).with_name('decision-matrix-lint-result.json'); res.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':'PASS','checks':obj['checks'],'output_sha256':obj['output_sha256'],'result':str(res)},sort_keys=True))
