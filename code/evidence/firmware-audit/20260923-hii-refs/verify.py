import hashlib
import importlib.util
import json
import struct
import uuid
from pathlib import Path

R=Path(__file__).resolve().parents[3]
O=Path(__file__).resolve().parent

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

fv=module('fv',R/'scripts/build_s3_drivers.py')
ifr=module('ifr',R/'import/from-windows/Users/kukuruza/bc250-bios/tools/uefi/e1_ifr_dump.py')
rom=(R/'candidates/clv-native-menu-bridge-v001/integration/BC250_5.00_clv_MENU_ONLY_EXPERIMENTAL.bin').read_bytes()
assert hashlib.sha256(rom).hexdigest()=='476076f280ca6385024db1bf643e042629153afff8bab2f9a52cc61c221e411e'
x=fv.decompress_inner(rom)['fv']; files,_=fv.walk_inner_fv(x)
bridge='63c4aed9-3e29-4ddf-877b-34eceadc7a85'
cbs='b04535e3-3004-4946-9eb7-149428983053'
setup='7b59104a-c00d-4158-87ff-f04d6396a915'
forms={}; refs=[]; predicates=[]
for f in files:
    b=x[f['off']:f['off']+f['size']]
    if not any(uuid.UUID(g).bytes_le in b for g in [bridge,cbs,setup]):
        continue
    packages=ifr.find_packages(b)
    strings={}
    for off,typ,size in packages:
        if typ==4: strings.update({k:v.rstrip('\0') for k,v in ifr.parse_sibt(b[off:off+size])[1]})
    for off,typ,size in packages:
        if typ!=2: continue
        pos=off+4; guid=None; form=None; stack=[]
        while pos<off+size:
            op=b[pos]; length=b[pos+1]&127; scope=b[pos+1]>>7
            assert length>=2 and pos+length<=off+size
            raw=b[pos:pos+length]
            if op==0x0e:guid=str(uuid.UUID(bytes_le=raw[2:18]))
            if op==1:
                form,sid=struct.unpack_from('<HH',raw,2)
                forms[(guid,form)]=strings.get(sid,'')
            if op==0x0f and length==33:
                refs.append({'source_guid':guid,'source_form':form,'target_guid':str(uuid.UUID(bytes_le=raw[17:33])),'target_form':struct.unpack_from('<H',raw,13)[0]})
            if f['guid'].startswith('899407D7') and pos in (0x11ef7,0x1202a):
                assert b[pos:pos+6]==bytes.fromhex('470247021602')
                predicates.append({'ffs_offset':hex(pos),'form':hex(form),'scope':[hex(i) for i in stack],'expression':'FALSE FALSE OR = FALSE'})
            if op==0x29:
                assert stack
                stack.pop()
            elif scope:stack.append(op)
            pos+=length
        assert not stack and pos==off+size
links=[q for q in refs if q['source_guid']==bridge]
expected={(cbs,0x7007),(cbs,0x7008),(cbs,0x7009),(cbs,0x7005),(setup,0x28ea)}
assert len(links)==5 and {(q['target_guid'],q['target_form']) for q in links}==expected
for q in links:
    key=(q['target_guid'],q['target_form']);assert key in forms
    q['target_title']=forms[key]
assert any(q['source_guid']==setup and q['target_guid']==bridge and q['target_form']==1 for q in refs)
assert len(predicates)==2
result={'status':'PASS_BINARY_TARGET_RESOLUTION','candidate_sha256':hashlib.sha256(rom).hexdigest(),'links':links,'setup_entry_present':True,'predicates':predicates,'limits':['Static resolution only','Original malformed predicate interpretation by AMI remains unknown','FALSE replacement is not proof of identical UI behavior','No SoC or clock actuation proof']}
(O/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
