#!/usr/bin/env python3
"""Own offline consumer census; reuses unchanged supported firmware extractor."""
import hashlib, json, re, struct, subprocess, sys, uuid
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path('scripts').resolve()))
from firmware_audit import Extractor
OUT = Path(__file__).resolve().parent
ROM = Path('evidence/donor/retroweb-20260916/BC250_5.00_clv.bin')
EXPECTED = 'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
PATTERNS = {'heap_guid': uuid.UUID('d97d161a-16cd-4ada-b9f6-aec3f9fccc2c').bytes_le, 'nvtb': b'NVTB', 'inv': b'$INV'}
TARGETS = {0x1364,0x1363,0x11ed,0x1204,0x1331,0x1373,0x1374}
def offsets(b, p):
    return [m.start() for m in re.finditer(re.escape(p), b)]
def digest(b): return hashlib.sha256(b).hexdigest()
def instruction_rows(text, code, rva):
    result = []
    for line in text.splitlines():
        m = re.match(r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2} )+)\s*(.*?)\s*$', line)
        if not m: continue
        address, raw, asm = int(m[1],16), bytes.fromhex(m[2]), m[3]
        assert code[address-rva:address-rva+len(raw)] == raw
        fields = asm.split(None,1)
        result.append({'rva':address,'bytes':raw.hex(),'mnemonic':fields[0] if fields else '', 'operands':fields[1] if len(fields)>1 else ''})
    return result
class Census(Extractor):
    def save_executable(self,b,t,c):
        row = dict(c,type=t,size=len(b),sha256=digest(b),**{k:offsets(b,p) for k,p in PATTERNS.items()})
        rows.append(row)
        # Full supported census gets sections and decoded scan, not only marker hits.
        if t == 'TE':
            machine,nsec,sub,strip = struct.unpack_from('<HBBH',b,2)
            base = struct.unpack_from('<Q',b,16)[0]; delta = strip-40; sh = 40
            entry = struct.unpack_from('<I',b,8)[0]
        else:
            pe = struct.unpack_from('<I',b,0x3c)[0]; assert b[pe:pe+4] == b'PE\0\0'
            machine,nsec = struct.unpack_from('<HH',b,pe+4)
            optsize = struct.unpack_from('<H',b,pe+20)[0]; opt = pe+24
            magic = struct.unpack_from('<H',b,opt)[0]
            base = struct.unpack_from('<Q' if magic==0x20b else '<I',b,opt+(24 if magic==0x20b else 28))[0]
            delta = 0; sh = opt+optsize; entry = struct.unpack_from('<I',b,opt+16)[0]
        assert machine in (0x14c,0x8664)
        row.update(imagebase=base,delta=delta,machine=machine,entry=entry,sections=[])
        stem = re.sub('[^A-Za-z0-9_-]','_',c.get('ui') or c['ffs_guid'])+'-'+row['sha256'][:12]
        row['stem'] = stem
        instructions = []
        for i in range(nsec):
            o = sh+40*i; vs,rva,size,raw = struct.unpack_from('<IIII',b,o+8); flags = struct.unpack_from('<I',b,o+36)[0]
            raw -= delta
            row['sections'].append(dict(rva=rva,raw=raw,size=size,virtual_size=vs,flags=flags))
            if not flags & (0x20|0x20000000): continue
            assert 0 <= raw <= raw+size <= len(b)
            code = b[raw:raw+size]; path=OUT/(stem+f'-{i}.code'); path.write_bytes(code)
            cmd=['objdump','-D','-z','--insn-width=16','-b','binary','-m','i386:x86-64' if machine==0x8664 else 'i386','-M','intel',f'--adjust-vma={rva}',str(path)]
            text=subprocess.run(cmd,capture_output=True,text=True,check=True).stdout
            (OUT/(stem+f'-{i}.asm')).write_text(text)
            instructions += instruction_rows(text,code,rva)
        row['instruction_count'] = len(instructions)
        row['marker_instructions'] = [x for x in instructions if re.search(r'0x(?:4254564e|564e4924)\b',x['operands'])]
        row['target_candidates'] = [x for x in instructions if any(re.search(r'\b0x'+format(v,'x')+r'\b',x['operands']) for v in TARGETS)]
        (OUT/(stem+'.instructions.json')).write_text(json.dumps(instructions,separators=(',',':'))+'\n')
        (OUT/(stem+'.bin')).write_bytes(b)
        print(c.get('ui',c['ffs_guid']),t,'GUID',len(row['heap_guid']),'NVTB',len(row['nvtb']),'INV',len(row['inv']),'markers',len(row['marker_instructions']))
rows=[]
b=ROM.read_bytes(); assert len(b)==16777216 and digest(b)==EXPECTED
extractor=Census(b,OUT,'clv'); extractor.extract()
prior=json.loads(Path('evidence/firmware-audit/20260919-inv-buffer-lifetime/census.json').read_text())
assert sorted(r['sha256'] for r in rows)==sorted(r['sha256'] for r in prior['records'])
result=dict(input=str(ROM),sha256=EXPECTED,extractor_sha256=digest(Path('scripts/firmware_audit.py').read_bytes()),objdump=subprocess.run(['objdump','--version'],capture_output=True,text=True,check=True).stdout.splitlines()[0],records=rows)
(OUT/'census.json').write_text(json.dumps(result,indent=2)+'\n')
print('TOTAL',len(rows),'unique',len({r['sha256'] for r in rows}),'GUID',sum(bool(r['heap_guid']) for r in rows),'NVTB',sum(bool(r['nvtb']) for r in rows),'INV',sum(bool(r['inv']) for r in rows),'instruction byte rows',sum(r['instruction_count'] for r in rows))
