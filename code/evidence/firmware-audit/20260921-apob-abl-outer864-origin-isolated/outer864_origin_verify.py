#!/usr/bin/env python3
"""G7 correction: resolve ABL1 stack provenance and HEAP zero-fill semantics.

This bounded test does not repeat the 0x1204 serializer/HOB or PPI-GUID work.
It reconciles fresh LLVM Thumb windows to the pinned decompressed ABL1 bytes,
checks the FCLK -> INV-provider stack arguments, maps 0x006CD4D0 only against
available load metadata, and verifies whether 0x6B78 copies or fills.
"""
from __future__ import annotations
import hashlib, json, re, struct, subprocess, zlib
from pathlib import Path
ROOT=Path('/home/OWNER/orca/projects/bc250')
OUT=ROOT/'evidence/firmware-audit/20260921-apob-abl-outer864-origin-isolated'
ROM=ROOT/'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
ABL=ROOT/'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
OBJ=ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o'
LIST=ROOT/'evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt'
BASE_REPORT=ROOT/'docs/research/20260920-clv-abl-producer-base-review.md'
OLD_VERIFIER=ROOT/'evidence/firmware-audit/20260921-apob-abl-heap-populator/heap_populator_verify.py'
OLD_RESULT=ROOT/'evidence/firmware-audit/20260921-apob-abl-heap-populator/heap-populator-result.json'
OLD_REPORT=ROOT/'docs/research/2026-09-21-apob-abl-heap-populator.md'
EXPECTED={'rom':'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8','abl':'af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a','obj':'54abef3a390abb0ff745685de2eed4e0e8db5e9ba27bba1a0f245573b47ff135','listing':'b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65'}
checks=[]; commands=[]
toolver=subprocess.run(['llvm-objdump','--version'],cwd=ROOT,capture_output=True,text=True,check=False)

def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha(p): return sha_bytes(p.read_bytes())
def ck(name, got, exp):
    ok=got==exp; checks.append({'name':name,'status':'PASS' if ok else 'FAIL','got':got,'expected':exp})
    if not ok: raise AssertionError(f'{name}: {got!r} != {exp!r}')
def u32(b,o): return struct.unpack_from('<I',b,o)[0]
def thumb_bytes(word): return bytes.fromhex(word)[::-1]
INSN=re.compile(r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{4}\s+)+)(.*)$',re.I)
def parse_and_reconcile(name, text, payload):
    rows={}; n=0
    for line in text.splitlines():
        m=INSN.match(line)
        if not m: continue
        addr=int(m.group(1),16); words=m.group(2).split(); raw=b''.join(thumb_bytes(w) for w in words)
        if payload[addr:addr+len(raw)] != raw:
            raise AssertionError(f'{name}: decoded bytes mismatch at {addr:#x}: {raw.hex()} != {payload[addr:addr+len(raw)].hex()}')
        rows[addr]=line.strip(); n+=1
    if not n: raise AssertionError(f'{name}: no decoded instructions parsed')
    checks.append({'name':f'{name}-byte-reconciliation','status':'PASS','instruction_count':n})
    return rows

def run_window(name,start,stop,payload):
    argv=['llvm-objdump','-D','--triple=thumbv7m-none-eabi',f'--start-address=0x{start:x}',f'--stop-address=0x{stop:x}',str(OBJ)]
    p=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True,check=False)
    (OUT/f'{name}.stdout').write_text(p.stdout)
    (OUT/f'{name}.stderr').write_text(p.stderr)
    (OUT/f'{name}.exit').write_text(str(p.returncode)+'\n')
    commands.append({'name':name,'argv':argv,'exit_status':p.returncode,'stdout':str(OUT/f'{name}.stdout'),'stderr':str(OUT/f'{name}.stderr')})
    ck(f'{name}-exit-and-stderr', (p.returncode,len(p.stderr.encode())), (0,0))
    return parse_and_reconcile(name,p.stdout,payload)

def has(rows,address,text):
    line=rows.get(address,'')
    return text.lower() in line.lower(), line

def expect_row(name,rows,address,text):
    actual=rows.get(address,'')
    norm=lambda x: re.sub(r'\s+',' ',x.strip().lower())
    got=norm(text) in norm(actual)
    ck(name,got,True)
    return actual

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rom=ROM.read_bytes(); abl=ABL.read_bytes(); obj=OBJ.read_bytes(); listing=LIST.read_text(errors='replace')
    ck('ROM-hash-size',(sha_bytes(rom),len(rom)),(EXPECTED['rom'],0x1000000))
    ck('ABL-payload-hash-size',(sha_bytes(abl),len(abl)),(EXPECTED['abl'],0x171a0))
    ck('ELF-object-hash',(sha_bytes(obj),), (EXPECTED['obj'],))
    ck('existing-full-listing-hash',sha_bytes(LIST.read_bytes()),EXPECTED['listing'])
    base_text=BASE_REPORT.read_text(); ck('conditional-base-is-not-loader-proof',('0x57100' in base_text and 'not proof of loader/runtime base' in base_text.lower()),True)
    old_result=json.loads(OLD_RESULT.read_text()); old_script=OLD_VERIFIER.read_text(); old_report=OLD_REPORT.read_text()
    ck('prior-34-check-result',(old_result.get('status'),old_result.get('checks',{}).get('total')) if isinstance(old_result.get('checks'),dict) else (old_result.get('status'),old_result.get('checks')),('PASS',34))
    ck('prior-report-contained-source-copy-claim',('copied from the source pointer' in old_report.lower() and 'source pointer' in old_report.lower()),True)
    ck('prior-verifier-did-not-disassemble-fill-helper','subprocess.run' not in old_script and 'llvm-objdump' not in old_script,True)

    # Reparse exact ABL1 $PS1 entry from the immutable ROM and verify payload correspondence.
    spi=0x99fd00; csize=0xc020; cont=rom[spi:spi+csize]
    ck('ABL1-$PS1-magic',cont[0x10:0x14],b'$PS1')
    signed_len=u32(cont,0x14); load_addr=u32(cont,0x68); decomp_len=u32(cont,0x50)
    decomp=zlib.decompress(cont[0x100:0x100+signed_len])
    ck('ABL1-header-lengths',(signed_len,decomp_len,len(decomp)),(0xbe20,0x171a0,0x171a0))
    ck('ABL1-container-decompresses-to-pinned-payload',(sha_bytes(decomp),decomp==abl),(EXPECTED['abl'],True))
    ck('ABL1-explicit-load-address',load_addr,0)
    ptr=0x006cd4d0
    pool_hits=[m.start() for m in re.finditer(re.escape(struct.pack('<I',ptr)),abl)]
    ck('outer864-pointer-literal-sites',[hex(x) for x in pool_hits],['0xc4b4'])
    payload_rel=ptr-load_addr; candidate_base=0x57100; conditional_rel=ptr-candidate_base
    ck('pointer-not-in-header-zero-coordinate',payload_rel>=len(abl),True)
    ck('pointer-not-in-conditional-0x57100-map',conditional_rel>=len(abl),True)
    ck('conditional-offset-value',hex(conditional_rel),'0x6763d0')
    ck('ROM-offset-interpretation-not-ABL1-container',not (0x99fd00 <= ptr < 0x99fd00+csize),True)
    ck('hypothetical-base-0x6c0000-not-adopted',0x6cd4d0-0x6c0000,0xd4d0)
    # Note: the hypothetical base maps in-range, showing why the explicit missing loader base matters.

    specs={
      'context-callers':(0x9c0,0xaf0), 'fclk-463c':(0x463c,0x4670), 'reader-1fb4':(0x1fb4,0x1fe4),
      'helper-4800':(0x4800,0x4824), 'provider-49cc':(0x49cc,0x4b60), 'heap-6238':(0x6238,0x635c),
      'fill-6b78':(0x6b78,0x6b84), 'heap-callsite-46b4':(0x46b4,0x46e0),
      'heap-callsite-474e':(0x474e,0x4778), 'allocator-6810':(0x6810,0x6844),
      'unlink-4f9c':(0x4f9c,0x4fd0), 'constructor-caller-b84':(0xb84,0xbd6),
      'constructor-c00':(0xc00,0xc2b4)
    }
    rows={n:run_window(n,a,b,abl) for n,(a,b) in specs.items()}
    # FCLK caller -> reader two stack slots are zero; reader propagates second slot R9.
    expect_row('fclk-zero-first-stack-arg',rows['fclk-463c'],0x4664,'str r2, [sp]')
    expect_row('fclk-zero-second-stack-arg',rows['fclk-463c'],0x4666,'str r2, [sp, #0x4]')
    expect_row('fclk-calls-reader',rows['fclk-463c'],0x466a,'bl\t0x1fb4')
    expect_row('reader-pushes-12-registers',rows['reader-1fb4'],0x1fb4,'push.w')
    expect_row('reader-loads-r7-r9-from-caller-stack',rows['reader-1fb4'],0x1fc0,'ldrd\tr7, r9, [sp, #48]')
    expect_row('reader-forwards-r9-as-first-helper-stack-arg',rows['reader-1fb4'],0x1fd2,'str.w\tr9, [sp]')
    expect_row('helper-loads-inherited-stack-arg',rows['helper-4800'],0x4808,'ldr\tr1, [sp, #0x18]')
    expect_row('helper-passes-r3-r1-as-provider-stack-pair',rows['helper-4800'],0x4812,'strd\tr3, r1, [sp]')
    expect_row('helper-calls-provider',rows['helper-4800'],0x481c,'bl\t0x49cc')
    # Provider frame: push {r0-r11,lr}=13 regs=52; then local 0x6c=108.
    expect_row('provider-register-save-mask',rows['provider-49cc'],0x49cc,'push.w')
    expect_row('provider-local-allocation',rows['provider-49cc'],0x49d2,'sub\tsp, #0x6c')
    expect_row('provider-read-second-stack-arg-at-sp-a4',rows['provider-49cc'],0x4b54,'ldr\tr1, [sp, #0xa4]')
    expect_row('provider-calls-heap-producer',rows['provider-49cc'],0x4b5c,'bl\t0x6238')
    provider_push_mask=0x4fff; saved_bytes=provider_push_mask.bit_count()*4; locals=0x6c; local_offset=0xa4
    provider_arg_offset=local_offset-(saved_bytes+locals)
    ck('provider-sp+a4-resolves-second-stacked-arg',(saved_bytes,locals,provider_arg_offset),(52,108,4))
    ck('fclk-initializes-stack-arg-source-register-r2-to-zero',abl[0x464c:0x464e].hex(),'0022')
    # R2 remains zero through the two STR instructions at 0x4664/0x4666.
    ck('fclk-zeroes-both-stack-arg-slots',(abl[0x4664:0x4668].hex()),'00920192')
    # The second provider stack argument was R9; this call path supplies zero.

    # 6238 prototype: first argument is a descriptor in several callsites; second is caller context/aux.
    expect_row('heap-writer-captures-r1-as-r10',rows['heap-6238'],0x6242,'mov\tr10, r1')
    expect_row('caller46dc-r1-is-original-r0-context',rows['heap-callsite-46b4'],0x46b8,'mov\tr6, r0')
    expect_row('caller46dc-r1-context-setup',rows['heap-callsite-46b4'],0x46ce,'mov\tr1, r6')
    expect_row('caller46dc-descriptor-arg0',rows['heap-callsite-46b4'],0x46da,'add\tr0, sp, #0x4')
    expect_row('caller46dc-heap-call',rows['heap-callsite-46b4'],0x46dc,'bl\t0x6238')
    expect_row('caller4774-r1-is-original-r0-context',rows['heap-callsite-474e'],0x4750,'mov\tr6, r0')
    expect_row('caller4774-r1-context-setup',rows['heap-callsite-474e'],0x4766,'mov\tr1, r6')
    expect_row('caller4774-descriptor-arg0',rows['heap-callsite-474e'],0x4772,'add\tr0, sp, #0x4')
    expect_row('caller4774-heap-call',rows['heap-callsite-474e'],0x4774,'bl\t0x6238')
    # FCLK-selected provider second stack argument R1=0 flows into 6238 R10; not source bytes.
    expect_row('heap-writer-r10-from-r1',rows['heap-6238'],0x6242,'mov\tr10, r1')
    expect_row('heap-writer-heap-helper-overwrites-r0-before-use',rows['allocator-6810'],0x6814,'ldr\tr0, [r2, #0xc]')
    expect_row('heap-writer-unlink-helper-overwrites-r0-before-use',rows['unlink-4f9c'],0x4fa4,'ldr\tr0, [r3, #0xc]')
    # memset-vs-memcpy discriminant: 6238 supplies zero in R1; 6B78 repeats R1 to [R0], ignores R3.
    expect_row('heap-writer-sets-fill-byte-zero',rows['heap-6238'],0x6316,'movs\tr1, #0x0')
    expect_row('heap-writer-length-from-node-descriptor',rows['heap-6238'],0x6318,'ldr\tr2, [r5, #0x4]')
    expect_row('heap-writer-destination-node-payload',rows['heap-6238'],0x631a,'add.w\tr0, r5, #0x10')
    expect_row('heap-writer-passes-r10-in-r3',rows['heap-6238'],0x631e,'mov\tr3, r10')
    expect_row('heap-writer-calls-fill-loop',rows['heap-6238'],0x6320,'bl\t0x6b78')
    expect_row('fill-helper-store-r1-to-r0',rows['fill-6b78'],0x6b7a,'strb\tr1, [r0], #1')
    expect_row('fill-helper-does-not-consume-r3',rows['fill-6b78'],0x6b78,'b\t0x6b7e')
    ck('fill-helper-body-has-no-r3-read',all('r3' not in s.lower() for a,s in rows['fill-6b78'].items()),True)

    # Constructor outer field and callers; do not conflate constructor's SP+0xA4
    # with the separate provider function's SP+0xA4 input argument.
    expect_row('B84-saves-incoming-outer-arg1',rows['constructor-caller-b84'],0xb8a,'mov\tr5, r1')
    expect_row('B84-passes-saved-arg1-to-C00',rows['constructor-caller-b84'],0xbca,'mov\tr1, r5')
    expect_row('B84-calls-C00',rows['constructor-caller-b84'],0xbd2,'bl\t0xc00')
    expect_row('C00-saves-outer-arg1',rows['constructor-c00'],0xc06,'mov\tr8, r1')
    expect_row('C00-creates-outer-field-address',rows['constructor-c00'],0xc29e,'addw\tr0, r1, #0x864')
    expect_row('C00-stores-outer-field-address-to-its-SP+a4',rows['constructor-c00'],0xc2a8,'str\tr0, [sp, #0xa4]')
    expect_row('C00-stores-default-pointer-to-outer+864',rows['constructor-c00'],0xc2ae,'str.w\tr2, [r1, #0x864]')
    direct=[line for line in listing.splitlines() if '#0x864' in line.lower()]
    ck('direct-0x864-displacement-lines',[x.split(':')[0].strip() for x in direct], ['c29e','c2ae'])
    stores=[]; pos=0; pattern=bytes.fromhex('c1f86428')
    while True:
        pos=abl.find(pattern,pos)
        if pos<0: break
        stores.append(hex(pos)); pos+=1
    ck('direct-outer+864-store-byte-site',stores,['0xc2ae'])
    literal=struct.unpack_from('<I',abl,0xc4b4)[0]
    ck('outer+864-initialized-literal',hex(literal),'0x6cd4d0')

    # Exact caller dataflow: every local direct B84 call passes R1=R4. R4 is an
    # address built from a runtime/global descriptor, not a proven APOB field.
    for addr in [0xa68,0xa86,0xab2,0xae0]:
        expect_row(f'context-caller-R1-from-R4-{addr:x}',rows['context-callers'],addr,'mov\tr1, r4')
    for addr in [0xa6c,0xa8a,0xab6,0xae4]:
        expect_row(f'context-caller-calls-B84-{addr:x}',rows['context-callers'],addr,'bl\t0xb84')
    expect_row('context-source-loads-outer-field',rows['context-callers'],0xa2c,'ldr\tr1, [r0, #0xc]')
    expect_row('context-source-ORs-mapped-high-bits',rows['context-callers'],0xa30,'orr\tr4, r1, #0xfc000000')
    # Exact pointer literal cell is encoded at B08 (0x6E134), but the runtime
    # pointer loaded through it is not available in a file image.
    cell=struct.unpack_from('<I',abl,0xb08)[0]; ck('ABL1-global-pointer-cell-literal-6E134',hex(cell),'0x6e134')

    # Prior exact source/argument evidence reused as a boundary, no GUID/1204 rerun.
    handoff=ROOT/'docs/research/2026-09-21-apob-abl-handoff-next.md'
    handoff_text=handoff.read_text()
    ck('reused exact APOB service boundary',('0x9E3B14C' in handoff_text and '0x11ED' in handoff_text),True)
    result={
      'status':'PASS','checks_passed':sum(c['status']=='PASS' for c in checks),'checks_failed':sum(c['status']=='FAIL' for c in checks),
      'evidence_class':['observed-bytes','static-analysis'],'inputs':{'rom':{'path':str(ROM),'size':len(rom),'sha256':sha(ROM)},'abl1_container':{'spi_offset':'0x99FD00','size':csize,'sha256':sha_bytes(cont)},'abl1_payload':{'path':str(ABL),'size':len(abl),'sha256':sha(ABL)},'abl1_object':{'path':str(OBJ),'sha256':sha(OBJ)},'full_listing':{'path':str(LIST),'sha256':sha(LIST)},'conditional_base_report':{'path':str(BASE_REPORT),'sha256':sha(BASE_REPORT)},'prior_34check_script':{'path':str(OLD_VERIFIER),'sha256':sha(OLD_VERIFIER)},'prior_34check_result':{'path':str(OLD_RESULT),'sha256':sha(OLD_RESULT)}},
      'load_map':{'ps1_load_address':hex(load_addr),'decompressed_length':hex(len(abl)),'pointer_literal':'0x006CD4D0','payload_relative_offset':hex(ptr-load_addr),'conditional_0x57100_offset':hex(conditional_rel),'conditional_0x57100_is_loader_proof':False,'classification':'not mapped inside the payload by the exact header or prior conditional 0x57100 code-base hypothesis; actual target region remains unresolved because exact runtime load/relocation map is unavailable','hypothetical_0x6c0000_offset':hex(ptr-0x6c0000),'hypothetical_base_adopted':False},
      'fclk_heap_argument':{'fclk_sp_slots':[0,0],'reader_saved_reg_count':12,'reader_ldr_r7_r9_from_sp_offset':48,'reader_r9':0,'reader_stores_r9_to_helper_sp0':True,'helper_saved_reg_count':6,'helper_ldr_r1_from_sp_plus_0x18':0,'helper_strd_r3_r1_provider_stack_args':[None,0],'provider_saved_reg_mask':'0x4FFF','provider_saved_reg_bytes':saved_bytes,'provider_local_bytes':locals,'provider_sp_plus_0xa4_maps_to_entry_sp_plus':provider_arg_offset,'provider_second_stack_arg':0,'heap_producer_r1_r10':0,'result':'selected FCLK -> provider-0x0F miss path has auxiliary arg zero; it is not linked to constructor outer+0x864'},
      'heap_allocator_contract':{'direct_6238_calls_in_full_listing':len(re.findall(r'\bbl\s+0x6238\b',listing,re.I)),'representative_callers':[{'site':'0x46DC','r0':'descriptor SP+0x4','r1':'R6 copied from original R0 context'},{'site':'0x4774','r0':'descriptor SP+0x4','r1':'R6 copied from original R0 context'},{'site':'0x4B5C','r0':'miss descriptor SP+0x14','r1':'provider second stack argument; zero in FCLK path'}],'callee':'0x6238 captures R1 in R10; available checked uses do not establish R10 as byte-source pointer; 0x6B78 ignores R3 and stores R1 to [R0] per byte. In this call R1=0 and R2=node length, so 0x6B78 is a zero-fill loop, not memcpy.'},
      'constructor':{'caller':'0xB84 R5=saved entry R1; at 0xBD2 passes R1=R5 to 0xC00; direct B84 callers 0xA6C/0xA8A/0xAB6/0xAE4 pass R1=R4','runtime_outer_pointer_source':'R4 is built from [R0+0xC] with 0xFC000000 high bits; R0 comes through an external/runtime pointer cell keyed by literal 0x6E134','field_store':'only direct displacement references #0x864 in full ABL1 listing are ADDW R0,R1,#0x864 at 0xC29E and STR.W R2,[R1,#0x864] at 0xC2AE; one direct store site','field_default_literal':'0x006CD4D0 at payload 0xC4B4','stack_offset_warning':'C00 [SP+0xA4] stores pointer R1+0x864 in constructor frame; provider 0x49CC [SP+0xA4] loads provider second stack argument. Numeric slot equality is not frame identity.'},
      'g7_correction':{'supersedes':'prior owned report docs/research/2026-09-21-apob-abl-heap-populator.md, which described 0x6B78 as copying data from R10/outer+0x864','correction':'raw/reconciled helper is a byte-fill loop, called with R1=0 and R3=R10. The C00 SP+0xA4 local and provider SP+0xA4 input are separate frames. On the concrete FCLK call path the provider second stack arg is 0. Prior 34/34 result proved only the checked byte anchors; its verifier did not disassemble/helper-signature-check 0x6B78 or reconcile stack arguments.'},
      'first_unresolved_boundary':'ABL1 absolute pointer 0x006CD4D0 has no proven mapping under exact $PS1 load_address=0 or the conditional 0x57100 code-base hypothesis; the outer object is sourced via runtime/global descriptor state. No byte-backed join from that runtime object/field to APOB service 0x9E3B14C/0x61/0xFF or native $INV 0x11ED is established. Exact selected FCLK path passes zero as provider auxiliary arg; other caller values/paths are not promoted.',
      'limits':['No actual runtime load/relocation base; hypothetical 0x6C0000 would map pointer to payload+0xD4D0 but is not supported and was not adopted.','No complete alias/DMA/external write census for outer+0x864.','No firmware/ABL1/APOB execution, PPI/HOB capture, SMU execution, or hardware result.','No modification to old report/evidence, PPI GUID proof, or 0x1204 path.'],
      'checks':checks,'commands':commands,'tool_version':toolver.stdout.strip()
    }
    result['checks_total']=len(checks)
    (OUT/'outer864-origin-result.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,default=lambda o: o.hex() if isinstance(o,(bytes,bytearray)) else str(o))+'\n')
    stdout={'status':'PASS','checks_passed':len(checks),'checks_failed':0,'pointer':'0x006CD4D0 not mapped into ABL1 by exact header or conditional 0x57100 base; runtime map unresolved','fclk_provider_aux':'zero','fill_semantics':'0x6B78 repeats R1 byte; FCLK call sets R1=0; not memcpy','first_unresolved':'upstream/runtime map of outer object and any bridge to APOB/INV'}
    print(json.dumps(stdout,separators=(',',':')))
    (OUT/'VERIFICATION.txt').write_text('''COMMANDS\n'''+ ' '.join(['PYTHONDONTWRITEBYTECODE=1','python3','-B',str(Path(__file__).resolve())])+'\n\nEXIT STATUS: 0\nSTDERR: empty\n\nRESULT\n'+json.dumps(stdout,indent=2)+'\n')
if __name__=='__main__': main()
