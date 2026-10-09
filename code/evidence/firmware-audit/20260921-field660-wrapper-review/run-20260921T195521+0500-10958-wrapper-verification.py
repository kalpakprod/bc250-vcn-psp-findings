#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,re,sys
rawp,dumpp,listingp,romp,objp=sys.argv[1:]
raw=Path(rawp).read_bytes(); dump=Path(dumpp).read_bytes(); listing=Path(listingp).read_text(); rom=Path(romp).read_bytes(); obj=Path(objp).read_bytes()
start,end=0x10958,0x1096a
rows=[]
for line in listing.splitlines():
 m=re.match(r'^\s*([0-9a-fA-F]+):\s+(.*)$',line)
 if not m: continue
 address=int(m.group(1),16)
 if not start<=address<end: continue
 parts=m.group(2).split(); i=0
 while i<len(parts) and re.fullmatch(r'[0-9a-fA-F]{4}',parts[i]): i+=1
 if i>=len(parts): continue
 rows.append({'address':address,'mnemonic':parts[i].lower(),'operands':' '.join(parts[i+1:]).split('@')[0].strip().lower(),'raw_line':line.strip()})
expected=[('push','{r4, r5}'),('ldr.w','r4, [r0, #0x660]'),('mov','r3, r2'),('mov','r2, r1'),('mov','r12, r4'),('pop','{r4, r5}'),('movs','r1, #0x1'),('bx','r12')]
observed=[(x['mnemonic'],x['operands']) for x in rows]; raw_slice=raw[start:end]; dump_slice=dump[start:end]
checks=[('pinned CLV ROM SHA-256',hashlib.sha256(rom).hexdigest()=='ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'),('exact ABL1 SHA-256',hashlib.sha256(raw).hexdigest()=='af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a'),('ABL1 size',len(raw)==94624),('ELF .data length equals ABL1',len(dump)==len(raw)),('ELF .data is byte-identical to ABL1',dump==raw),('wrapper bytes',raw_slice.hex()=='30b4d0f8604613460a46a44630bc01216047'),('eight wrapper instructions',len(rows)==8),('exact AAPCS register sequence',observed==expected),('r0 not overwritten',all(not (x['mnemonic'] in ('mov','movs','movw','movt','ldr','ldr.w','ldrb','ldrh','pop') and x['operands'].split(',')[0].strip()=='r0') for x in rows)),('no store through r0',not any(x['mnemonic'].startswith(('str','stm')) and '[r0' in x['operands'] for x in rows)),('r4/r5 stack save restored',rows[0]['mnemonic']=='push' and rows[5]['mnemonic']=='pop' and rows[0]['operands']==rows[5]['operands']),('callback tail branch via r12',rows[-1]['mnemonic']=='bx' and rows[-1]['operands']=='r12')]
result={'status':'PASS' if all(ok for _,ok in checks) else 'FAIL','checks':{'passed':sum(ok for _,ok in checks),'failed':sum(not ok for _,ok in checks),'total':len(checks)},'inputs':{'rom_sha256':hashlib.sha256(rom).hexdigest(),'rom_size':len(rom),'abl1_sha256':hashlib.sha256(raw).hexdigest(),'abl1_size':len(raw),'elf_sha256':hashlib.sha256(obj).hexdigest(),'data_section_sha256':hashlib.sha256(dump).hexdigest(),'wrapper_range':'0x10958..0x1096A','wrapper_bytes':raw_slice.hex()},'AAPCS_trace':{'entry_r0':'pointer-like base used by LDR [r0,#0x660]','callback_target':'loaded from entry_r0+0x660 into r4 then r12','callback_r0':'same incoming r0; no destination write to r0 in wrapper','callback_r1':'constant 1','callback_r2':'entry r1','callback_r3':'entry r2','lr':'preserved; final BX R12 is a tail branch','stack':'push/pop r4,r5 balanced before tail branch'},'accepted_claim':'Within bytes 0x10958..0x1096A, the wrapper preserves incoming R0 for the indirect callback and does not write through that pointer.','rejected_claim':'The wrapper itself mutates the pointee addressed by incoming R0.','limits':['The indirect callback may mutate the pointee; that body is outside this wrapper-only check.','No initializer or callback-target body was analyzed.','No runtime, SVC handler, MMIO/PLL, physical clock, or hardware result.'],'checks_detail':[{'name':n,'passed':ok} for n,ok in checks]}
print(json.dumps(result,indent=2))
if result['status']!='PASS': raise SystemExit(1)
