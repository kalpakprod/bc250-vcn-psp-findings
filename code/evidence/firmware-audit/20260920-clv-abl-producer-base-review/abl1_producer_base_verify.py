#!/usr/bin/env python3
"""Independent conditional base-0x57100 ABL1 producer/callback/table review."""
from __future__ import annotations
import hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
PAY=ROOT/'evidence/firmware-audit/20260920-clv-sync-stage2-abl-memory/ABL1-clv-decompressed.bin';TH=ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt'
checks=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ck(ok,label,got,exp):checks.append({'label':label,'status':'PASS' if ok else 'FAIL','got':got,'expected':exp});return ok
b=PAY.read_bytes();d=TH.read_text();base=0x57100
ck(sha(PAY)=='af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a','payload-hash',sha(PAY),'af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a');ck(len(d)>1000000,'full-disassembly-present',len(d),'>1M')
# Four absolute callback anchors and mapped local Thumb code entries.
anchors=[(0xb218,0x67abd,0x109bc,'13b5'),(0xb21c,0x67a95,0x10994,'01b1'),(0xb220,0x61e19,0xad18,'30b4'),(0xb224,0x67a59,0x10958,'30b4')]
for lo,val,entry,pro in anchors:
 ck(struct.unpack_from('<I',b,lo)[0]==val,f'literal-{hex(lo)}',hex(struct.unpack_from('<I',b,lo)[0]),hex(val));ck(val-base==entry+1,f'map-{hex(lo)}',hex(val-base),hex(entry+1));ck(b[entry:entry+len(bytes.fromhex(pro))].hex()==pro,f'code-{hex(entry)}',b[entry:entry+len(bytes.fromhex(pro))].hex(),pro)
# Callback slot/dataflow and exact producer writes.
for off,h in [(0xb1f8,'c0f82c15'),(0x757c,'a5f86000'),(0x7586,'00f021f8'),(0x75e2,'7468'),(0x7e00,'02f0aaff'),(0x7e30,'08f046ff'),(0xae22,'0684'),(0x10d40,'008c'),(0x10e50,'0784'),(0x109c0,'90f8'),(0x10a04,'e160')]: ck(b[off:off+len(bytes.fromhex(h))].hex()==h,f'raw-{hex(off)}',b[off:off+len(bytes.fromhex(h))].hex(),h)
# Table pointer from classifier literal under base57100 and raw halfwords.
table_ptr=struct.unpack_from('<I',b,0x7540)[0];table_off=table_ptr-base;ck(table_ptr==0x6db04,'classifier-literal',hex(table_ptr),'0x6db04');ck(table_off==0x16a04,'mapped-table-offset',hex(table_off),'0x16a04');half=[struct.unpack_from('<H',b,table_off+2*i)[0] for i in range(8)];ck(half==[0x6d6,0x532,0x532,0x352,0xe1,0,0,0xe1],'table-8-halfwords',[hex(x) for x in half],['0x6d6','0x532','0x532','0x352','0xe1','0x0','0x0','0xe1'])
result={'status':'PASS' if all(x['status']=='PASS' for x in checks) else 'FAIL','checks':{'passed':sum(x['status']=='PASS' for x in checks),'failed':sum(x['status']=='FAIL' for x in checks),'total':len(checks)},'candidate_base':'0x57100','anchors':[{'literal':hex(lo),'value':hex(val),'mapped_entry':hex(entry),'prologue':pro} for lo,val,entry,pro in anchors],'callback_path':{'slot':'0xB1F8 -> [r0+0x52C]','callback':'0x109BC','callback_channel_count':'[r0+0x4B]','callback_context_write':'[r4+0x0C]'},'producer_chain':['0x7548 -> r5=[r0+4]','0x757C -> [r5+0x60]=0x0320','0x7586 -> BL 0x75CC','0x7E00 -> BL 0xAD58','0x7E30 -> BL 0x10CC0','0xAD58/0x10CC0 -> [channel+0x20] writes'],'table':{'literal':'0x6DB04','mapped_payload_offset':'0x16A04','raw_halfwords':[hex(x) for x in half]},'conclusion':'Four independent absolute pointer literals map under conditional base 0x57100 to local Thumb code, including the callback stored in +0x52C. The classifier table literal maps to payload offset 0x16A04 with eight observed halfwords. The producer chain writes the per-channel +0x20 field before/around the memory policy flow. Base 0x57100 is conditional static coherence, not loader/runtime proof; raw table values have no assigned units or physical-domain meaning.', 'limitations':['No loader relocation contract or runtime execution.','No MCLK/UCLK/FCLK unit or hardware claim.','No direct BL/BLX to 0x95FC; callback/producer path is the recovered local edge.'],'checks_detail':checks}
(OUT/'abl1-producer-base-review-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'status':result['status'],'checks':result['checks'],'candidate_base':result['candidate_base'],'table':result['table'],'conclusion':result['conclusion']},sort_keys=True));raise SystemExit(0 if result['status']=='PASS' else 1)
