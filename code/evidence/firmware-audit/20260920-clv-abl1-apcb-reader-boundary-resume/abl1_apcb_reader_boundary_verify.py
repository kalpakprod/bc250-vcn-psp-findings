#!/usr/bin/env python3
"""Exact ABL1 common-reader boundary after UCLK/FCLK descriptor branches."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
ABL=ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
DIS=ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt'
PRIOR=ROOT/'evidence/firmware-audit/20260920-clv-abl1-fclk-uclk-branch-xhigh/abl1-fclk-uclk-branch-result.json'
EXPECTED={
 'rom':'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8',
 'abl':'af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a',
 'dis':'b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65',
 'prior':'d6d053b5e4a74a5b4fe0526e4d4659d22a500601074baad751977ab21e2ecdfa',
}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def j(v): return 'hex:'+bytes(v).hex() if isinstance(v,(bytes,bytearray)) else v
def check(cs,name,got,expected):
 ok=got==expected; cs.append({'check':name,'passed':ok,'got':j(got),'expected':j(expected)})
 if not ok: raise AssertionError(f'{name}: got {got!r}, expected {expected!r}')
def main():
 cs=[]
 for name,path,key in [('ROM',ROM,'rom'),('exact ABL1',ABL,'abl'),('exact disassembly',DIS,'dis'),('completed branch result',PRIOR,'prior')]:
  check(cs,f'{name} exists',path.exists(),True); check(cs,f'{name} sha256',sha(path),EXPECTED[key])
 blob=ABL.read_bytes(); dis=DIS.read_text(errors='replace'); prior=json.loads(PRIOR.read_text())
 check(cs,'completed prior branch status',prior.get('status'),'PASS')
 check(cs,'completed prior branch checks',prior.get('checks'),53)
 # Exact 0x1fb4 entry and context transfer.
 check(cs,'reader prologue push',blob[0x1fb4:0x1fb8],bytes.fromhex('2de9ff47'))
 check(cs,'reader preserves descriptor pointer r0->r5',blob[0x1fb8:0x1fba],bytes.fromhex('0546'))
 check(cs,'reader reads descriptor first halfword',blob[0x1fba:0x1fbc],bytes.fromhex('0088'))
 check(cs,'reader preserves output pointer r2->r6',blob[0x1fc4:0x1fc6],bytes.fromhex('1646'))
 check(cs,'reader preserves type pointer r3->r10',blob[0x1fc6:0x1fc8],bytes.fromhex('9a46'))
 check(cs,'reader rejects zero descriptor',blob[0x1fc8:0x1fca],bytes.fromhex('18bb'))
 # The UclkDiv1/Fclk caller descriptor pairs are exact bytes, not source labels.
 descriptor_pairs=[('UclkDiv1M0',0x2cf0,0x21),('UclkDiv1M1',0x2d20,0x22),('UclkDiv1M2',0x2d48,0x23),('UclkDiv1M3',0x2d70,0x24),('Fclk',0x464e,0x160)]
 for field,off,key in descriptor_pairs:
  if field.startswith('Uclk'):
   # M0 initializes the first halfword 0x20 and terminator; each branch writes its key at +0x46.
   keyoff = off + 4 if field == 'UclkDiv1M0' else off
   storeoff = off + 6 if field == 'UclkDiv1M0' else off + 2
   check(cs,f'{field} key immediate 0x{key:02x}',blob[keyoff:keyoff+2],bytes((key,0x20)))
   check(cs,f'{field} stores key into descriptor +0x46',blob[storeoff:storeoff+4],bytes.fromhex('adf84600'))
   if field == 'UclkDiv1M0':
    check(cs,'Uclk descriptor first halfword 0x20',blob[0x2cf0:0x2cf4],bytes.fromhex('adf84400'))
    check(cs,'Uclk descriptor terminator zero at +0x48',blob[0x2cfc:0x2d00],bytes.fromhex('adf84880'))
  else:
   # FCLK construction starts at 0x464e with movw r0,#0x15f then stores; caller descriptor bytes are the two halfword immediates.
   check(cs,'Fclk descriptor first immediate 0x15f',blob[0x464e:0x4652],bytes.fromhex('40f25f10'))
   check(cs,'Fclk descriptor second stored halfword 0x160',blob[0x4656:0x465c],bytes.fromhex('401cadf81420'))
 # Reader loop calls exact helper 0x4800 with first and second descriptor words.
 check(cs,'reader first helper call BL 0x4800',blob[0x1fd8:0x1fe4],bytes.fromhex('35f814005346414602f00efc'))
 check(cs,'reader success tests returned helper status',blob[0x1fe4:0x1fea],bytes.fromhex('68b10298c0b2'))
 check(cs,'reader second descriptor loop load',blob[0x2012:0x2018],bytes.fromhex('05eb44004088'))
 check(cs,'reader second helper call BL 0x4800',blob[0x2030:0x203e],bytes.fromhex('02aa35f814005346414602f0e1fb'))
 # Typed output stores selected by caller-supplied type byte at [r10].
 check(cs,'type dispatch loads caller type',blob[0x2042:0x2048],bytes.fromhex('9af800000128'))
 check(cs,'type 1 stores byte to r6',blob[0x2058:0x2064],bytes.fromhex('0298c143c9b239431bd03070'))
 check(cs,'type 2 stores halfword to r6',blob[0x2066:0x2072],bytes.fromhex('0298c14389b2394314d03080'))
 check(cs,'type 4 stores word to r6',blob[0x2074:0x207e],bytes.fromhex('029877ea00010ed03060'))
 check(cs,'type 8 stores doubleword to r6',blob[0x2080:0x2092],bytes.fromhex('dde90210ca4372ea000200d12fb1c6e90010'))
 check(cs,'reader returns success after typed store',blob[0x2092:0x209a],bytes.fromhex('012004b0bde8f087'))
 check(cs,'reader returns failure path',blob[0x209a:0x209e],bytes.fromhex('0020fae7'))
 # Exact payload strings tie helper to APCB/CBS parameter wording.
 for text in (b'APCB parameter disabled: Token %04x, Timepoint %04x', b'Config parameter %04x mapped to CBS token %04x', b'Get config parameter: token %04x, timepoint %04x'):
  check(cs,f'exact ABL1 string lead {text.decode()}',text in blob,True)
 result={
  'status':'PASS','checks':len(cs),'route':'exact ABL1 UCLK/FCLK common-reader boundary',
  'evidence_class':['observed-bytes','static-analysis'],
  'inputs':{'rom':str(ROM),'abl1':str(ABL),'disassembly':str(DIS),'completed_branch_result':str(PRIOR)},
  'hashes':{'rom':sha(ROM),'abl1':sha(ABL),'disassembly':sha(DIS),'completed_branch_result':sha(PRIOR)},
  'reader':{'payload_offset':'0x1fb4','role':'descriptor-driven typed configuration/APCB lookup boundary','descriptor_pairs':{'UclkDiv1M0':['0x20','0x21'],'UclkDiv1M1':['0x20','0x22'],'UclkDiv1M2':['0x20','0x23'],'UclkDiv1M3':['0x20','0x24'],'Fclk':['0x15f','0x160']},'helper':'payload+0x4800','typed_outputs':{'1':'byte [r6]','2':'halfword [r6]','4':'word [r6]','8':'doubleword [r6]'},'success':'r0=1 at 0x2092','failure':'r0=0 at 0x209a'},
  'fresh_result':'The exact 0x1fb4 edge is a descriptor-driven typed parameter reader: UclkDiv1 descriptors [0x20,0x21..0x24] and Fclk [0x15f,0x160] are iterated, each entry is queried through exact helper 0x4800, and the result is copied into a caller output as byte/halfword/word/doubleword according to caller type. This is a configuration/APCB lookup boundary, not a divider/PLL write.',
  'unresolved_edge':'payload+0x4800 and its external/indirect parameter provider remain the first consumer edge. No MCLK=UCLK=FCLK, ratio, PLL, training, synchronous-crossing, runtime, physical-clock, or hardware claim follows.',
  'limits':'Completed exact branch result was revalidated and reused; no duplicate branch search, no hardware/runtime action, no firmware/settings/shared-state changes.' ,'checks_detail':cs}
 (OUT/'abl1-apcb-reader-boundary-result.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps({'status':result['status'],'checks':len(cs),'reader':result['reader'],'unresolved_edge':result['unresolved_edge']},indent=2))
if __name__=='__main__':main()
