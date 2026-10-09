#!/usr/bin/env python3
"""Bounded exact-CLV selector->consumer->SMN write slice; no table census."""
from pathlib import Path
import hashlib, json, re, struct

ROM=Path('evidence/donor/retroweb-20260916/BC250_5.00_clv.bin')
SMU=Path('import/from-windows/Users/kukuruza/tmp_bc250/upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5')
ASM=Path('evidence/firmware-audit/20260921-smu-domain-selector/q3-aligned-ghidra.txt')
SLOTMAP=Path('evidence/firmware-audit/20260914-smu-address-trace/slot-domain-map.json')
NAME_SEARCH=Path('evidence/firmware-audit/20260921-smu-domain-selector/register-symbol-search.stdout')
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
# Whole-program exactness line and byte agreement for every listed Ghidra instruction.
chk(listing.startswith('PASS: entire loaded program memory equals clv-matching robin-5 body, bytes=262400'), 'Ghidra program memory matches exact Robin-5 payload')
records=[]
for line in listing.splitlines():
    m=re.match(r'^([0-9a-fA-F]{8})\s+([0-9a-fA-F]+)\s+(.+)$',line)
    if not m: continue
    off=int(m.group(1),16); op=bytes.fromhex(m.group(2)); asm=m.group(3).strip()
    assert b[off:off+len(op)]==op,(hex(off),op.hex(),b[off:off+len(op)].hex(),asm)
    records.append((off,op.hex(),asm))
chk(len(records)>250, 'bounded aligned Ghidra instruction listing matches exact payload bytes')
rows={a:(raw,asm) for a,raw,asm in records}
def ins(addr,raw,needle):
    got=rows.get(addr)
    chk(got is not None and got[0]==raw and needle in got[1], f'{addr:#x}: {needle}')
# Handler bound / per-domain denial; this is the new discriminator missed by old verifier.
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
ins(0x2ea5f,'a554d2','call8 0x00000fa8')
ins(0x2ea68,'a557d2','call8 0x00000fe4')
ins(0x2ea6f,'a553d2','call8 0x00000fa8')
chk('0x2EA10 movi.n a12,0x14' in listing and '0x2EA17 bltu a12,a10' in listing, 'Ghidra disassembly confirms selector max is 20, not 12')
# One accepted selector, and the two blocked adjacent Group-5 domains.
def selector_info(n):
    i=n-1
    domain_ptr=0x13ef4+i*4
    did=u32(domain_ptr)
    desc=0xf7a8+did*0x1c
    group=u8(desc)
    prog_ptr=0xf7bc+did*0x1c
    raw=u32(prog_ptr)
    return {'selector':n,'loop_i':i,'target_slot':0x1402c+n*12,'consumer_slot':0x14038+i*12,
            'domain_ptr':domain_ptr,'domain_id':did,'group_desc':desc,'group_id':group,
            'program_ptr':prog_ptr,'program_offset':raw}
s11=selector_info(11); s12=selector_info(12); s13=selector_info(13); s14=selector_info(14)
chk(s11['target_slot']==s11['consumer_slot']==0x140b0,'selector 11 target write joins loop consumer at 0x140B0')
chk(s11['domain_ptr']==0x13f1c and s11['domain_id']==0x18,'selector 11 consumer reads domain ID 0x18')
chk(s11['group_desc']==0xfa48 and s11['group_id']==6,'domain ID 0x18 resolves internal Group 6')
chk(s11['program_ptr']==0xfa5c and s11['program_offset']==0x6d150,'domain 0x18 descriptor program pointer is raw offset 0x6D150')
chk((s12['domain_id'],s12['group_id'],s12['program_offset'])==(0x13,5,0x6c900),'selector 12 would map Group 5 domain 0x13, explicitly rejected')
chk((s13['domain_id'],s13['group_id'],s13['program_offset'])==(0x14,5,0x6c928),'selector 13 would map domain 0x14, equal to handler bound and rejected')
chk((s14['domain_id'],s14['group_id'],s14['program_offset'])==(0x15,5,0x6c950),'selector 14 maps Group 5 domain 0x15 and passes visible ID filters')
# 2E788 and 235C8 demonstrate scaling, divider encoding, SMN destination and poll.
ins(0x2e7f3,'252df5','call8 0x00023ac4')
ins(0x2e7f6,'8192a6','l32r a8,0x00018240')
ins(0x2e7fc,'630800','lsi f6,a8,0x0')
ins(0x2e7ff,'60452a','mul.s f4,f5,f6')
ins(0x2e805,'2547f5','call8 0x00023c78')
ins(0x2e821,'e506f5','call8 0x00023890')
ins(0x238af,'522595','l32i a5,a5,0x254')
ins(0x2392e,'a5c9ff','call8 0x000235c8')
ins(0x23939,'92c524','addi a9,a5,0x24')
ins(0x23944,'d22980','l32i a13,a9,0x200')
ins(0x23c83,'a598ff','call8 0x0002360c')
ins(0x23c86,'9127cf','l32r a9,0x00017924')
ins(0x23c89,'8127cf','l32r a8,0x00017928')
ins(0x23ca4,'250517','call8 0x0003acf8')
ins(0x23caa,'00a7ea','utrunc.s a10,f7,0x0')
ins(0x23cad,'a2ca3f','addi a10,a10,0x3f')
ins(0x23cb0,'a52100','call8 0x00023ecc')
ins(0x3acf8,'362100','entry a1,0x10')
ins(0x3ad01,'7032fa','div0.sf f3,f2')
ins(0x3ad49,'60027a','divn.sf f0,f2,f6')
ins(0x235d0,'b1d9ce','l32r a11,0x00017134')
ins(0x235d5,'a1e2ce','l32r a10,0x00017160')
ins(0x235fc,'65f1f7','call8 0x0001b514')
ins(0x23604,'326e80','s32i a3,a14,0x200')
chk(u32(0x18240)==0x16f50 and abs(f32(0x16f50)-0.001)<1e-9,'request scaling literal 0x18240 -> 0x16F50 is 0.001f')
chk(abs(f32(0x17924)-0.1)<1e-6 and abs(f32(0x17928)-256.0)<1e-6,'23C78 scales decoded group base by 0.1 and 256.0 before divider conversion')
chk(u32(0x17460)==0x37800000,'U9.16 group-base converter uses 2^-16 fraction literal')
chk(u32(0x17134)==0xfffff and u32(0x17160)==0x010ffe00,'235C8 SMN mask/base literals match')
chk(u32(0x178b8)==0x5afff and u32(0x178bc)==0x5b7ff,'235C8 second-core IPC interval literals match')
window_base=u32(0x17160)+0x200
smn_program=window_base+(s11['program_offset']&u32(0x17134))
smn_poll=window_base+((s11['program_offset']+0x24)&u32(0x17134))
chk(window_base==0x01100000 and smn_program==0x0116d150 and smn_poll==0x0116d174,'selector 11 SMU-window program/poll offsets are 0x0116D150/0x0116D174')
chk(not (u32(0x178b8)<s11['program_offset']<=u32(0x178bc)),'selector 11 uses direct SMN store branch, not IPC range')
# Group6 base coefficient is run-time/initialised input; ROM zero does not justify a numeric divider prediction.
group6_base=0xf568+6*0x48
chk(u32(group6_base)==0,'Group 6 rate/base word is zero in static image; runtime coefficient unresolved')
# Domain IDs used by the dedicated DF selector are a separate namespace; the dynamic array does not directly select 0x0E..0x12.
dynamic_ids=[u32(0x13ef4+i*4) for i in range(20)]
chk(not (set(dynamic_ids)&set(range(0x0e,0x13))),'Q3 1D dynamic domain list has no direct DF table IDs 0x0E..0x12')
# Prior exact map corroborates address/domain6 but intentionally provides no physical semantic name.
slotmap=json.loads(SLOTMAP.read_text()); smap=[x for x in slotmap['slots'] if x.get('index')==24]
chk(len(smap)==1 and smap[0]['domain_index']==6 and smap[0]['programming_address']=='0x6d150' and smap[0]['semantic_name'] is None,'prior Robin3 map ties slot24 to domain-index6/address0x6D150 but leaves semantic name null')
chk(NAME_SEARCH.exists() and NAME_SEARCH.read_text()=='','selected local symbol/docs address search returned no hits')
result={
 'status':'PASS','checks':len(checks),'byte_matched_ghidra_instructions':len(records),
 'selector_example':{'mailbox':'Queue ID 3 msg 0x1D','status_accepted':1,'selector_index':11,'target_slot':'0x140B0','internal_domain_id':'0x18','internal_group_id':6,'descriptor_group_address':'0xFA48','program_pointer_address':'0xFA5C','raw_program_offset':'0x6D150','SMU_window_program':'0x0116D150','SMU_window_poll':'0x0116D174','path':'0x2EA08 -> 0x2E788 -> 0x23AC4/0x23C78 -> 0x23890 -> 0x235C8'},
 'filter':{'high16_index_valid':'1..20','zero_or_gt20':'status 0xFF','selector12':'domain0x13 -> return data 0xFFFFFFFF/status1','selector13':'domain0x14 -> return data 0xFFFFFFFF/status1','selector14':'domain0x15 Group5 passes the visible ID filters'},
 'scale_path':{'low16':'ufloat.s (raw unsigned integer converted to float)','0x18240':'pointer 0x16F50 = 0.001f','group_base':'U9.16 -> float via 0x2360C','factors':'0.1f * 256.0f','ratio_helper':'0x3ACF8 soft-float divide instructions','to_program_code':'truncate + 0x3F -> 0x23ECC internal divider/DID encoder','unit':'no explicit MHz label; numeric scale alone does not assign MCLK/UCLK/FCLK'},
 'hardware_name':'unresolved; local firmware supplies internal Group 6 and SMN-window offsets; bounded local symbolic-address search has no hits; prior Robin3 slot24 map semantic_name=null',
 'no_direct_df_selector':'Q3 1D dynamic-ID array contains no descriptors 0x0E..0x12 used by dedicated DF P-state path',
 'baseline':{'rom_sha256':hashlib.sha256(rom).hexdigest(),'smu_sha256':hashlib.sha256(b).hexdigest(),'AmdSetup+0x316':'0x24 @ 0x7E5'},
 'first_unresolved':'physical clock identity, runtime Group6 base/scale, explicit unit, and any MCLK/UCLK/FCLK/crossing selector'
}
Path('evidence/firmware-audit/20260921-smu-domain-selector/selector-result.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,sort_keys=True))
