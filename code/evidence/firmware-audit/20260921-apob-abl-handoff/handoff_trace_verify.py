#!/usr/bin/env python3
"""Targeted static cross-stage trace for native MemoryClockSpeed handoff.

This follows token 0x11ED (AmdSetup+0x316), not the already closed 0x1204
serializer/HOB boundary. It verifies a positive APOB-PPI GUID join, the exact
ABL1 APCB/CBS getter path, and the open SMU-PEI producer copy. It reports the
first missing byte-backed edge without assigning runtime semantics.
"""
from __future__ import annotations
import hashlib, json, struct, uuid
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
CENSUS = ROOT/'evidence/firmware-audit/20260919-inv-token-consumers/census.json'
ROM = ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
ABL1 = ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
PMFW = ROOT/'import/from-windows/Users/kukuruza/tmp_bc250/recon/robin5_psp_bodies/SMU_OFFCHIP_FW~0x8_0.58.7.1.body'
APCB_DETAIL = ROOT/'evidence/firmware-audit/20260920-clv-apcb-abl-apob-interface/apcb-detail.json'
MODS = ROOT/'evidence/firmware-audit/20260919-inv-token-consumers'
EXP = {
    'rom':'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8',
    'abl1':'af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a',
    'pmfw':'cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37',
    'CbsBasePei':'6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77',
    'AmdNbioSmuV10Pei':'905b8be68afd1dce5453acef8273cbf94bdae6d41823c25438ace286348e2c80',
    'AmdMemAm4Pei':'1ef4e7b944672a9a48b6fcb16c4d35cb6d23bb8306429dc3eb10ee1d0c7bb5f8',
    'AmdMemoryHobInfoPeim':'aad3f828ccef4cf8878cad8c9ee1e47743748f652a1ef54af04de759983b4619',
}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def check(cs,name,got,exp):
    ok=got==exp; cs.append({'name':name,'status':'PASS' if ok else 'FAIL','got':got,'expected':exp})
    if not ok: raise AssertionError(f'{name}: {got!r} != {exp!r}')
def raw_offset(row,rva):
    for sec in row['sections']:
        if sec['rva'] <= rva < sec['rva']+sec['size']:
            return rva-sec['rva']+sec['raw']
    raise ValueError(f'RVA not in sections: {row.get("ui")} {rva:#x}')
def at(row,b,rva,n):
    o=raw_offset(row,rva); return b[o:o+n]
def guid_at(row,b,ptr):
    rva=ptr-int(row['imagebase']); o=raw_offset(row,rva)
    return b[o:o+16], rva, o

def main():
    census=json.loads(CENSUS.read_text()); rows={r['ui']:r for r in census['records'] if r.get('ui')}
    rom=ROM.read_bytes(); abl=ABL1.read_bytes(); pmfw=PMFW.read_bytes(); checks=[]
    check(checks,'ROM hash',sha(ROM),EXP['rom']); check(checks,'ROM size',len(rom),0x1000000)
    check(checks,'ABL1 hash',sha(ABL1),EXP['abl1']); check(checks,'PMFW hash',sha(PMFW),EXP['pmfw'])
    bodies={}
    for name in ['CbsBasePei','AmdNbioSmuV10Pei','AmdMemAm4Pei','AmdMemoryHobInfoPeim']:
        row=rows[name]; p=MODS/(row['stem']+'.bin'); bodies[name]=p.read_bytes()
        check(checks,f'{name} hash',sha(p),EXP[name])

    # Native MemoryClockSpeed 0x11ED writers: TE RVAs translated through the
    # module section map (RVA-0x190 is implied by its section headers).
    cb=rows['CbsBasePei']; cbs=bodies['CbsBasePei']; sm=rows['AmdNbioSmuV10Pei']; smu=bodies['AmdNbioSmuV10Pei']
    check(checks,'CbsBasePei INV 0x11ED header',at(cb,cbs,0x9837,5).hex(),'baed110000')
    check(checks,'CbsBasePei Setup+0x316 load',at(cb,cbs,0x9857,6).hex(),'8a8216030000')
    check(checks,'CbsBasePei INV value store',at(cb,cbs,0x985d,3).hex(),'884103')
    check(checks,'AmdNbioSmuV10Pei INV 0x11ED header',at(sm,smu,0xb8b7,5).hex(),'baed110000')
    check(checks,'AmdNbioSmuV10Pei Setup+0x316 load',at(sm,smu,0xb8d7,6).hex(),'8a8216030000')
    check(checks,'AmdNbioSmuV10Pei INV value store',at(sm,smu,0xb8dd,3).hex(),'884103')
    setup=0x4cf
    check(checks,'pinned AmdSetup+0x316 byte',rom[setup+0x316],0x24)

    # Positive APOB-PPI GUID join. AmdMem descriptor +4 and AmdMemoryHob
    # LocatePpi argument point to the same GUID bytes in their module images.
    amrow=rows['AmdMemAm4Pei']; am=bodies['AmdMemAm4Pei']; hrow=rows['AmdMemoryHobInfoPeim']; hob=bodies['AmdMemoryHobInfoPeim']
    am_guid, am_guid_rva, am_guid_raw=guid_at(amrow,am,0x09e3afc0)
    hob_guid, hob_guid_rva, hob_guid_raw=guid_at(hrow,hob,0x09eb92f4)
    check(checks,'AmdMem APOB PPI descriptor GUID pointer RVA',hex(am_guid_rva),'0x11a0')
    check(checks,'AmdMemoryHob LocatePpi GUID pointer RVA',hex(hob_guid_rva),'0x1640')
    check(checks,'AmdMem/AmdMemoryHob GUID bytes join',am_guid.hex(),hob_guid.hex())
    check(checks,'joined PPI GUID',str(uuid.UUID(bytes_le=am_guid)),'e54e6e84-020b-4081-8156-37e9c62c1ed6')
    check(checks,'AmdMem APOB service pointer push',at(amrow,am,0x8a0,5).hex(),'684cb1e309')
    check(checks,'AmdMem service argument 0xFF',at(amrow,am,0x8ca,5).hex(),'68ff000000')
    check(checks,'AmdMem service message 0x61',at(amrow,am,0x8cf,2).hex(),'6a61')
    check(checks,'AmdMem service call 0xCD9',at(amrow,am,0x8d1,5).hex(),'e803040000')
    check(checks,'AmdMem InstallPpi slot',at(amrow,am,0x3e5,3).hex(),'ff5018')
    check(checks,'AmdMem PPI +0x44 callback data',at(amrow,am,0x3d7,7).hex(),'c740446ea0e309')
    check(checks,'AmdMemoryHob LocatePpi slot',at(hrow,hob,0x277,3).hex(),'ff5020')
    check(checks,'AmdMemoryHob InstallPeiMemory slot',at(hrow,hob,0x299,3).hex(),'ff5044')
    check(checks,'AmdMemoryHob reads returned PPI +0x28',at(hrow,hob,0xad0,3).hex(),'8b4828')
    check(checks,'AmdMemoryHob reads returned PPI +0x2c',at(hrow,hob,0xad6,4).hex(),'668b482c')
    check(checks,'AmdMemoryHob reads returned PPI +0x30',at(hrow,hob,0xade,3).hex(),'8a4830'); check(checks,'AmdMemoryHob reads returned PPI +0x31',at(hrow,hob,0xae4,3).hex(),'8a4831'); check(checks,'AmdMemoryHob reads returned PPI +0x40',at(hrow,hob,0xae7,3).hex(),'8b4040')
    check(checks,'AmdMem body lacks direct 0x11ED literal',b'\xed\x11\x00\x00' not in am,True)

    # Exact ABL1 APCB/CBS provider path: a separate token 7 namespace maps
    # enum 0x24 to policy 0x708. This is a positive semantic contrast, not a
    # claim that token 7 equals native INV 0x11ED.
    check(checks,'ABL1 getter token 7',abl[0x2264:0x2266].hex(),'0720')
    check(checks,'ABL1 getter call 0x1F2C',abl[0x2266:0x226a].hex(),'fff761fe')
    check(checks,'ABL1 provider selector 0x0F',abl[0x4810:0x4812].hex(),'0f20')
    check(checks,'ABL1 provider group 0x1707',abl[0x4b0e:0x4b14].hex(),'0f2240f2621a')
    table=abl[0x228a:0x228a+40]
    check(checks,'ABL1 TBB table fragment',table.hex(),'1450161a50501c1f225050505025502850502b505050502e3134505037503a3d4044474a50504d00')
    target=0x228a+table[0x24-2]*2
    check(checks,'ABL1 enum 0x24 target',hex(target),'0x2318')
    check(checks,'ABL1 enum 0x24 policy value 0x708',abl[target:target+4].hex(),'40f20870')
    check(checks,'ABL1 body lacks direct 0x11ED literal',b'\xed\x11\x00\x00' not in abl,True)

    # PMFW is a bounded carrier check, not an absence proof for computed/DMA paths.
    check(checks,'PMFW lacks $INV marker',b'$INV' not in pmfw,True)
    check(checks,'PMFW lacks NVTB marker',b'NVTB' not in pmfw,True)
    check(checks,'PMFW lacks direct 0x11ED literal',b'\xed\x11\x00\x00' not in pmfw,True)
    ap=json.loads(APCB_DETAIL.read_text()); check(checks,'APCB parser image hash',ap['images'][0]['sha256'],EXP['rom'])
    raw_rows=[]
    for g in ap['images'][0]['apcb']['groups']:
        if g.get('signature')!='CBSG': continue
        for s in g.get('subgroups',[]):
            for r in s.get('token_rows',[]):
                if r.get('u8_1')==7: raw_rows.append({'instance':s['instance'],'absolute':hex(0xAB1000+int(s['offset'],16)+8+int(r['body_offset'],16)),'u8_0':r['u8_0'],'u8_1':r['u8_1'],'u16_le':r['u16_le']})
    check(checks,'APCB raw CBSG rows with second byte 7',len(raw_rows),2)

    result={'status':'PASS','checks':{'passed':sum(x['status']=='PASS' for x in checks),'failed':sum(x['status']=='FAIL' for x in checks),'total':len(checks)},'evidence_class':['observed-bytes','static-analysis'],'inputs':{'rom':{'path':str(ROM),'sha256':sha(ROM),'size':len(rom)},'census':{'path':str(CENSUS),'sha256':sha(CENSUS)},'abl1':{'path':str(ABL1),'sha256':sha(ABL1),'size':len(abl)},'pmfw':{'path':str(PMFW),'sha256':sha(PMFW),'size':len(pmfw)}},'trace':{'native_0x11ed':{'field':'AmdSetup+0x316','pinned_value':'0x24','preserved_label':'1800MHz (UI label only)','cbs_rvas':['0x9837','0x9857','0x985D'],'smu_pei_rvas':['0xB8B7','0xB8D7','0xB8DD']},'apob_to_memory_hob':{'amd_mem_service':{'pointer':'0x9E3B14C','message':'0x61','argument':'0xFF','call_rva':'0x8D1'},'ppi_guid':'e54e6e84-020b-4081-8156-37e9c62c1ed6','amd_mem_guid_rva':'0x11A0','amd_mem_guid_raw':'0x1008','memory_hob_guid_rva':'0x1640','memory_hob_guid_raw':'0x14A8','ppi_fields':['+0x28','+0x2C','+0x30','+0x31','+0x40'],'install_pei_memory_rva':'0x299'},'abl1_provider':{'getter_token':7,'timepoint':2,'path':['0x2264 -> 0x1F2C','0x4810 selector 0x0F','0x4B0E group 0x1707'],'enum_0x24_policy_value':'0x708','policy_value_dec':1800},'apcb_raw_token7_contrast':raw_rows,'smu_carrier':{'pmfw_marker_hits':{'$INV':0,'NVTB':0},'direct_0x11ed_literal_hits':0}},'first_missing_boundary':{'location':'between Cbs/AmdNbioSmuV10Pei `$INV 0x11ED` buffer production and AmdMemAm4Pei APOB service/PPI population; downstream ABL1 provider table remains separate','statement':'The exact open UEFI writers preserve Setup+0x316=0x24 in `$INV 0x11ED`. AmdMemAm4Pei requests APOB service 0x9E3B14C/0x61/0xFF and installs the PPI identified by GUID e54e6e84-020b-4081-8156-37e9c62c1ed6; AmdMemoryHobInfoPeim locates that same GUID, reads returned fields, and calls InstallPeiMemory. Exact ABL1 separately reads APCB/CBS token 7 and maps enum 0x24 to 0x708. No byte-backed edge identifies `$INV 0x11ED` as an input to the APOB service, the joined PPI fields, ABL1 runtime context, or SMU PMFW. The first missing boundary is the APOB service/PPI population input, before training/clock actuator semantics.','not_repeated':'The existing UclkDiv1M0 `$INV 0x1204` serializer/HOB path was not checked.'},'limits':['Static bytes only; no APOB service, PPI, ABL1, SMU, firmware runtime or hardware execution.','APCB rows with u8_1=7 are retained as raw parser fields and are not renamed to native `$INV` token 0x11ED.','PMFW marker no-hits are bounded carrier evidence, not proof against computed, indirect or DMA delivery.'],'checks_detail':checks}
    out=OUT/'apob-abl-handoff-result.json'; out.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps({'status':'PASS','checks':len(checks),'result':str(out),'first_missing_boundary':result['first_missing_boundary']},indent=2))
if __name__=='__main__': main()
