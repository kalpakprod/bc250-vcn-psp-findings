__file__='/home/OWNER/orca/projects/bc250/candidates/clv-native-menu-bridge-v001/build_integration.py'
"""Exact CLV navigation + canonical voltage-form predicates; no setpoint changes."""
from pathlib import Path
import importlib.util, json, lzma, struct, subprocess, uuid, hashlib
R=Path(__file__).resolve().parents[2];D=Path(__file__).resolve().parent;W=D/'dxe-build'
S=importlib.util.spec_from_file_location('fv',R/'scripts/build_s3_drivers.py');M=importlib.util.module_from_spec(S);S.loader.exec_module(M)
E=R/'import/from-windows/Users/kukuruza/tmp_bc250/worktrees/edk2-bc250-capture/BaseTools/Source/C/bin'
B=W/'Build/ClvMenuPkg/RELEASE_GCCNOLTO/X64';EFI=B/'ClvNativeMenu.efi';DEP=B/'ClvMenuPkg/ClvMenu/OUTPUT/ClvNativeMenu.depex'
O=Path('/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260923-menu-reproduction');O.mkdir(exist_ok=True);ledger=[]
def run(cmd):
 p=subprocess.run([str(x) for x in cmd],capture_output=True,text=True);ledger.append({'cmd':[str(x) for x in cmd],'stdout':p.stdout,'stderr':p.stderr,'exit':p.returncode});assert p.returncode==0,ledger[-1]
run([E/'GenSec','-s','EFI_SECTION_PE32','-o',O/'menu.pe32',EFI]);run([E/'GenSec','-s','EFI_SECTION_DXE_DEPEX','-o',O/'menu.depex',DEP])
run([E/'GenFfs','-t','EFI_FV_FILETYPE_DRIVER','-g','63c4aed9-3e29-4ddf-877b-34eceadc7a85','-s','-o',O/'ClvNativeMenu.ffs','-i',O/'menu.depex','-i',O/'menu.pe32'])
base=(R/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin').read_bytes();assert M.sha256(base)=='ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
x=M.decompress_inner(base);inv,flen=M.walk_inner_fv(x['fv']);fv=bytearray(x['fv']);setup=next(f for f in inv if f['guid'].startswith('899407D7'));off=setup['off'];before=bytes(fv[off:off+setup['size']])
# Reuse the byte-verified 80-byte replacement of a one-incoming-reference stub.
changes=json.loads((R/'candidates/s3-drivers/S3B-verdict.json').read_text())['changes']
M.apply_unhide_inner(fv,inv,changes)
ref=off+0x12079;assert fv[ref:ref+2]==b'\x0f\x21';assert fv[ref+17:ref+33]==uuid.UUID('b04535e3-3004-4946-9eb7-149428983053').bytes_le
fv[ref+13:ref+15]=struct.pack('<H',1);fv[ref+17:ref+33]=uuid.UUID('63c4aed9-3e29-4ddf-877b-34eceadc7a85').bytes_le
# Preserve all existing labels except the navigation entry's unique string.
needle='GFX Configuration'.encode('utf-16-le');assert before.count(needle)==1;k=before.index(needle);fv[off+k:off+k+len(needle)]='CLV Tuning'.ljust(len(needle)//2).encode('utf-16-le')
pe=(R/'evidence/firmware-audit/20260919-inv-token-consumers/Setup-10cc728ae3f8.bin').read_bytes();peoff=before.find(pe);assert peoff==124
for rel,old in [(0x2323,'4706ec000100'),(0x2456,'470679000000')]:
 p=off+peoff+0xfb58+rel;assert fv[p:p+6]==bytes.fromhex(old);fv[p:p+6]=bytes.fromhex('470247021602') # FALSE FALSE OR -> FALSE; length preserved
# Only two noncanonical FALSE records: outer grayout and MEMIO suppression.
ffs=(O/'ClvNativeMenu.ffs').read_bytes();pos=(max(f['off']+f['size'] for f in inv)+7)&~7;assert len(ffs)<=flen-pos;assert all(v==255 for v in fv[pos:]);fv[pos:pos+len(ffs)]=ffs
newinv,_=M.walk_inner_fv(fv);assert len(newinv)==len(inv)+1
for f in inv:
 if f['guid']!=setup['guid']:assert bytes(fv[f['off']:f['off']+f['size']])==x['fv'][f['off']:f['off']+f['size']]
fvim=(len(fv)+4).to_bytes(3,'little')+b'\x17'+fv;stream=x['raw']+bytes(x['raw_pad'])+fvim;comp=lzma.compress(stream,format=lzma.FORMAT_ALONE,filters=M.LZMA_FILTERS);gh=bytearray(x['guided_hdr']);gh[:3]=(len(gh)+len(comp)).to_bytes(3,'little');csz=24+len(gh)+len(comp);cpos=x['cpos'];end=M.OUTER_FV+M.OUTER_LEN;assert all(v==255 for v in base[cpos+x['csz']:end]);assert cpos+csz<=end
h=bytearray(base[cpos:cpos+24]);h[20:23]=csz.to_bytes(3,'little');M.ffs_header_checksum(h);out=bytearray(base);out[cpos:end]=h+gh+comp+bytes([255])*(end-cpos-csz)
assert out[:M.OUTER_FV]==base[:M.OUTER_FV] and out[end:]==base[end:];assert M.decompress_inner(out)['fv']==fv
rom=O/'BC250_5.00_clv_MENU_ONLY_EXPERIMENTAL.bin';assert not rom.exists();rom.write_bytes(out)
result={'rom':str(rom),'sha256':M.sha256(out),'source_sha256':M.sha256(base),'native_FFS':len(inv),'result_FFS':len(newinv),'new_driver_bytes':len(ffs),'inner_FV_size_unchanged':flen,'NVRAM_PSP_APCB_unchanged':True,'voltage_change':'only canonical FALSE expressions; NO SETPOINT/SoC CONTROL','runtime':'UNRUN','commands':ledger}
(O/'build-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='commands'},indent=2))
