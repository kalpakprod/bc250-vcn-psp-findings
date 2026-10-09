#!/usr/bin/env python3
"""Byte-backed stack propagation and fill-vs-copy review for exact CLV ABL1."""
from __future__ import annotations
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path('/home/OWNER/orca/projects/bc250')
ROM = ROOT / 'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
ABL = ROOT / 'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
OUT = Path(__file__).resolve().parent
EXPECTED_ROM = 'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'
EXPECTED_ABL = 'af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a'
blob = ABL.read_bytes()
checks=[]

def check(name, observed, expected):
    passed = observed == expected
    checks.append({'name':name,'passed':passed,'observed':observed,'expected':expected})
    if not passed:
        raise AssertionError(f'{name}: {observed!r} != {expected!r}')

def hx(addr, size):
    return blob[addr:addr+size].hex()

def popcount(x):
    return x.bit_count()

rom_hash=hashlib.sha256(ROM.read_bytes()).hexdigest()
abl_hash=hashlib.sha256(blob).hexdigest()
check('ROM hash',rom_hash,EXPECTED_ROM)
check('ABL1 hash',abl_hash,EXPECTED_ABL)
check('ABL1 size',len(blob),94624)

# At 0x463C a selector branch r1==0x0F clears two outgoing stack arguments.
check('selector function entry instruction',hx(0x463c,2),'164a')
check('selector compares r1 with 0x0F',hx(0x4648,2),'0f29')
check('non-0x0F branch bypasses zero-argument path',hx(0x464a,2),'1bd1')
check('selected path sets r2=0',hx(0x464c,2),'0022')
check('selected path stores first stack arg r2=0',hx(0x4664,2),'0092')
check('selected path stores second stack arg r2=0',hx(0x4666,2),'0192')
check('selector calls reader at 0x1FB4',hx(0x466a,4),'fdf7a3fc')

# Reader saves twelve registers (0x30 bytes); its LDRD reads caller entry SP+0/+4.
reader_push=struct.unpack_from('<H',blob,0x1fb6)[0]
check('reader push mask',hex(reader_push),'0x47ff')
check('reader saved register word count',popcount(reader_push),12)
check('reader stack-pair load',hx(0x1fc0,4),'dde90c79')
check('reader forwards r9 (second stack arg) to helper stack',hx(0x1fd2,4),'cdf80090')
check('reader helper call to 0x4800',hx(0x1fe0,4),'02f00efc')

# 0x4800 wrapper saves six registers, reads its first stack argument, then
# forwards that value as the second stack argument to 0x49CC.
check('0x4800 wrapper push',hx(0x4800,2),'7cb5')
check('wrapper load from entrySP+0',hx(0x4808,2),'0699')
check('wrapper forwards value in r1 to outgoing stack arg +4',hx(0x4812,4),'cde90031')
check('wrapper call to 0x49CC',hx(0x481c,4),'00f0d6f8')

# 0x49CC saves thirteen registers (0x34), then 0x6C local bytes: SP is
# entrySP-0xA0. Therefore [SP+0xA4] is the second stacked argument entrySP+4.
service_push=struct.unpack_from('<H',blob,0x49ce)[0]
check('0x49CC push mask',hex(service_push),'0x4fff')
check('0x49CC saved register word count',popcount(service_push),13)
service_push_bytes=popcount(service_push)*4
locals_bytes=0x6c
frame_bytes=service_push_bytes+locals_bytes
check('0x49CC frame delta',hex(frame_bytes),'0xa0')
check('0x49CC subtracts 0x6C',hx(0x49d2,2),'9bb0')
check('0x4B54 load offset',hx(0x4b54,2),'2999')
check('0x4B54 [SP+0xA4] maps to entrySP+4',hex(0xa4-frame_bytes),'0x4')
check('0x4B5C calls helper 0x6238',hx(0x4b5c,4),'01f06cfb')

# 0x6238 receives r0=local descriptor pointer and r1=the loaded stack value;
# it saves r0/r1 into r4/r10. Its later zero-fill call is distinct from copy.
helper_push=struct.unpack_from('<H',blob,0x623a)[0]
check('0x6238 helper push mask',hex(helper_push),'0x4ff8')
check('0x6238 helper saved register word count',popcount(helper_push),10)
check('helper captures r0 descriptor in r4',hx(0x623c,2),'0446')
check('helper captures r1 scalar in r10',hx(0x6242,2),'8a46')
check('helper zeroes fill byte r1 before fill call',hx(0x6316,2),'0021')
check('helper calls 0x6B78 fill loop',hx(0x6320,4),'00f02afc')

# Fill loop: store the scalar in r1, not source bytes. Adjacent routine loads
# a byte from [r1] then stores that byte and is the distinct copy loop.
check('copy loop source byte load at 0x6B6A',hx(0x6b6a,4),'11f8013b')
check('copy loop writes loaded r3 at 0x6B6E',hx(0x6b6e,4),'00f8013b')
check('fill loop stores r1 directly at 0x6B7A',hx(0x6b7a,4),'00f8011b')
check('fill loop decrements length',hx(0x6b7e,2),'521e')
check('fill loop branches while unsigned length remains',hx(0x6b80,2),'fbd2')
check('fill helper returns',hx(0x6b82,2),'7047')

# Separate 0x0862 call site: stack descriptor constants and caller context
# differ from the 0x4B5C descriptor/zero-argument call.
check('separate call site stores 0x218 descriptor word',hx(0x850,2),'0090')
check('separate call site stores 0xA045 descriptor word',hx(0x856,2),'0190')
check('separate call site stores type 2',hx(0x85c,4),'8df80800')
check('separate call site passes caller context r4',hx(0x85a,2),'2146')
check('separate call site to 0x6238',hx(0x862,4),'05f0e9fc')

result={
    'status':'PASS',
    'checks':{'passed':sum(x['passed'] for x in checks),'failed':sum(not x['passed'] for x in checks),'total':len(checks)},
    'input':{'rom':str(ROM),'rom_sha256':rom_hash,'abl1':str(ABL),'abl1_sha256':abl_hash,'abl1_size':len(blob)},
    'stack_path':{
        'scope':'only the branch at 0x463C where r1==0x0F; runtime execution not shown',
        'caller_0x463C':{'stack_args':[0,0],'call':'0x466A -> 0x1FB4'},
        'reader_0x1FB4':{'saved_registers':12,'stack_delta':'0x30','loads':'LDRD R7,R9,[SP,#0x30]','forwards':'R9 to helper 0x4800 stack arg +0'},
        'wrapper_0x4800':{'saved_registers':6,'stack_delta':'0x18','loads':'[SP,#0x18] = entrySP+0','forwards_to_0x49CC_stack_arg_plus4':0},
        'service_0x49CC':{'saved_registers':13,'locals':'0x6C','total_frame':'0xA0','load':'[SP,#0xA4] = entrySP+4','observed_value_on_selected_path':0,'call':'0x4B5C -> 0x6238'},
        'helper_0x6238':{'r0':'caller-local descriptor pointer','r1':'zero on selected path','semantic_prototype':'not fully identified'},
    },
    'fill_vs_copy':{
        'copy_loop':'0x6B6A LDRB R3,[R1],#1; 0x6B6E STRB R3,[R0],#1',
        'fill_loop':'0x6B7A STRB R1,[R0],#1; 0x6B7E decrement count; 0x6B80 loop while unsigned count remains',
        'fill_byte_on_helper_path':'0 because 0x6316 MOVS R1,#0 immediately precedes the 0x6320 call to 0x6B78',
    },
    'separate_0x862_call':'constructs local descriptor [0x218,0xA045,type=2], passes caller context r4 as r1; this is not evidence that its input is the selected 0x4B5C stack argument',
    'limits':['No function names or physical clock/ratio semantics assigned.','The branch and input are conditional; no firmware execution/hardware behavior inferred.','No $INV 0x11ED, AmdSetup field, FCLK, MCLK, or APOB link follows from this helper path.'],
    'checks_detail':checks,
}
(OUT/'stack-path-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'checks':len(checks),'passed':result['checks']['passed'],'failed':result['checks']['failed'],'stack_entry_plus4_value':0,'fill_loop':'STRB r1,[r0],#1','separate_0x862_input':'local descriptor + caller r4'},indent=2))
