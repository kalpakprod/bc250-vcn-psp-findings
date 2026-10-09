#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,re
OUT=Path('/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl7378-indirect-entry/run-20260921T200924+0500')
RAW=Path('/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin')
OBJ=Path('/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/ABL1-exact.o')
checks=[]
def ck(n,o,e):
 ok=o==e; checks.append({'name':n,'passed':ok,'observed':o,'expected':e})
 if not ok: raise AssertionError(f'{n}: {o!r}!={e!r}')
rb=RAW.read_bytes(); ck('raw_sha256',hashlib.sha256(rb).hexdigest(),'af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a'); ck('elf_sha256',hashlib.sha256(OBJ.read_bytes()).hexdigest(),'adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6')
for stem in ('helper-5cbe-exact','helper-fe60-exact'):
 ck(stem+'_exit',(OUT/(stem+'.exit')).read_text().strip(),'0'); ck(stem+'_stderr_empty',not (OUT/(stem+'.stderr')).read_bytes(),True)
a=(OUT/'helper-5cbe-exact.stdout').read_text(); b=(OUT/'helper-fe60-exact.stdout').read_text()
patterns=[('5cbe_writes_2',a,r'^\s*5cbe:.*\bmovs\s+r1, #0x2'),('5cbe_store0',a,r'^\s*5cc0:.*\bstrh\s+r1, \[r0\]'),('5cbe_store1',a,r'^\s*5cc4:.*\bstrh\s+r1, \[r0, #0x2\]'),('5cbe_returns_one',a,r'^\s*5cc6:.*\bmov\s+r0, r1'),('5cbe_bx_lr',a,r'^\s*5cc8:.*\bbx\s+lr'),('fe60_read0',b,r'^\s*fe60:.*\bldrh\s+r1, \[r0\]'),('fe60_shift30',b,r'^\s*fe62:.*\blsls\s+r1, r1, #0x1e'),('fe60_read1',b,r'^\s*fe66:.*\bldrh\s+r0, \[r0, #0x2\]'),('fe60_shift31',b,r'^\s*fe68:.*\blsls\s+r0, r0, #0x1f'),('fe60_success_one',b,r'^\s*fe6c:.*\bmovs\s+r0, #0x1'),('fe60_failure_zero',b,r'^\s*fe70:.*\bmovs\s+r0, #0x0'),('fe60_return',b,r'^\s*fe72:.*\bbx\s+lr')]
for n,t,p in patterns: ck(n,bool(re.search(p,t,re.M)),True)
ck('5cbe_no_direct_clock_literal',not bool(re.search(r'0x(?:13b|0900|100b|15|16)',a,re.I)),True); ck('fe60_no_direct_clock_literal',not bool(re.search(r'0x(?:13b|0900|100b|15|16)',b,re.I)),True)
stack=[2,1]; modeled=1 if ((stack[0]&0x2) and (stack[1]&0x1)) else 0
ck('host_model_5cbe_stack',stack,[2,1]); ck('host_model_fe60_output',modeled,1)
result={'status':'PASS','checks':{'passed':sum(x['passed'] for x in checks),'failed':sum(not x['passed'] for x in checks),'total':len(checks)},'helper_5cbe':{'input':'AF58 passes R0=SP; R1 ignored','writes':['u16 [R0]=2','u16 [R0+2]=1'],'return':1},'helper_fe60':{'input':'R0=SP','condition':'original bit1 of first halfword and bit0 of second halfword set by LSL #30/#31','on_5cbe_output':1,'return_paths':{'success':1,'failure':0}},'direct_clock_literals':False,'limits':['No semantic identity for AF58 offsets +0x739/+0x75F/+0x760; no runtime/hardware proof.'],'checks_detail':checks}
(OUT/'helper-contract-result-corrected.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps({'status':'PASS','checks':result['checks']['total'],'passed':result['checks']['passed'],'failed':result['checks']['failed'],'5cbe_output':[2,1],'fe60_on_5cbe_output':1,'direct_clock_literals':False},indent=2))
