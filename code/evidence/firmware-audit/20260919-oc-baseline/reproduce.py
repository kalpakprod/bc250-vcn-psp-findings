#!/usr/bin/env python3
"""Bounded local identity reconciliation; imports the existing firmware parser."""
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
import firmware_audit as fw

sha = lambda b: hashlib.sha256(b).hexdigest()

class Fingerprints(fw.Extractor):
    def __init__(self, data):
        super().__init__(data, Path('.'), 'identity')
        self.logos = []

    def save_executable(self, body, image_type, context):
        self.records.append({'guid': context.get('ffs_guid'), 'ui': context.get('ui', ''),
                             'sha256': sha(body), 'size': len(body)})

    def walk_sections(self, blob, context, depth):
        if context.get('ffs_guid') == '7BB28B99-61BB-11D5-9A5D-0090273FC14D':
            self.logos.append({'depth': depth, 'sha256': sha(blob), 'size': len(blob),
                              'steam_label': b'Steam' in blob or 'Steam'.encode('utf-16-le') in blob,
                              'png': b'\x89PNG\r\n\x1a\n' in blob, 'jpeg': b'\xff\xd8\xff' in blob})
        super().walk_sections(blob, context, depth)

paths = sorted(set(
    list((ROOT / 'candidates').glob('*SteamLogo*.bin')) +
    list((ROOT / 'candidates').glob('*FirstMarker*.bin')) +
    list((ROOT / 'candidates').glob('*W9*.bin')) +
    list((ROOT / 'candidates').glob('*8c_omarchy*.bin')) +
    list((ROOT / 'evidence/programmer/reads/20260918').glob('*.bin')) +
    list((ROOT / 'evidence/programmer/reads/20260919').glob('*.bin')) +
    [ROOT / x for x in ['evidence/donor/retroweb-20260916/BC250_5.00_clv.bin',
                        'evidence/programmer/reads/20260911/read-a.bin',
                        'evidence/programmer/reads/20260911/read-b.bin', 'dump/2.bin']]
))
base = (ROOT / 'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin').read_bytes()
results = []
for p in paths:
    data = p.read_bytes()
    assert len(data) == 0x1000000, p
    digest = sha(data)
    inventory = fw.analyze_image(p)
    extractor = Fingerprints(data)
    modules = extractor.extract()
    fv_checks = []
    for fv in inventory['firmware_volumes']:
        off, size = fv['base'], fv['header_length']
        header = data[off:off + size]
        fv_checks.append({**fv, 'checksum_zero': sum(struct.unpack('<' + 'H' * (size // 2), header)) & 65535 == 0})
    results.append({'path': str(p.relative_to(ROOT)), 'size': len(data), 'sha256': digest,
                    'regions': {name: sha(data[a:b]) for name, a, b in [('nvram', 0, 0x20000), ('psp_area', 0x8e0000, 0xab0000), ('apcb_area', 0xab0000, 0xae0000), ('dxe_fv', 0xae0000, 0xe00000), ('pei_area', 0xe00000, 0x1000000)]},
                    'psp_valid': inventory['psp']['checksum_match'],
                    'bhd_valid': inventory['bhd']['checksum_match'],
                    'apcb_valid': inventory['apcb']['checksum_match'],
                    'fv': fv_checks, 'modules': modules, 'logos': extractor.logos,
                    'amdsetup_at_0x4bb': data[0x4bb:0x4bf] == b'NVAR' and data[0x4c6:0x4cf] == b'AmdSetup\0',
                    'same_as_clv_outside_dxe': data[:0xae0000] == base[:0xae0000] and data[0xe00000:] == base[0xe00000:]})
    assert sha(p.read_bytes()) == digest, 'input changed during analysis'
log = ROOT / 'evidence/runtime/20260919-w10-boot/cpuinfo.txt'
text = log.read_text()
cpu = {'path': str(log.relative_to(ROOT)), 'sha256': sha(log.read_bytes()),
       'logical_processors': sum(line.startswith('processor\t') for line in text.splitlines()),
       'cpu_cores_values': sorted(set(line.split(':', 1)[1].strip() for line in text.splitlines() if line.startswith('cpu cores')))}
report = {'scope': 'local observed-bytes; no current board claim', 'parser_sha256': sha((ROOT / 'scripts/firmware_audit.py').read_bytes()), 'images': results, 'historical_cpu': cpu}
out = Path(__file__).with_name('identity.json')
with out.open('x') as f:
    json.dump(report, f, indent=2)
    f.write('\n')
for row in results:
    special = [m for m in row['modules'] if any(x in m['ui'].lower() for x in ['mei', 'unlock', 'marker', 'vcn'])]
    print(json.dumps({'path': row['path'], 'sha256': row['sha256'], 'special_modules': special, 'logos': row['logos'], 'checks': [row['psp_valid'], row['bhd_valid'], row['apcb_valid'], all(v['checksum_zero'] for v in row['fv'])]}))
print(json.dumps(cpu))
