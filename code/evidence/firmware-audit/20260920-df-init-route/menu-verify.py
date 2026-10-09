"""Exact-clv native HII audit, reusing existing package/string decoder."""
import hashlib
import importlib.util
import json
import struct
from collections import deque
from pathlib import Path

out=Path(__file__).resolve().parent
p=Path('evidence/firmware-audit/20260919-inv-token-consumers')
rom=Path('evidence/donor/retroweb-20260916/BC250_5.00_clv.bin').read_bytes()
assert hashlib.sha256(rom).hexdigest()=='ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
census=json.loads((p/'census.json').read_text());assert census['sha256']==hashlib.sha256(rom).hexdigest()
parser=Path('import/from-windows/Users/kukuruza/bc250-bios/tools/uefi/e1_ifr_dump.py')
spec=importlib.util.spec_from_file_location('ifr',parser);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
stem='CbsSetupDxe-7ff717d51c9a';b=(p/(stem+'.bin')).read_bytes()
rec=next(r for r in census['records'] if r.get('stem')==stem)
assert hashlib.sha256(b).hexdigest()==rec['sha256']
packages=m.find_packages(b);so,_,sn=next(x for x in packages if x[1]==4)
ss=dict(m.parse_sibt(b[so:so+sn])[1]);ss={k:v.rstrip('\0') for k,v in ss.items()}
fo,_,fn=next(x for x in packages if x[1]==2)
forms={};refs=[];questions=[];stack=[];form=None;current=None;pos=fo+4
wanted={0x316,0x32f,0x330,0x6a3,0x6e5,0x6e6,0x703,0x704}
while pos<fo+fn:
    op=b[pos];ln=b[pos+1]&127;scope=b[pos+1]>>7
    assert ln>=2 and pos+ln<=fo+fn,(hex(pos),ln)
    raw=b[pos:pos+ln];body=raw[2:]
    conditions=[{'op':hex(s['op']),'module_offset':hex(s['pos'])} for s in stack if s['op'] in (0x0a,0x19,0x1e)]
    if op==1:
        form,title=struct.unpack_from('<HH',body);forms[form]=ss.get(title,str(title))
    if op in (5,6,7):
        prompt,helpid,qid,vid,offset,flags=struct.unpack_from('<HHHHHB',body)
        current={'qid':hex(qid),'form':hex(form),'label':ss.get(prompt,''),'help':ss.get(helpid,''),
                 'varstore_id':hex(vid),'offset':hex(offset),'flags':hex(flags),'reset_required':bool(flags&16),
                 'callback':bool(flags&4),'read_only':bool(flags&1),'conditions':conditions,
                 'module_offset':hex(pos),'raw':raw.hex(),'options':[]}
        if offset in wanted:questions.append(current)
        if op==7:
            size=1<<(body[11]&3)
            current['bounds']=[int.from_bytes(body[12+i*size:12+(i+1)*size],'little') for i in range(3)]
    if op==9 and current is not None:
        sid,fl,typ=struct.unpack_from('<HBB',body)
        size={0:1,1:2,2:4,3:8,4:1}.get(typ)
        if size:current['options'].append({'label':ss.get(sid,''),'value':int.from_bytes(body[4:4+size],'little'),'default':bool(fl&16)})
    if op==15 and len(body)>=13:
        prompt,_,qid,vid,offset,flags,target=struct.unpack_from('<HHHHHBH',body)
        refs.append({'source':form,'target':target,'label':ss.get(prompt,''),'conditions':conditions,'module_offset':hex(pos)})
    if op==0x29:
        assert stack,hex(pos)
        popped=stack.pop()
        if popped['op'] in (5,6,7):current=None
    elif scope:stack.append({'op':op,'pos':pos})
    pos+=ln
assert pos==fo+fn and not stack
paths={0x7000:[0x7000]};q=deque([0x7000])
while q:
    node=q.popleft()
    for r in refs:
        if r['source']==node and not r['conditions'] and r['target'] not in paths:
            paths[r['target']]=paths[node]+[r['target']];q.append(r['target'])
for item in questions:
    path=paths.get(int(item['form'],16));item['unconditional_ref_path']=[{'form':hex(f),'title':forms[f]} for f in path] if path else None
# Recheck persistence callsite bytes using existing section map.
instructions=json.loads((p/(stem+'.instructions.json')).read_text())
selected=[r for r in instructions if 0x2ec<=r['rva']<=0x32d or 0x86c<=r['rva']<=0x924 or 0xad1<=r['rva']<=0xb03 or '0x40278' in r['operands']]
for r in selected:
    a=r['rva'];data=bytes.fromhex(r['bytes'])
    sec=next(s for s in rec['sections'] if s['rva']<=a and a+len(data)<=s['rva']+s['size'])
    off=sec['raw']+a-sec['rva'];assert b[off:off+len(data)]==data
assert b[0x3f028:0x3f03a]=='AmdSetup\0'.encode('utf-16-le')
assert next(r for r in instructions if r['rva']==0x919)['bytes']=='ff5058'
result={'status':'PASS','rom_sha256':hashlib.sha256(rom).hexdigest(),'module_sha256':rec['sha256'],
 'parser_sha256':hashlib.sha256(parser.read_bytes()).hexdigest(),'forms_package_offset':hex(fo),
 'ifr_bytes_walked':fn-4,'questions':questions,'refs':refs,'forms':{hex(k):v for k,v in forms.items()},
 'persistence_instruction_evidence':selected,
 'limits':['Static form reachability starts at CBS form7000; main AMITSE integration/live visibility not proven.',
           'RESET_REQUIRED and CALLBACK are IFR flags, not physical application evidence.',
           'Existing parser HIDDEN means conditional scope, not evaluated truth.',
           'No setting saved and no hardware command executed.']}
(out/'menu-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'questions':questions},indent=2))
