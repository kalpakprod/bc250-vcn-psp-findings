#!/usr/bin/env python3
"""Bounded decoded call-site inventory, with unresolved indirect edges retained."""
import json, re, struct, hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
C=json.loads((P/'census.json').read_text())
T={0x1364,0x1363,0x11ed,0x1204,0x1331,0x1373,0x1374}
READERS={'AmdFabricAriPei':(0x1d3c,0x1e8f),'AmdCcxVhAriDxe':(0x5ac4,0x5c65)}
def values(op):
    # Memory displacements and objdump address comments are NOT immediates.
    op=re.sub(r'\[[^]]*\]','',op.split('#')[0])
    return {int(v,16) for v in re.findall(r'\b0x([0-9a-f]+)\b',op)}
def raw_rva(r,raw):
    for s in r['sections']:
        if s['raw']<=raw<s['raw']+s['size']:return s['rva']+raw-s['raw']
def pointer_scan(b,v,width):
    return [m.start() for m in re.finditer(re.escape(v.to_bytes(width,'little')),b)]
summary=[]; windows=[]; alltargets=[]; reader_results=[]
for r in C['records']:
    r.setdefault('ui', r['ffs_guid'])
    ins=json.loads((P/(r['stem']+'.instructions.json')).read_text()); by={x['rva']:x for x in ins}
    b=(P/(r['stem']+'.bin')).read_bytes()
    for x in r['target_candidates']:
        category='memory-displacement-or-comment'
        if x['mnemonic'].startswith(('j','call')):category='control-flow-address-not-token'
        elif values(x['operands'])&T:category='immediate-candidate'
        alltargets.append(dict(module=r['ui'],category=category,**x))
        if category=='immediate-candidate':
            j=ins.index(x); windows.append('\nTARGET '+r['ui']+' '+hex(x['rva']))
            windows += [f"{z['rva']:08X} {z['bytes']} {z['mnemonic']} {z['operands']}" for z in ins[max(0,j-6):j+12]]
    if not (r['heap_guid'] or r['nvtb']):continue
    guid_addresses=[raw_rva(r,x) for x in r['heap_guid']]
    guidrefs=[]
    for x in ins:
        refs=values(x['operands'])
        comment=re.search(r'# 0x([0-9a-f]+)',x['operands'])
        if comment: refs.add(int(comment[1],16))
        if any(a in refs or a+r['imagebase'] in refs for a in guid_addresses if a is not None):guidrefs.append(x)
    indirect=[x for x in ins if x['mnemonic'] in ('call','jmp') and not re.fullmatch(r'0x[0-9a-f]+',x['operands'])]
    row=dict(module=r['ui'],stem=r['stem'],sha256=r['sha256'],type=r['type'],guid_raw=r['heap_guid'],guid_rva=guid_addresses,guid_refs=guidrefs,nvtb_raw=r['nvtb'],inv_raw=r['inv'],indirect_edges=indirect,reader=READERS.get(r['ui']),classification='heap-library marker only; no literal NVTB/INV parser' if not r['nvtb'] else 'confirmed INV reader')
    if r['inv'] and not r['nvtb']: row['classification']='heap library plus INV serializer; no literal NVTB/INV reader'
    summary.append(row)
    if r['ui'] not in READERS:continue
    start,end=READERS[r['ui']]
    direct=[x for x in ins if x['mnemonic'].startswith(('call','j')) and re.fullmatch(r'0x[0-9a-f]+',x['operands']) and start<=int(x['operands'],16)<end and not start<=x['rva']<end]
    addressrefs=[x for x in ins if not x['mnemonic'].startswith(('call','j')) and ((values(x['operands'])&{start,start+r['imagebase']}) or re.search(r'# '+hex(start)+r'\b',x['operands']))]
    pointers={str(w)+':'+hex(v):pointer_scan(b,v,w) for w in (4,8) for v in {start,start+r['imagebase']}}
    # Scan every code byte for E8/E9 targeting any reader byte. Non-boundary hits are kept, not promoted.
    raw_edges=[]
    for s in r['sections']:
        if not s['flags']&(0x20|0x20000000):continue
        for off in range(s['raw'],s['raw']+s['size']-4):
            if b[off] not in (0xe8,0xe9):continue
            at=s['rva']+off-s['raw']; dest=(at+5+struct.unpack_from('<i',b,off+1)[0])&0xffffffff
            if start<=dest<end and not start<=at<end:
                raw_edges.append(dict(rva=at,target=dest,bytes=b[off:off+5].hex(),decoded_boundary=at in by,decoded=by.get(at)))
    result=dict(module=r['ui'],start=start,end_exclusive=end,direct_external_edges=direct,address_materializations=addressrefs,stored_pointers=pointers,raw_rel32_external_edges=raw_edges,unresolved_indirect_edges=indirect)
    reader_results.append(result)
    ranges=[(start,end)] + [(x['rva']-40,x['rva']+110) for x in direct]
    if r['ui']=='AmdCcxVhAriDxe': ranges += [(0x3a58,0x4020),(0x7950,0x7a18),(0x5c68,0x5da5)]
    for a,z in ranges:
        windows.append('\nREADER/HEAP '+r['ui']+' '+hex(a)+'..'+hex(z))
        windows += [f"{x['rva']:08X} {x['bytes']} {x['mnemonic']} {x['operands']}" for x in ins if a<=x['rva']<z]
(P/'coverage.json').write_text(json.dumps(dict(scope='All 233 supported executable code sections; objdump linear boundaries, direct branches, exact stored pointers and RIP-relative materializations. Arbitrary runtime/computed indirect targets not solved.',modules=summary,readers=reader_results,target_candidates=alltargets),indent=2)+'\n')
(P/'semantic-windows.txt').write_text('\n'.join(windows)+'\n')
lines=['# Caller coverage matrix','', 'All addresses hexadecimal, module RVA. GUID raw offsets shown. Indirect edge counts are retained UNRESOLVED module-wide, not asserted reader callers.','', '| Module | Type | GUID raw | NVTB raw | Reader / direct callers : token | Indirect edges | Classification |','|---|---|---|---|---|---:|---|']
for r in summary:
    calls={'AmdFabricAriPei':'1D3C / 1EBD:10FF, 1F94:1104','AmdCcxVhAriDxe':'5AC4 / 5CA5:1000, 5CF1:1001'}.get(r['module'],'none identified')
    lines.append('| '+ ' | '.join([r['module'],r['type'],','.join(f'{x:X}' for x in r['guid_raw']),','.join(f'{x:X}' for x in r['nvtb_raw']) or '—',calls,str(len(r['indirect_edges'])),r['classification']])+' |')
(P/'caller-matrix.md').write_text('\n'.join(lines)+'\n')
print('supported',len(C['records']),'selected',len(summary),'readers',len(reader_results),'target candidate classifications',{k:sum(x['category']==k for x in alltargets) for k in {x['category'] for x in alltargets}})
for r in reader_results:print(r['module'],'direct',[(hex(x['rva']),x['operands']) for x in r['direct_external_edges']],'addressrefs',r['address_materializations'],'stored',r['stored_pointers'],'raw-rel32',len(r['raw_rel32_external_edges']),'unresolved indirect',len(r['unresolved_indirect_edges']))
