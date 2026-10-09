#!/usr/bin/env python3
"""Independent byte/operand assertions for the explicitly bounded caller result."""
import hashlib,json,re,struct,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent
C=json.loads((P/'census.json').read_text()); V=json.loads((P/'coverage.json').read_text())
checks=[]
def check(label,condition):
    checks.append(dict(check=label,passed=bool(condition)))
    assert condition,label
R={r.get('ui',r['ffs_guid']):r for r in C['records']}
def body(name):return (P/(R[name]['stem']+'.bin')).read_bytes()
def raw(name,rva):
    for s in R[name]['sections']:
        if s['rva']<=rva<s['rva']+s['size']:return rva-s['rva']+s['raw']
    raise ValueError(hex(rva))
def exact(name,rva,h):
    b=body(name); off=raw(name,rva); expected=bytes.fromhex(h)
    check(name+' '+hex(rva)+' '+h,b[off:off+len(expected)]==expected)
check('ROM hash and size',len(Path(C['input']).read_bytes())==16777216 and hashlib.sha256(Path(C['input']).read_bytes()).hexdigest()==C['sha256'])
prior=json.loads(Path('evidence/firmware-audit/20260919-inv-buffer-lifetime/census.json').read_text())
check('233 exact predecessor identities',len(C['records'])==233 and len({x['sha256'] for x in C['records']})==233 and sorted(x['sha256'] for x in C['records'])==sorted(x['sha256'] for x in prior['records']))
check('42 HOB GUID and exactly two NVTB bodies',len(V['modules'])==42 and {n for n,r in R.items() if r['nvtb']}=={'AmdFabricAriPei','AmdCcxVhAriDxe'})
for r in C['records']:check('body digest '+r['stem'],hashlib.sha256((P/(r['stem']+'.bin')).read_bytes()).hexdigest()==r['sha256'])
f='AmdFabricAriPei';d='AmdCcxVhAriDxe'
for n,a,h in [(f,0x1eb0,'68ff100000'),(f,0x1ebd,'e87afeffff'),(f,0x1f8b,'6804110000'),(f,0x1f94,'e8a3fdffff'),(f,0x1d4d,'bb4e565442'),(f,0x1dfc,'813e24494e56'),(d,0x5adc,'440fb7e1'),(d,0x5ae9,'be4e565442'),(d,0x5bbe,'813b24494e56'),(d,0x5ca0,'b900100000'),(d,0x5ca5,'e81afeffff'),(d,0x5cec,'b901100000'),(d,0x5cf1,'e8cefdffff'),(d,0x5c32,'66443923'),(d,0x5c3b,'6644392b'),(d,0x5cbc,'b9291001c0'),(d,0x5cc3,'49c1e00e'),(d,0x5cd1,'4181e000400000'),(d,0x5ce5,'0f30'),(d,0x5d05,'b9231001c0'),(d,0x5d10,'49c1e02d'),(d,0x5d17,'48ba0000000000200000'),(d,0x5d34,'0f30'),(d,0x3cbf,'4883c018'),(d,0x3ccd,'813848454150'),(d,0x3cda,'0fb6400d'),(d,0x3d00,'4883c210'),(d,0x3d09,'4883c120'),(d,0x3d0d,'e8baf8ffff'),(d,0x7a09,'b9feffffff'),(d,0xaef,'8d4a02'),(d,0xaf2,'e81d4f0000'),(d,0x5a73,'ff5708')]:exact(n,a,h)
check('CCX IDS handler table',struct.unpack_from('<QQQ',body(d),0x7f38)==(2,0x5c68,0xffffffff))
# Recover each argument from exact machine bytes, not substring matches.
requests=[]
for n,start,call in [(f,0x1eb0,0x1ebd),(f,0x1f8b,0x1f94),(d,0x5ca0,0x5ca5),(d,0x5cec,0x5cf1)]:
    ins=json.loads((P/(R[n]['stem']+'.instructions.json')).read_text())
    seq=[x for x in ins if start<=x['rva']<=call]
    token=struct.unpack_from('<I',body(n),raw(n,start)+1)[0]&0xffff
    # All external direct entry edges into the slice after the argument load are forbidden.
    entering=[]
    for x in ins:
        if x['mnemonic'].startswith(('j','call')) and re.fullmatch(r'0x[0-9a-f]+',x['operands']):
            dest=int(x['operands'],16)
            if start<dest<=call and not start<=x['rva']<call:entering.append(x)
    check('closed direct argument slice '+n+' '+hex(call),not entering)
    if n==d:check('CX constant immediately precedes call '+hex(call),len(seq)==2)
    else:
        allowed={'lea','mov'}
        check('stack argument unchanged '+hex(call),all(x['mnemonic'] in allowed and not re.search(r'\[(?:e|r)sp(?:\+0x0)?\],',x['operands']) for x in seq[1:-1]))
    requests.append(dict(module=n,call_rva=call,token=token,instructions=seq))
check('no target among all four direct requests',not {x['token'] for x in requests}&{0x1364,0x1363,0x11ed,0x1204,0x1331,0x1373,0x1374})
for r in V['readers']:
    check('all raw E8/E9 entries agree '+r['module'],len(r['raw_rel32_external_edges'])==2 and all(x['decoded_boundary'] and x['target']==r['start'] for x in r['raw_rel32_external_edges']))
    check('no exact stored reader pointer/materialization '+r['module'],not r['address_materializations'] and not any(r['stored_pointers'].values()))
# All target immediates are adjacent serializer ID stores, not requests.
immediates=[x for x in V['target_candidates'] if x['category']=='immediate-candidate']
check('49 serializer IDs',len(immediates)==49)
for x in immediates:
    n=x['module'];a=x['rva'];off=raw(n,a);b=body(n)
    check('serializer mov edx; mov eax,[ebp-8]; mov [eax],dx '+n+' '+hex(a),b[off]==0xba and b[off+5:off+11]==bytes.fromhex('8b45f8668910'))
# Independent LLVM decode of CCX; compare every printed byte against image.
text=(P/'ccx-independent-llvm.txt').read_text(); count=0
for line in text.splitlines():
    m=re.match(r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2} )+)\s*(.*)$',line)
    if not m:continue
    a=int(m[1],16);bs=bytes.fromhex(m[2]);check('LLVM bytes '+hex(a),body(d)[raw(d,a):raw(d,a)+len(bs)]==bs);count+=1
check('LLVM decoded reader and both MSR edges',count>100 and '5ca5:' in text and '5cf1:' in text and 'wrmsr' in text)
# Displacement-vs-immediate controls use the real disassembler, not a regex fixture alone.
fixture=bytes.fromhex('8b8364130000 b964130000 66b96413 b960130000 83c104 68feffffff 6afe')
(P/'operand-controls.code').write_bytes(fixture)
p=subprocess.run(['objdump','-D','-z','--insn-width=16','-b','binary','-m','i386','-M','intel',str(P/'operand-controls.code')],capture_output=True,text=True,check=True)
(P/'operand-controls.txt').write_text(p.stdout)
check('actual displacement control', 'DWORD PTR [ebx+0x1364]' in p.stdout)
check('actual immediate control', 'ecx,0x1364' in p.stdout and 'cx,0x1364' in p.stdout)
check('transformed token arithmetic control',((0x1360+4)&0xffff)==0x1364)
check('imm8 sign-extension control',struct.unpack('b',bytes.fromhex('fe'))[0]&0xffffffff==0xfffffffe)
# Byte-backed MSR formulas, synthetic values only; not hardware writes.
for v in [0,1,2,3,0x1364,0xffffffffffffffff]:
    old=0x123456789abcdef0
    for shift in [14,45]:
        mask=1<<shift; result=old^(((v<<shift)^old)&mask)
        check('MSR masked synthetic '+str(shift)+' '+hex(v),(result&~mask)==(old&~mask) and bool(result&mask)==bool(v&1))
result=dict(passed=len(checks),failed=0,checks=checks,requests=requests,llvm_byte_rows=count,limits='No execution of firmware; fixtures are host-only. Arbitrary computed indirect destinations, runtime code and GUIDs remain unresolved.')
(P/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS',len(checks),'checks; LLVM byte rows',count,'direct requests',[(x['module'],hex(x['call_rva']),hex(x['token'])) for x in requests])
