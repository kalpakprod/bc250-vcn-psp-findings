#!/usr/bin/env python3
"""Bounded exact-CLV ABL item-0x17 -> callback -> DD4/SVC6 reachability test."""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; OUT=Path(__file__).resolve().parent
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
PAY=ROOT/'evidence/firmware-audit/20260920-clv-sync-stage2-abl-memory/ABL1-clv-decompressed.bin'
OBJ=ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o'
FULL=ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt'
BASE=ROOT/'evidence/firmware-audit/20260921-abl-item17-consumer/prior-base-review-result.json'
PSTATE=ROOT/'evidence/firmware-audit/20260921-abl1-pstate-inputs/abl1-pstate-inputs-result.json'
CALLERS=OUT/'direct-12ac-callers.txt'
EXPECTED={'rom':'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8',
'payload':'af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a',
'obj':'54abef3a390abb0ff745685de2eed4e0e8db5e9ba27bba1a0f245573b47ff135',
'full':'b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65'}
checks=[]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ck(name,actual,expected):
 a=actual.hex() if isinstance(actual,bytes) else actual
 e=expected.hex() if isinstance(expected,bytes) else expected
 checks.append({'name':name,'actual':a,'expected':e,'status':'PASS' if actual==expected else 'FAIL'})
ck('ROM_sha256',sha(ROM),EXPECTED['rom']); ck('ROM_size',ROM.stat().st_size,16777216)
ck('ABL1_payload_sha256',sha(PAY),EXPECTED['payload']); ck('ABL1_payload_size',PAY.stat().st_size,94624)
ck('exact_object_sha256',sha(OBJ),EXPECTED['obj']); ck('full_listing_sha256',sha(FULL),EXPECTED['full'])
base_review=json.loads(BASE.read_text()); pstate=json.loads(PSTATE.read_text())
ck('conditional_base_review_status',base_review['status'],'PASS')
ck('conditional_base_review_checks',base_review['checks'],{'failed':0,'passed':28,'total':28})
ck('candidate_base',base_review['candidate_base'],'0x57100')
ck('prior_local_gate_status',pstate['status'],'PASS'); ck('prior_local_gate_checks',pstate['checks'],{'failed':0,'passed':54,'total':54})
# Confirm every newly captured disassembly command exited 0 with empty stderr.
WINDOWS={p.stem:p for p in OUT.glob('*.objdump')}
for p in sorted(OUT.glob('*.objdump')):
 exitp=OUT/(p.stem+'.exit'); errp=OUT/(p.stem+'.stderr')
 ck('objdump_exit:'+p.stem,exitp.read_text().strip(),'0')
 ck('objdump_stderr:'+p.stem,errp.read_bytes(),b'')

def parse(p):
 d={}
 for line in p.read_text().splitlines():
  parts=line.split('\t')
  if len(parts)<3: continue
  m=re.match(r'\s*([0-9a-f]+):',parts[0])
  if m: d[int(m.group(1),16)]=(parts[1].strip().lower(),parts[2].split('@',1)[0].strip().lower())
 return d
R={k:parse(v) for k,v in WINDOWS.items()}
def ins(win,addr,mnem,op=''):
 got=R.get(win,{}).get(addr)
 ok=bool(got and got[0]==mnem and (not op or re.search(op,got[1])))
 ck(f'{win}:{addr:#x}',ok,True)
# Caller supplies selector 0x17 to dispatch item with a context/data pair.
for w,a,m,o in [('caller-selector-7e30-7e40',0x7e34,'ldr',r'r0,\s*\[r4\]'),('caller-selector-7e30-7e40',0x7e36,'movs',r'r1,\s*#0x17'),('caller-selector-7e30-7e40',0x7e38,'mov',r'r2,\s*r4'),('caller-selector-7e30-7e40',0x7e3a,'bl',r'0xc60')]: ins(w,a,m,o)
# Dispatcher gate: helper value 1 selects E50, not FD8.
for w,a,m,o in [('dispatch-0c60-0d10',0xc6c,'bl',r'0x6c20'),('dispatch-0c60-0d10',0xc70,'ldr',r'r3,\s*\[sp,\s*#0x4\]'),('dispatch-0c60-0d10',0xc72,'cmp',r'r3,\s*#0x1'),('dispatch-0c60-0d10',0xc74,'bls',r'0xc7a'),('dispatch-0c60-0d10',0xc80,'bl',r'0xe50'),('dispatch-0c60-0d10',0xc8e,'bl',r'0xfd8')]: ins(w,a,m,o)
# Conditional table mapping: literal, 8-byte key/pointer rows, match and indirect call.
b=PAY.read_bytes(); base=0x57100
literal=int.from_bytes(b[0xf10:0xf14],'little')
ck('table_literal_0xf10',literal,0x6e224)
ck('conditional_table_offset',literal-base,0x17124)
rows=[]
for off in range(0x17124,0x1717c,8):
 ptr=int.from_bytes(b[off:off+4],'little'); key=int.from_bytes(b[off+4:off+8],'little'); rows.append((off,ptr,key))
ck('8-byte_callback_table_rows',len(rows),11)
row17=next((x for x in rows if x[2]==0x17),None)
ck('item17_row',row17,(0x17134,0x606fd,0x17))
ck('table_terminator',b[0x17174:0x1717c],bytes(8))
callback_ptr=row17[1] if row17 else 0
thumb=callback_ptr-base
ck('candidate_thumb_pointer',thumb,0x95fd); ck('candidate_entry',thumb&~1,0x95fc)
ck('target_prologue',b[0x95fc:0x9600],bytes.fromhex('2de9f04f'))
for w,a,m,o in [('dispatch-loop-0e50-0ed0',0xe5a,'mov',r'r6,\s*r1'),('dispatch-loop-0e50-0ed0',0xe5c,'mov',r'r10,\s*r2'),('dispatch-loop-0e50-0ed0',0xe64,'cmp',r'r6,\s*#0x8'),('dispatch-loop-0e50-0ed0',0xe66,'beq',r'0xe84'),('dispatch-loop-0e50-0ed0',0xe6e,'bl',r'0xfb8'),('dispatch-loop-0e50-0ed0',0xe76,'cbz',r'r0,\s*0xe8c'),('dispatch-loop-0e50-0ed0',0xe8c,'ldr.w',r'r8,\s*\[pc,\s*#0x80\]'),('dispatch-loop-0e50-0ed0',0xe94,'add.w',r'r0,\s*r8,\s*r4,\s*lsl\s*#3'),('dispatch-loop-0e50-0ed0',0xe98,'ldr',r'r0,\s*\[r0,\s*#0x4\]'),('dispatch-loop-0e50-0ed0',0xe9a,'cmp',r'r0,\s*r6'),('dispatch-loop-0e50-0ed0',0xe9c,'bne',r'0xeca'),('dispatch-loop-0e50-0ed0',0xe9e,'ldr.w',r'r2,\s*\[r8,\s*r4,\s*lsl\s*#3\]'),('dispatch-loop-0e50-0ed0',0xea2,'mov',r'r1,\s*r9'),('dispatch-loop-0e50-0ed0',0xea4,'mov',r'r0,\s*r10'),('dispatch-loop-0e50-0ed0',0xea6,'blx',r'r2'),('dispatch-loop-0e50-0ed0',0xea8,'cbz',r'r0,\s*0xeae'),('dispatch-loop-0e50-0ed0',0xeb0,'ldr.w',r'r0,\s*\[r8,\s*r4,\s*lsl\s*#3\]'),('dispatch-loop-0e50-0ed0',0xeb4,'cmp',r'r0,\s*#0x0'),('dispatch-loop-0e50-0ed0',0xeb6,'bne',r'0xe84'),('dispatch-loop-0e50-0ed0',0xe84,'add',r'sp,\s*#0x158'),('dispatch-loop-0e50-0ed0',0xe88,'pop.w',r'\{r4,\s*r5,\s*r6,\s*r7,\s*r8,\s*r9,\s*r10,\s*pc\}')]: ins(w,a,m,o)
# FB8 is the E50 setup helper and returns zero to continue table dispatch.
for w,a,m,o in [('fb8-0fb8-0fd8',0xfba,'movs',r'r4,\s*#0x0'),('fb8-0fb8-0fd8',0xfd2,'mov',r'r0,\s*r4'),('fb8-0fb8-0fd8',0xfd4,'pop',r'\{r4,\s*pc\}')]: ins(w,a,m,o)
# Handler: exact 6D10 return blocks the all-channel reducer and DD4 callsite.
for w,a,m,o in [('helper-6c20-6d22',0x6c2a,'bl',r'0x6d10'),('helper-6c20-6d22',0x6c2e,'str',r'r0,\s*\[r4,\s*#0x4\]'),('helper-6c20-6d22',0x6c36,'bl',r'0x6cd8'),('helper-6c20-6d22',0x6c3a,'str',r'r0,\s*\[r4,\s*#0xc\]'),('helper-6c20-6d22',0x6c3c,'bl',r'0x6ca0'),('helper-6c20-6d22',0x6c40,'str',r'r0,\s*\[r4,\s*#0x10\]'),('helper-6c20-6d22',0x6c46,'cbz',r'r1,\s*0x6c54'),('helper-6c20-6d22',0x6c54,'movs',r'r1,\s*#0x1'),('helper-6c20-6d22',0x6c4a,'str',r'r1,\s*\[r4,\s*#0x14\]'),('helper-6c20-6d22',0x6d1e,'movs',r'r0,\s*#0x1'),('helper-6c20-6d22',0x6d20,'pop',r'\{r4,\s*pc\}'),('gate-962a-9652',0x962c,'bl',r'0x6c20'),('gate-962a-9652',0x963e,'ldr',r'r0,\s*\[sp,\s*#0x164\]'),('gate-962a-9652',0x9644,'cmp',r'r0,\s*#0x1'),('gate-962a-9652',0x9646,'bls',r'0x9744'),('target-95fc-98b0',0x9744,'b',r'0x984e'),('target-95fc-98b0',0x9780,'bl',r'0xdd4'),('target-95fc-98b0',0x9848,'movs',r'r0,\s*#0x0'),('target-95fc-98b0',0x984a,'pop.w',r'\{r4,\s*r5,\s*r6,\s*r7,\s*r8,\s*r9,\s*r10,\s*r11,\s*pc\}'),('target-95fc-98b0',0x986e,'ldrh',r'r0,\s*\[r1,\s*r5\]'),('target-95fc-98b0',0x989a,'str.w',r'r0,\s*\[r4,\s*#0x2bc\]'),('target-95fc-98b0',0x98aa,'b',r'0x978e')]: ins(w,a,m,o)
# DD4 independently has the same +4 gate; the FB8 call follows only when value>1.
for w,a,m,o in [('dd4-0dd4-0e18',0xdde,'bl',r'0x6c20'),('dd4-0dd4-0e18',0xde2,'ldr',r'r3,\s*\[sp,\s*#0x4\]'),('dd4-0dd4-0e18',0xde4,'cmp',r'r3,\s*#0x1'),('dd4-0dd4-0e18',0xde6,'bls',r'0xe14'),('dd4-0dd4-0e18',0xdfc,'bl',r'0xfb8'),('dd4-0dd4-0e18',0xe14,'movs',r'r0,\s*#0x0'),('dd4-0dd4-0e18',0xe16,'b',r'0xe00')]: ins(w,a,m,o)
# Alternate helper paths and direct SVC6 callsites; exact wrapper protocol is not interpreted.
for w,a,m,o in [('helper-10c0-118c',0x10d2,'bl',r'0x6c20'),('helper-10c0-118c',0x10d6,'ldr',r'r0,\s*\[sp,\s*#0x58\]'),('helper-10c0-118c',0x10d8,'cbz',r'r0,\s*0x10ee'),('helper-10c0-118c',0x10e6,'movs',r'r0,\s*#0x9'),('helper-10c0-118c',0x1104,'bl',r'0x12ac'),('helper-118c-12ac',0x119e,'bl',r'0x6c20'),('helper-118c-12ac',0x11a2,'ldr',r'r0,\s*\[sp,\s*#0x58\]'),('helper-118c-12ac',0x11a4,'cbz',r'r0,\s*0x11ba'),('helper-118c-12ac',0x11b2,'movs',r'r0,\s*#0x9'),('helper-118c-12ac',0x11e8,'bl',r'0x12ac'),('svc6-12ac-12c8',0x12c0,'svc',r'#0x6'),('dispatcher-fallback-0fd8-1038',0x102c,'bl',r'0x12ac')]: ins(w,a,m,o)
# Direct-call sites only, from retained full exact listing; no broad indirect/xref census.
lines=[x for x in FULL.read_text().splitlines() if re.search(r'\bbl\s+0x12ac\b',x)]
addrs=[]
for line in lines:
 m=re.match(r'\s*([0-9a-f]+):',line)
 if m: addrs.append(int(m.group(1),16))
ck('direct_12ac_call_sites',addrs,[0x102c,0x1104,0x11e8])
ck('direct_12ac_callers_stdout_matches',CALLERS.read_text().splitlines(),lines)
result={'status':'PASS' if all(c['status']=='PASS' for c in checks) else 'FAIL','checks':{'passed':sum(c['status']=='PASS' for c in checks),'failed':sum(c['status']=='FAIL' for c in checks),'total':len(checks)},'conditional_base':'0x57100','table':{'literal_file_offset':'0xF10','literal':'0x0006E224','payload_table':'0x17124','item_key':'0x17','row_file_offset':'0x17134','row_pointer':'0x000606FD','mapped_thumb':'0x95FD','entry':'0x95FC'},'reachability':{'conditional_dispatch':'Accepted as a static edge only: selector 0x17 reaches the keyed row and BLX 0x95FC under candidate base 0x57100; the loader/runtime base and active object are unproven.','dispatcher':'The 0x0C60 local helper returns +4=1 and takes BLS to 0x0E50, not 0x0FD8; E50 setup helper 0x0FB8 returns 0 and table scan proceeds. After callback return 0, the matched row pointer is nonzero so E50 exits at 0x0E84 with status 0.','dd4':'Conditional/unresolved alias boundary: 0x6D10 initially writes 1 at SP+0x164; then 0x95FC calls memset-like 0x6B78 on dynamic R4+0x278 for 0x40 bytes. No address/value read proves that target is disjoint from the SP status block. If disjoint, BLS 0x9744 -> 0x984E skips DD4; if overlapping, DD4 could be entered. DD4 itself calls 0x6C20, sees +4=1, and BLS-returns 0 before its 0x0FB8 call.','outgoing_value':'On the non-aliased path, 0x984E reads a U16 from a runtime table at 0x986E, stores it to context+0x2BC at 0x989A, and returns callback status R0=0; E50 checks that zero at 0x0EA8. The numeric table value is not established by this static window.','svc6':'Rejected on the known direct item17 edges: 0x0C60 does not select fallback 0x0FD8 (callsite 0x102C); 0x95FC skips direct alternate calls 0x118C/0x10C0 on the non-aliased path, and those helpers independently gate their 0x12AC calls on block+0x14==0. SVC #6 at 0x12C0 is not shown reachable from this row. Global SVC6 reachability is not claimed.'},'direct_12ac_call_sites':[hex(a) for a in addrs],'limits':['0x57100 is conditional static coherence, not loader/runtime-base proof.','No runtime dispatcher execution, SVC6 handler/recipient, units, clock effect, training, physical or hardware claim.'],'checks_detail':checks}
(OUT/'item17-reachability-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':result['status'],'checks':result['checks'],'reachability':result['reachability'],'direct_12ac_call_sites':result['direct_12ac_call_sites'],'failed':[c['name'] for c in checks if c['status']=='FAIL']},sort_keys=True))
raise SystemExit(0 if result['status']=='PASS' else 1)
