#!/usr/bin/env python3
"""Verify the exact ABL1 callback boundary and a concrete +0x20 producer chain."""
from __future__ import annotations
import hashlib, json, re, struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ABL = ROOT / 'evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin'
THUMB = OUT / 'abl1-data-thumb-llvm.txt'
EXPECTED = 'af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a'

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def u32(b: bytes, off: int) -> int:
    return struct.unpack_from('<I', b, off)[0]

def check(cs, name, got, expected):
    ok = got == expected
    cs.append({'check': name, 'passed': ok, 'got': got, 'expected': expected})
    if not ok:
        raise AssertionError(f'{name}: got {got!r}, expected {expected!r}')

def raw_window(b: bytes, off: int, n: int = 8) -> str:
    return b[off:off+n].hex()

def text_lines(text: str, addrs):
    by = {}
    for line in text.splitlines():
        m = re.match(r'\s*([0-9a-f]+):', line)
        if m:
            a = int(m.group(1), 16)
            if a in addrs:
                by[f'0x{a:04X}'] = line.strip()
    return by

def find_raw32(b: bytes, values):
    result = {}
    for value in values:
        pat = struct.pack('<I', value)
        hits=[]; start=0
        while True:
            i=b.find(pat, start)
            if i < 0: break
            hits.append(i); start=i+1
        result[f'0x{value:08X}'] = [f'0x{x:X}' for x in hits]
    return result

def main():
    cs=[]; b=ABL.read_bytes(); text=THUMB.read_text(errors='replace')
    check(cs, 'ABL1 exact hash', sha(ABL), EXPECTED)
    check(cs, 'full Thumb disassembly exists', THUMB.exists(), True)
    check(cs, 'full Thumb disassembly is non-empty', len(text)>1000000, True)

    # Exact raw instructions used by the producer chain and callback boundary.
    expected_semantics = {
        'function_95fc_prologue': (0x95FC, r'push\.w\s+\{r4, r5, r6, r7, r8, r9, r10, r11, lr\}'),
        'caller_7e00_bl_ad58': (0x7E00, r'bl\s+0xad58\b'),
        'caller_7e30_bl_10cc0': (0x7E30, r'bl\s+0x10cc0\b'),
        'initializer_b1f8_store_52c': (0xB1F8, r'str\.w\s+r1, \[r0, #0x52c\]'),
        'producer_ad58_store_channel_20': (0xAE22, r'strh(?:\.w)?\s+r6, \[r0, #0x20\]'),
        'producer_10cc0_read_channel_20': (0x10D40, r'ldrh(?:\.w)?\s+r0, \[r0, #0x20\]'),
        'producer_10cc0_store_channel_20': (0x10E50, r'strh(?:\.w)?\s+r7, \[r0, #0x20\]'),
        'preceding_7544_write_context_60': (0x757C, r'strh(?:\.w)?\s+r0, \[r5, #0x60\]'),
        'handoff_7544_to_75cc': (0x7586, r'bl\s+0x75cc\b'),
        '75cc_context_load': (0x75E2, r'ldr(?:\.w)?\s+r4, \[r6, #0x4\]'),
        'callback_entry': (0x109BC, r'push\s+\{r0, r1, r4, lr\}'),
        'callback_channel_count': (0x109C0, r'ldrb(?:\.w)?\s+r0, \[r0, #0x4b\]'),
        'callback_channel_pointer_write': (0x10A04, r'str\s+r1, \[r4, #0xc\]'),
    }
    semantic_lines={}
    text_by_addr={}
    for line in text.splitlines():
        m=re.match(r'\s*([0-9a-f]+):',line)
        if m: text_by_addr[int(m.group(1),16)]=line.strip()
    raw_checks={}
    for name,(off,pattern) in expected_semantics.items():
        line=text_by_addr.get(off,'')
        ok=bool(re.search(pattern,line,re.I))
        check(cs, f'semantic {name}', ok, True)
        semantic_lines[name]={'payload_offset':f'0x{off:X}','line':line,'pattern':pattern}
        raw_checks[name]={'payload_offset':f'0x{off:X}','bytes':raw_window(b,off,4 if off in (0x95fc,0x7e00,0x7e30,0xb1f8,0x757c,0x7586) else 2)}

    # The exact ABL1 body has no direct call to 0x95FC in the fresh disassembly.
    direct=[]
    for line in text.splitlines():
        if re.search(r'\b(bl|blx)\s+0x95fc\b', line, re.I): direct.append(line.strip())
        if re.search(r'\b(bl|blx)\s+.*\+0x95fc\b', line, re.I): direct.append(line.strip())
    check(cs, 'direct BL/BLX callers of 0x95FC', len(direct), 0)

    # Resolve the callback initializer under the reviewer-proposed base only
    # after four independent pointer anchors land on exact local Thumb code.
    callback_literal = u32(b, 0xB218)
    check(cs, 'callback literal at payload 0xB218', callback_literal, 0x00067ABD)
    base_candidate = 0x57100
    pointer_anchors = {
        0xB218: (0x00067ABD, 0x109BC, r'push\s+\{r0, r1, r4, lr\}', 'callback +0x52C'),
        0xB21C: (0x00067A95, 0x10994, r'cbz\s+r1', 'callback post-selector helper'),
        0xB220: (0x00061E19, 0x0AD18, r'push\s+\{r4, r5\}', 'runtime callback helper'),
        0xB224: (0x00067A59, 0x10958, r'push\s+\{r4, r5\}', 'runtime callback helper'),
    }
    anchor_rows=[]
    for literal_off,(value,local_entry,pattern,label) in pointer_anchors.items():
        check(cs, f'pointer literal at 0x{literal_off:X}', u32(b,literal_off), value)
        mapped=value-base_candidate
        check(cs, f'base 0x{base_candidate:X} maps 0x{literal_off:X}', mapped, local_entry | 1)
        line=text_by_addr.get(local_entry,'')
        ok=bool(re.search(pattern,line,re.I))
        check(cs, f'mapped target {label} at 0x{local_entry:X}', ok, True)
        anchor_rows.append({'literal_payload_offset':f'0x{literal_off:X}','literal':f'0x{value:08X}','base':f'0x{base_candidate:X}','mapped_thumb':f'0x{mapped:X}','local_code_entry':f'0x{local_entry:X}','line':line,'label':label})
    check(cs, 'independent code anchors for base candidate', len(anchor_rows), 4)
    callback_boundary = {
        'initializer_store_payload_offset':'0xB1F8',
        'initializer_literal_payload_offset':'0xB218',
        'callback_literal':'0x00067ABD',
        'candidate_runtime_base':'0x57100',
        'callback_local_thumb':'0x109BD',
        'callback_local_code_entry':'0x109BC',
        'independent_anchor_count':len(anchor_rows),
        'anchors':anchor_rows,
        'interpretation':'Four independent absolute pointer literals map under base 0x57100 to exact local Thumb code; +0x52C therefore resolves conditionally to local callback 0x109BC with high static mapping confidence, while the loader/base relation itself remains unmeasured.'
    }

    # No direct function-pointer variant for the exact target in the payload,
    # including the observed callback address base and common zero-base form.
    pointer_values=[]
    for base in (0, 0x57100, 0x60000, 0x08000000, 0x006A0000):
        for off in (0x95FC,0x95FD): pointer_values.append(base+off)
    pointer_hits=find_raw32(b,pointer_values)
    target_collision = pointer_hits.get('0x000606FD', [])
    other_target_hits = {k:v for k,v in pointer_hits.items() if k != '0x000606FD' and v}
    check(cs, 'target pointer variants have no validated local reference', not other_target_hits and target_collision == ['0x17134'], True)

    # Record the producer dataflow in register/object form.
    producer_chain = [
        {'site':'0x7548','effect':'r5 = [r0+0x04]','evidence':'same entry object later handed to 0x75CC'},
        {'site':'0x757C','effect':'[r5+0x60] = 0x0320 (halfword)','evidence':'raw little-endian bytes a5f86000; LLVM display strh.w r0,[r5,#0x60]'},
        {'site':'0x7586','effect':'BL 0x75CC with original r0','evidence':'handoff preserves entry object'},
        {'site':'0x75E2','effect':'r4 = [r6+0x04]','evidence':'r6 is original 0x75CC argument; therefore r4 aliases 0x7548 r5'},
        {'site':'0x7E00','effect':'BL 0xAD58(r4)','evidence':'direct Thumb call'},
        {'site':'0xAD58..0xAE22','effect':'callback [r4+0x52C](r4,index); r0=[r4+0x0C]; STRH r6,[r0+0x20]','evidence':'direct bytes/disassembly'},
        {'site':'0x7E30','effect':'BL 0x10CC0(r4)','evidence':'direct Thumb call'},
        {'site':'0x10CC0..0x10E50','effect':'callback 0x109BC selects channel; LDRH r0,[channel+0x20] for reduction; STRH r7,[channel+0x20]','evidence':'direct bytes/disassembly'},
    ]
    result={
        'status':'PASS','checks':len(cs),'evidence_class':['observed-bytes','static-analysis'],
        'input':str(ABL),'abl1_sha256':sha(ABL),'disassembly':str(THUMB),
        'direct_calls_95fc':direct,'raw_checks':raw_checks,'semantic_lines':semantic_lines,
        'callback_boundary':callback_boundary,'searched_target_pointer_variants':pointer_hits,'target_pointer_scan_qualification':{'known_collision':'0x000606FD at payload 0x17134','validated_local_reference':False},
        'producer_chain':producer_chain,
        'conclusion':'Four pointer anchors support conditional runtime base 0x57100: callback slot +0x52C at 0xB1F8 maps literal 0x00067ABD to local Thumb callback 0x109BC, which selects channel index and writes [context+0x0C]. The exact producer path then writes the same per-channel +0x20 field: 0x7E00->0xAD58 writes selected r6; 0x7E30->0x10CC0 reduces and writes r7; preceding 0x7544->0x75CC seeds +0x60 with 0x0320. The immediate caller of 0x95FC still has no direct in-payload BL/BLX edge; loader/base relation and invocation dispatch remain unresolved.',
        'limits':'No MHz/unit/training/hardware/runtime-precedence claim; base 0x57100 is a conditional static mapping supported by four code anchors, not a loader/runtime proof; no source-to-binary flat-offset assumption.'
    }
    out=OUT/'abl1-producer-trace-result.json'; out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':'PASS','checks':len(cs),'direct_calls_95fc':0,'callback_literal':hex(callback_literal),'producer_sites':['0xAD58','0x10CC0'],'result':str(out)},indent=2))

if __name__=='__main__': main()
