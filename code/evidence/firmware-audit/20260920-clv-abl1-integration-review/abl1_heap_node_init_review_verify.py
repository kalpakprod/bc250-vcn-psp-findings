#!/usr/bin/env python3
"""One-edge raw-byte check: ABL1 0xA04E HEAP lookup node fields vs header init."""
from pathlib import Path
import hashlib, json, re
ROOT=Path('/home/OWNER/orca/projects/bc250')
ABL=ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
LIST=ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt'
OUT=ROOT/'evidence/firmware-audit/20260920-clv-abl1-integration-review'
RESULT=OUT/'review-result.json'
EXPECTED={'abl':'af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a','listing':'b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65'}
checks=[]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def check(name,got,expected):
    ok=got==expected
    def show(v): return v.hex() if isinstance(v,bytes) else v
    checks.append({'check':name,'status':'PASS' if ok else 'FAIL','got':show(got),'expected':show(expected)})
    if not ok: raise AssertionError(f'{name}: {got!r} != {expected!r}')
def instr(blob,text,addr):
    hits=re.findall(rf'^\s*{addr:x}:\s+((?:[0-9a-fA-F]{{4}}\s+)+)\s*(.*?)\s*$',text,re.M)
    if len(hits)!=1: raise AssertionError(f'instruction {addr:#x}: expected one listing row, got {len(hits)}')
    halfwords,tail=hits[0]
    raw=b''.join(int(w,16).to_bytes(2,'little') for w in halfwords.split())
    asm=' '.join(re.sub(r'<[^>]*>','',tail).split(' @ ')[0].split())
    check(f'listing bytes match ABL1 at {addr:#x}',blob[addr:addr+len(raw)],raw)
    return asm
blob=ABL.read_bytes(); listing_raw=LIST.read_bytes(); listing=listing_raw.decode()
check('exact ABL1 SHA-256',sha(ABL),EXPECTED['abl'])
check('exact Thumb listing SHA-256',sha(LIST),EXPECTED['listing'])
expected={
0x4b1a:'movw r6, #0xa04e',0x4b34:'add r0, sp, #0x24',0x4b38:'str r6, [sp, #0x24]',0x4b3a:'bl 0x6374',
0x6374:'ldr r2, [pc, #0x70]',0x6378:'ldr r7, [pc, #0x70]',0x637c:'ldr r3, [r2]',0x637e:'cmp r3, r7',
0x6394:'ldr r5, [r0]',0x6396:'ldr r4, [r3]',0x6398:'cmp r4, r5',0x639c:'ldr r3, [r3, #0xc]',
0x63a8:'ldrb r1, [r3, #0x9]',0x63aa:'adds r2, r3, r1',0x63ac:'adds r2, #0x10',0x63ae:'str r2, [r0, #0x8]',
0x63b0:'ldr r2, [r3, #0x4]',0x63b2:'subs r1, r2, r1',0x63b4:'str r1, [r0, #0x4]',
0x63fa:'ldr r1, [pc, #0x24]',0x63fe:'strd r1, r2, [r0, #24]',0x6404:'strd r3, r2, [r1, #4]',
0x6408:'str r3, [r1, #0xc]',0x640a:'ldr r3, [pc, #0x18]',0x640c:'str r3, [r1]',
0x6412:'str r3, [r1, #0x14]',0x6414:'str r2, [r1, #0x1c]',0x6418:'strb r1, [r0, #0x10]',
0x6f78:'bl 0x63f8'}
for addr,want in expected.items(): check(f'instruction semantics at {addr:#x}',instr(blob,listing,addr),want)
check('lookup table-base literal',blob[0x63e8:0x63ec],bytes.fromhex('00 30 07 00'))
check('lookup HEAP comparison literal',blob[0x63ec:0x63f0],b'HEAP')
check('initializer table-base literal',blob[0x6420:0x6424],bytes.fromhex('00 30 07 00'))
check('initializer HEAP store literal',blob[0x6424:0x6428],b'HEAP')
result={'status':'PASS','checks':len(checks),'evidence_class':['observed-bytes','static-analysis'],
'inputs':{'abl1':str(ABL),'thumb_listing':str(LIST)},'hashes':{'abl1':sha(ABL),'thumb_listing':sha(LIST)},
'lookup_node_layout':{'key':'node+0 (compared with requested key)','size':'u32 node+4','metadata_byte':'u8 node+9','next_link':'pointer node+0xC','payload_start':'node+0x10+metadata_byte','payload_length':'u32(node+4)-metadata_byte','descriptor_outputs':{'payload_pointer':'descriptor+8','payload_length':'descriptor+4'}},
'key_query':'selector 0x0F materializes immediate 0xA04E at 0x4B1A, stores it to [SP+0x24] at 0x4B38, and calls 0x6374 at 0x4B3A.',
'initializer':'0x63F8 is called at 0x6F78. It loads table base literal 0x73000, loads the HEAP tag literal, and stores HEAP at [base+0]. This is arena/header/sentinel initialization only; this bounded routine does not demonstrate production of a linked node keyed 0xA04E. It does not prove that no other producer exists.',
'rom_scalar_qualification':'The earlier raw-image check tests only exact contiguous little-endian 32-bit scalar byte strings. Those misses do not prove there is no ROM representation. The decompressed ABL1 itself contains the 0xA04E MOVW immediate and the 0x73000 table-base literals.',
'limitations':['No runtime HEAP snapshot or node producer was identified by this one-edge check.','The parsed APCB/CBSG group 0x1707 has no established schema link to the runtime HEAP key.','No runtime, MHz, voltage, physical clock, mode, or MCLK=UCLK=FCLK claim.'],
'checks_detail':checks}
RESULT.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'checks':result['checks'],'key_query':result['key_query'],'lookup_node_layout':result['lookup_node_layout'],'initializer':result['initializer'],'rom_scalar_qualification':result['rom_scalar_qualification']},separators=(',',':')))
