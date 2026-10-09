#!/usr/bin/env python3
"""Independent bounded decode of item17's local single-state continuation."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
ROOT=Path('/home/OWNER/orca/projects/bc250')
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
ABL=ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
EXPECTED_ROM='ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
EXPECTED_ABL='af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a'
b=ABL.read_bytes(); checks=[]
def check(n,g,e):
 ok=g==e; checks.append({'name':n,'passed':ok,'got':g,'expected':e})
 if not ok: raise AssertionError(f'{n}: {g!r}!={e!r}')
def hx(a,n): return b[a:a+n].hex()
rom_hash=hashlib.sha256(ROM.read_bytes()).hexdigest(); abl_hash=hashlib.sha256(b).hexdigest()
check('rom_hash',rom_hash,EXPECTED_ROM); check('abl_hash',abl_hash,EXPECTED_ABL); check('abl_size',len(b),94624)
# exact 0x6D10 -> 0x6C20 -> 0x95FC guard
check('helper6D10_return_constant',hx(0x6d1e,4),'0120bd10')
check('metadata_store_helper_result_at_plus4',hx(0x6c2e,2),'6060')
check('95fc_reads_scratch_plus164',hx(0x963e,2),'5998')
check('95fc_compares_slot_to_one',hx(0x9644,2),'0128')
check('95fc_bls_to_9744',hx(0x9646,2),'7dd9')
check('9744_unconditional_b_to_984e',hx(0x9744,2),'83e0')
check('984e_helper_config_args_r0',hx(0x9850,2),'0420')
check('984e_helper_config_args_r1',hx(0x9852,2),'0021')
check('984e_calls_130c',hx(0x9854,4),'f7f75afd')
check('984e_continuation_b_to_989e',hx(0x9858,2),'21e0')
# single-state path writes aggregate +2bc from a runtime +70 halfword, no +20 channel write in bounded window
check('984e_loads_context_3c4',hx(0x988e,4),'d4f803c4')
check('984e_reads_runtime_plus70',hx(0x9896,4),'006f005b')
check('984e_stores_context_plus2bc',hx(0x989a,4),'c4f802bc')
check('984e_next_reduces_or_returns',hx(0x989e,4),'d4f803c4')
# helper 0x130c is a generic callback/config dispatch: no direct MMIO/SMN literal or clock register write in body.
check('130c_pushes_args',hx(0x130c,4),'0fb410b5')
check('130c_argument_test',hx(0x1310,8),'80f020040c43049a')
check('130c_calls_local_1354',hx(0x1328,4),'00f814bc')
check('1354_indirect_table_call_loop',hx(0x1332,0x20),'70b500252c4606462c4604e00868804700b10125641c56f824100029f6d1284670bd')
check('984e_window_has_no_svc6_opcode',b[0x984e:0x98b0].count(b'\x06\xdf'),0)
check('984e_window_has_no_known_smn_mmio_write_literals',all(x not in b[0x984e:0x98b0] for x in (b'\x00\x00\x15\x01',b'\x00\x00\x16\x01',b'\x14\x04\xd8\x01')),True)
result={'status':'PASS','checks':{'passed':sum(x['passed'] for x in checks),'failed':sum(not x['passed'] for x in checks),'total':len(checks)},'inputs':{'rom_sha256':rom_hash,'abl_sha256':abl_hash},'selected_path':{'helper_6d10':'returns 1','branch':'0x9646 -> 0x9744 -> 0x984E','single_state':'0x984E -> 0x130C -> 0x989A stores context+0x2BC from runtime context+0x70','visible_channel_plus20_write':'not in bounded 0x984E..0x98B0 window'},'helper_130c':{'prototype':'not recovered; body dispatches via local callback/table helper 0x1354','direct_known_clock_register_write':'not observed in bounded body'},'limits':['0x57100 loader base conditional','0x130C indirect helper/provider semantics remain unresolved','no physical clock/training/SMU/hardware behavior'] ,'checks_detail':checks}
(ABL.parent/'reachable-config-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':'PASS','checks':len(checks),'passed':result['checks']['passed'],'failed':result['checks']['failed'],'next_local_edge':'0x130C -> indirect helper/provider 0x1354','physical_clock':'UNRESOLVED'},indent=2))
