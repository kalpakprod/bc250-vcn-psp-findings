#!/usr/bin/env python3
"""Bounded exact-ABL1 source/binary applicability check for memory-policy leads."""
import hashlib,json,re,struct,sys,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
SOURCE=ROOT/'import/from-windows/Users/kukuruza/tmp_bc250/recon/lorek123_psp/ABL1_decompiled.c'
STRINGS=ROOT/'import/from-windows/Users/kukuruza/tmp_bc250/recon/lorek123_psp/ABL1_strings.txt'
ROM_SHA='ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
CONT_SHA='95ae7826a69ea56b8c52ac703b85f181d45bdc309de334c2b7f9f4130376d515'
DEC_SHA='af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a'
def sha(data):return hashlib.sha256(data).hexdigest()
def sha_file(p):return sha(p.read_bytes())
def ck(c,l,d=None):checks.append({'label':l,'status':'PASS' if c else 'FAIL','details':d});return c
checks=[]
rom=ROM.read_bytes();ck(sha(rom)==ROM_SHA,'rom-hash',sha(rom));ck(len(rom)==0x1000000,'rom-size',len(rom))
off=0x99fd00; size=0xc020; blob=rom[off:off+size]
ck(sha(blob)==CONT_SHA,'abl1-container-hash',sha(blob));ck(blob[0x10:0x14]==b'$PS1','ps1-magic',blob[0x10:0x14].hex())
signed=struct.unpack_from('<I',blob,0x14)[0];ck(signed==48672,'signed-length',signed)
payload=zlib.decompress(blob[0x100:0x100+signed]);(OUT/'ABL1-clv-decompressed.bin').write_bytes(payload)
ck(len(payload)==94624,'decompressed-length',len(payload));ck(sha(payload)==DEC_SHA,'decompressed-hash',sha(payload));ck(payload[:4]==bytes.fromhex('10402de9'),'arm-entry',payload[:16].hex())
ck(sha_file(SOURCE)=='9501f2ed3abd96ac54cc317c26ae64d068f94a1a0d572d3c886c7877e4bb8f1b','source-hash',sha_file(SOURCE));ck(sha_file(STRINGS)=='c27bf19fb46415703c1e761641d3ac08102dda775b9152ea1b6a557c47741170','strings-hash',sha_file(STRINGS))
# Historical address anchors adjacent to the memory-policy routine.
anchors=[
 ('Determine DRAM Target MEMCLK',0x82d4),
 ('Synchronize MEMCLK Across Channels and Set Limits',0x99d8),
 ('Memory P-state Enabled.',0x8370),
 ('Memory P-state Disabled.',0x838c),
 ('Current Memory P-state: %d',0x894c),
]
rows=[]
for text,source_addr in anchors:
 needle=text.encode(); actual=payload.find(needle); at_source=payload[source_addr:source_addr+len(needle)]
 rows.append({'text':text,'historical_source_address':hex(source_addr),'exact_payload_match_offset':None if actual<0 else hex(actual),'bytes_at_historical_offset':at_source.hex(),'direct_address_match':actual==source_addr})
 ck(actual>=0,f'exact-string-present:{text}',rows[-1]); ck(actual!=source_addr,f'source-address-map-disagrees:{text}',rows[-1])
# Concrete source function lead exists, but no exact current-binary binding from these anchors.
src=SOURCE.read_text(errors='replace');ck('FUN_000096fc' in src,'historical-memory-sync-function-present')
result={'status':'PASS' if all(x['status']=='PASS' for x in checks) else 'FAIL','checks':{'passed':sum(x['status']=='PASS' for x in checks),'failed':sum(x['status']=='FAIL' for x in checks),'total':len(checks)},'input':{'rom':str(ROM),'rom_sha256':sha(rom),'abl1_spi_offset':'0x99FD00','container_sha256':sha(blob),'decompressed_sha256':sha(payload),'decompressed_length':len(payload)},'historical_source':{'decompiled':str(SOURCE),'decompiled_sha256':sha_file(SOURCE),'strings':str(STRINGS),'strings_sha256':sha_file(STRINGS),'version_label':'d00_e09_ABL1~0x31_22.4.6.0','memory_function_lead':'FUN_000096fc'},'anchor_rows':rows,'conclusion':'BOUNDARY: historical ABL1 source contains a memory-speed/P-state routine lead, but its source address map does not match the exact clv ABL1 decompressed payload string locations. Direct source-to-current-binary applicability is therefore UNPROVEN; do not apply source semantics to clv as if the function were bound. Exact payload hash/provenance is preserved for a future ARM disassembly/dataflow match.','limitations':['String-address mismatch falsifies direct address applicability, not all possible source algorithm similarity.','No ARM disassembly/function match was claimed from this check.','No firmware execution, hardware, training, clock, voltage, or settings action.'],'checks_detail':checks}
(OUT/'abl-memory-falsification-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':result['status'],'checks':result['checks'],'conclusion':result['conclusion'],'anchors':rows},sort_keys=True));sys.exit(0 if result['status']=='PASS' else 1)
