#!/usr/bin/env python3
import hashlib,json,re,struct
from pathlib import Path
P=Path(__file__).resolve().parent
rows=json.loads((P/'census.json').read_text())['records']; report=[]; windows=[]; total=0
for r in rows:
 if not r['guid_offsets']: continue
 name=r.get('ui',r['ffs_guid']); b=(P/(name+'.bin')).read_bytes(); assert hashlib.sha256(b).hexdigest()==r['sha256']
 base=int(r['imagebase'],16); delta=int(r['delta'],16); lines=(P/(name+'-0.asm')).read_text().splitlines(); ins=[]
 for l in lines:
  m=re.match(r'\s*([0-9a-f]+):\s*((?:[0-9a-f]{2} )*[0-9a-f]{2})\s*(.*)',l)
  if not m: continue
  a=int(m[1],16); raw=bytes.fromhex(m[2]); assert b[a-delta:a-delta+len(raw)]==raw,(name,hex(a));total+=1
  ins.append((a,m[3].strip(),l))
 va=base+delta+r['guid_offsets'][0]; guidrefs=[a for a,s,l in ins if hex(va) in s]
 def window(a,bound=20):
  j=next(j for j,(x,s,l) in enumerate(ins) if x==a);return '\n'.join(l for x,s,l in ins[max(0,j-bound):j+8])
 def callers(target):return [a for a,s,l in ins if re.fullmatch(r'call\s+0x'+format(target,'x'),s)]
 def ptrs(target):return [hex(m.start()) for m in re.finditer(re.escape(struct.pack('<I',base+target)),b)]
 rr=dict(module=name,guid_refs=[hex(a) for a in guidrefs])
 if name!='CbsBasePei':
  g=guidrefs[0];wrapper=max(a for a,s,l in ins if a<g and s=='push   ebp');wc=callers(wrapper); assert len(wc)==1
  gateway=max(a for a,s,l in ins if a<wc[0] and s=='push   ebp'); cc=callers(gateway)
  rr.update(wrapper=hex(wrapper),gateway=hex(gateway),wrapper_calls=[hex(a) for a in wc],gateway_calls=[hex(a) for a in cc],wrapper_pointer_occurrences=ptrs(wrapper),gateway_pointer_occurrences=ptrs(gateway))
  windows.append(name+' wrapper/gateway\n'+window(g,15)+'\n'+window(wc[0],17))
  for a in cc: windows.append(name+' gateway caller '+hex(a)+'\n'+window(a,12))
 # Decoded signed immediates + arithmetic candidates are retained, not merely raw u32 scans.
 rr['minus_two_instructions']=[l for a,s,l in ins if re.search(r'0xfffffffe\b|(?<![0-9a-f])-0x2\b',s)]
 rr['raw_push_imm8_minus_two']=[hex(m.start()) for m in re.finditer(b'\x6a\xfe',b)]
 report.append(rr)
(P/'caller-windows.txt').write_text('\n\n'.join(windows)+'\n')
(P/'verification.json').write_text(json.dumps(dict(byte_lines_checked=total,interfaces=report),indent=2)+'\n')
print('PASS listing byte lines',total)
for r in report: print(r['module'],r.get('wrapper'),r.get('gateway'),r.get('gateway_calls'),r['minus_two_instructions'])
