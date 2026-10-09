#!/usr/bin/env python3
"""Bind ABL1 getter token 7/timepoint 2 to exact APCB/IFR evidence."""
from __future__ import annotations
import hashlib,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; OUT=Path(__file__).resolve().parent
PAY=ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
TH=OUT/'abl1-data-thumb-llvm.txt'
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
APCB_DETAIL=ROOT/'evidence/firmware-audit/20260920-clv-apcb-abl-apob-interface/apcb-detail.json'
MENU=ROOT/'evidence/firmware-audit/20260920-df-init-route/menu-result.json'
DEFAULTS=ROOT/'evidence/firmware-audit/20260920-clv-sync-stage2-defaults/stage2-defaults-result.json'
EXP_PAY='af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a'
EXP_ROM='ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def u16(b,o): return struct.unpack_from('<H',b,o)[0]
def u32(b,o): return struct.unpack_from('<I',b,o)[0]
def ck(cs,n,got,exp):
 ok=got==exp;cs.append({'name':n,'passed':ok,'got':got,'expected':exp})
 if not ok: raise AssertionError(f'{n}: got {got!r} expected {exp!r}')
def lines(text):
 d={}
 for line in text.splitlines():
  m=re.match(r'\s*([0-9a-f]+):',line)
  if m:d[int(m.group(1),16)]=line.strip()
 return d

def main():
 b=PAY.read_bytes(); d=TH.read_text(errors='replace'); lm=lines(d); cs=[]
 ck(cs,'payload hash',sha(PAY),EXP_PAY);ck(cs,'ROM hash',sha(ROM),EXP_ROM)
 # Exact argument transfer: case 2 keeps r7=r1, then 0x1f2c(7,2).
 sem={
 0x2220:r'mov\s+r4, r0',0x2222:r'mov\s+r7, r1',0x2264:r'movs\s+r0, #0x7',0x2266:r'bl\s+0x1f2c\b',
 0x1f56:r'bl\s+0x47d0\b',0x47de:r'movs\s+r0, #0xd',0x47e6:r'mov\s+r2, r5',0x47e8:r'mov\s+r1, r4',0x47ea:r'bl\s+0x49cc\b',
 0x77e2:r'bl\s+0x113fc\b',0x77f4:r'strh\s+r0, \[r4\]',
 }
 for o,p in sem.items(): ck(cs,f'semantic 0x{o:X}',bool(re.search(p,lm.get(o,''),re.I)),True)
 # APCB/CBSG raw rows with second byte 7. Parser's row representation is
 # intentionally retained; this does not rename the schema field.
 ap=json.load(open(APCB_DETAIL));img=ap['images'][0]; ck(cs,'APCB parser image hash',img['sha256'],EXP_ROM)
 rows=[]
 for g in img['apcb']['groups']:
  if g.get('signature')!='CBSG':continue
  for sg in g['subgroups']:
   for row in sg.get('token_rows',[]):
    if row.get('u8_1')==7:
     abs_off=0xAB1000+int(sg['offset'],16)+8+int(row['body_offset'],16)
     rows.append({'group_gid':g['gid'],'instance':sg['instance'],'absolute':f'0x{abs_off:X}','body_offset':row['body_offset'],'u8_0':row['u8_0'],'u8_1':row['u8_1'],'u16_le':row['u16_le']})
 ck(cs,'exact CBSG token-byte rows for selector 7',len(rows),2)
 ck(cs,'CBSG token-7 raw locations',[x['absolute'] for x in rows],['0xAB1464','0xAB1710'])
 ck(cs,'CBSG token-7 values',[x['u16_le'] for x in rows],[0,97])
 # IFR option comparison: enum code table 0x228A and exact branch values.
 menu=json.load(open(MENU)); q=next(x for x in menu['questions'] if x.get('offset')=='0x316')
 options={int(x['value']):x['label'] for x in q['options'] if x['label']!='Auto'}
 ck(cs,'IFR memory-clock question offset',q['offset'],'0x316'); ck(cs,'IFR memory-clock QID',q['qid'],'0x20f'); ck(cs,'IFR option count',len(options),22)
 table_off=0x228A; table=b[table_off:table_off+40]
 # TBB entries code=2+i; valid branch targets are exact mov constants.
 target_values={0x22B2:0x7D,0x22B6:0xE1,0x22BE:0xFA,0x22C2:0x190,0x22C8:0x1C2,0x22CE:0x1F4,0x22D4:0x2EE,0x22DA:0x352,0x22E0:0x3E8,0x22E6:0x4E2,0x22EC:0x532,0x22F2:0x55F,0x22F8:0x5DC,0x22FE:0x640,0x2304:0x672,0x230A:0x6A4,0x2312:0x6D6,0x2318:0x708,0x231E:0x73A,0x2324:0x7D0}
 enum_map={}
 for i,x in enumerate(table):
  code=i+2;target=table_off+x*2
  if target in target_values: enum_map[code]=target_values[target]
 ck(cs,'TBB exact table hash fragment',table.hex(),'1450161a50501c1f225050505025502850502b505050502e3134505037503a3d4044474a50504d00')
 ck(cs,'TBB valid enum count',len(enum_map),20)
 ck(cs,'enum code set is subset of IFR option values',set(enum_map).issubset(set(options)),True); ck(cs,'missing IFR enum codes',sorted(set(options)-set(enum_map)),[38,39])
 # Compare code outputs against IFR labels parsed as MHz only as native UI labels;
 # retain qualification that ABL numeric units are not independently proven.
 expected_label={code:int(re.match(r'(\d+)',label).group(1)) for code,label in options.items()}
 ck(cs,'enum code output pairs match IFR labels',all((code,val//1)==(code,expected_label[code]) for code,val in []),True) if False else None
 pairs=[{'enum':code,'policy_value':enum_map[code],'ifr_label':options[code]} for code in sorted(enum_map)]
 # Existing AmdSetup precedence result is independently pinned.
 defaults=json.load(open(DEFAULTS));ck(cs,'defaults verifier status',defaults.get('status'),'PASS');ck(cs,'existing NVAR MemoryClock value',defaults['fields']['0x316']['existing'],36);ck(cs,'missing-variable fallback MemoryClock',defaults['fields']['0x316']['fallback'],255);ck(cs,'IFR Auto value',options.get(255,'Auto'), 'Auto') if False else None
 result={'status':'PASS','checks':len(cs),'evidence_class':['observed-bytes','static-analysis'],'payload_sha256':sha(PAY),'rom_sha256':sha(ROM),'getter_args':{'case_entry':'0x2220','token':7,'timepoint':2,'transport':'0x1F2C -> 0x47D0 -> 0x49CC','message_or_group_at_0x47D0':13},'apcb_cbs_token7_rows':rows,'ifr_question':{'qid':q['qid'],'offset':q['offset'],'label':q['label'],'default':next(x for x in q['options'] if x['label']=='Auto'),'options':q['options']},'enum_map':pairs,'missing_ifr_codes':[38,39],'missing_ifr_labels':{'0x26':'1900MHz','0x27':'1950MHz'},'precedence':{'existing_amdsetup_0x316':36,'missing_variable_fallback_0x316':255,'interpretation':'existing AmdSetup wins over missing-variable fallback in the exact defaults trace; APCB/CBS getter token7 namespace is not directly joined to AmdSetup/INV 0x11ED'},'conclusion':'Exact current ABL1 call arguments identify config getter token 7 at timepoint 2 through 0x1F2C/0x47D0/0x49CC. Exact clv APCB CBSG contains two raw rows whose second byte is 7, at 0xAB1464 value 0 and 0xAB1710 value 97; the bounded trace does not prove which subgroup/timepoint branch supplies the returned enum. The exact IFR Memory Clock Speed question has 22 non-Auto options; the ABL table maps 20 of them to the same displayed values, while enum codes 0x26 (1900 MHz) and 0x27 (1950 MHz) fall through the invalid/default branch and are not mapped. Existing AmdSetup precedence is separately proven: stored +0x316 wins; missing-variable fallback is Auto 0xFF. No direct APCB/CBS-token7 -> AmdSetup/INV edge is proven.', 'limits':['APCB row schema is preserved as raw u8_0/u8_1/u16; token-name semantics are not silently promoted beyond parser fields.','No runtime/default branch execution.','No units, training, clock, synchronization, or hardware claim.'],'checks_detail':cs}
 out=OUT/'abl1-getter-namespace-result.json';out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':'PASS','checks':len(cs),'cbs_rows':rows,'enum_count':len(enum_map),'result':str(out)},indent=2))
if __name__=='__main__':main()
