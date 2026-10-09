#!/usr/bin/env python3
"""Exact ABL1 FCLK caller/provider context and key transformation trace."""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT=Path('/home/OWNER/orca/projects/bc250')
OUT=ROOT/'evidence/firmware-audit/20260921-abl1-df-key-join'
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
ABL=ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
OBJ=ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o'
APCB=ROOT/'evidence/firmware-audit/20260920-clv-apcb-abl-apob-interface/apcb-detail.json'
ROM_SHA='ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
ABL_SHA='af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a'
OBJ_SHA='54abef3a390abb0ff745685de2eed4e0e8db5e9ba27bba1a0f245573b47ff135'
checks=[]; commands=[]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def chk(name, ok, detail):
 checks.append({'name':name,'status':'PASS' if ok else 'FAIL','detail':detail})
 if not ok: raise AssertionError(f'{name}: {detail}')
def run(name, argv):
 p=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True,check=False)
 (OUT/f'{name}.stdout').write_text(p.stdout); (OUT/f'{name}.stderr').write_text(p.stderr); (OUT/f'{name}.exit').write_text(str(p.returncode)+'\n')
 commands.append({'name':name,'argv':argv,'exit_status':p.returncode})
 chk(name+'_exit_and_stderr',p.returncode==0 and p.stderr=='',f'exit={p.returncode}; stderr_bytes={len(p.stderr.encode())}')
 return p.stdout

def expect(blob, off, hexs, label):
 raw=b''.join(bytes.fromhex(t[2:]+t[:2]) for t in (hexs[i:i+4] for i in range(0,len(hexs),4))); got=blob[off:off+len(raw)]
 chk(label,got==raw,f'ABL1+0x{off:X}: got={got.hex()} expected={raw.hex()}')

def thumb_bytes(token): return bytes.fromhex(token[2:]+token[:2])
def listing_has(text, pieces, label): chk(label,all(x in text for x in pieces),f'anchors={pieces}')

try:
 OUT.mkdir(parents=True,exist_ok=True)
 for p,want,size in [(ROM,ROM_SHA,16777216),(ABL,ABL_SHA,94624),(OBJ,OBJ_SHA,95312)]:
  got=sha(p); chk('input_'+p.name,got==want and p.stat().st_size==size,f'size={p.stat().st_size}; sha256={got}')
 blob=ABL.read_bytes(); apcb=json.loads(APCB.read_text())
 # Reuse parser output as a separate namespace-correspondence input; do not infer causality.
 group=next(g for g in apcb['images'][0]['apcb']['groups'] if g.get('gid')=='0x1707')
 chk('apcb_exact_1707_group',group.get('gid')=='0x1707' and len(group.get('subgroups',[]))==2,f'gid={group.get("gid")}; subgroups={len(group.get("subgroups",[]))}')
 sub15=next(s for s in group['subgroups'] if s.get('instance')==15)
 row160=next(r for r in sub15['token_rows'] if r.get('body_offset')=='0x160')
 chk('apcb_1707_subgroup15_row160_observed',row160.get('u8_0')==1 and row160.get('u8_1')==189 and row160.get('u16_le')==96,f'row={row160}')
 # Direct caller 0x5FAE: output local, selector, call, then commit to context+0x78.
 expect(blob,0x5fa4,'f24040b0','caller_5fa4_seeds_0x4b0')
 expect(blob,0x5fa8,'9001','caller_5fa8_stores_seed_to_sp4')
 expect(blob,0x5faa,'210f','caller_5faa_sets_selector_0x0f')
 expect(blob,0x5fac,'a801','caller_5fac_passes_sp4_as_output_pointer')
 expect(blob,0x5fae,'f7fefb45','caller_5fae_calls_fclk_463c')
 expect(blob,0x5fb2,'9b01','caller_5fb2_reloads_fclk_result')
 expect(blob,0x5fba,'f8a53078','caller_5fba_stores_halfword_to_context_plus_0x78')
 expect(blob,0x5e70,'4605','caller_5e70_preserves_context_r0_in_r5')
 # FCLK branch and reader input: no R1 rewrite between cmp and call, reader preserves it in r8.
 expect(blob,0x4648,'290f','fclk_4648_gates_selector_0x0f')
 expect(blob,0x464e,'f240105f','fclk_464e_builds_key_0x015f')
 expect(blob,0x4656,'1c40','fclk_4656_increments_to_0x0160')
 expect(blob,0x465c,'ab03','fclk_465c_sets_type_ptr_sp_plus_0x0c')
 expect(blob,0x466a,'f7fdfca3','fclk_466a_calls_reader_1fb4')
 expect(blob,0x1fbe,'4688','reader_1fbe_preserves_input_r1_as_r8')
 expect(blob,0x1fd2,'f8cd9000','reader_1fd2_forwards_r9_to_helper_stack_arg')
 expect(blob,0x1fd6,'aa02','reader_1fd6_sets_helper_output_pointer')
 expect(blob,0x1fde,'4641','reader_1fde_restores_r1_from_r8')
 expect(blob,0x1fe0,'f002fc0e','reader_1fe0_calls_helper_4800')
 # Helper/provider: FCLK scalar 0x0f reaches provider r2; token goes r1 then gets replaced by provider table/key path.
 expect(blob,0x4804,'460d','helper_4804_saves_reader_r1_as_r5')
 expect(blob,0x4808,'9906','helper_4808_loads_reader_stack_arg')
 expect(blob,0x4810,'200f','helper_4810_sets_provider_selector_0x0f')
 expect(blob,0x4812,'e9cd3100','helper_4812_writes_provider_stack_args')
 expect(blob,0x4816,'4613','helper_4816_moves_reader_output_to_provider_r3')
 expect(blob,0x4818,'462a','helper_4818_moves_fclk_selector_to_provider_r2')
 expect(blob,0x481a,'4621','helper_481a_moves_token_to_provider_r1')
 expect(blob,0x481c,'f000f8d6','helper_481c_calls_provider_49cc')
 expect(blob,0x49dc,'49fc','provider_49dc_loads_table_pointer_overwriting_r1_token')
 expect(blob,0x4a1e,'f2417107','provider_4a1e_prepares_literal_0x1707')
 expect(blob,0x4b0e,'220f','provider_4b0e_reasserts_selector_0x0f')
 expect(blob,0x4b1a,'f24a064e','provider_4b1a_replaces_token_with_key_0xa04e')
 expect(blob,0x4b1e,'e9cd2101','provider_4b1e_stores_selector_and_0x1707_pair')
 expect(blob,0x4b34,'a809','provider_4b34_builds_lookup_descriptor_sp24')
 expect(blob,0x4b36,'9929','provider_4b36_loads_stack_arg1_for_lookup')
 expect(blob,0x4b3a,'f001fc1b','provider_4b3a_calls_heap_lookup_6374')
 expect(blob,0x4bf0,'9a28','provider_4bf0_loads_type_pointer_stack_arg0')
 expect(blob,0x4bf2,'f3c10182','provider_4bf2_extracts_returned_type')
 expect(blob,0x4bfa,'7011','provider_4bfa_stores_returned_type_byte')
 # Fixed key reaches HEAP lookup as descriptor key; 6374 reads [r0] and compares against node key.
 expect(blob,0x637c,'6813','heap_lookup_637c_reads_heap_header')
 expect(blob,0x6394,'6805','heap_lookup_6394_reads_requested_key_from_descriptor')
 expect(blob,0x6396,'681c','heap_lookup_6396_reads_node_key')
 expect(blob,0x6398,'42ac','heap_lookup_6398_compares_key')
 expect(blob,0x63a8,'7a59','heap_lookup_63a8_reads_metadata_byte')
 expect(blob,0x63ae,'6082','heap_lookup_63ae_stores_payload_pointer')
 # Run exact disassembly windows and preserve literal output.
 obj=str(OBJ)
 specs=[
  ('caller_5e68',['llvm-objdump','-D','--triple=thumbv7m-none-eabi','--start-address=0x5e68','--stop-address=0x5fc0',obj],['5fa4:','movw\tr0, #0x4b0','5fae:','bl\t0x463c','5fba:','strh.w\tr3, [r5, #0x78]']),
  ('fclk_463c',['llvm-objdump','-D','--triple=thumbv7m-none-eabi','--start-address=0x463c','--stop-address=0x4696',obj],['4648:','cmp\tr1, #0xf','464e:','movw\tr0, #0x15f','466a:','bl\t0x1fb4']),
  ('reader_1fb4',['llvm-objdump','-D','--triple=thumbv7m-none-eabi','--start-address=0x1fb4','--stop-address=0x1fe4',obj],['1fbe:','mov\tr8, r1','1fde:','mov\tr1, r8','1fe0:','bl\t0x4800']),
  ('helper_4800',['llvm-objdump','-D','--triple=thumbv7m-none-eabi','--start-address=0x4800','--stop-address=0x4830',obj],['4810:','movs\tr0, #0xf','4818:','mov\tr2, r5','481a:','mov\tr1, r4','481c:','bl\t0x49cc']),
  ('provider_49cc',['llvm-objdump','-D','--triple=thumbv7m-none-eabi','--start-address=0x49cc','--stop-address=0x4c0c',obj],['4a1e:','movw\tr1, #0x1707','4b0e:','movs\tr2, #0xf','4b1a:','movw\tr6, #0xa04e','4b3a:','bl\t0x6374','4bfa:','strb\tr1, [r2]']),
  ('heap_6374',['llvm-objdump','-D','--triple=thumbv7m-none-eabi','--start-address=0x6374','--stop-address=0x63c0',obj],['6394:','ldr\tr5, [r0]','6398:','cmp\tr4, r5','63ae:','str\tr2, [r0, #0x8]']),
 ]
 listings={}
 for name,argv,anchors in specs:
  text=run(name,argv); listings[name]=text; listing_has(text,anchors,name+'_listing_anchors')
 # Verify direct disassembly byte coverage for each listing.
 for name,text in listings.items():
  count=0; ok=True
  for line in text.splitlines():
   import re
   m=re.match(r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{4}\s+)+)',line)
   if not m: continue
   addr=int(m.group(1),16); raw=b''.join(thumb_bytes(t) for t in m.group(2).split()); count+=1
   if blob[addr:addr+len(raw)]!=raw: ok=False; break
  chk(name+'_decoded_bytes_match_abl1',ok,f'instructions={count}')
 result={
  'status':'PASS','checks_passed':len(checks),'checks_failed':0,'timestamp':dt.datetime.now(ZoneInfo('Asia/Almaty')).isoformat(),
  'evidence_class':['observed-bytes','static-analysis'],
  'inputs':{'rom':{'path':str(ROM),'sha256':sha(ROM),'size':ROM.stat().st_size},'abl1':{'path':str(ABL),'sha256':sha(ABL),'size':ABL.stat().st_size},'object':{'path':str(OBJ),'sha256':sha(OBJ),'size':OBJ.stat().st_size},'apcb_detail':{'path':str(APCB),'sha256':sha(APCB)}},
  'new_dataflow_edge':{
   'caller':'0x5FA4 seeds local 0x4B0; 0x5FAA sets R1=0x0F; 0x5FAC passes SP+0x04; 0x5FAE BL 0x463C; 0x5FBA stores returned halfword to context+0x78 (R5 preserved from caller R0 at 0x5E70).',
   'reader':'FCLK 0x463C leaves R1=0x0F unchanged into 0x1FB4; reader 0x1FBE saves R1 in R8 and 0x1FDE restores it before BL 0x4800.',
   'helper':'0x4800 saves reader R1 in R5, sets selector R0=0x0F, moves R5 to provider R2 at 0x4818, and moves token R4 to provider R1 at 0x481A.',
   'provider':'0x49CC dispatches selector 0x0F; its case overwrites the token-derived provider path with literal 0x1707 and fixed lookup key 0xA04E at 0x4A1E/0x4B1A, then calls HEAP lookup 0x6374 at 0x4B3A. The provider type pointer is stack arg0 and receives a returned width/type byte at 0x4BF0..0x4BFA.',
   'heap':'0x6374 compares descriptor key [R0] against HEAP node key and returns payload pointer/length through descriptor +8/+4; selected key is therefore fixed 0xA04E in this selector case.',
  },
  'namespace_correlation':{'provider_literal_0x1707':'Exact APCB parser also reports CBSG gid 0x1707 (instances 13 and 15; instance15 row body offset 0x160 has u8_0=1,u8_1=189,u16_le=96). This is a numeric static correspondence only; no schema/runtime join to AmdSetup INV 0x1373/0x1374 or ABL1 key 0x015F/0x0160 is proven.'},
  'limits':{'not_proven':['FCLK token 0x015F/0x0160 semantic unit/frequency','AmdSetup INV 0x1373/0x1374 delivery into ABL1 HEAP','runtime loader/base/execution','divider/PLL actuation','physical clock or hardware behavior'],'first_unresolved':'The ABL1 provider selector-0x0F path reaches HEAP key 0xA04E, but the producer/populator of the matching HEAP node and any source bridge from native INV 0x1373/0x1374 remain unresolved.'},
  'checks':checks,'commands':commands}
 (OUT/'result.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
 (OUT/'commands.txt').write_text('\n'.join(f"{c['name']}: {' '.join(c['argv'])}; exit={c['exit_status']}" for c in commands)+'\n')
 print(json.dumps({'status':'PASS','checks_passed':len(checks),'checks_failed':0,'new_edge':'caller 0x5FAE R1=0x0F -> reader 0x1FB4 -> helper 0x4800 R2=0x0F -> provider case 0x0F -> fixed HEAP key 0xA04E; APCB literal correspondence 0x1707 observed','first_unresolved':'HEAP 0xA04E producer and INV 0x1373/0x1374 bridge'},separators=(',',':')))
except Exception as e:
 failed={'status':'FAIL','error':f'{type(e).__name__}: {e}','checks':checks,'commands':commands}; (OUT/'result.json').write_text(json.dumps(failed,indent=2)+'\n'); print(json.dumps({'status':'FAIL','error':str(e),'checks_passed':sum(x['status']=='PASS' for x in checks),'checks_failed':sum(x['status']=='FAIL' for x in checks)},separators=(',',':'))); raise
