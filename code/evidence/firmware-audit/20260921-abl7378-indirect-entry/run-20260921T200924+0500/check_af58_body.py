#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,struct,re
OUT=Path('/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl7378-indirect-entry/run-20260921T200924+0500')
RAW=Path('/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin')
OBJ=Path('/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/ABL1-exact.o')
checks=[]
def check(n,o,e):
 ok=o==e; checks.append({'name':n,'passed':ok,'observed':o,'expected':e})
 if not ok: raise AssertionError(f'{n}: {o!r} != {e!r}')
b=RAW.read_bytes(); text=(OUT/'target-af58-body.stdout').read_text()
check('raw_sha256',hashlib.sha256(b).hexdigest(),'af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a')
check('raw_size',len(b),94624)
check('ELF_sha256',hashlib.sha256(OBJ.read_bytes()).hexdigest(),'adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6')
check('AF58_objdump_exit',(OUT/'target-af58-body.exit').read_text().strip(),'0')
check('AF58_objdump_stderr_empty',not (OUT/'target-af58-body.stderr').read_bytes(),True)
for n,p in (('af58_push',r'^\s*af58:.*\bpush\s+\{r3, r4, r5, lr\}'),('save_incoming_r0',r'^\s*af5a:.*\bmovs\s+r4, r0'),('null_branch',r'^\s*af5c:.*\bbne\s+0xaf64'),('null_helper_call',r'^\s*af60:.*\bbl\s+0x64c8'),('forward_saved_r0_as_r1',r'^\s*af64:.*\bmov\s+r1, r4'),('pass_stack_as_r0',r'^\s*af66:.*\bmov\s+r0, sp'),('opaque_call_5cbe',r'^\s*af68:.*\bbl\s+0x5cbe'),('opaque_call_fe60',r'^\s*af6e:.*\bbl\s+0xfe60'),('result_compare',r'^\s*af72:.*\bcmp\s+r0, #0x0'),('write_739',r'^\s*af7a:.*\bstrb\.w\s+r0, \[r1, #0x739\]'),('write_75f',r'^\s*af80:.*\bstrb\.w\s+r0, \[r1, #0x75f\]'),('write_760',r'^\s*af86:.*\bstrb\.w\s+r0, \[r1, #0x760\]'),('return',r'^\s*af8a:.*\bpop\s+\{r3, r4, r5, pc\}')):
 check(n,bool(re.search(p,text,re.M)),True)
check('no_direct_BL_7378',not bool(re.search(r'\bbl\s+0x7378\b',text,re.I)),True)
check('no_direct_BL_AF90',not bool(re.search(r'\bbl\s+0xaf90\b',text,re.I)),True)
check('table_count_byte_RVA_17100',b[0x17100],2)
check('record0_callback_field_RVA_170D0',struct.unpack_from('<I',b,0x170d0)[0],0x62059)
check('record1_callback_field_RVA_170F4',struct.unpack_from('<I',b,0x170f4)[0],0)
result={'status':'PASS','checks':{'passed':sum(x['passed'] for x in checks),'failed':sum(not x['passed'] for x in checks),'total':len(checks)},'inputs':{'raw':str(RAW),'raw_sha256':hashlib.sha256(b).hexdigest(),'elf':str(OBJ),'elf_sha256':hashlib.sha256(OBJ.read_bytes()).hexdigest()},'target':{'callback_pointer':'0x62059','conditional_base':'0x57100 (unproven)','conditional_rva':'0xaf58','direct_calls':['0x64c8 (null-R0 only)','0x5cbe (R0=SP, R1=saved incoming R0)','0xfe60 (R0=SP)'],'memory_writes':['[R4+0x28]+0x739','[R4+0x28]+0x75f','[R4+0x28]+0x760'],'return':'0xaf8a pop {r3,r4,r5,pc}','direct_link_to_7378':False,'direct_link_to_AF90':False,'opaque_boundaries':['0x5cbe','0xfe60']},'table_termination':{'count_pointer':'0x6e200 -> conditional RVA 0x17100','count_byte':2,'record_stride':'0x24','record0_plus8':'0x62059','record1_plus8':'0x0','later_records_interpreted':False},'limits':['No runtime execution or indirect callee semantics; 0x5cbe and 0xfe60 were not followed in this bounded task.','No clock-policy identity inferred from context-relative byte offsets.','Conditional base 0x57100 remains unproven.'],'checks_detail':checks}
(OUT/'af58-body-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'checks':result['checks']['total'],'passed':result['checks']['passed'],'failed':result['checks']['failed'],'target':'0x62059 -> conditional RVA 0xaf58','direct_link_to_7378':False,'direct_link_to_AF90':False,'opaque_boundaries':['0x5cbe','0xfe60']},indent=2))
