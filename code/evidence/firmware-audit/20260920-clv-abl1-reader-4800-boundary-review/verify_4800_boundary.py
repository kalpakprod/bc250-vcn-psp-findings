#!/usr/bin/env python3
"""Verify raw Thumb BL targets and explicit-target disassembly for ABL1 helper 0x4800."""
from pathlib import Path
import hashlib,json,re,subprocess
ROOT=Path('/home/OWNER/orca/projects/bc250'); OUT=Path(__file__).resolve().parent
ABL=ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'; OBJ=ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o'; LIST=ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt'; PREV=ROOT/'evidence/firmware-audit/20260920-clv-abl1-apcb-consumer-resume/abl1-apcb-consumer-result.json'; RESULT=OUT/'4800-boundary-result.json'
EXPECTED={'abl':'af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a','obj':'', 'listing':'b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65','prev':'3950e5136254db2aa9c96c91caba4d48da4a11c369b38a36703c9f54cef45ee9'}
EXPECTED['obj']='54abef3a390abb0ff745685de2eed4e0e8db5e9ba27bba1a0f245573b47ff135'
checks=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def chk(name,got,want):
 ok=got==want; show=lambda v: v.hex() if isinstance(v,bytes) else v; checks.append({'check':name,'status':'PASS' if ok else 'FAIL','got':show(got),'expected':show(want)})
 if not ok:raise AssertionError(f'{name}: {got!r} != {want!r}')
def decode_bl(blob,a):
 h1=int.from_bytes(blob[a:a+2],'little');h2=int.from_bytes(blob[a+2:a+4],'little');S=(h1>>10)&1;J1=(h2>>13)&1;J2=(h2>>11)&1;I1=1^(J1^S);I2=1^(J2^S);imm=(S<<24)|(I1<<23)|(I2<<22)|((h1&0x3ff)<<12)|((h2&0x7ff)<<1)
 if S:imm-=1<<25
 return a+4+imm
b=ABL.read_bytes();
for name,p,key in [('ABL1',ABL,'abl'),('exact ELF object',OBJ,'obj'),('full listing',LIST,'listing'),('prior provider result',PREV,'prev')]:chk(name+' exists',p.is_file(),True);chk(name+' SHA-256',sha(p),EXPECTED[key])
prev=json.loads(PREV.read_text());chk('prior provider status',prev['status'],'PASS');chk('prior provider checks',prev['checks'],36)
# Direct raw BL target from common reader to helper and helper to provider.
chk('raw BL at reader 0x1FE0',b[0x1fe0:0x1fe4].hex(),'02f00efc')
chk('decoded reader BL target',decode_bl(b,0x1fe0),0x4800)
chk('helper raw entry bytes',b[0x4800:0x4808].hex(),'7cb504460d46401e')
chk('raw BL at helper 0x481C',b[0x481c:0x4820],bytes.fromhex('00f0d6f8'))
chk('decoded helper BL target',decode_bl(b,0x481c),0x49cc)
# Existing linear listing visibly starts at 0x4802 because it decoded 0x47FE as a 32-bit instruction; this is a listing-boundary artifact, not the raw target.
chk('linear listing has no standalone 0x4800 row',len(re.findall(r'^\s*4800:',LIST.read_text(),re.M)) ,0)
chk('linear listing has 0x4802 row',len(re.findall(r'^\s*4802:',LIST.read_text(),re.M)),1)
# Run LLVM on the exact target object with explicit Thumb architecture and address window.
cmd=['llvm-objdump','-D','--triple=thumbv7m-none-eabi','--start-address=0x4800','--stop-address=0x4830',str(OBJ)]
run=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
(OUT/'target-disassembly.stdout').write_text(run.stdout,encoding='utf-8');(OUT/'target-disassembly.stderr').write_text(run.stderr,encoding='utf-8');(OUT/'target-disassembly.exit').write_text(str(run.returncode)+'\n')
chk('explicit-target llvm exit',run.returncode,0)
out=run.stdout
for needle in ('4800: b57c','4802: 4604','4808: 9906','4812: e9cd 3100','481c: f000 f8d6','bl\t0x49cc'):
 chk('explicit-target disassembly contains '+needle,needle in out,True)
result={'status':'PASS','checks':len(checks),'evidence_class':['observed-bytes','static-analysis'],'inputs':{'abl1':str(ABL),'exact_object':str(OBJ),'full_listing':str(LIST),'prior_provider_result':str(PREV)},'hashes':{'abl1':sha(ABL),'exact_object':sha(OBJ),'full_listing':sha(LIST),'prior_provider_result':sha(PREV)},'raw_targets':{'reader_bl_0x1fe0':'0x4800','helper_bl_0x481c':'0x49CC'},'boundary':'The raw BL at 0x1FE0 targets 0x4800. The exact target bytes begin 7c b5 (PUSH {R2,R3,R4,R5,R6,LR}); the linear full listing starts at 0x4802 because it decoded preceding bytes at 0x47FE as a 32-bit instruction. The helper BL at 0x481C targets 0x49CC. Prior 0x4800 helper claims use the valid raw target; only the linear-listing row boundary was misleading.','limits':'This resolves instruction boundary only. It does not add provider semantics, runtime/base proof, hardware behavior, or clock meaning.','checks_detail':checks,'execution':{'command':cmd,'stdout':run.stdout,'stderr':run.stderr,'exit_status':run.returncode}}
RESULT.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':'PASS','checks':len(checks),'reader_bl_target':'0x4800','helper_bl_target':'0x49CC','explicit_objdump_exit':run.returncode},separators=(',',':')))
