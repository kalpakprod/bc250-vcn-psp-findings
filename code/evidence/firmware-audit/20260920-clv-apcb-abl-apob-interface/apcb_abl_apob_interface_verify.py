#!/usr/bin/env python3
"""Independent exact-byte APCB/ABL/APOB/INV interface boundary check."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
MEM=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/AmdMemAm4Pei-1ef4e7b94467.instructions.json'
HOB=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/AmdMemoryHobInfoPeim-aad3f828ccef.instructions.json'
PSP=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/AmdPspPeiV2-1158720bbf95.instructions.json'
CBS=ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/CbsBasePei-6ff112922ad8.instructions.json'
FA=OUT/'firmware-audit.json'; AD=OUT/'apcb-detail.json'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ins(p): return {int(x['rva']):x for x in json.loads(p.read_text())}
def ck(cs,label,got,exp):
 ok=got==exp; cs.append({'label':label,'status':'PASS' if ok else 'FAIL','got':got,'expected':exp}); return ok

def main():
 cs=[]; rom=ROM.read_bytes(); ck(cs,'clv-hash',sha(ROM),'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'); ck(cs,'clv-size',len(rom),0x1000000)
 fa=json.loads(FA.read_text())['images'][0]; ad=json.loads(AD.read_text())['images'][0]
 ck(cs,'firmware-parser-input-hash',fa['sha256'],'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8')
 ap=fa['apcb']; ck(cs,'APCB-offset',ap['offset'],0xAB1000); ck(cs,'APCB-size',ap['size'],2972); ck(cs,'APCB-checksum',ap['checksum_match'],True); ck(cs,'APCB-DFG+130',ap['dfg_words']['0x130'],'0x001FFF00'); ck(cs,'APCB-DFG+16C',ap['dfg_words']['0x16C'],'0x001FFF00')
 # BHD type 0x61 is declared but has no flash body; 0x63 is an 8 KiB NV copy.
 bhd={x['type']:x for x in fa['bhd']['entries']}; ck(cs,'BHD-APOB-type61-size',bhd[97]['size'],0); ck(cs,'BHD-APOB_NV_COPY-type63-size',bhd[99]['size'],8192); ck(cs,'BHD-APOB_NV_COPY-spi',bhd[99]['spi_offset'],0xAB3000)
 mem=ins(MEM); hob=ins(HOB); psp=ins(PSP); cbs=ins(CBS)
 # Existing AmdSetup -> INV producer edge.
 ck(cs,'Cbs INV header 0x11ED',cbs[0x9837]['operands'],'edx,0x11ed'); ck(cs,'Cbs Setup+316 load',cbs[0x9857]['operands'],'al,BYTE PTR [edx+0x316]'); ck(cs,'Cbs INV store',cbs[0x985d]['operands'],'BYTE PTR [ecx+0x3],al')
 # APOB service request and validation markers in AmdMemAm4Pei.
 for r,b in {0x8a0:'684cb1e309',0x8ca:'68ff000000',0x8cf:'6a61',0x8d1:'e803040000',0x8fc:'813b41504f42',0xc73:'813e24505350',0xc96:'813f24424844'}.items(): ck(cs,f'AmdMem:{hex(r)}-bytes',mem[r]['bytes'],b)
 direct_inv=[x for x in mem.values() if '0x11ed' in x.get('operands','').lower() or '+0x316' in x.get('operands','').lower()]; ck(cs,'AmdMem-no-direct-INV-or-Setup316',len(direct_inv),0)
 # APOB/PPI input -> HOB/InstallPeiMemory output.
 ck(cs,'AmdMemoryHob LocatePpi slot',hob[0xac3]['operands'],'DWORD PTR [eax+0x20]'); ck(cs,'AmdMemoryHob PPI field+28',hob[0xad0]['operands'],'ecx,DWORD PTR [eax+0x28]'); ck(cs,'AmdMemoryHob PPI field+2c',hob[0xad6]['operands'],'cx,WORD PTR [eax+0x2c]'); ck(cs,'AmdMemoryHob PPI field+30',hob[0xade]['operands'],'cl,BYTE PTR [eax+0x30]'); ck(cs,'AmdMemoryHob PPI field+31',hob[0xae4]['operands'],'cl,BYTE PTR [eax+0x31]'); ck(cs,'AmdMemoryHob PPI field+40',hob[0xae7]['operands'],'eax,DWORD PTR [eax+0x40]'); ck(cs,'AmdMemoryHob InstallPeiMemory slot',hob[0x299]['operands'],'DWORD PTR [eax+0x44]'); direct_hob_inv=[x for x in hob.values() if '0x11ed' in x.get('operands','').lower() or '+0x316' in x.get('operands','').lower()]; ck(cs,'AmdMemoryHob-no-direct-INV-or-Setup316',len(direct_hob_inv),0)
 # PSP PEI output is C2P/PPI infrastructure, not an APCB token read in this bounded window.
 ck(cs,'AmdPspPei C2P/status message 0x66',psp[0x305]['operands'],'0x66'); ck(cs,'AmdPspPei InstallPpi slot',psp[0x2b9]['operands'],'DWORD PTR [ecx+0x18]')
 result={'status':'PASS' if all(x['status']=='PASS' for x in cs) else 'FAIL','checks':{'passed':sum(x['status']=='PASS' for x in cs),'failed':sum(x['status']=='FAIL' for x in cs),'total':len(cs)},'input':{'path':str(ROM),'sha256':sha(ROM),'size':len(rom)},'apcb':{'offset':'0xAB1000','size':2972,'checksum':'C0','dfg_words':{'0x130':'0x001FFF00','0x16C':'0x001FFF00'},'parser_report':str(FA),'detail_report':str(AD)},'bhd_boundary':{'type_0x61_apob_size':0,'type_0x63_apob_nv_copy_size':8192,'type_0x63_spi_offset':'0xAB3000'},'edges':{'persisted_setup_to_inv':{'module':'CbsBasePei','field':'Setup+0x316','token':'0x11ED','rvas':['0x9837','0x9857','0x985D']},'apob_service_to_ppi':{'module':'AmdMemAm4Pei','rvas':['0x8A0','0x8CA','0x8CF','0x8D1','0x8FC','0xC73','0xC96'],'interpretation':'service request (literal 0x9E3B14C, message 0x61, arg 0xFF) and returned APOB/$PSP/$BHD validation'},'ppi_to_memory_output':{'module':'AmdMemoryHobInfoPeim','locate_ppi_rva':'0xAC3','input_fields':['+0x28','+0x2C','+0x30','+0x31','+0x40'],'install_pei_memory_rva':'0x299'},'psp_pei_common_ppi':{'module':'AmdPspPeiV2','install_ppi_rva':'0x2B9','message_literal':'0x66','note':'bounded PSP/PEI infrastructure only'}},'conclusion':'The bounded exact-byte path separates sources: clv APCB/DFG is a parsed flash policy surface; CbsBasePei serializes persisted AmdSetup into $INV token 0x11ED; AmdMemAm4Pei requests a runtime APOB service and validates APOB/$PSP/$BHD; AmdMemoryHobInfoPeim consumes a PPI structure and calls InstallPeiMemory. No direct Setup/$INV read is present in AmdMemoryHobInfoPeim. This qualifies a source/provenance boundary relevant to persisted settings being ignored, but does not prove that INV never feeds the APOB service indirectly or establish runtime precedence/training.', 'limitations':['Static byte analysis and parser output only; no firmware execution or training.','No direct APCB-to-APOB merge call was recovered in this bounded scope.','AmdMem service/message semantics and PPI GUID identity remain partly closed.'], 'checks_detail':cs}
 (OUT/'apcb-abl-apob-interface-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps({'status':result['status'],'checks':result['checks'],'conclusion':result['conclusion']},sort_keys=True)); raise SystemExit(0 if result['status']=='PASS' else 1)
if __name__=='__main__':main()
