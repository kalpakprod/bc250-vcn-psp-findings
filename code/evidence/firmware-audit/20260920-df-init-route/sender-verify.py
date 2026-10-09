"""Supplement the existing DF evidence: bounded references and BIOS port census."""
import hashlib
import json
import re
import struct
from pathlib import Path

out = Path(__file__).resolve().parent
root = Path.cwd()
source = Path('import/from-windows/Users/kukuruza/tmp_bc250/upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5')
b = source.read_bytes()
assert hashlib.sha256(b).hexdigest() == 'cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37'
rom = Path('evidence/donor/retroweb-20260916/BC250_5.00_clv.bin').read_bytes()
assert hashlib.sha256(rom).hexdigest() == 'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
assert rom[0x8fef00:0x8fef00+len(b)] == b
word = lambda a: struct.unpack_from('<I', b, a)[0]
listing = (out/'sender-smu.txt').read_text()
rows = re.findall(r'^([0-9a-f]{8}) ([0-9a-f]+) (.+)$', listing, re.M)
insns = {}
for address, raw, ins in rows:
    a, data = int(address,16), bytes.fromhex(raw)
    assert b[a:a+len(data)] == data, address
    insns[a] = (data, ins)
leads = []
for pc in range(0x1b000,0x39000-2):
    if b[pc]&15 == 1 and ((pc+3)&~3)+(int.from_bytes(b[pc+1:pc+3],'little')-65536)*4 == 0x171ec:
        leads.append(pc)
missing = set(leads)-insns.keys()
assert missing == {0x2935d}
assert insns[0x2935c] == (bytes.fromhex('a2a1a3'), 'movi a10,0x1a3')
assert len(leads) == 51
accesses12 = [{'pc':hex(a),'instruction':ins} for a,(_,ins) in insns.items()
              if re.search(r'^(?:l8ui|l16ui|l32i(?:\.n)?|s8i) .*0x12$',ins)]
assert accesses12 == [{'pc':'0x1e041','instruction':'s8i a3,a4,0x12'}]
assert word(0xba0) == 0x7000
assert word(0x7aa8) == 0x79b4 and word(0x79b4+9*8) == 0x1c3b0
ports = {str(q):[hex(word(0x7000+12+12*q+4*j)) for j in range(3)] for q in (2,5)}
assert ports == {'2':['0x3010998','0x3010564','0x3010528'],
                 '5':['0x3010700','0x3010704','0x3010718']}
# Reuse existing extractor provenance and section map; no new extraction/parser.
p = Path('evidence/firmware-audit/20260919-inv-token-consumers')
census = json.loads((p/'census.json').read_text())
assert census['sha256'] == hashlib.sha256(rom).hexdigest()
values = (0x3010700,0x3010704,0x3010718,0x3b10700,0x3b10704,0x3b10718)
raw_hits, decoded_hits, bodies, checked_rows = [], [], 0, 0
selected = []
for rec in census['records']:
    if 'stem' not in rec:
        continue
    stem = rec['stem']
    data = (p/(stem+'.bin')).read_bytes()
    assert hashlib.sha256(data).hexdigest() == rec['sha256'], stem
    bodies += 1
    for value in values:
        start = 0
        while (at := data.find(struct.pack('<I',value),start)) >= 0:
            raw_hits.append({'module':stem,'value':hex(value),'offset':hex(at)})
            start = at+1
    instructions = json.loads((p/(stem+'.instructions.json')).read_text())
    for ins in instructions:
        a, raw = ins['rva'], bytes.fromhex(ins['bytes'])
        sec = next(s for s in rec['sections'] if s['rva'] <= a and a+len(raw) <= s['rva']+s['size'])
        off = sec['raw']+a-sec['rva']
        assert data[off:off+len(raw)] == raw, (stem,hex(a))
        checked_rows += 1
        if any(re.search(r'\b0x'+format(v,'x')+r'\b',ins['operands']) for v in values):
            decoded_hits.append({'module':stem,**ins})
        if stem == 'AmdNbioSmuV10Dxe-b158f039f48d' and (0x2d15<=a<=0x2d4d or 0x30ec<=a<=0x3120 or 0x31cc<=a<=0x326c):
            selected.append(ins)
assert not raw_hits and not decoded_hits
assert next(i for i in selected if i['rva']==0x2d43)['bytes'] == 'ba09000000'
assert next(i for i in selected if i['rva']==0x3267)['bytes'] == 'ba2805b103'
result = {'status':'PASS','scope':'bounded static analysis; no execution of firmware',
          'smu_instruction_records_verified':len(rows),'l32r_raw_leads':len(leads),
          'decoded_literal_refs':50,'unaligned_false_positive':'0x2935D inside MOVI at0x2935C',
          'offset12_accesses':accesses12,'queue_argument_response_message_ports':ports,
          'bios_modules_hashed':bodies,'bios_instruction_records_verified':checked_rows,
          'queue5_literal_raw_hits':raw_hits,'queue5_literal_decoded_hits':decoded_hits,
          'bios_message9_candidate':{'module':'AmdNbioSmuV10Dxe-b158f039f48d',
              'call_site':'0x2D48','callee':'0x3120','argument0_register':'0x03B10998','message_register':'0x03B10528',
              'conclusion':'Q2-like port tuple, not the Q5 init port tuple; address-alias interpretation is static inference.'},
          'limits':['No global absence-of-reader proof: computed/interior aliases, wider loads, indirect calls and DMA not exhaustively resolved.',
                    'No BIOS sender of Q5 init established; no host-reachability proof.',
                    'UEFI executable census excludes closed PSP/ABL code and compressed unextracted content.',
                    'Disassembler semantics and runtime state are not validated by byte equality alone.']}
(out/'sender-bios-selected.json').write_text(json.dumps(selected,indent=2)+'\n')
print(json.dumps(result,indent=2))
