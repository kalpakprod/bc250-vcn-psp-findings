#!/usr/bin/env python3
"""Validate the BC250 project contract, focused skills, memory indexes, and local links."""
from __future__ import annotations
import re, sys
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]
errors=[]

def require(ok,msg):
    if not ok: errors.append(msg)

copies=[ROOT/x for x in ('AGENT_CONTRACT.md','AGENTS.md','CLAUDE.md','EMPRYO.md')]
data=[p.read_bytes() for p in copies]
require(len(set(data))==1,'contract compatibility copies are not byte-identical')
contract=copies[0].read_text(errors='replace')
# Balance the XML-like contract sections used by the repository convention.
tags=re.findall(r'<(/?)([A-Za-z_][\w-]*)(?:\s[^>]*)?>',contract)
stack=[]
for closing,name in tags:
    if closing:
        if not stack or stack[-1]!=name: errors.append(f'unbalanced contract tag: closing {name}'); break
        stack.pop()
    else: stack.append(name)
require(not stack,f'unclosed contract tags: {stack}')
# Validate focused skill metadata and local links.
skills=ROOT/'.agents'/'skills'
for skill in sorted(skills.glob('*/SKILL.md')):
    txt=skill.read_text(errors='replace')
    m=re.match(r'^---\n(.*?)\n---\n',txt,re.S)
    require(bool(m),f'{skill}: missing YAML frontmatter')
    if not m: continue
    try: meta=yaml.safe_load(m.group(1)) or {}
    except Exception as e: errors.append(f'{skill}: invalid frontmatter: {e}'); continue
    name=meta.get('name'); desc=meta.get('description')
    require(name==skill.parent.name,f'{skill}: name does not match directory')
    require(isinstance(name,str) and re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',name or ''),f'{skill}: invalid name')
    require(isinstance(desc,str) and bool(desc.strip()),f'{skill}: empty description')
# Validate instinct YAML.
for p in sorted((ROOT/'memory'/'instincts').glob('*.yaml')):
    try: obj=yaml.safe_load(p.read_text()) or {}
    except Exception as e: errors.append(f'{p}: invalid YAML: {e}'); continue
    for key in ('trigger','action','evidence','confidence'): require(key in obj,f'{p}: missing {key}')
# Check relative Markdown links from contract and canonical docs.
for p in [ROOT/'AGENTS.md',ROOT/'docs'/'knowledge-sources.md',ROOT/'memory'/'INDEX.md']:
    txt=p.read_text(errors='replace')
    for target in re.findall(r'\]\(([^)]+)\)',txt):
        target=target.split('#',1)[0]
        if not target or target.startswith(('http:','https:','mailto:','<')): continue
        target=target.strip('<>')
        require((p.parent/target).exists(),f'{p}: broken local link {target}')
# No secret-like files in the canonical contour outside intentionally raw import.
# Generated dependency trees can legitimately contain public certificate bundles
# (for example certifi/cacert.pem) and are ignored by git. Do not treat those
# as project artifacts; scan the tracked/documentary contour instead.
secret_scan_skip = {
    ROOT/'.venv',
    ROOT/'venv',
    ROOT/'tools'/'cutter'/'.venv',
    ROOT/'tools'/'cutter'/'vendor',
    ROOT/'tools'/'cutter'/'profile',
    ROOT/'tools'/'cutter'/'downloads',
    ROOT/'tools'/'cutter'/'logs',
}
def is_skipped_generated(path):
    return any(path == base or base in path.parents for base in secret_scan_skip)
for p in ROOT.iterdir():
    if p.name=='import' or is_skipped_generated(p): continue
    if p.is_file() and (p.name.startswith('.env') or p.suffix.lower() in {'.pem','.key','.p12','.pfx'}):
        errors.append(f'secret-like canonical file: {p}')
    if p.is_dir():
        for q in p.rglob('*'):
            if is_skipped_generated(q): continue
            if q.is_file() and (q.name.startswith('.env') or q.suffix.lower() in {'.pem','.key','.p12','.pfx'}):
                errors.append(f'secret-like canonical file: {q}')
if errors:
    print('FAILED')
    print('\n'.join(errors))
    raise SystemExit(1)
print(f'OK contract_copies={len(copies)} skills={len(list(skills.glob("*/SKILL.md")))} instincts={len(list((ROOT/"memory"/"instincts").glob("*.yaml")))}')
