#!/usr/bin/env python3
"""Trace exact ABL1 memory-speed input selection upstream of +0x20 writers."""
from __future__ import annotations
import hashlib,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; OUT=Path(__file__).resolve().parent
PAY=ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
TH=OUT/'abl1-data-thumb-llvm.txt'
EXP='af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def u32(b,o): return struct.unpack_from('<I',b,o)[0]
def ck(cs,n,got,exp):
 ok=got==exp;cs.append({'name':n,'passed':ok,'got':got,'expected':exp})
 if not ok: raise AssertionError(f'{n}: got {got!r} expected {exp!r}')
def line_map(text):
 out={}
 for line in text.splitlines():
  m=re.match(r'\s*([0-9a-f]+):',line)
  if m: out[int(m.group(1),16)]=line.strip()
 return out

def main():
 b=PAY.read_bytes(); text=TH.read_text(errors='replace'); lm=line_map(text); cs=[]
 ck(cs,'payload hash',sha(PAY),EXP); ck(cs,'thumb listing present',TH.exists(),True); ck(cs,'payload length',len(b),94624)
 # Exact structural/raw anchors for the config selector and producer consumers.
 raw={
  0x2220:'04460f46',0x2234:'94f83103',0x223c:'b4f81605',0x2248:'c8620021',0x224e:'86626068',
  0x225a:'206802ab',0x2264:'0720fff7',0x2266:'fff761fe',0x1f2c:'2de9ff41',0x1f56:'02f03bfc',
  0x47d0:'7cb50446',0x47de:'0d20cde9',0x47ea:'00f0eff8',0x77e2:'09f00bfe',0x77f4:'20804ff0',
  0xadcc:'816a49b1',0xadd0:'022911d0',0xade4:'2068806a',0xadf8:'c66a46a2',
  0x10ccc:'d0e90a97',0x10e1c:'a4f86050',0x10e50:'0784'}
 for o,h in raw.items(): ck(cs,f'raw 0x{o:X}',b[o:o+len(bytes.fromhex(h))].hex(),h)
 # Exact semantic lines.
 sem={
  0x2234:r'ldrb(?:\.w)?\s+r0, \[r4, #0x331\]',
  0x223c:r'ldrh(?:\.w)?\s+r0, \[r4, #0x516\]',
  0x2248:r'str\s+r0, \[r1, #0x2c\]',
  0x224e:r'str\s+r6, \[r0, #0x28\]',
  0x225a:r'ldr\s+r0, \[r4\]',
  0x2266:r'bl\s+0x1f2c\b',
  0x1f56:r'bl\s+0x47d0\b',
  0x47de:r'movs\s+r0, #0xd',
  0x47ea:r'bl\s+0x49cc\b',
  0x77e2:r'bl\s+0x113fc\b',
  0x77f4:r'strh\s+r0, \[r4\]',
  0xadcc:r'ldr\s+r1, \[r0, #0x28\]',
  0xadd0:r'cmp\s+r1, #0x2',
  0xade4:r'ldr\s+r0, \[r4\]',
  0xade8:r'ldr\.w\s+r0, \[r0, #0x770\]',
  0xadf8:r'ldr\s+r6, \[r0, #0x2c\]',
  0x10ccc:r'ldrd\s+r9, r7, \[r0, #40\]',
  0x10e1c:r'strh\.w\s+r5, \[r4, #0x60\]',
  0x10e50:r'strh\s+r7, \[r0, #0x20\]',
 }
 for o,p in sem.items(): ck(cs,f'semantic 0x{o:X}',bool(re.search(p,lm.get(o,''),re.I)),True)
 # Numeric enum map in exact current bytes; these are policy values, not units.
 enum={
 0x22b2:0x7d,0x22b6:0xe1,0x22be:0xfa,0x22c2:0x190,0x22c8:0x1c2,
 0x22ce:0x1f4,0x22d4:0x2ee,0x22da:0x352,0x22e0:0x3e8,0x22e6:0x4e2,
 0x22ec:0x532,0x22f2:0x55f,0x22f8:0x5dc,0x22fe:0x640,0x2304:0x672,
 0x230a:0x6a4,0x2312:0x6d6,0x2318:0x708,0x231e:0x73a,0x2324:0x7d0,
 }
 enum_rows=[]
 for o,v in enum.items():
  line=lm.get(o,''); m=re.search(r'(?:movw|movs)\s+r0, #0x([0-9a-f]+)',line,re.I)
  got=int(m.group(1),16) if m else None
  ck(cs,f'enum output 0x{o:X}',got,v); enum_rows.append({'site':f'0x{o:X}','value':f'0x{v:X}','line':line})
 ck(cs,'APCB/CBS getter strings in exact payload',b'APCB Config parameter' in b and b'Get config parameter' in b,True)
 # Result: distinguish concrete input from unresolved source.
 result={
  'status':'PASS','checks':len(cs),'evidence_class':['observed-bytes','static-analysis'],
  'input':str(PAY),'payload_sha256':sha(PAY),'candidate_base':'0x57100',
  'config_selector':{
   'entry':'0x2220','context':'r4','action_param':'r7=r1',
   'override_enable':'[r4+0x331] != 0','override_value':'[r4+0x516] != 0xFFFF',
   'override_write':'[r4+0x04]+0x2C <- [r4+0x516]; [r4+0x04]+0x28 <- 2',
   'apcb_path':'case 2 calls 0x1F2C with (r0=7, r1=2); 0x1F2C calls 0x47D0; 0x47D0 sets r0=0xD and calls 0x49CC with token=7,timepoint=2 and output pointer',
   'apcb_strings':['APCB Config parameter %04x mapped to CBS token %04x','Get config parameter: token %04x, timepoint %04x','Get config parameter from default: token %04x, timepoint %04x'],
   'enum_output':enum_rows,
   'unknown':'The 0x49CC/APCB-CBS helper output is not mapped to AmdSetup+0x316/$INV 0x11ED in this bounded trace.'
  },
  'override_field_producer':{
   'site':'0x77E2->0x77F4','call':'0x113FC(r0=0x72,r1=0x96)','effect':'returns a u16 assembled from parameter bytes and stores it to [r4+0x516]','source_boundary':'0x1145A -> 0x6AC0/0x6B14 parameter transport; semantic Setup/APCB identity not independently bound.'
  },
  'ad58_input':{
   'mode':'[r4+0x04]+0x28','selected_value':'[r4+0x04]+0x2C when mode==2','default':'0x0320','special':'if [r4+0x04]+0x790 == 6 then 0x01C2','mode0_bound':'min(0x0320, [ [r4]+0x28 ]+0x770)','write':'for each selected channel: [r4+0x0C]+0x20 <- r6; mirror [r4+0x04]+0x2C <- r6'
  },
  '10cc0_input':{
   'mode_speed_load':'ldrd r9,r7,[[r4+0x04]+0x28]','mode_branches':'r9==0 or r9==1 receive distinct paths; other values log an error','channel_reduce':'reads selected channel +0x20, starts candidate 0x7D1, reduces; compares against [r4+0x60] and stores lower result','write':'each selected channel +0x20 <- [r4+0x60] after reduction'
  },
  'enum_map':enum_rows,
  'conclusion':'The original speed input is concretely selected before AD58: explicit override [r4+0x516] or APCB/CBS getter token 7 at timepoint 2, then enum-mapped to the listed numeric policy values and written to [r4+4]+0x2C with mode 2. AD58 consumes that field; 10CC0 reduces per-channel +0x20 and clamps context +0x60. Setup/INV identity, units, loader/runtime execution, training, and hardware remain unresolved.',
  'limits':['Numeric values are observed policy constants; strings mention MHz but no unit conversion is proven.','APCB/CBS helper is an exact local config boundary, not a proven AmdSetup/INV edge.','No runtime or hardware claim.']
 }
 out=OUT/'abl1-producer-input-result.json';out.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'status':'PASS','checks':len(cs),'enum_count':len(enum_rows),'result':str(out),'conclusion':result['conclusion']},indent=2))
if __name__=='__main__':main()
