#!/usr/bin/env python3
"""Byte-backed exact ABL1 memory-speed function match."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
PAY=ROOT/'evidence/firmware-audit/20260920-clv-sync-stage2-abl-memory/ABL1-clv-decompressed.bin'
SRC=ROOT/'import/from-windows/Users/kukuruza/tmp_bc250/recon/lorek123_psp/ABL1_decompiled.c'
DIS=OUT/'abl1-thumb-95fc-9870.txt';ERR=OUT/'abl1-disasm.stderr';SNIP=OUT/'ABL1-FUN-000096fc-snippet.c'
EXPECTED={PAY:'af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a',SRC:'9501f2ed3abd96ac54cc317c26ae64d068f94a1a0d572d3c886c7877e4bb8f1b',DIS:'dc4db013c5f495151cb8e449a1e4d9754b4b9bdada99a8a41088e05725289edb',ERR:'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',SNIP:'78f0353182fe246ddc0b0b4bb9d3e91ecfa339b27d93f54bcf3f048bfa7366ec'}
def sha(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1<<20),b''):h.update(c)
 return h.hexdigest()
def ck(c,l,d=None):checks.append({'label':l,'status':'PASS' if c else 'FAIL','details':d});return c
checks=[]
for p,w in EXPECTED.items():ck(sha(p)==w,'hash:'+str(p),{'observed':sha(p),'expected':w})
b=PAY.read_bytes();
# Exact ARM/Thumb code bytes: prologue + context/array fields + min/output writes.
for r,expected in {0x95fc:'2de9f04f',0x9600:'0468',0x96f0:'d4f8c403',0x96f4:'90f87400',0x9672:'008c',0x9674:'c1f87802',0x971a:'d2f87822',0x973e:'c4f8bc62',0x9758:'0684',0x975a:'95f84b00',0x9846:'5fb0',0x9848:'0020',0x984a:'bde8f08f'}.items():
 ck(b[r:r+len(bytes.fromhex(expected))].hex()==expected,'exact-ABL1-byte:'+hex(r),{'observed':b[r:r+len(bytes.fromhex(expected))].hex(),'expected':expected})
s=SRC.read_text(errors='replace'); snippet=SNIP.read_text(errors='replace'); distext=DIS.read_text(errors='replace')
for needle in ['FUN_000096fc','Synchronize_Mem_Speed_for_each_c','iVar6 + 0x3c4','iVar6 + 0x278','param_1[3] + 0x20','iVar6 + 700','uVar8 = 0x7d1']:
 ck(needle in s or needle in snippet,'historical-source-structure:'+needle)
ck('e92d 4ff0' in distext,'thumb-disassembly-prologue')
ck('95fc:' in distext and '973e:' in distext and '9758:' in distext,'thumb-disassembly-key-windows')
result={'status':'PASS' if all(x['status']=='PASS' for x in checks) else 'FAIL','checks':{'passed':sum(x['status']=='PASS' for x in checks),'failed':sum(x['status']=='FAIL' for x in checks),'total':len(checks)},'isa_and_base':{'payload_sha256':sha(PAY),'arm_thumb':'Thumb-2 function at exact payload offset 0x95FC; Thumb prologue e92d4ff0','historical_source_function':'FUN_000096fc at source label 0x96FC; exact control structure matches at payload 0x95FC (address delta -0x100, treated as observed alignment not assumed base)'},'matched_dataflow':{'context':'r4 = [r0] at 0x9600','channel_count':'[r4+0x3c4] then byte +0x74 at 0x96F0/96F4','per_channel_speed_input':'ldrh [r0+0x20] at 0x9672; r0=[r5+0xc]','speed_table_store':'str.w to [r1+0x278] at 0x9674','min_reduction':'reads table [r4 + indexed*0x40 + 0x278] and stores min to [r4+0x2bc] at 0x973E','writeback':'strh min to [r0+0x20] at 0x9758; loop count [r5+0x4b] at 0x975A'},'conclusion':'Exact clv ABL1 contains a Thumb-2 memory-speed synchronization function structurally matching historical FUN_000096fc. It collects per-channel memory-speed values, reduces a table to a minimum, and writes the selected speed back through a runtime structure at +0x20. This is a concrete memory-training/policy structure match, but no edge from AmdSetup+0x316/INV 0x11ED or UCLK/FCLK ratio semantics is shown.', 'limitations':['Historical source text remains provenance lead; no source-to-binary hash identity.','The exact input population of the ABL1 context and physical MHz conversion remain unresolved.','No firmware execution, training, hardware, voltage, or settings action.'],'checks_detail':checks}
(OUT/'abl1-memory-function-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':result['status'],'checks':result['checks'],'isa_and_base':result['isa_and_base'],'matched_dataflow':result['matched_dataflow'],'conclusion':result['conclusion']},sort_keys=True));sys.exit(0 if result['status']=='PASS' else 1)
