"""Decode only pinned PSP code windows with installed LLVM; no firmware execution."""
import hashlib
import json
import re
import struct
import subprocess
from pathlib import Path

out = Path(__file__).resolve().parent
rom = Path('evidence/donor/retroweb-20260916/BC250_5.00_clv.bin').read_bytes()
assert hashlib.sha256(rom).hexdigest() == 'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
base, size = 0x984f00, 108400
b = rom[base:base+size]
assert hashlib.sha256(b).hexdigest() == '5b6828bff3f10f1b120b279932af156438e1bdd724508e44b7630fce9716251f'
# Recheck the directory descriptor, without copying security material.
entries = [struct.unpack_from('<IIII',rom,0x8e0010+16*i) for i in range(struct.unpack_from('<I',rom,0x8e0008)[0])]
assert any(t&255 == 0x28 and n==size and (loc&0xffffff)==base for t,n,loc,_ in entries)
version = subprocess.run(['llvm-mc','--version'],capture_output=True,text=True,check=True).stdout
(out/'sender-llvm-version.txt').write_text(version)
cmd = ['llvm-mc','--disassemble','--triple=thumbv7','--show-encoding']
windows=[]
for lo,hi in [(0x118e8,0x11994),(0xc51c,0xc52a),(0xfb48,0xfb5e),(0xfb9e,0xfbae),(0xfc80,0xfc90)]:
    r=subprocess.run(cmd,input=' '.join('0x%02x'%x for x in b[lo:hi])+'\n',capture_output=True,text=True)
    (out/f'sender-llvm-{lo:x}.stdout').write_text(r.stdout)
    (out/f'sender-llvm-{lo:x}.stderr').write_text(r.stderr)
    assert r.returncode==0 and not r.stderr,(hex(lo),r.returncode,r.stderr)
    a=lo; decoded=[]
    for line in r.stdout.splitlines():
        m=re.search(r'encoding: \[(.*?)\]',line)
        if not m: continue
        raw=bytes(int(x,16) for x in m[1].split(','))
        assert b[a:a+len(raw)]==raw,hex(a)
        ins=line.split('@')[0].strip();row={'relative':hex(a),'rom':hex(base+a),'bytes':raw.hex(),'instruction':ins}
        lit=re.search(r'\[pc, #(\d+)\]',ins)
        if lit:
            adr=((a+4)&~3)+int(lit[1]);row.update(literal_rom=hex(base+adr),literal_value=hex(struct.unpack_from('<I',b,adr)[0]))
        decoded.append(row);a+=len(raw)
    assert a==hi,(hex(a),hex(hi))
    windows.append({'start':hex(lo),'end':hex(hi),'instructions':decoded})
# Raw Thumb BL candidates; caller windows above validate all four instruction sites.
calls=[]
for a in range(0,len(b)-4,2):
    h1,h2=struct.unpack_from('<HH',b,a)
    if h1&0xf800!=0xf000 or h2&0xd000!=0xd000: continue
    s=(h1>>10)&1;j1=(h2>>13)&1;j2=(h2>>11)&1
    imm=(s<<24)|((1^(j1^s))<<23)|((1^(j2^s))<<22)|((h1&0x3ff)<<12)|((h2&0x7ff)<<1)
    if s: imm-=1<<25
    if a+4+imm==0x118e8: calls.append(hex(a))
assert calls==['0xc526','0xfb58','0xfba8','0xfc8a']
print(json.dumps({'status':'PASS','input_psp_type':'0x28','input_sha256':hashlib.sha256(b).hexdigest(),
 'rom_base':hex(base),'size':size,'function_relative':'0x118e8','function_rom':'0x9967e8',
 'command':cmd,'direct_BL_sites':calls,'windows':windows,
 'conclusion':'Generic Queue5 transport found in PSP type28; C526 loads message/argument/timeout from caller structure. No constant message9 producer identified.',
 'limits':['Static code only; SVC mapping implementation and live availability unverified.',
           'Relative addresses refer to complete PSP entry, not an assumed stripped body.',
           'Indirect/tail callers not exhaustively enumerated.']},indent=2))
