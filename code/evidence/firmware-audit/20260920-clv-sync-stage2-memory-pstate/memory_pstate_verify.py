#!/usr/bin/env python3
"""Narrow exact-clv Memory P-state IFR/gate/serializer check."""
import hashlib, importlib.util, json, struct, sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ROM = ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin"
MOD = ROOT / "evidence/firmware-audit/20260919-inv-token-consumers/CbsSetupDxe-7ff717d51c9a.bin"
MOD_INS = ROOT / "evidence/firmware-audit/20260919-inv-token-consumers/CbsSetupDxe-7ff717d51c9a.instructions.json"
BASE_INS = ROOT / "evidence/firmware-audit/20260919-inv-token-consumers/CbsBasePei-6ff112922ad8.instructions.json"
PARSER = ROOT / "import/from-windows/Users/kukuruza/bc250-bios/tools/uefi/e1_ifr_dump.py"
MENU_RESULT = ROOT / "evidence/firmware-audit/20260920-df-init-route/menu-result.json"


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda: f.read(1<<20), b''): h.update(c)
    return h.hexdigest()

def check(cond, label, details=None):
    checks.append({'label': label, 'status': 'PASS' if cond else 'FAIL', 'details': details})
    return cond

def load_ins(p): return {int(x['rva']): x for x in json.loads(p.read_text())}

checks=[]
check(sha(ROM)=='ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8','clv-rom-hash',sha(ROM))
check(sha(MOD)=='7ff717d51c9a447c6954c63b633cf836f1e4396c2b01f4bf590268a60ac1d0d8','CbsSetupDxe-hash',sha(MOD))
check(sha(PARSER)=='480aa6fc70ed12e8d1dbec2c32dfb45ddadcd7c2f9075ceac6dad6486bc50ebb','existing-ifr-parser-hash',sha(PARSER))
rom=ROM.read_bytes(); body=0x4cf
check(len(rom)==0x1000000,'clv-size',len(rom))
raw=rom[body+0x36d]
check(raw==0xff,'current-MemoryPstate-byte',{'absolute':hex(body+0x36d),'raw':hex(raw),'meaning':'persisted Auto encoding'})

spec=importlib.util.spec_from_file_location('ifr',PARSER); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
b=MOD.read_bytes(); packages=mod.find_packages(b); so,_,sn=next(x for x in packages if x[1]==4); fo,_,fn=next(x for x in packages if x[1]==2)
strings=dict(mod.parse_sibt(b[so:so+sn])[1]); strings={k:v.rstrip('\0') for k,v in strings.items()}
forms={}; refs=[]; target=None; stack=[]; form=None; pos=fo+4
while pos<fo+fn:
    op=b[pos]; ln=b[pos+1]&0x7f; scope=b[pos+1]>>7; rawop=b[pos:pos+ln]; payload=rawop[2:]
    check(ln>=2 and pos+ln<=fo+fn,'ifr-opcode-boundary',{'pos':hex(pos),'len':ln})
    if op==1:
        form,title=struct.unpack_from('<HH',payload); forms[form]=strings.get(title,str(title))
    conditions=[{'op':hex(x['op']),'pos':hex(x['pos'])} for x in stack if x['op'] in (0x0a,0x19,0x1e)]
    if op in (5,6,7):
        prompt,helpid,qid,vid,offset,flags=struct.unpack_from('<HHHHHB',payload)
        cur={'qid':hex(qid),'form':hex(form),'label':strings.get(prompt,''),'varstore':hex(vid),'offset':hex(offset),'flags':hex(flags),'conditions':conditions,'options':[],'module_offset':hex(pos)}
        if vid==0x5000 and offset==0x36d: target=cur
        if op==7:
            width=1<<(payload[11]&3); cur['bounds']=[int.from_bytes(payload[12+i*width:12+(i+1)*width],'little') for i in range(3)]
    if op==9 and target is not None and form==0x7032:
        sid,fl,typ=struct.unpack_from('<HBB',payload); width={0:1,1:2,2:4,3:8,4:1}.get(typ)
        if width: target['options'].append({'label':strings.get(sid,''),'value':int.from_bytes(payload[4:4+width],'little'),'default':bool(fl&0x10)})
    if op==15 and len(payload)>=13:
        prompt,_,qid,vid,offset,flags,target_form=struct.unpack_from('<HHHHHBH',payload)
        refs.append({'source':form,'target':target_form,'label':strings.get(prompt,''),'conditions':conditions,'module_offset':hex(pos)})
    if op==0x29:
        if stack: stack.pop()
        if form==0x7032 and target is not None and not stack: pass
    elif scope: stack.append({'op':op,'pos':pos})
    pos+=ln
check(target is not None,'MemoryPstate-question-present',target)
if target:
    check(target['qid']=='0x25e','MemoryPstate-qid',target['qid'])
    check(target['form']=='0x7032','MemoryPstate-form',target['form'])
    check(target['flags']=='0x10','MemoryPstate-flags-reset-only',target['flags'])
    check(target['conditions']==[],'MemoryPstate-no-conditional-scope',target['conditions'])
    check(target['options']==[{'label':'Auto','value':255,'default':True},{'label':'Enabled','value':1,'default':False},{'label':'Disabled','value':0,'default':False}],'MemoryPstate-options',target['options'])
# Exact unconditional navigation chain from existing exact menu audit refs.
refset={(x['source'],x['target']):x for x in refs if not x['conditions']}
path=[0x7000,0x7008,0x702e,0x7030,0x7032]
for a,z in zip(path,path[1:]): check((a,z) in refset,f'unconditional-ref:{a:#x}->{z:#x}',refset.get((a,z)))

base=load_ins(BASE_INS)
# Serializer: record header 0x123c is opened, then Setup+0x36d value is stored
# into its current destination before the cursor advances to header 0x123d.
for rva,expected in {0xa7c1:'ba3c120000',0xa7e1:'8a826d030000',0xa7e7:'884103'}.items():
    d=base.get(rva); check(d is not None and d['bytes']==expected,f'CbsBasePei-serializer:{rva:#x}',{'observed':d,'expected':expected})
# Default helper and serialized record are static only; no final consumer claim.
result={'status':'PASS' if all(x['status']=='PASS' for x in checks) else 'FAIL','checks':{'passed':sum(x['status']=='PASS' for x in checks),'failed':sum(x['status']=='FAIL' for x in checks),'total':len(checks)},'evidence_class':['observed-bytes','static-analysis'],'inputs':{'rom':str(ROM),'rom_sha256':sha(ROM),'module':str(MOD),'module_sha256':sha(MOD),'parser':str(PARSER),'parser_sha256':sha(PARSER)},'memory_pstate':{'body_offset':'0x36d','absolute_offset':hex(body+0x36d),'current_raw':hex(raw),'question':target,'unconditional_path':[hex(x) for x in path]},'serializer':{'module':'CbsBasePei','record_id':'0x123c','source':'AmdSetup+0x36d','bytes_checked':{hex(k):v for k,v in [(0xa7c1,'ba3c120000'),(0xa7e1,'8a826d030000'),(0xa7e7,'884103')]}},'limitations':['Help text is UI guidance, not hardware constraint.','Serializer reaches an INV record; downstream consumer, training behavior, units, and actual FCLK/UCLK/MCLK application remain unresolved.','No browser execution, NVRAM save/reset, firmware execution, hardware action, or settings change.'],'checks_detail':checks}
(OUT/'memory-pstate-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':result['status'],'checks':result['checks'],'question':target,'serializer_record':'0x123c','current_raw':hex(raw),'unconditional_path':[hex(x) for x in path]},sort_keys=True))
sys.exit(0 if result['status']=='PASS' else 1)
