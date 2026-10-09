#!/usr/bin/env python3
"""Bounded alias-range analysis for ABL1 0x95FC's local status and context fill."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[3]; OUT=Path(__file__).resolve().parent
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
PAY=ROOT/'evidence/firmware-audit/20260920-clv-sync-stage2-abl-memory/ABL1-clv-decompressed.bin'
OBJ=ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o'
WIN={k:OUT/f'{k}.objdump' for k in ['dispatch-context-0c60-0c8e','dispatch-callback-0e50-0ea8','fill-loop-6b78-6b84','frame-fill-95fc-9652']}
checks=[]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ck(n,a,e):
 a=a.hex() if isinstance(a,bytes) else a; e=e.hex() if isinstance(e,bytes) else e
 checks.append({'name':n,'actual':a,'expected':e,'status':'PASS' if a==e else 'FAIL'})
ck('ROM_sha256',sha(ROM),'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8')
ck('ABL1_sha256',sha(PAY),'af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a')
ck('exact_object_sha256',sha(OBJ),'54abef3a390abb0ff745685de2eed4e0e8db5e9ba27bba1a0f245573b47ff135')
for name,p in WIN.items():
 ck('objdump_exit:'+name,(OUT/(name+'.exit')).read_text().strip(),'0')
 ck('objdump_stderr:'+name,(OUT/(name+'.stderr')).read_bytes(),b'')
def rows(path):
 d={}
 for line in path.read_text().splitlines():
  c=line.split('\t')
  if len(c)<3: continue
  m=re.match(r'\s*([0-9a-f]+):',c[0])
  if m:d[int(m.group(1),16)]=(c[1].strip().lower(),c[2].split('@',1)[0].strip().lower())
 return d
R={k:rows(p) for k,p in WIN.items()}
def ins(w,a,m,o=''):
 v=R[w].get(a); ck(f'{w}:{a:#x}',bool(v and v[0]==m and (not o or re.search(o,v[1]))),True)
# Incoming call argument remains an unknown dynamic object, not a stack-relative value.
for args in [('dispatch-context-0c60-0c8e',0xc64,'mov',r'r4,\s*r0'),('dispatch-context-0c60-0c8e',0xc68,'mov',r'r6,\s*r2'),('dispatch-context-0c60-0c8e',0xc80,'bl',r'0xe50'),('dispatch-callback-0e50-0ea8',0xe56,'mov',r'r9,\s*r0'),('dispatch-callback-0e50-0ea8',0xe5c,'mov',r'r10,\s*r2'),('dispatch-callback-0e50-0ea8',0xea4,'mov',r'r0,\s*r10'),('frame-fill-95fc-9652',0x9600,'ldr',r'r4,\s*\[r0\]'),('frame-fill-95fc-9652',0x9602,'sub',r'sp,\s*#0x17c'),('frame-fill-95fc-9652',0x962a,'add',r'r0,\s*sp,\s*#0x160'),('frame-fill-95fc-9652',0x962c,'bl',r'0x6c20'),('frame-fill-95fc-9652',0x9636,'add.w',r'r0,\s*r4,\s*#0x278'),('frame-fill-95fc-9652',0x963a,'bl',r'0x6b78'),('frame-fill-95fc-9652',0x963e,'ldr',r'r0,\s*\[sp,\s*#0x164\]'),('frame-fill-95fc-9652',0x9646,'bls',r'0x9744'),('fill-loop-6b78-6b84',0x6b7a,'strb',r'r1,\s*\[r0\],\s*#1'),('fill-loop-6b78-6b84',0x6b80,'bhs',r'0x6b7a')]:ins(*args)
b=PAY.read_bytes()
ck('local_buffer_start',0x160,0x160); ck('local_status_field',0x164,0x164); ck('local_buffer_end_exclusive',0x17c,0x17c)
ck('fill_length',0x40,0x40); ck('fill_byte',0xff,0xff)
result={
 'status':'INCONCLUSIVE_ALIAS_UNRESOLVED' if all(c['status']=='PASS' for c in checks) else 'FAIL',
 'checks':{'passed':sum(c['status']=='PASS' for c in checks),'failed':sum(c['status']=='FAIL' for c in checks),'total':len(checks)},
 'stack_buffer':{'start_offset_from_current_sp':'0x160','size':'0x1c','end_exclusive':'0x17c','guard_word':'[SP+0x164..0x168)'},
 'fill_target':{'expression':'[R4+0x278, R4+0x2B8)','length':'0x40','byte':'0xff','fill_loop':'0x6B7A..0x6B80'},
 'R4_origin':{'chain':'0x7E38 passes caller R4 as R2 -> 0x0C60 preserves R2 in R6 -> 0x0E50 preserves R2 in R10 -> callback R0=R10 -> 0x95FC loads R4=[R0]','absolute_value':'UNRESOLVED','lifetime':'caller-supplied dynamic context; no allocation/loader/runtime address is recovered in the bounded windows'},
 'alias_condition':{'gate_word_overlap':'[R4+0x278, R4+0x2B8) intersects [SP+0x164, SP+0x168)','exact_relation':'R4 + 0x278 < SP + 0x168 AND SP + 0x164 < R4 + 0x2B8','verdict':'not provable or falsifiable from these exact static operands; distinct base registers are not a non-alias proof'},
 'branch_consequence':{'before_fill':'0x6D10 returns 1; 0x6C20 stores 1 to the local +4 word','after_fill_if_disjoint':'[SP+0x164] remains 1 and BLS 0x9744 -> 0x984E is taken','after_fill_if_overlap':'fill byte 0xff can replace guard word; the `<=1` branch no longer follows from 0x6D10 alone; subsequent stack-field values and branch remain runtime/object-layout dependent'},
 'outgoing_value':{'nonalias_path':'0x984E reads a U16 from a runtime table at 0x986E, stores it to context+0x2BC at 0x989A, and returns status R0=0; the exact U16 is not statically resolved here','DD4_path':'conditional on guard overwrite; DD4 then has its own 0x6C20/6D10 +4=1 gate and returns 0 before 0x0FB8 if its local buffer is not itself aliased'},
 'decision':'The claim that 0x6D10=1 guarantees branch 0x984E is REJECTED without an alias/lifetime proof. The new disassembly narrows the missing fact to the runtime addresses/ownership of R4 and current SP; no hardware action is used.',
 'limits':['No runtime stack/object addresses or loader base captured.','No claim that DD4 is actually invoked; reachability is conditional on aliasing.','No SVC ABI, handler, clock, training, physical frequency, hardware, ROM, or register semantics.'],
 'checks_detail':checks}
(OUT/'item17-alias-bounds-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':result['status'],'checks':result['checks'],'R4_origin':result['R4_origin'],'alias_condition':result['alias_condition'],'branch_consequence':result['branch_consequence'],'decision':result['decision']},sort_keys=True))
raise SystemExit(0 if result['status']=='INCONCLUSIVE_ALIAS_UNRESOLVED' else 1)
