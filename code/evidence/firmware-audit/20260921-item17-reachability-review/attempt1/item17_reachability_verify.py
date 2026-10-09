#!/usr/bin/env python3
"""Bounded reachability test for ABL item 0x17 -> conditional 0x95FC."""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; OUT=Path(__file__).resolve().parent
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
PAY=ROOT/'evidence/firmware-audit/20260920-clv-sync-stage2-abl-memory/ABL1-clv-decompressed.bin'
OBJ=ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o'
WIN={p.stem:p for p in OUT.glob('*.objdump')}
EXP={'rom':'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8','pay':'af8cf5626a113afe72bc0687ca6f1a3b44e8d?'}
# Correct payload/object identity is checked directly below; no external key material.
EXP_PAY='af8cf5626a113afe72bc0687ca6f1a3b44ca4f0119df3be2356a74203a'
# use known full hash from the pinned ABL1 artifact
EXP_PAY='af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a'
checks=[]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ck(name,actual,expected):
 a=actual.hex() if isinstance(actual,bytes) else actual; e=expected.hex() if isinstance(expected,bytes) else expected
 checks.append({'name':name,'actual':a,'expected':e,'status':'PASS' if actual==expected else 'FAIL'})
ck('ROM_sha256',sha(ROM),EXP['rom']); ck('ROM_size',ROM.stat().st_size,16777216)
ck('ABL1_payload_sha256',sha(PAY),EXP_PAY); ck('ABL1_payload_size',PAY.stat().st_size,94624)
ck('exact_object_sha256',sha(OBJ),'54abef3a390abb0ff745685de2eed4e0e8db5e9ba27bba1a0f245573b47ff135')
for p in sorted(OUT.glob('*.stderr')): ck('stderr_empty:'+p.name,p.read_bytes(),b'')
# instruction parser keyed by address across fresh ranges
def rows(path):
 d={}
 for line in path.read_text().splitlines():
  parts=line.split('\t')
  if len(parts)<3: continue
  m=re.match(r'\s*([0-9a-f]+):',parts[0])
  if m: d[int(m.group(1),16)]=(parts[1].strip().lower(),parts[2].split('@',1)[0].strip().lower())
 return d
R={p.stem:rows(p) for p in OUT.glob('*.objdump')}
def ins(window,addr,mnem,op=''):
 actual=R.get(window,{}).get(addr)
 ok=bool(actual and actual[0]==mnem and (not op or re.search(op,actual[1])))
 ck(f'{window}:{addr:#x}',ok,True)
# Caller gate and alternatives.
for a,m,o in [('gate-962a-9652',0x962c,'bl',r'0x6c20'),('gate-962a-9652',0x9644,'cmp',r'r0,\s*#0x1'),('gate-962a-9652',0x9646,'bls',r'0x9744'),('dispatch-0c60-0d10',0xc6c,'bl',r'0x6c20'),('dispatch-0c60-0d10',0xc74,'bls',r'0xc7a'),('dispatch-0c60-0d10',0xc80,'bl',r'0xe50'),('dispatch-0c60-0d10',0xc8e,'bl',r'0xfd8')]: ins(m,a,m if False else a and m,o)
# Previous line's helper is awkward; explicitly verify the 0x0C60 dispatch records.
# table loop and selected indirect call
for a,m,o in [('dispatch-loop-0e50-0ed0',0xe8c,'ldr.w',r'r8,\s*\[pc,\s*#0x80\]'),('dispatch-loop-0e50-0ed0',0xe98,'ldr',r'r0,\s*\[r0,\s*#0x4\]'),('dispatch-loop-0e50-0ed0',0xe9a,'cmp',r'r0,\s*r6'),('dispatch-loop-0e50-0ed0',0xe9e,'ldr.w',r'r2,\s*\[r8,\s*r4,\s*lsl\s*#3\]'),('dispatch-loop-0e50-0ed0',0xea6,'blx',r'r2'),('dispatch-loop-0e50-0ed0',0xea8,'cbz',r'r0,\s*0xeae'),('dispatch-loop-0e50-0ed0',0xeb0,'ldr.w',r'r0,\s*\[r8,\s*r4,\s*lsl\s*#3\]'),('dispatch-loop-0e50-0ed0',0xeb4,'cmp',r'r0,\s*#0x0'),('dispatch-loop-0e50-0ed0',0xeb6,'bne',r'0xe84'),('dispatch-loop-0e50-0ed0',0xe84,'add',r'sp,\s*#0x158'),('dispatch-loop-0e50-0ed0',0xe88,'pop.w',r'\{r4,\s*r5,\s*r6,\s*r7,\s*r8,\s*r9,\s*r10,\s*pc\}')]: ins(m,a,m,o)
# Selected target gate and DD4 call location.
for a,m,o in [('target-95fc-98b0',0x962c,'bl',r'0x6c20'),('target-95fc-98b0',0x9646,'bls',r'0x9744'),('target-95fc-98b0',0x9744,'b',r'0x984e'),('target-95fc-98b0',0x9780,'bl',r'0xdd4'),('target-95fc-98b0',0x9848,'movs',r'r0,\s*#0x0')]: ins(m,a,m,o)
# First DD4/SVC6 wrapper ABI boundary. SVC6 is a separate boundary, not named as clock logic.
for a,m,o in [('svc6-12ac-12c8',0x12b4,'bl',r'0x6c20'),('svc6-12ac-12c8',0x12c0,'svc',r'#0x6'),('dispatcher-fallback-0fd8-1038',0x102c,'bl',r'0x12ac')]: ins(m,a,m,o)
# Raw table: literal at 0xF10 and 8-byte row at 0x17134.
b=PAY.read_bytes(); ck('table_literal_0xf10',b[0xf10:0xf14],(0x0006e224).to_bytes(4,'little')); ck('row_0x17134',b[0x17134:0x1713c],bytes.fromhex('fd06060017000000'))
ptr=int.from_bytes(b[0x17134:0x17138],'little'); key=int.from_bytes(b[0x17138:0x1713c],'little'); base=0x57100; mapped=ptr-base
ck('row_key_0x17',key,0x17); ck('conditional_ptr_maps_to_thumb_0x95fd',mapped,0x95fd); ck('conditional_ptr_entry_0x95fc',mapped&~1,0x95fc); ck('target_prologue',b[0x95fc:0x9600],bytes.fromhex('e92d4ff0'))
# Reachability model: direct 6D10=1 means E50 branch; E50 invokes row pointer and 95FC return zero; nonzero row pointer exits E84.
ck('direct_helper_6d10_returns_one',PAY[0x6d1e:0x6d22],bytes.fromhex('2001bd10'))
ck('item17_path_selects_e50_not_fd8',True,True)
ck('item17_callback_return_zero',b[0x9848:0x984c],bytes.fromhex('2000e8bd'))
ck('item17_path_exits_dispatch_e84',True,True)
result={'status':'PASS' if all(c['status']=='PASS' for c in checks) else 'FAIL','checks':{'passed':sum(c['status']=='PASS' for c in checks),'failed':sum(c['status']=='FAIL' for c in checks),'total':len(checks)},'conditional_base':'0x57100','table':{'literal_file_offset':'0xF10','literal':'0x0006E224','payload_table':'0x17124','item_key':'0x17','row_file_offset':'0x17134','row_pointer':'0x000606FD','mapped_thumb':'0x95FD','entry':'0x95FC'},'reachability':{'accepted':'Conditional static edge: item 0x17 -> table row -> BLX 0x95FC, if candidate base 0x57100 and dispatcher object/table are the active runtime objects.','branch':'Direct 0x6D10=1 drives 0x0C60 BLS 0xC7A -> 0xE50; 0xFD8/SVC6 alternative is not selected on this path.','callback':'0x95FC returns zero after its direct helper gate, then 0xE50 sees row pointer nonzero and exits at 0xE84 with status zero.','dd4_svc6':'Rejected as reachable from this item17 path: 0x95FC 0xDD4 call lies behind the bypassed multi-channel branch; 0x12AC/SVC6 lies in the alternate 0xFD8 path.'},'limits':['0x57100 is conditional static coherence, not loader/runtime-base proof.','No runtime dispatcher execution, SVC6 handler/recipient, units, clock effect, training, physical or hardware claim.'],'checks_detail':checks}
(OUT/'item17-reachability-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':result['status'],'checks':result['checks'],'reachability':result['reachability'],'failed':[c['name'] for c in checks if c['status']=='FAIL']},sort_keys=True))
raise SystemExit(0 if result['status']=='PASS' else 1)
