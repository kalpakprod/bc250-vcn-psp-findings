#!/usr/bin/env python3
"""Bounded ABL1 0xA04E lookup/copy trace using disassembler-parsed exact windows."""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
ABL=ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
DIS=ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt'
WINDOW=OUT/'abl1-window-disasm.stdout'
INIT=OUT/'abl1-init-window-disasm.stdout'
CALL=OUT/'abl1-init-call-disasm.stdout'
TAIL=OUT/'abl1-pointer-tail-disasm.stdout'
LOOKUP=OUT/'abl1-lookup-window-disasm.stdout'
PREV=ROOT/'evidence/firmware-audit/20260920-clv-abl1-runtime-heap-boundary/abl1-runtime-heap-boundary-result.json'
PROVIDER=ROOT/'evidence/firmware-audit/20260920-clv-abl1-apcb-consumer-resume/abl1-apcb-consumer-result.json'
APCB=OUT/'apcb-detail.json'
EXP={'rom':'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8',
     'abl':'af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a',
     'dis':'b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65',
     'previous':'46a126825991b945716fe6cf52b4b68df5054304a16feac086067451a2dc5ce5',
     'provider':'3950e5136254db2aa9c96c91caba4d48da4a11c369b38a36703c9f54cef45ee9'}
LINE=re.compile(r'^\s*([0-9a-fA-F]+):\s+((?:[0-9a-fA-F]{4}\s+)+)\s*(.*?)\s*$')

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def printable(x):
 return 'hex:'+x.hex() if isinstance(x,(bytes,bytearray)) else x
def check(rows,name,got,expected):
 ok=got==expected; rows.append({'check':name,'passed':ok,'got':printable(got),'expected':printable(expected)})
 if not ok: raise AssertionError(f'{name}: got={got!r} expected={expected!r}')
def parse_dis(path, source):
 rows={}
 for line in path.read_text().splitlines():
  m=LINE.match(line)
  if not m: continue
  addr=int(m.group(1),16); halfwords=m.group(2).split()
  raw=b''.join(int(x,16).to_bytes(2,'little') for x in halfwords)
  asm=re.sub(r'<[^>]*>', '', m.group(3)).split(' @ ')[0]
  asm=' '.join(asm.split())
  rows[addr]=(raw,asm,line)
  if source[addr:addr+len(raw)]!=raw:
   raise AssertionError(f'disassembly/source byte mismatch at 0x{addr:x}')
 return rows

def ins(rows, addr):
 if addr not in rows: raise AssertionError(f'missing disassembly instruction 0x{addr:x}')
 return rows[addr][2]
def main():
 cs=[]
 for label,path,key in [('ROM',ROM,'rom'),('ABL1',ABL,'abl'),('full Thumb listing',DIS,'dis'),
  ('prior heap result',PREV,'previous'),('prior provider result',PROVIDER,'provider'),
  ('fresh APCB parse',APCB,None),('focused Thumb disassembly',WINDOW,None),
  ('heap-init Thumb disassembly',INIT,None),('heap-init caller disassembly',CALL,None)]:
  check(cs,label+' exists',path.is_file(),True)
  if key: check(cs,label+' sha256',sha(path),EXP[key])
 rom=ROM.read_bytes(); b=ABL.read_bytes()
 prev=json.loads(PREV.read_text()); provider=json.loads(PROVIDER.read_text()); ap=json.loads(APCB.read_text())
 check(cs,'prior heap result PASS',prev['status'],'PASS'); check(cs,'prior heap check count',prev['checks'],32)
 check(cs,'prior provider PASS',provider['status'],'PASS'); check(cs,'prior provider check count',provider['checks'],36)
 check(cs,'parser tool',ap['tool'],'scripts/apcb_detail.py'); check(cs,'parser one image',len(ap['images']),1)
 img=ap['images'][0]; check(cs,'parser input hash',img['sha256'],EXP['rom'])
 ar=img['apcb']; check(cs,'APCB offset',ar['offset'],'0xAB1000'); check(cs,'APCB size',ar['size'],2972)
 check(cs,'APCB checksum match',ar['checksum_match'],True)
 cbs=[g for g in ar['groups'] if g['gid']=='0x1707']; check(cs,'CBSG group present',len(cbs),1)
 check(cs,'CBSG subgroup count',len(cbs[0]['subgroups']),2)
 win=parse_dis(WINDOW,b); init=parse_dis(INIT,b); call=parse_dis(CALL,b); tail=parse_dis(TAIL,b); lookup=parse_dis(LOOKUP,b)
 # These are decoded instruction anchors; their halfword bytes are also checked against exact ABL1 bytes by parse_dis().
 expected_win={
  0x4b10:'movw r10, #0x162',0x4b18:'movs r5, #0x1',
  0x4b1a:'movw r6, #0xa04e',0x4b34:'add r0, sp, #0x24',
  0x4b36:'ldr r1, [sp, #0xa4]',0x4b38:'str r6, [sp, #0x24]',
  0x4b3a:'bl 0x6374',0x4b3e:'cbz r0, 0x4ba6',
  0x4b40:'sub.w r0, r10, r5',0x4b44:'movs r1, #0x8',0x4b46:'add.w r0, r0, r0, lsl #1',
  0x4b4a:'add.w r0, r1, r0, lsl #1',0x4b4e:'strd r0, r6, [sp, #20]',
  0x4b52:'movs r0, #0x4',0x4b56:'strb.w r0, [sp, #0x1c]',0x4b5a:'add r0, sp, #0x14',
  0x4b5c:'bl 0x6238',0x4b68:'ldr r6, [sp, #0x20]',0x4b6a:'str r6, [sp, #0x30]',
  0x4bae:'ldr r0, [sp, #0x2c]',0x4bb0:'ldr.w r1, [r0, r4, lsl #2]',
  0x4c0a:'ldr.w r0, [r0, r4, lsl #2]',0x4c0e:'adds r1, r0, r2',
  0x4c14:'ldr r2, [sp, #0x78]',0x4c16:'ldrb r3, [r1, r0]',
  0x4c18:'strb r3, [r2, r0]',0x4c5e:'ldr r2, [sp, #0x30]',
  0x4c6a:'str.w r0, [r2, r7, lsl #2]'}
 for addr,asm in expected_win.items():
  actual=' '.join((tail[addr][1] if addr in tail else win[addr][1]).split())
  check(cs,f'0x{addr:x} instruction',actual,asm)
 # 6374 runtime table search node flow + output pointer/length stores.
 expected_init={
  0x6374:'ldr r2, [pc, #0x70]',0x6376:'push {r3, r4, r5, r6, r7, lr}',
  0x6378:'ldr r7, [pc, #0x70]',0x637c:'ldr r3, [r2]',0x637e:'cmp r3, r7',0x638c:'ldr r4, [r2, #0x8]',
  0x6394:'ldr r5, [r0]',0x6396:'ldr r4, [r3]',0x6398:'cmp r4, r5',
  0x639c:'ldr r3, [r3, #0xc]',0x63a6:'cbz r6, 0x63ba',0x63a8:'ldrb r1, [r3, #0x9]',
  0x63aa:'adds r2, r3, r1',0x63ac:'adds r2, #0x10',
  0x63ae:'str r2, [r0, #0x8]',0x63b0:'ldr r2, [r3, #0x4]',
  0x63b2:'subs r1, r2, r1',0x63b4:'str r1, [r0, #0x4]',0x63b6:'movs r0, #0x0'}
 for addr,asm in expected_init.items():
  actual=' '.join(lookup[addr][1].split())
  check(cs,f'0x{addr:x} lookup instruction',actual,asm)
 check(cs,'0x6374 pointer literal raw bytes',b[0x63e8:0x63ec].hex(),'00300700')
 check(cs,'0x6374 sentinel bytes',b[0x63ec:0x63f0],b'HEAP')
 # 63f8 header init, called from 6f78.
 expected_hdr={0x63fa:'ldr r1, [pc, #0x24]',0x63fe:'strd r1, r2, [r0, #24]',
  0x6404:'strd r3, r2, [r1, #4]',0x6408:'str r3, [r1, #0xc]',
  0x640c:'str r3, [r1]',0x6412:'str r3, [r1, #0x14]',0x6414:'str r2, [r1, #0x1c]',
  0x6418:'strb r1, [r0, #0x10]'}
 for addr,asm in expected_hdr.items():
  actual=' '.join(init[addr][1].split())
  check(cs,f'0x{addr:x} heap-header instruction',actual,asm)
 check(cs,'heap init table base literal',b[0x6420:0x6424].hex(),'00300700')
 check(cs,'heap init magic',b[0x6424:0x6428],b'HEAP')
 check(cs,'heap initializer called from exact ABL1 routine',call[0x6f78][1].split()[0],'bl')
 check(cs,'heap initializer call target',call[0x6f78][1].split()[1],'0x63f8')
 # Input/output qualification: the returned +8 body pointer is reused as an entry-vector base at 4bae;
 # selected entry bytes are copied through the indirect destination pointer held at SP+0x78; pointer table separately gets entries.
 check(cs,'request-size formula',8+3*(0x162-1),0x42b)
 check(cs,'aligned ROM A04E key absent',rom.find((0xa04e).to_bytes(4,'little')),-1)
 check(cs,'aligned ROM runtime base 0x73000 absent',rom.find((0x73000).to_bytes(4,'little')),-1)
 result={'status':'PASS','checks':len(cs),'evidence_class':['observed-bytes','static-analysis'],
  'inputs':{'rom':str(ROM),'abl1':str(ABL),'full_thumb_listing':str(DIS),'focused_disassembly':str(WINDOW),
   'heap_init_disassembly':str(INIT),'heap_init_call_disassembly':str(CALL),'pointer_tail_disassembly':str(TAIL),'lookup_disassembly':str(LOOKUP),'prior_heap_result':str(PREV),
   'prior_provider_result':str(PROVIDER),'fresh_apcb_parse':str(APCB)},
  'hashes':{'rom':sha(ROM),'abl1':sha(ABL),'full_thumb_listing':sha(DIS),'focused_disassembly':sha(WINDOW),
   'heap_init_disassembly':sha(INIT),'heap_init_call_disassembly':sha(CALL),'pointer_tail_disassembly':sha(TAIL),'lookup_disassembly':sha(LOOKUP),'prior_heap_result':sha(PREV),
   'prior_provider_result':sha(PROVIDER),'fresh_apcb_parse':sha(APCB)},
  'bridge':{
   'lookup_input':'Provider selector 0x0f places key 0xA04E in descriptor SP+0x24 and calls 0x6374 (0x4B1A-0x4B3A).',
   'runtime_table':'0x6374 reads the table base literal 0x73000, checks sentinel HEAP, and compares requested key with node+0. On hit it stores a payload pointer to descriptor+8 (node+0x10+metadata byte) and a remaining payload length to descriptor+4 (node size less metadata byte).',
   'initializer':'Exact ABL1 routine 0x63F8 writes a HEAP-tagged arena header at 0x73000 and is called at 0x6F78. This proves header initialization only, not a populated node keyed 0xA04E.',
   'consumer':'After hit, provider 0x4B40-0x4B5C submits a second request (computed size 0x42B, key 0xA04E, type 4) to 0x6238. The first result body pointer at SP+0x2C is then read as an entry-vector base at 0x4BAE; selected entry bytes are copied to an indirect destination buffer addressed by `[SP+0x78]` at 0x4C14-0x4C18. The separate 0x6238 output pointer is kept at SP+0x30 and receives per-entry pointers at 0x4C6A.',
   'scope':'Static bridge from the 0xA04E runtime lookup body into a frame-indirect byte destination and a heap-backed pointer table is proven. The destination identity behind SP+0x78 is unresolved; no byte path names a clock descriptor or a frequency domain.'},
  'closed_boundary':'The runtime HEAP header initializer is internal to ABL1, but the source/population of the linked node whose key is 0xA04E is not recovered in the checked chain. The pinned ROM has no aligned 0xA04E or 0x73000 scalar. Existing APCB parsing confirms valid APCB/CBSG structure only; no schema-backed APCB/CBSG-to-HEAP conversion is established.',
  'limitations':['No ABL1/AGESA firmware execution, runtime HEAP snapshot, or hardware behavior was performed.','No identity is assigned to the indirect SP+0x78 output pointer.','No token/value is assigned MHz, voltage, frequency, or 1:1 semantics.','The CBSG raw row schema and runtime AP(C)B-to-HEAP producer remain unresolved.'],
  'checks_detail':cs}
 (OUT/'abl1-runtime-heap-followup-result.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'status':result['status'],'checks':len(cs),'bridge':result['bridge'],'closed_boundary':result['closed_boundary']},indent=2))
if __name__=='__main__': main()
