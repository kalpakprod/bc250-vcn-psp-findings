#!/usr/bin/env python3
"""Offline bounded PEI interface census; writes only beside this evidence script."""
import hashlib,json,struct,subprocess,sys,uuid,re
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path('scripts').resolve()))
from firmware_audit import Extractor
OUT=Path(__file__).resolve().parent
ROM=Path('evidence/donor/retroweb-20260916/BC250_5.00_clv.bin')
EXPECTED='ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
GUID=uuid.UUID('04126c85-5c4e-458f-abc1-29f1f7da365e').bytes_le
HEAP_GUID=uuid.UUID('d97d161a-16cd-4ada-b9f6-aec3f9fccc2c').bytes_le
rows=[]
def offsets(b,p):
 return [m.start() for m in re.finditer(re.escape(p),b)]
class Census(Extractor):
 def save_executable(self,b,t,c):
  row=dict(c,type=t,size=len(b),sha256=hashlib.sha256(b).hexdigest(),guid_offsets=offsets(b,GUID),heap_guid_offsets=offsets(b,HEAP_GUID))
  rows.append(row)
  if not row['guid_offsets']: return
  name=c.get('ui',c['ffs_guid']); stem=re.sub('[^A-Za-z0-9_-]','_',name)
  path=OUT/(stem+'.bin'); path.write_bytes(b)
  if t=='TE':
   machine,nsec,sub,strip=struct.unpack_from('<HBBH',b,2); base=struct.unpack_from('<Q',b,16)[0]; delta=strip-40
   row.update(imagebase=hex(base),delta=hex(delta),sections=[])
   for i in range(nsec):
    o=40+40*i; vs,rva,size,raw=struct.unpack_from('<IIII',b,o+8); flags=struct.unpack_from('<I',b,o+36)[0]
    row['sections'].append(dict(rva=hex(rva),raw=hex(raw-delta),size=size,flags=hex(flags)))
    if not flags&0x20: continue
    code=OUT/(stem+f'-{i}.code'); code.write_bytes(b[raw-delta:raw-delta+size])
    cmd=['objdump','-D','-b','binary','-m','i386','-M','intel',f'--adjust-vma={rva}',str(code)]
    p=subprocess.run(cmd,capture_output=True,text=True,check=True); (OUT/(stem+f'-{i}.asm')).write_text(p.stdout)
  else:
   p=subprocess.run(['objdump','-d','-M','intel',str(path)],capture_output=True,text=True,check=True); (OUT/(stem+'.asm')).write_text(p.stdout)
  print(name,row['guid_offsets'],row.get('imagebase'))
b=ROM.read_bytes(); assert hashlib.sha256(b).hexdigest()==EXPECTED
Census(b,OUT,'clv').extract()
(OUT/'census.json').write_text(json.dumps(dict(input=str(ROM),sha256=EXPECTED,extractor_sha256=hashlib.sha256(Path('scripts/firmware_audit.py').read_bytes()).hexdigest(),records=rows),indent=2)+'\n')
print('records',len(rows),'unique',len({r['sha256'] for r in rows}),'hits',sum(bool(r['guid_offsets']) for r in rows))
