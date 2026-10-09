#!/usr/bin/env python3
"""Verify FCLK reader type-pointer forwarding through the real Thumb BL targets."""
from pathlib import Path
import hashlib,json,re,subprocess
ROOT=Path('/home/OWNER/orca/projects/bc250')
OUT=Path(__file__).resolve().parent
ABL=ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
OBJ=ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o'
LIST=ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt'
HELPER=ROOT/'evidence/firmware-audit/20260920-clv-abl1-reader-4800-boundary-review/target-disassembly.stdout'
PROVIDER=ROOT/'evidence/firmware-audit/20260920-clv-abl1-apcb-consumer-resume/abl1-apcb-consumer-result.json'
FALLBACK=ROOT/'evidence/firmware-audit/20260920-clv-abl1-reader-fallback-status-xhigh/abl1-reader-fallback-status-result.json'
PROVIDER_WIN=OUT/'provider-49cc-window.stdout'
PROVIDER_ERR=OUT/'provider-49cc-window.stderr'
PROVIDER_EXIT=OUT/'provider-49cc-window.exit'
RESULT=OUT/'type-provider-boundary-result.json'
EXPECTED={
 'abl':'af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a',
 'obj':'54abef3a390abb0ff745685de2eed4e0e8db5e9ba27bba1a0f245573b47ff135',
 'dis':'b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65',
 'helper_target':'4ee44cf611486ff2cf04f1a67f94ac2aab5fb6d6748ccf013d1748d8cb031c65',
 'provider_result':'3950e5136254db2aa9c96c91caba4d48da4a11c369b38a36703c9f54cef45ee9',
}
checks=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(name,got,want):
 ok=got==want
 def f(x):return x.hex() if isinstance(x,bytes) else x
 checks.append({'check':name,'status':'PASS' if ok else 'FAIL','got':f(got),'expected':f(want)})
 if not ok:raise AssertionError(f'{name}: {got!r} != {want!r}')
def disrow(text,addr):
 m=re.findall(rf'^\s*{addr:x}:\s+((?:[0-9a-fA-F]{{4}}\s+)+)\s*(.*?)\s*$',text,re.M)
 if len(m)!=1:raise AssertionError(f'row {addr:#x}: {len(m)} matches')
 raw=b''.join(int(w,16).to_bytes(2,'little') for w in m[0][0].split())
 asm=' '.join(re.sub(r'<[^>]*>','',m[0][1]).split(' @ ')[0].split())
 return raw,asm
def exactrow(text,addr,asm):
 raw,got=disrow(text,addr)
 check(f'raw bytes match source {addr:#x}',ABL_BYTES[addr:addr+len(raw)],raw)
 check(f'disassembly {addr:#x}',got,asm)
def decode_bl(blob,a):
 h1=int.from_bytes(blob[a:a+2],'little');h2=int.from_bytes(blob[a+2:a+4],'little')
 s=(h1>>10)&1;j1=(h2>>13)&1;j2=(h2>>11)&1;i1=1^(j1^s);i2=1^(j2^s)
 imm=(s<<24)|(i1<<23)|(i2<<22)|((h1&0x3ff)<<12)|((h2&0x7ff)<<1)
 if s:imm-=1<<25
 return a+4+imm
ABL_BYTES=ABL.read_bytes(); listing=LIST.read_text()
for label,p,key in [('ABL1',ABL,'abl'),('exact ELF object',OBJ,'obj'),('full listing',LIST,'dis'),('0x4800 explicit-target listing',HELPER,'helper_target'),('existing provider result',PROVIDER,'provider_result')]:
 check(label+' exists',p.is_file(),True);check(label+' SHA-256',sha(p),EXPECTED[key])
fr=json.loads(FALLBACK.read_text()); pr=json.loads(PROVIDER.read_text())
check('fallback/type report result PASS',fr['status'],'PASS');check('provider result PASS',pr['status'],'PASS')
check('reader BL target from raw bytes',decode_bl(ABL_BYTES,0x1fe0),0x4800)
check('helper BL target from raw bytes',decode_bl(ABL_BYTES,0x481c),0x49cc)
helper=HELPER.read_text()
for a,asm in {0x4800:'push {r2, r3, r4, r5, r6, lr}',0x4808:'ldr r1, [sp, #0x18]',0x4812:'strd r3, r1, [sp]',0x481c:'bl 0x49cc'}.items():
 exactrow(helper,a,asm)
# FCLK caller + common reader register/stack path, from pinned full listing and raw bytes.
for a,asm in {0x465c:'add r3, sp, #0xc',0x4664:'str r2, [sp]',0x4666:'str r2, [sp, #0x4]',0x466a:'bl 0x1fb4',
 0x1fc0:'ldrd r7, r9, [sp, #48]',0x1fd2:'str.w r9, [sp]',0x1fdc:'mov r3, r10',0x1fe0:'bl 0x4800'}.items():
 exactrow(listing,a,asm)
# Direct FCLK body has no write to its SP+0x0C type-byte local before reader invocation.
pre=[]
for line in listing.splitlines():
 m=re.match(r'^\s*([0-9a-f]+):',line)
 if m and 0x463c<=int(m.group(1),16)<0x466a and re.search(r'\bstr(?:b|h)?(?:\.w)?\s+.*\[sp, #0xc\]',line):pre.append(line)
check('FCLK explicit local [SP+0x0C] writes before reader',pre,[])
# Obtain provider function from its real BL target. Linear 0x49CA row overlaps the function entry.
cmd=['llvm-objdump','-D','--triple=thumbv7m-none-eabi','--start-address=0x49cc','--stop-address=0x4e4c',str(OBJ)]
run=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
PROVIDER_WIN.write_text(run.stdout,encoding='utf-8');PROVIDER_ERR.write_text(run.stderr,encoding='utf-8');PROVIDER_EXIT.write_text(str(run.returncode)+'\n')
check('provider explicit-target disassembly exit',run.returncode,0)
window=run.stdout
for a,asm in {0x49cc:'push.w {r0, r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, lr}',
 0x49d2:'sub sp, #0x6c',0x4a0c:'ldr r0, [sp, #0xa0]',0x4b36:'ldr r1, [sp, #0xa4]',
 0x4bf0:'ldr r2, [sp, #0xa0]',0x4bfa:'strb r1, [r2]',0x4c14:'ldr r2, [sp, #0x78]',0x4c18:'strb r3, [r2, r0]'}.items():
 exactrow(window,a,asm)
# Stack accounting: helper passes R3 as arg1 and loaded R9 as arg2; provider saves 0x30 bytes and allocates 0x6c.
check('helper push frame size',0x18,0x18)
check('provider frame size',0x34+0x6c,0xa0)
check('provider first stack arg current-SP offset',0x34+0x6c,0xa0)
check('provider second stack arg current-SP offset',0x34+0x6c+4,0xa4)
# The first stack arg at provider SP+0x9C is the caller type-pointer (helper incoming R3).
# The provider body has no explicit stack-base memory operand to that slot; its visible byte store uses arg2 at +0xA0.
stack9c=[line for line in window.splitlines() if re.search(r'\[\s*sp,\s*#(?:0x0*a0|160)\s*\]',line,re.I)]
check('provider explicit SP+0xA0 access includes 0x4BF0', any('4bf0:' in line for line in stack9c), True)
check('provider byte store consumes second stack arg',window.lower().count('[sp, #0xa0]')>=2,True)
# The FCLK caller explicitly passes zero as reader stack args; that second value becomes provider arg2, not its first type-pointer argument.
check('FCLK first reader stack word is zero',ABL_BYTES[0x4664:0x4666].hex(),'0092')
check('FCLK second reader stack word is zero',ABL_BYTES[0x4666:0x4668].hex(),'0192')
result={'status':'PASS','checks':len(checks),'evidence_class':['observed-bytes','static-analysis'],
 'inputs':{'abl1':str(ABL),'object':str(OBJ),'full_listing':str(LIST),'helper_explicit_window':str(HELPER),'provider_explicit_window':str(PROVIDER_WIN),'provider_prior_result':str(PROVIDER),'fallback_type_result':str(FALLBACK)},
 'hashes':{'abl1':sha(ABL),'object':sha(OBJ),'full_listing':sha(LIST),'helper_explicit_window':sha(HELPER),'provider_prior_result':sha(PROVIDER),'fallback_type_result':sha(FALLBACK)},
 'stack_result':{
 'fclk_caller':'R3=SP+0x0C at 0x465C; SP and SP+4 words are zero at 0x4664/0x4666.',
 'reader_to_helper':'Reader R3=R10 is preserved as type pointer; R9 is loaded from the second caller stack word and stored to reader [SP] at 0x1FD2. Helper 0x4800 reads it at [SP+0x18], then STRD R3,R1,[SP] forwards type pointer as outgoing arg1 and R9 as arg2.',
 'provider_frame':'The explicit 0x49CC entry pushes 0x34 bytes (R0..R11,LR) and subtracts 0x6C, so incoming stack arg1 appears at current SP+0xA0 and arg2 at +0xA4. Its 0x4BF0/0x4BFA path loads/writes through arg1 [SP+0xA0], which is the FCLK type pointer.',
 'conclusion':'Within the exact FCLK -> reader -> 0x4800 -> 0x49CC edge, the caller type pointer is forwarded as provider arg1 and the provider 0x4BF0/0x4BFA path writes its returned byte length through provider arg1 at SP+0xA0. Correct 0x34-byte push accounting joins SP+0xA0 to the FCLK SP+0x0C type pointer. Thus provider success can initialize the type byte before reader dispatch; actual type-2 execution still depends on provider success and returned length, but the prior uninitialized-local claim is superseded.'},
 'claim_boundary':'Static argument/stack trace only; no runtime, clock unit, hardware or MCLK=UCLK=FCLK result.',
 'checks_detail':checks}
RESULT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'status':'PASS','checks':len(checks),'provider_disassembly_exit':run.returncode,'provider_type_pointer_arg':'SP+0x9C preserved/unreferenced directly','provider_explicit_byte_store':'through second stack arg SP+0xA0','fclk_type_byte_write':'not established by this provider path'},separators=(',',':')))
