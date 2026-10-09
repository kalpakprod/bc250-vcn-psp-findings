#!/usr/bin/env python3
"""Verify the bounded ABL1 callback-provider byte chain from pinned local inputs."""
from __future__ import annotations
import hashlib, json, re, struct
from pathlib import Path
ROOT=Path('/home/OWNER/orca/projects/bc250')
OUT=ROOT/'evidence/firmware-audit/20260921-abl-callback-targets'
RAW=ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
OBJ=ROOT/'evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/ABL1-exact.o'
checks=[]
def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def u32(data:bytes,off:int)->int: return struct.unpack_from('<I',data,off)[0]
def check(name,observed,expected):
    ok=observed==expected
    checks.append({'name':name,'passed':ok,'observed':observed,'expected':expected})
    if not ok: raise AssertionError(f'{name}: {observed!r} != {expected!r}')
raw=RAW.read_bytes(); obj=OBJ.read_bytes()
check('raw_payload_sha256',hashlib.sha256(raw).hexdigest(),'af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a')
check('raw_payload_size',len(raw),94624)
check('ELF_object_sha256',hashlib.sha256(obj).hexdigest(),'adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6')
check('ELF_data_bytes_equal_raw_payload',obj[0x1a8:0x1a8+len(raw)]==raw,True)
check('caller_table_pointer_literal_0x141c',u32(raw,0x141c),0x6e27c)
check('list_provider_record_literal_0x5510',u32(raw,0x5510),0x6e284)
check('record_initializer_pointer_literals_0x50d4',tuple(u32(raw,x) for x in (0x50d4,0x50dc,0x50e0,0x50e4)),(0x587b1,0x58659,0x5865d,0x58661))
check('callback_list_words_at_RVA_0x1717c',tuple(u32(raw,x) for x in (0x1717c,0x17180)),(0x6e284,0))
check('descriptor_function_fields_at_RVA_0x17184',tuple(u32(raw,x) for x in (0x17184,0x17188,0x1718c,0x17190)),(0x587b1,0x58659,0x5865d,0x58661))
check('BLX_R0_target_is_Thumb_pointer',bool(u32(raw,0x50d4)&1),True)
base=0x57100  # Prior report's conditional static base only; runtime base unproven.
check('conditional_table_base_maps_to_RVA_0x1717c',0x6e27c-base,0x1717c)
check('conditional_record_pointer_maps_to_RVA_0x17184',0x6e284-base,0x17184)
check('conditional_target_maps_to_RVA_0x16b0',(0x587b1 & ~1)-base,0x16b0)
check('target_entry_bytes_at_RVA_0x16b0',raw[0x16b0:0x16b6].hex(), '014800787047')
check('callback_literal_at_RVA_0x16b8',u32(raw,0x16b8),0x6e131)
# Require the fresh bounded LLVM Thumb windows and their exact observed edge/initializer instructions.
windows={
 'caller':'provider-thumb-1320-1420',
 'list_provider':'provider-54fc-557c',
 'record_initializer':'provider-helper-50c0-5120',
 'target_entry':'target-entry-16b0-16b6',
}
for key,stem in windows.items():
    check(f'{key}_LLVM_exit', (OUT/f'{stem}.exit').read_text().strip(),'0')
    check(f'{key}_LLVM_stderr_empty', not (OUT/f'{stem}.stderr').read_bytes(),True)
caller=(OUT/'provider-thumb-1320-1420.stdout').read_text()
prov=(OUT/'provider-54fc-557c.stdout').read_text()
init=(OUT/'provider-helper-50c0-5120.stdout').read_text()
target=(OUT/'target-entry-16b0-16b6.stdout').read_text()
for name,text,pattern in (
 ('callsite_133e_BLX_R0',caller,r'^\s*133e:.*\bblx\s+r0\b'),
 ('caller_1370_calls_list_provider',caller,r'^\s*1370:.*\bbl\s+0x54fc\b'),
 ('caller_1376_calls_enumerator',caller,r'^\s*1376:.*\bbl\s+0x1332\b'),
 ('enumerator_loads_callback_pointer',caller,r'^\s*133c:.*\bldr\s+r0,\s*\[r1\]'),
 ('list_provider_calls_record_initializer',prov,r'^\s*5500:.*\bbl\s+0x50c0\b'),
 ('list_provider_stores_record_pointer',prov,r'^\s*5506:.*\bstr\s+r0,\s*\[r4\]'),
 ('list_provider_stores_null_sentinel',prov,r'^\s*550a:.*\bstr\s+r0,\s*\[r4,\s*#0x4\]'),
 ('record_initializer_stores_first_target',init,r'^\s*50c4:.*\bstr\s+r1,\s*\[r0\]'),
 ('target_loads_byte_then_returns',target,r'^\s*16b2:.*\bldrb\s+r0,\s*\[r0\]'),
 ('target_returns',target,r'^\s*16b4:.*\bbx\s+lr\b'),
): check(name,bool(re.search(pattern,text,re.M)),True)
result={
 'status':'PASS' if all(c['passed'] for c in checks) else 'FAIL',
 'checks':{'passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks),'total':len(checks)},
 'inputs':{'abl1_raw':str(RAW),'abl1_raw_sha256':sha(RAW),'abl1_elf':str(OBJ),'abl1_elf_sha256':sha(OBJ),'abl1_raw_size':len(raw)},
 'trace':{
  'selected_prior_edge':'conditional prior path 0x984E -> 0x130C -> 0x1354 (reused, not rechecked)',
  'list_base_pointer_literal':'0x6e27c at ABL1 RVA 0x141c',
  'list_provider':'0x54fc receives list base, calls 0x50c0, stores record pointer 0x6e284 to list[0], stores null to list[1]',
  'record_initializer':'0x50c0 writes callback record fields at 0x6e284: [0]=0x587b1, [1]=0x58659, [2]=0x5865d, [3]=0x58661',
  'populated_list':'[0x6e284, 0x00000000] (one descriptor then terminator)',
  'BLX_R0_site':'0x133e',
  'direct_BLX_R0_target':'0x587b1 (Thumb pointer); first record word only',
  'target_window':'under conditional base 0x57100 only, pointer maps to ABL1 RVA 0x16b0; bytes decode as LDR literal, LDRB, BX LR; literal at RVA 0x16b8 is 0x6e131',
  'conditional_base':'0x57100 is reused from prior review; runtime loader base remains unproven',
  'sibling_record_fields_not_followed':['0x58659','0x5865d','0x58661'],
 },
 'limits':['static observed bytes/disassembly only','does not prove runtime provider execution or callback reachability','does not identify the byte read at 0x6e131','does not interpret callback as a clock/SVC handler','does not follow the sibling fields or the separate 0x10958 track'],
 'checks_detail':checks,
}
(OUT/'callback-targets-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'checks':result['checks']['total'],'passed':result['checks']['passed'],'failed':result['checks']['failed'],'table_base':'0x6e27c','record':'0x6e284','BLX_R0_site':'0x133e','direct_target':'0x587b1','conditional_RVA':'0x16b0','runtime_base':'UNPROVEN'},indent=2))
