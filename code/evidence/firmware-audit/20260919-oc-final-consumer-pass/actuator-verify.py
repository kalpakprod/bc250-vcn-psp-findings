#!/usr/bin/env python3
"""Read-only raw correspondence checks and synthetic f32 encoding controls.
Writes only a new actuator-verification.json; refuses an existing output.
"""
from pathlib import Path
import hashlib, json, re, struct, sys
E = Path(__file__).resolve().parent
S = Path('import/from-windows/Users/kukuruza/tmp_bc250/upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5')
R = Path('evidence/donor/retroweb-20260916/BC250_5.00_clv.bin')
b, r = S.read_bytes(), R.read_bytes()
assert len(b)==262400 and hashlib.sha256(b).hexdigest()=='cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37'
assert len(r)==16777216 and hashlib.sha256(r).hexdigest()=='ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
assert r[0x8fef00:0x93f000]==b
u32=lambda a: struct.unpack_from('<I',b,a)[0]
f32=lambda a: struct.unpack_from('<f',b,a)[0]
f=lambda x: struct.unpack('<f',struct.pack('<f',x))[0]
counts={}; calls=0; literals=0; warnings=[]
for p in sorted(E.glob('actuator-pass*.txt'))+[E/'scaling-consumers-followup.txt']:
    text=p.read_text(); assert text.startswith('PASS: entire loaded program memory')
    assert 'FAILED:' not in text
    warnings += [dict(file=p.name,line=s) for s in text.splitlines() if 'NO EXISTING FUNCTION' in s]
    n=0
    for addr, raw, asm in re.findall(r'^([0-9a-f]{8}) ([0-9a-f]+) (.+)$',text,re.M):
        a=int(addr,16); data=bytes.fromhex(raw)
        assert b[a:a+len(data)]==data,(p.name,addr); n+=1
        if asm.startswith('call8 '):
            w=int.from_bytes(data,'little'); assert w&63==37
            imm=w>>6; imm=imm-(1<<18) if imm&(1<<17) else imm
            assert (a&~3)+4+4*imm==int(asm.split()[-1],16),(p.name,addr)
            calls+=1
        if asm.startswith('l32r '):
            assert data[0]&15==1
            target=((a+3)&~3)+(int.from_bytes(data[1:3],'little')-65536)*4
            assert target==int(asm.split(',')[-1],16),(p.name,addr)
            literals+=1
    counts[p.name]=n
assert u32(0x175f0)==0xee7c and u32(0x178a8)==0xee98
assert u32(0x178a8)+0x250==u32(0x175f0)+0x26c==0xf0e8
assert u32(0x175f0)+0x250==0xf0cc
assert u32(0x17618)+0x1dc==u32(0x17aa8)+0xdc==0x1424c # separate modeling destination
assert u32(0x171a4)+0x230==0x115a030
# Channel identity checks:
# Selector 0 write in FUN_0002bdec: s32i a3, a2, 0x230
assert b[0x2be09:0x2be0c] == bytes.fromhex('32628c')
# Selector 1 write in FUN_0002be40: or a3, a3, 1; s32i a3, a4, 0x230
assert b[0x2be66:0x2be69] == bytes.fromhex('503320') and b[0x2be6c:0x2be6f] == bytes.fromhex('32648c')
# String search confirmation: SVI2/VR12 literals are absent from firmware
assert not any(s in b for s in [b'SVI', b'svi', b'SVI2', b'svi2', b'VR12', b'VR13'])

addrs=[0x170ac,0x17124,0x1714c,0x171a4,0x17278,0x1727c,0x17280,0x17338,0x17320,0x175f0,0x175fc,0x17604,0x17614,0x17618,0x178a8,0x17aa8,0x180cc,0x180d0,0x180d4,0x180d8,0x180dc,0x180e0,0x180e4,0x18148]
# Finite in-range synthetic cases only: not an emulator or live voltage prediction.
def encode(v):
    v=f(v)
    return 0 if v>=f32(0x17278) else int(f(f(f(f32(0x17278)-v)*f32(0x1727c))+f32(0x17280)))
vectors=[dict(volts=v,vid=encode(v)) for v in [0.8,1.0,1.1,1.15,1.25,1.55]]
# Exact binary32 arithmetic yields 71 at 1.1, not ideal-real 72.
assert [x['vid'] for x in vectors]==[120,88,71,64,48,0]
result=dict(status='PASS',identities=[dict(path=str(p),size=len(x),sha256=hashlib.sha256(x).hexdigest()) for p,x in [(S,b),(R,r)]],rom_body_offset='0x8fef00',instruction_counts=counts,independent_call8_target_checks=calls,independent_l32r_target_checks=literals,warnings=warnings,rejected_semantic_entries=['actuator-pass7.txt:20758 is interior code, not a function entry; do not use decompile','actuator-pass7.txt:20b08 is interior code, not a function entry; do not use decompile'],literals=[dict(address=hex(a),raw=b[a:a+4].hex(),u32=hex(u32(a)),f32=f32(a)) for a in addrs],synthetic_f32_encoder_vectors=vectors,limits='Byte/target correspondence does not independently validate all Ghidra instruction semantics; no hardware/emulator test or CPU/SoC pad mapping')
with (E/(sys.argv[1] if len(sys.argv)>1 else 'actuator-verification.json')).open('x') as out: json.dump(result,out,indent=2); out.write('\n')
print(json.dumps(result,indent=2))
