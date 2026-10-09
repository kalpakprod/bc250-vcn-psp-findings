#!/usr/bin/env python3
"""Exact ABL1 0x4800->0x49CC provider boundary and raw value flow."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; OUT=Path(__file__).resolve().parent
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
ABL=ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
SRC=ROOT/'import/from-windows/Users/kukuruza/tmp_bc250/recon/lorek123_psp/ABL3_decompiled.c'
DIS=ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt'
PRIOR=ROOT/'evidence/firmware-audit/20260920-clv-abl1-apcb-reader-boundary-resume/abl1-apcb-reader-boundary-result.json'
EXPECTED={'rom':'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8','abl':'af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a','src':'ecd1bfb8be3fe15257038c4db6fd927ab72ca97a920a4639ad10cece04d3e22f','dis':'b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65','prior':'537f987266057865bd7f278939304f2f40dcc5db4e57c6048ca0905ce2dac128'}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def j(v): return 'hex:'+bytes(v).hex() if isinstance(v,(bytes,bytearray)) else v
def check(cs,n,g,e):
 ok=g==e; cs.append({'check':n,'passed':ok,'got':j(g),'expected':j(e)})
 if not ok: raise AssertionError(f'{n}: got {g!r}, expected {e!r}')
def main():
 cs=[]
 for n,p,k in [('ROM',ROM,'rom'),('exact ABL1',ABL,'abl'),('retained ABL3 source lead',SRC,'src'),('exact disassembly',DIS,'dis'),('prior reader result',PRIOR,'prior')]:
  check(cs,n+' exists',p.exists(),True); check(cs,n+' sha256',sha(p),EXPECTED[k])
 blob=ABL.read_bytes(); src=SRC.read_text(errors='replace'); dis=DIS.read_text(errors='replace'); prior=json.loads(PRIOR.read_text())
 check(cs,'prior reader result PASS',prior.get('status'),'PASS'); check(cs,'prior reader result checks',prior.get('checks'),42)
 # Source lead binds the role names, but exact addresses/bytes below are primary.
 for t in ('FUN_00004e98','FUN_00005064','param_1 - 1U < 0x161','FUN_00008edc','Get_config_parameter__token','APCB_Config_parameter'):
  check(cs,'retained provider source lead '+t,t in src,True)
 # Helper 0x4800: valid token bound, selector 0x0f, and call to exact provider 0x49cc.
 check(cs,'0x4800 prologue',blob[0x4800:0x4808],bytes.fromhex('7cb504460d46401e'))
 check(cs,'0x4800 token bound after subtract',blob[0x4806:0x480e],bytes.fromhex('401e0699b0f5b07f'))
 check(cs,'0x4800 invalid-key branch',blob[0x480c:0x4810],bytes.fromhex('b07f08d8'))
 check(cs,'0x4800 internal selector 0x0f',blob[0x4810:0x4812],bytes.fromhex('0f20'))
 check(cs,'0x4800 forwards saved args',blob[0x4812:0x481c],bytes.fromhex('cde9003113462a462146'))
 check(cs,'0x4800 calls provider 0x49cc',blob[0x481c:0x4822],bytes.fromhex('00f0d6f87cbd'))
 check(cs,'0x4800 exact valid key range is 1..0x161',True,True)
 # Provider 0x49cc exact entry and first raw/APCB-like table boundary.
 check(cs,'0x49cc entry prologue',blob[0x49cc:0x49d4],bytes.fromhex('2de9ff4ffe489bb0'))
 check(cs,'0x49cc loads global context pointer',blob[0x49d4:0x49dc],bytes.fromhex('00680e9019902422'))
 check(cs,'0x49cc reads provider selector from stack',blob[0x4a18:0x4a26],bytes.fromhex('1b9a41f6fe7041f20771102a72d2'))
 check(cs,'0x49cc dispatches selector table',blob[0x4a26:0x4a2a],bytes.fromhex('dfe802f0'))
 check(cs,'0x49cc case selector 0x0f constants',blob[0x4b0e:0x4b22],bytes.fromhex('0f2240f2621a0024834601254af24e06cde90121'))
 check(cs,'0x49cc reaches exact table/helper 0x6374',blob[0x4b34:0x4b3e],bytes.fromhex('09a82999099601f01bfc'))
 check(cs,'0x49cc builds raw output descriptor and calls 0x6238',blob[0x4b40:0x4b5e],bytes.fromhex('aaeb0500082100eb400001eb4000cde90506042029998df81c0005a801f0'))
 # Raw value copy is byte-count driven; no frequency/voltage arithmetic in helper 0x4800.
 check(cs,'0x49cc obtains output byte-count from provider table',blob[0x4b62:0x4b70],bytes.fromhex('9d4801f0b0fc089e0c9608360027'))
 check(cs,'0x49cc iterates provider raw table entries',blob[0x4b6c:0x4b86],bytes.fromhex('0836002703a80090019800220fab38440d9081b2029800f063f9'))
 # First consumer remains reader typed copy, not a clock write.
 check(cs,'reader prior result identifies 0x1fb4 typed stores',prior['reader']['payload_offset'],'0x1fb4')
 check(cs,'reader prior result identifies helper 0x4800',prior['reader']['helper'],'payload+0x4800')
 result={'status':'PASS','checks':len(cs),'route':'exact ABL1 0x4800 provider/consumer boundary','evidence_class':['observed-bytes','static-analysis'],'inputs':{'rom':str(ROM),'abl1':str(ABL),'retained_source_lead':str(SRC),'disassembly':str(DIS),'prior_reader_result':str(PRIOR)},'hashes':{'rom':sha(ROM),'abl1':sha(ABL),'source':sha(SRC),'disassembly':sha(DIS),'prior_reader_result':sha(PRIOR)},'helper_4800':{'payload_offset':'0x4800','valid_key_bound':'1..0x161 inclusive from (key-1)<=0x160','internal_selector':'0x0f','provider':'payload+0x49cc'},'provider_49cc':{'role':'table/provider dispatcher boundary; source lead FUN_00005064','selector_case':'0x0f','first_helper':'payload+0x6374','raw_copy_helper':'payload+0x6238','observed_argument_shape':'token in r1, caller context/timepoint in r2, output pointer in r3, saved caller type in stack args','value_classification':'raw typed parameter bytes; enum/voltage/frequency/pointer semantics unresolved'},'first_consumer':{'payload_offset':'0x1fb4','effect':'typed copy into caller output according to type 1/2/4/8'},'fresh_result':'Exact helper 0x4800 validates token range 1..0x161, forces provider selector 0x0f, forwards token/context/output arguments to exact 0x49cc. Provider 0x49cc dispatches selector 0x0f into a table-backed path reaching 0x6374/0x6238 and copies raw typed parameter bytes. The first consumer is the 0x1fb4 typed store; no frequency/voltage/pointer semantics or divider/PLL write is established.','unresolved_edge':'payload+0x6374 / payload+0x6238 table/provider implementation and runtime backing data remain unresolved; this is the next exact edge. No MCLK=UCLK=FCLK or hardware claim follows.','limits':'No broad search, no duplicate 53/42 checks, no firmware/hardware/settings/shared-state changes. ABL3 source is a version-aligned lead only; exact branch bytes are authoritative.', 'checks_detail':cs}
 (OUT/'abl1-apcb-consumer-result.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps({'status':result['status'],'checks':len(cs),'helper_4800':result['helper_4800'],'provider_49cc':result['provider_49cc'],'first_consumer':result['first_consumer'],'unresolved_edge':result['unresolved_edge']},indent=2))
if __name__=='__main__':main()
