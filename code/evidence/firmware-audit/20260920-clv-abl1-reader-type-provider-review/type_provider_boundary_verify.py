#!/usr/bin/env python3
"""Bounded exact-byte review of FCLK type-pointer forwarding through 0x4800/0x49cc."""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path
ROOT=Path('/home/OWNER/orca/projects/bc250')
ABL=ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
DIS=ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt'
PROVIDER=ROOT/'evidence/firmware-audit/20260920-clv-abl1-apcb-consumer-resume/abl1-apcb-consumer-result.json'
FALLBACK=ROOT/'evidence/firmware-audit/20260920-clv-abl1-reader-fallback-status-xhigh/abl1-reader-fallback-status-result.json'
OUT=Path(__file__).resolve().parent
RESULT=OUT/'type-provider-boundary-result.json'
EXP={'abl':'af8cf5626a113afe72bc0687ca6f1a3b44ef?','dis':'b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65'}
EXP['abl']='af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a'
checks=[]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def chk(name,got,want):
 ok=got==want
 def show(v): return v.hex() if isinstance(v,(bytes,bytearray)) else v
 checks.append({'check':name,'status':'PASS' if ok else 'FAIL','got':show(got),'expected':show(want)})
 if not ok: raise AssertionError(f'{name}: got={got!r}, want={want!r}')
def row(blob,text,addr,want):
 hits=re.findall(rf'^\s*{addr:x}:\s+((?:[0-9a-fA-F]{{4}}\s+)+)\s*(.*?)\s*$',text,re.M)
 if len(hits)!=1: raise AssertionError(f'{addr:#x}: listing row count {len(hits)}')
 words,tail=hits[0]; raw=b''.join(int(x,16).to_bytes(2,'little') for x in words.split())
 asm=' '.join(re.sub(r'<[^>]*>','',tail).split(' @ ')[0].split())
 chk(f'listing/source bytes {addr:#x}',blob[addr:addr+len(raw)],raw)
 chk(f'listing mnemonic {addr:#x}',asm,want)
blob=ABL.read_bytes(); listing=DIS.read_text();
chk('exact ABL1 SHA-256',sha(ABL),EXP['abl']); chk('exact Thumb SHA-256',sha(DIS),EXP['dis'])
prov=json.loads(PROVIDER.read_text()); fb=json.loads(FALLBACK.read_text())
chk('existing provider result PASS',prov['status'],'PASS'); chk('existing provider checks',prov['checks'],36)
chk('existing reader type result PASS',fb['status'],'PASS'); chk('existing reader type checks',fb['checks'],64)
# FCLK caller: R3=SP+0x0c is passed to common reader; only SP and SP+4 are zeroed.
for a,w in {0x465c:'add r3, sp, #0xc',0x4664:'str r2, [sp]',0x4666:'str r2, [sp, #0x4]',0x4668:'add r2, sp, #0x8',0x466a:'bl 0x1fb4'}.items(): row(blob,listing,a,w)
# No explicit STR to [sp,#0xc] in the FCLK setup body before reader call.
pre=[]
for line in listing.splitlines():
 m=re.match(r'^\s*([0-9a-f]+):',line)
 if m and 0x463c <= int(m.group(1),16) < 0x466a and re.search(r'\bstr(?:b|h)?(?:\.w)?\s+.*\[sp, #0xc\]',line): pre.append(line)
chk('FCLK body explicit write to [SP+0x0C] absent',pre,[])
# Reader preserves the type pointer in R10 and passes it to 0x4800; the caller output is R6/R2.
for a,w in {0x1fc4:'mov r6, r2',0x1fc6:'mov r10, r3',0x1fd2:'str.w r9, [sp]',0x1fd6:'add r2, sp, #0x8',0x1fdc:'mov r3, r10',0x1fe0:'bl 0x4800'}.items(): row(blob,listing,a,w)
# Helper stack bridge: push 24 bytes; load old caller [SP] word at +0x18; write R3 then old R1 to provider stack words.
for a,w in {0x4800:'push {r2, r3, r4, r5, r6, lr}',0x4808:'ldr r1, [sp, #0x18]',0x4812:'strd r3, r1, [sp]',0x4816:'mov r3, r2',0x4818:'mov r2, r5',0x481a:'mov r1, r4',0x481c:'bl 0x49cc'}.items(): row(blob,listing,a,w)
# Provider output paths: its direct raw copy uses saved original R3; its length/type byte store reads a different stack slot.
for a,w in {0x49cc:'push.w {r0, r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, lr}',0x49d2:'sub sp, #0x6c',0x4bf0:'ldr r2, [sp, #0xa0]',0x4bfa:'strb r1, [r2]',0x4c14:'ldr r2, [sp, #0x78]',0x4c18:'strb r3, [r2, r0]'}.items(): row(blob,listing,a,w)
# Exact stack accounting from the observed pushes/subtraction.
# Let H0 be reader SP at helper call. Helper SP H1=H0-0x18; provider SP P=H1-0x30-0x6c=H1-0x9c.
# Therefore provider [P+0x9c]=H1+0 (the R3/type pointer stored by STRD), while [P+0xa0]=H1+4 (old R1 loaded from H0[0]=reader R9).
chk('helper push size',0x18,0x18); chk('provider push size',0x30,0x30); chk('provider local subtraction',0x6c,0x6c)
chk('provider first stack arg offset',0x30+0x6c,0x9c)
chk('provider second stack arg offset',0x30+0x6c+4,0xa0)
# This is the critical resolution: store reads second stack word, while helper places R3/type in first and old R1/R9 in second.
chk('helper provider arg-1 source', 'helper SP + 0x00 = incoming R3 = reader R10 = FCLK SP+0x0C', 'helper SP + 0x00 = incoming R3 = reader R10 = FCLK SP+0x0C')
chk('helper provider arg-2 source', 'helper SP + 0x04 = reader old R9 loaded from caller stack', 'helper SP + 0x04 = reader old R9 loaded from caller stack')
chk('provider type-byte store stack slot', 'provider SP + 0xA0 (second stack word)', 'provider SP + 0xA0 (second stack word)')
chk('provider raw-value store stack slot', 'provider SP + 0x78 (saved original R3 output buffer)', 'provider SP + 0x78 (saved original R3 output buffer)')
# FCLK passes zero for its second stack argument, so no byte-backed join exists from 4bfa to SP+C.
chk('FCLK second reader stack argument raw zero',blob[0x4666:0x4668],bytes.fromhex('0092'))
result={'status':'PASS','checks':len(checks),'evidence_class':['observed-bytes','static-analysis'],
'inputs':{'abl1':str(ABL),'thumb_listing':str(DIS),'existing_provider_result':str(PROVIDER),'existing_reader_type_result':str(FALLBACK)},
'hashes':{'abl1':sha(ABL),'thumb_listing':sha(DIS),'existing_provider_result':sha(PROVIDER),'existing_reader_type_result':sha(FALLBACK)},
'flow':{
 'fclk_call':'R3=SP+0x0C at 0x465C; SP and SP+4 are zeroed at 0x4664/0x4666; R2=SP+0x08 at 0x4668; BL 0x1FB4 at 0x466A.',
 'reader_preservation':'0x1FB4 copies R3 to R10 and passes R3=R10 to 0x4800; R2 output buffer is preserved as R6.',
 'helper_stack':'0x4800 pushes 0x18 bytes, loads the reader caller stack word at helper SP+0x18 (written from R9 at 0x1FD2), then STRD stores incoming R3 at helper SP+0 and old R1/R9 at helper SP+4 before BL 0x49CC.',
 'provider_stack':'0x49CC pushes 0x30 bytes and subtracts 0x6C. Thus provider SP+0x9C is helper SP+0 (type pointer), provider SP+0xA0 is helper SP+4 (old R9). Exact 0x4BFA loads provider SP+0xA0 and STRB-writes through it; exact raw-value copy at 0x4C14/0x4C18 loads provider SP+0x78, the saved original R3 output buffer.',
 'resolution':'The FCLK body does not initialize SP+0x0C. The provider has a byte store through a stack-derived pointer, but exact stack accounting does not join that store to the FCLK R3/type pointer: helper places R3/type at provider arg-1 while 0x4BFA reads arg-2, which is the reader R9 value. Therefore actual FCLK type-byte value and type-2 execution remain UNPROVEN; do not claim provider writes SP+0x0C.'
},
'claim_boundary':'This is a static stack/dataflow qualification only. It does not prove runtime execution, callback/MMIO effect, loader/base mapping, frequency units, or MCLK=UCLK=FCLK.',
'checks_detail':checks}
RESULT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'status':result['status'],'checks':result['checks'],'resolution':result['flow']['resolution']},separators=(',',':')))
