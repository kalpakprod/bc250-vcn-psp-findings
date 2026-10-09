"""Pinned continuation checks: service dispatch, TOS caller, and false UEFI leads."""
import hashlib
import json
import re
import struct
import subprocess
from pathlib import Path

out = Path(__file__).resolve().parent
rom = Path('evidence/donor/retroweb-20260916/BC250_5.00_clv.bin').read_bytes()
assert hashlib.sha256(rom).hexdigest() == 'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
base = 0x984f00
word = lambda a: struct.unpack_from('<I',rom,a)[0]
# Chain selecting opcode1037: compare to1030; positive delta7 <61;
# TBB entry7 -> BFB2; B at BFB2 -> C51C.
for rel,raw in {0xbce8:'41f23002',0xbcec:'9042',0xbcee:'a0eb0201',
                0xbcf4:'58dc',0xbda8:'3d29',0xbdaa:'dad2',0xbdac:'07e0',
                0xbdbe:'dfe801f0',0xbfb2:'b3e2',0xc51c:'04f13800',
                0xc520:'04f14402',0xc524:'0bc8',0xc526:'05f0dff9'}.items():
    b=bytes.fromhex(raw);assert rom[base+rel:base+rel+len(b)]==b,hex(rel)
delta=0x1037-0x1030
assert 0<delta<61
slot=0xbdbe+4+delta
assert 0xbdbe+4+2*rom[base+slot]==0xbfb2
h=struct.unpack_from('<H',rom,base+0xbfb2)[0]
disp=(h&0x7ff)*2
if disp&2048:disp-=4096
assert 0xbfb2+4+disp==0xc51c

# Exact code windows only, not mixed code/data output from discovery.
windows=[]
for name,start,end in [('tos-wrapper',0x8faec4,0x8faefc),('tos-caller',0x8fe046,0x8fe054),
                       ('t28-case',base+0xc51c,base+0xc52a)]:
    cmd=['llvm-mc','--disassemble','--triple=thumbv7','--show-encoding']
    r=subprocess.run(cmd,input=' '.join('0x%02x'%x for x in rom[start:end])+'\n',capture_output=True,text=True)
    (out/f'goal-{name}.stdout').write_text(r.stdout);(out/f'goal-{name}.stderr').write_text(r.stderr)
    assert r.returncode==0 and not r.stderr,(name,r.returncode,r.stderr)
    pc=start;decoded=[]
    for line in r.stdout.splitlines():
        m=re.search(r'encoding: \[(.*?)\]',line)
        if not m:continue
        data=bytes(int(x,16) for x in m[1].split(','))
        assert rom[pc:pc+len(data)]==data
        decoded.append({'rom':hex(pc),'bytes':data.hex(),'instruction':line.split('@')[0].strip()});pc+=len(data)
    assert pc==end
    windows.append({'name':name,'command':cmd,'exit':r.returncode,'instructions':decoded})
assert rom[0x8faede:0x8faee2]==bytes.fromhex('41f23700')
assert rom[0x8fe04c:0x8fe04e]==bytes.fromhex('0f20')
# Verify module identity and instruction bytes for the false1037 serialization lead.
p=Path('evidence/firmware-audit/20260919-inv-token-consumers')
stem='AmdFabricAriPei-c5b99650a442'
b=(p/(stem+'.bin')).read_bytes()
assert hashlib.sha256(b).hexdigest()=='c5b99650a442ed9be1cf3a62e7571f7eb163b9f80a60d4fcc7b3e9afe4506f78'
selected=[r for r in json.loads((p/(stem+'.instructions.json')).read_text()) if 0x772f<=r['rva']<=0x7755]
for r in selected:
    off=r['rva']-0x198;data=bytes.fromhex(r['bytes']);assert b[off:off+len(data)]==data
assert next(r for r in selected if r['rva']==0x7737)['bytes']=='668910'
assert next(r for r in selected if r['rva']==0x7755)['bytes']=='884103'
print(json.dumps({'status':'PASS','evidence_class':'observed-bytes/static-analysis',
 't28_service_opcode':'0x1037','dispatch':['BCF4','BDA8','BDAC','BDBE[7]','BFB2','C51C','C526','118E8'],
 'request_fields':{'0x38':'SMU command','0x3C':'SMU argument','0x40':'poll limit','0x44':'returned argument'},
 'tos_wrapper_rom':'0x8FAEC4','tos_wrapper_service':'0x1037 via SVC F2',
 'tos_only_direct_BL_caller_message':'0x0F at ROM8FE04C; not init9',
 'false_uefi1037_lead':'AmdFabricAriPei772F stores a16-bit record ID, then a byte from source+98; not PSP service call',
 'build_decision':'Do not patch the serialization token or substitute init9 for a proven coefficient-control route.',
 'windows':windows,'false_lead_instructions':selected,
 'remaining':['BIOS-callable path to coefficient changes not demonstrated.',
              'Direct-call enumeration excludes indirect calls and other components.',
              'No physical domain/voltage encoding inferred from service discovery.',
              'No ROM patch, emulation, hardware execution, or flash.']},indent=2))
