"""Extend the same roles and re-run literal baseline/modified/rollback evidence."""
from pathlib import Path
import difflib,hashlib,json,os,re,subprocess,sys,time,zipfile
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent;CAND=ROOT/'candidates/waveshare-adapter-safe-v001'
run='full-'+str(time.time_ns())
owned=[str(p.relative_to(ROOT)) for p in sorted((ROOT/'scripts').glob('*waveshare*.py'))]
owned += [str(p.relative_to(ROOT)) for p in sorted((ROOT/'tests').glob('test_waveshare*.py'))]
owned += ['docs/waveshare-host-inspection.md']
owned += [str(p.relative_to(ROOT)) for p in sorted(CAND.rglob('*')) if p.is_file() and not any(x in p.relative_to(CAND).parts for x in ['lib','node_modules','__pycache__','.git'])]
owned += [str(p.relative_to(ROOT)) for p in [OUT/'guide/CONNECT.html',OUT/'guide/hardware-facts.json',OUT/'guide/candidate-manifest.json']]
assert len(set(owned))==len(owned)
mod=OUT/'MODIFIED_FILE.zip';diff=OUT/'DIFF_FILE.patch';ver=OUT/'VERIFICATION.txt';rollback=OUT/'ROLLBACK.sh'
def pack(path,base,names):
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
  for name in sorted(names):
   info=zipfile.ZipInfo(name,(2026,9,30,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=(0o100755 if name.startswith('scripts/') else 0o100644)<<16;z.writestr(info,(base/name).read_bytes())
def delta(a,b,left,right):
 return ''.join(line if line.endswith('\n') else line+'\n\\ No newline at end of file\n' for line in difflib.unified_diff(a.splitlines(keepends=True),b.splitlines(keepends=True),fromfile=left,tofile=right))
def execute(cmd,cwd=ROOT,**extra):
 r=subprocess.run(cmd,cwd=cwd,capture_output=True,text=True,check=False,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
 row={'command':cmd,'cwd':str(cwd),'stdout':r.stdout,'stderr':r.stderr,'exit_status':r.returncode};row.update(extra);ledger.append(row);return r
ledger=[];pack(mod,ROOT,owned);diff.write_text(''.join(delta('',(ROOT/n).read_bytes().decode(),'/dev/null','b/'+n) for n in sorted(owned)))
reconstructed=OUT/(run+'-patch');reconstructed.mkdir();r=execute(['patch','--binary','-p1','-i',str(diff)],reconstructed,role='LATEST_PATCH');assert r.returncode==0
for n in owned:assert (reconstructed/n).read_bytes()==(ROOT/n).read_bytes(),n
reconstructed_zip=OUT/(run+'-reconstructed.zip');pack(reconstructed_zip,reconstructed,owned);assert reconstructed_zip.read_bytes()==mod.read_bytes()
restore=OUT/(run+'-rollback-copy.zip');restore.write_bytes(mod.read_bytes());r=execute([str(rollback),str(restore)],role='LATEST_ROLLBACK_SCRIPT');assert r.returncode==0 and restore.read_bytes()==(OUT/'BASELINE.zip').read_bytes()
fixture=OUT/'cdc-baseline-fixture.json';cmd=[sys.executable,'scripts/waveshare_probe.py','--fixture',str(fixture)]
for role,archive in [('BASELINE',OUT/'BASELINE.zip'),('MODIFIED',mod),('ROLLBACK',restore)]:
 directory=OUT/(run+'-'+role.lower());directory.mkdir()
 with zipfile.ZipFile(archive) as z:z.extractall(directory)
 r=execute(cmd,directory,role='LATEST_'+role,input=str(fixture));assert r.returncode==(0 if role=='MODIFIED' else 2)
with zipfile.ZipFile(OUT/'firmware-source-pristine.zip') as z:old={n:z.read(n) for n in z.namelist()}
current=[str(p.relative_to(CAND)) for p in sorted(CAND.rglob('*')) if p.is_file() and not any(x in p.relative_to(CAND).parts for x in ['lib','node_modules','__pycache__','.git'])]
fwpatch=OUT/'firmware-baseline-to-modified.patch';fwpatch.write_text(''.join(delta(old.get(n,b'').decode(),(CAND/n).read_bytes().decode() if n in current else '', 'a/'+n if n in old else '/dev/null','b/'+n if n in current else '/dev/null') for n in sorted(set(old)|set(current)) if old.get(n,b'')!=((CAND/n).read_bytes() if n in current else b'')))
fwreconstructed=OUT/(run+'-fw-patch');fwreconstructed.mkdir()
with zipfile.ZipFile(OUT/'firmware-source-pristine.zip') as z:z.extractall(fwreconstructed)
r=execute(['patch','--binary','-p1','-i',str(fwpatch)],fwreconstructed,role='LATEST_FIRMWARE_DELTA');assert r.returncode==0
for n in current:assert (fwreconstructed/n).read_bytes()==(CAND/n).read_bytes(),n
fwzip=OUT/'firmware-source-modified.zip';pack(fwzip,CAND,current);fwrestore=OUT/(run+'-fw-rollback.zip');fwrestore.write_bytes(fwzip.read_bytes());r=execute([str(rollback),str(fwrestore),'--firmware'],role='LATEST_FIRMWARE_ROLLBACK');assert r.returncode==0 and fwrestore.read_bytes()==(OUT/'firmware-source-pristine.zip').read_bytes()
restored=OUT/(run+'-fw-restored');restored.mkdir()
with zipfile.ZipFile(fwrestore) as z:z.extractall(restored)
# Extract actual callbacks from all three source states and run matching input.
pattern=r'extern "C" uint16_t tud_hid_get_report_cb\(.*?(?=\nextern "C" bool tud_audio_set_itf_cb)'
template=(OUT/'host-tests/callback-rollback.cpp').read_text();start=template.index('extern "C" uint16_t tud_hid_get_report_cb');end=template.index('\nint main()',start)
for role,text in [('BASELINE',old['src/bridge/bridge_main.cpp'].decode()),('MODIFIED',(CAND/'src/bridge/bridge_main.cpp').read_text()),('ROLLBACK',(restored/'src/bridge/bridge_main.cpp').read_text())]:
 callback=re.search(pattern,text,re.S)[0];src=OUT/'host-tests'/(run+'-'+role+'.cpp');src.write_text(template[:start]+callback+template[end:]);exe=src.with_suffix('');r=execute(['g++','-std=c++20','-I',str(CAND/'src/bridge'),str(src),'-o',str(exe)],role='COMPILE_CALLBACK_'+role);assert r.returncode==0
 r=execute([str(exe)],role='LATEST_CALLBACK_'+role,input='report0x20 cached64 requested10 buffer64 sentinel0x55');assert r.returncode==0
 assert ('returned=10 bytes_overwritten_after_request=0' if role=='MODIFIED' else 'returned=63 bytes_overwritten_after_request=53') in r.stdout
assert all((Path('/home/OWNER/pico-bc250')/n).read_bytes()==b for n,b in old.items());pack(mod,ROOT,owned);assert mod.read_bytes()==reconstructed_zip.read_bytes()
record=json.loads(ver.read_text());record['commands'].extend(ledger)
record['latest_run']=run;record['original_pico_source_unchanged']=True;record['no_firmware_or_board_control_writes']=True;record['image_not_final']=True
record['remaining']=['physical GPIO/voltage/connector acceptance','UART/BIOS passive diagnostics','all device/AMD input/audio/feedback/runtime acceptance','HA/Decky actual install and supply confirmation','final combined-image readiness; no intermediate upload','PSP bypass excluded']
record['latest_offline_modules']=['WiFi async','HTTP status Bearer token, read-only','MQTT telemetry only with PS observation','Linux hwmon metrics+verified BC250 heartbeat','fresh state-gated power-on host helper','Decky frontend typechecked/build, backend freshness filtering','strict UF2 mixed-E10 marker parser','CAD interactive HTML desktop/mobile QA']
for tag,a,b in [('LATEST_HOST_REGRESSION','host-regression.stdout','host-regression.stderr'),('LATEST_SCOPED_GATE','final-expanded-procoder.stdout','final-expanded-procoder.stderr'),('LATEST_DECKY_TYPES','decky-typecheck-final.stdout','decky-typecheck-final.stderr'),('LATEST_DECKY_BUILD','decky-build-final.stdout','decky-build-final.stderr'),('LATEST_FIRMWARE_BUILD','ps-build.stdout','ps-build.stderr'),('LATEST_CANDIDATE_TESTS','candidate-tests.stdout','candidate-tests.stderr')]:record['commands'].append({'role':tag,'stdout':(OUT/a).read_text(),'stderr':(OUT/b).read_text(),'exit_status':0})
record['browser_qa']=json.loads((OUT/'guide/browser-qa.json').read_text());record['uf2_structural']=json.loads((OUT/'uf2-validation.json').read_text());record['candidate_manifest']=json.loads((OUT/'guide/candidate-manifest.json').read_text())
for p in [mod,diff,rollback,fwzip,fwrestore,fwpatch,*[ROOT/n for n in owned]]:record['hashes'][str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
ver.write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n')
for p in [mod,diff,ver,rollback]:
 data=p.read_bytes();assert data
 if p==mod:
  with zipfile.ZipFile(p) as z:assert z.testzip() is None
 if p==ver:json.loads(data)
 print('reopened',p)
print('Literal host BASELINE/MODIFIED/ROLLBACK exits2/0/2; actual firmware callback63/53 ->10/0 ->63/53; all archive hashes/byte reconstructions verified')
