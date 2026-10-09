#!/usr/bin/env python3
"""Verify one Q3 0x1D selector consumer and its scale/register route."""
from pathlib import Path
import hashlib, json, re, struct

ROM=Path('evidence/donor/retroweb-20260916/BC250_5.00_clv.bin')
SMU=Path('import/from-windows/Users/kukuruza/tmp_bc250/upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5')
ASM=Path('evidence/firmware-audit/20260921-smu-domain-selector/q3-aligned-ghidra.txt')
rom=ROM.read_bytes(); b=SMU.read_bytes(); listing=ASM.read_text(errors='replace')
assert len(rom)==0x1000000 and hashlib.sha256(rom).hexdigest()=='ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
assert len(b)==262400 and hashlib.sha256(b).hexdigest()=='cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37'
assert rom[0x8FEF00:0x8FEF00+len(b)]==b and rom[0x7E5]==0x24
checks=[]
def chk(ok,msg):
    assert ok,msg
    checks.append(msg)
def u8(o): return b[o]
def u32(o): return struct.unpack_from('<I',b,o)[0]
def f32(o): return struct.unpack_from('<f',b,o)[0]
# The output was made by existing Ghidra 12.1.3 OcConsumerRead.java and asserts complete program memory equality.
chk(listing.startswith('PASS: entire loaded program memory equals clv-matching robin-5 body, bytes=262400'), 'Ghidra loaded memory == exact Robin-5 payload')
# Check every Ghidra listing instruction is at its exact byte offset in the pinned payload.
records=[]
for line in listing.splitlines():
    m=re.match(r'^([0-9a-fA-F]{8})\s+([0-9a-fA-F]+)\s+(.+)$',line)
    if not m: continue
    off=int(m.group(1),16); op=bytes.fromhex(m.group(2)); asm=m.group(3).strip()
    if off+len(op)<=len(b):
        chk_bytes=(b[off:off+len(op)]==op)
        assert chk_bytes,(hex(off),op.hex(),b[off:off+len(op)].hex(),asm)
        records.append((off,op.hex(),asm))
chk(len(records)>250, 'bounded Ghidra listing instructions byte-match exact payload')
lookup={off:(raw,asm) for off,raw,asm in records}
def ins(off,raw,needle):
    got=lookup.get(off)
    chk(got is not None and got[0]==raw and needle in got[1], f'{off:#x} {needle}')
# Q3 handler bounds/rejects: maximum 20, zero rejected; domain IDs 0x13 and 0x14 return data 0xFFFFFFFF/status 1.
ins(0x2ea10,'1c4c','movi.n a12,0x14')
ins(0x2ea14,'a0a0f5','extui a10,a10,0x10,0x10')
ins(0x2ea17,'a73c3f','bltu a12,a10')
ins(0x2ea1a,'bcca','beqz.n a10')
ins(0x2ea24,'1c38','movi.n a8,0x13')
ins(0x2ea26,'871b3a','beq a11,a8')
ins(0x2ea29,'c71b37','beq a11,a12')
ins(0x2ea2f,'30e0f4','extui a14,a3,0x0,0x10')
ins(0x2ea35,'000eda','ufloat.s f0,a14')
ins(0x2ea3b,'034c50','ssi f0,a12,0x140')
ins(0x2ea41,'65d4ff','call8 0x0002e788')
ins(0x2ea5c,'b2a0ff','movi a11,0xff')
ins(0x2ea5f,'a554d2','call8 0x00000fa8')
ins(0x2ea66,'7cfb','movi.n a11,0xff')
ins(0x2ea68,'a557d2','call8 0x00000fe4')
ins(0x2ea6d,'0c1b','movi.n a11,0x1')
ins(0x2ea6f,'a553d2','call8 0x00000fa8')
# One selector -> target consumer -> descriptor -> register example, plus the two rejected neighbors.
selector=11; loop_i=selector-1
selector_target=0x1402c+selector*12
loop_target=0x14038+loop_i*12
domain_ptr=0x13ef4+loop_i*4
domain_id=u32(domain_ptr)
desc_base=0xf7a8+domain_id*0x1c
group=u8(desc_base)
prog_ptr=0xf7bc+domain_id*0x1c
raw_prog=u32(prog_ptr)
smu_win_base=(u32(0x17160)+0x200)
smn_prog=smu_win_base+(raw_prog & u32(0x17134))
smn_poll=smu_win_base+((raw_prog+0x24)&u32(0x17134))
chk(selector_target==loop_target==0x140b0,'selector 11 target slot aliases consumer loop slot 10 at 0x140B0')
chk(domain_ptr==0x13f1c and domain_id==0x18,'selector 11 maps to internal domain ID 0x18')
chk(desc_base==0xfa48 and group==6,'domain 0x18 descriptor is Group 6')
chk(prog_ptr==0xfa5c and raw_prog==0x6d150,'domain 0x18 program pointer contains raw offset 0x6D150')
chk(u32(0x17134)==0xfffff and u32(0x17160)==0x010ffe00 and smu_win_base==0x01100000,'0x235C8 aperture base/mask resolve to 0x01100000')
chk(smn_prog==0x0116d150 and smn_poll==0x0116d174,'selector 11 resolves to SMN-window program/poll addresses 0x0116D150/174')
chk(not (0x5afff<raw_prog<=0x5b7ff),'selector 11 is outside the 0x235C8 second-core IPC interval')
# Adjacent group-5 selectors are rejected by the exact compare branches; the next group-5 selector remains allowed.
def resolve_index(n):
    di=u32(0x13ef4+(n-1)*4)
    return di, u8(0xf7a8+di*0x1c), u32(0xf7bc+di*0x1c)
d12,g12,r12=resolve_index(12); d13,g13,r13=resolve_index(13); d14,g14,r14=resolve_index(14)
chk((d12,g12,r12)==(0x13,5,0x6c900),'selector 12 maps Group5 domain 0x13 and matches handler reject constant')
chk((d13,g13,r13)==(0x14,5,0x6c928),'selector 13 maps Group5 domain 0x14 and matches handler reject bound 0x14')
chk((d14,g14,r14)==(0x15,5,0x6c950),'selector 14 maps Group5 domain 0x15 and passes the two visible ID filters')
# No directly selectable Q3 1D IDs for the dedicated DF-table descriptors 0x0E..0x12.
dynamic_ids=[u32(0x13ef4+i*4) for i in range(20)]
df_ids=set(range(0x0e,0x13))
chk(not (set(dynamic_ids)&df_ids),'Q3 1D dynamic ID set has no direct DF descriptors 0x0E..0x12')
# Scaling path: request is floated unchanged in 2EA08, then 2E788 multiplies by 0.001 before 23C78.
chk(u32(0x18240)==0x16f50 and abs(f32(0x16f50)-0.001)<1e-9,'target scale pointer 0x18240 -> 0x16F50 = 0.001f')
chk(abs(f32(0x17924)-0.1)<1e-6 and abs(f32(0x17928)-256.0)<1e-6,'23C78 multiplies decoded group-base by 0.1 and 256.0')
chk(u32(0x17460)==0x37800000,'U9.16 group-base fractional scale is 2^-16')
chk(abs(f32(0xf718))<1e-9,'Group6 U9.16 base word in static image is zero; runtime initialized base remains unknown')
# Compare the exact chosen address to the older slot map without treating it as a semantic-name proof.
slotmap=json.loads(Path('evidence/firmware-audit/20260914-smu-address-trace/slot-domain-map.json').read_text())
slot24=[x for x in slotmap['slots'] if x.get('index')==24]
chk(len(slot24)==1 and slot24[0]['domain_index']==6 and slot24[0]['programming_address']=='0x6d150' and slot24[0]['semantic_name'] is None,'prior Robin3 slot24 map shares raw address/domain6 but leaves semantic_name null')
result={
  'status':'PASS','checks':len(checks),'ghidra_byte_matched_instructions':len(records),
  'queue3_0x1d':{'selector_rule':'high16 index 1..20; zero/>20 status 0xFF','deny_ids':['0x13','0x14'],'denied_status':'status 1 with return data 0xFFFFFFFF','accepted_example':{'selector_index':selector,'array_entry':loop_i,'target_slot':hex(selector_target),'domain_id':hex(domain_id),'internal_group':group,'raw_program_offset':hex(raw_prog),'smu_window_program':hex(smn_prog),'smu_window_poll':hex(smn_poll),'status':1},'neighbor_selectors':{'12':{'domain':hex(d12),'rejected':True},'13':{'domain':hex(d13),'rejected':True},'14':{'domain':hex(d14),'rejected':False}},'scaling':{'low16':'integer -> ufloat.s','target_scale':'*0.001f','group_base':'U9.16 -> float','vco_factor':'*0.1f*256','ratio_helper':'0x3ACF8 software float divide','encoder':'truncate + 0x3F -> 0x23ECC divider code','unit_label':'not encoded/proven; no MHz claim'},'df_descriptors_directly_selected':False},
  'hardware_name_search':{'result':'historical slot/domain labels only; no physical clock name found in the selected local symbol/source corpus','same_address_old_map':'slot 24 / internal domain_index 6 / semantic_name=null (Robin3 map; corroboration only)'},
  'remaining_boundary':'which physical clock the Group6 domain-0x18 register controls; caller/provider source and runtime value of the Group6 U9.16 base; external unit/MCLK-UCLK-FCLK identity',
  'baseline':{'rom_sha256':hashlib.sha256(rom).hexdigest(),'smu_sha256':hashlib.sha256(b).hexdigest(),'AmdSetup+0x316':'0x24 at ROM 0x7E5'},
}
Path('evidence/firmware-audit/20260921-smu-domain-selector/selector-result.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,sort_keys=True))
