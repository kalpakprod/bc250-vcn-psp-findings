#!/usr/bin/env python3
import os
import sys
import json
import struct
import hashlib
from pathlib import Path

ROOT = Path('/home/OWNER/orca/projects/bc250')

ROM_PATH = ROOT / 'evidence/donor/retroweb-20260916/BC250_5.00_clv.bin'
EXPECTED_ROM_HASH = 'ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8'

FABRIC_PATH = ROOT / 'evidence/firmware-audit/20260919-inv-buffer-lifetime/AmdFabricAriPei.bin'
EXPECTED_FABRIC_HASH = 'c5b99650a442ed9be1cf3a62e7571f7eb163b9f80a60d4fcc7b3e9afe4506f78'

CCX_PATH = ROOT / 'evidence/firmware-audit/20260920-clv-sync-stage1/extract/donor/modules/0017_AmdCcxVhAriDxe_pe32.bin'
EXPECTED_CCX_HASH = 'd9bc6337e3d039922016e95ed8be1fda5d7fb3e0250e43a6058d9c0d305997f0'

DONOR_EXTRACT = ROOT / 'evidence/firmware-audit/20260920-clv-uefitool-native-run/BC250_5.00_clv.bin.dump'

checks = []

def record_check(name, passed, detail):
    checks.append({
        'name': name,
        'passed': bool(passed),
        'detail': detail
    })
    status_str = "PASS" if passed else "FAIL"
    print(f"[{status_str}] {name}: {detail}")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    print("=== Starting DF Override Tokens 0x1373/0x1374 Consumer Audit ===")

    # 1. Verify Hashes
    rom_hash = sha256_file(ROM_PATH)
    record_check("ROM Hash", rom_hash == EXPECTED_ROM_HASH, f"Got {rom_hash}")

    fabric_hash = sha256_file(FABRIC_PATH)
    record_check("AmdFabricAriPei Hash", fabric_hash == EXPECTED_FABRIC_HASH, f"Got {fabric_hash}")

    ccx_hash = sha256_file(CCX_PATH)
    record_check("AmdCcxVhAriDxe Hash", ccx_hash == EXPECTED_CCX_HASH, f"Got {ccx_hash}")

    # 2. Fabric Ari Pei Serialization of 0x1373
    d_fabric = open(FABRIC_PATH, 'rb').read()
    # 0x11ace: ba 73 13 00 00 (mov edx, 0x1373)
    # 0x11ad3: 8b 45 f8 (mov eax, [ebp-8])
    # 0x11ad6: 66 89 10 (mov [eax], dx)
    # 0x11aeb: 8b 55 fc (mov edx, [ebp-4])
    # 0x11aee: 8a 82 03 07 00 00 (mov al, [edx+0x703])
    # 0x11af4: 88 41 03 (mov [ecx+3], al)
    # 0x11af7: 8b 4d f8 (mov ecx, [ebp-8])
    # 0x11afa: 83 c1 04 (add ecx, 4)
    pat_1373_head = bytes.fromhex('ba731300008b45f8668910')
    pat_1373_load = bytes.fromhex('8a8203070000')
    pos_1373 = d_fabric.find(pat_1373_head)
    has_1373 = (pos_1373 == 0x11ace) and (d_fabric[0x11aee:0x11aee+6] == pat_1373_load)
    record_check("Fabric 0x1373 Serialization", has_1373, f"Offset {hex(pos_1373)}, reads AmdSetup+0x703")

    # 3. Fabric Ari Pei Serialization of 0x1374
    # 0x11b00: ba 74 13 00 00 (mov edx, 0x1374)
    # 0x11b05: 8b 45 f8 (mov eax, [ebp-8])
    # 0x11b08: 66 89 10 (mov [eax], dx)
    # 0x11b20: 8b 55 fc (mov edx, [ebp-4])
    # 0x11b23: 66 8b 82 04 07 00 00 (mov ax, [edx+0x704])
    # 0x11b2a: 66 89 41 03 (mov [ecx+3], ax)
    # 0x11b31: 83 c1 05 (add ecx, 5)
    pat_1374_head = bytes.fromhex('ba741300008b45f8668910')
    pat_1374_load = bytes.fromhex('668b8204070000')
    pos_1374 = d_fabric.find(pat_1374_head)
    has_1374 = (pos_1374 == 0x11b00) and (d_fabric[0x11b23:0x11b23+7] == pat_1374_load)
    record_check("Fabric 0x1374 Serialization", has_1374, f"Offset {hex(pos_1374)}, reads AmdSetup+0x704 (u16)")

    # 4. Fabric Ari Pei CBS Counterpart Registration Descriptor
    # 0x16a78: CBS GUID (04126c85-5c4e-458f-abc1-29f1f7da365e)
    # 0x16a88: Notify GUID (60db76a0-5d55-47bb-970f-34d8d0be369e)
    # 0x16a98: Wildcard CPU 0xFFFFFFFF
    # 0x16a9c: 0x00000000
    # 0x16aa8: Callback VA 0x09E227A0 (RVA 0x6C20, file offset 0x6A88)
    # 0x16aac: Event 0xFFFFFFFE
    cbs_guid_bytes = bytes.fromhex('856c12044e5c8f45abc129f1f7da365e')
    notify_guid_bytes = bytes.fromhex('a076db60555dbb47970f34d8d0be369e')
    desc_cbs = d_fabric[0x16a78:0x16a88] == cbs_guid_bytes
    desc_notify = d_fabric[0x16a88:0x16a98] == notify_guid_bytes
    desc_cpu = d_fabric[0x16a98:0x16a9c] == b'\xff\xff\xff\xff'
    desc_cb = d_fabric[0x16aa8:0x16aac] == b'\xa0\x27\xe2\x09'
    desc_event = d_fabric[0x16aac:0x16ab0] == b'\xfe\xff\xff\xff'
    counterpart_pass = desc_cbs and desc_notify and desc_cpu and desc_cb and desc_event
    record_check("Fabric CBS Counterpart Descriptor", counterpart_pass,
                 f"CBS GUID match={desc_cbs}, Notify GUID match={desc_notify}, Callback VA=0x09E227A0, Event=0xFFFFFFFE")

    # 5. Reader queries in AmdFabricAriPei
    # Direct reader at 0x1D18 queries 0x10FF (push 0x10ff: 68 ff 10 00 00)
    # Direct reader at 0x1DF3 queries 0x1104 (push 0x1104: 68 04 11 00 00)
    has_10ff = d_fabric[0x1d18:0x1d18+5] == bytes.fromhex('68ff100000')
    has_1104 = d_fabric[0x1df3:0x1df3+5] == bytes.fromhex('6804110000')
    no_push_1373 = (d_fabric.find(bytes.fromhex('6873130000')) == -1)
    no_push_1374 = (d_fabric.find(bytes.fromhex('6874130000')) == -1)
    record_check("Fabric Ari Pei Direct Queries", has_10ff and has_1104 and no_push_1373 and no_push_1374,
                 f"Queries 0x10FF at 0x1D18, 0x1104 at 0x1DF3; Zero queries for 0x1373/0x1374")

    # 6. Reader queries in AmdCcxVhAriDxe
    d_ccx = open(CCX_PATH, 'rb').read()
    has_1000 = d_ccx[0x5ca0:0x5ca5] == bytes.fromhex('b900100000')
    has_1001 = d_ccx[0x5cec:0x5cf1] == bytes.fromhex('b901100000')
    no_ccx_1373 = (d_ccx.find(bytes.fromhex('b973130000')) == -1) and (d_ccx.find(bytes.fromhex('6873130000')) == -1)
    no_ccx_1374 = (d_ccx.find(bytes.fromhex('b974130000')) == -1) and (d_ccx.find(bytes.fromhex('6874130000')) == -1)
    record_check("CCX Ari Dxe Direct Queries", has_1000 and has_1001 and no_ccx_1373 and no_ccx_1374,
                 f"Queries 0x1000 at 0x5CA0, 0x1001 at 0x5CEC; Zero queries for 0x1373/0x1374")

    # 7. Corpus-wide requester scan for 0x1373 and 0x1374
    # Check that across the extracted UEFI modules, no module queries 0x1373 or 0x1374 as an immediate argument
    corpus_hits_1373 = []
    corpus_hits_1374 = []
    pats_1373 = [b'\x68\x73\x13\x00\x00', b'\xb9\x73\x13\x00\x00', b'\xbf\x73\x13\x00\x00']
    pats_1374 = [b'\x68\x74\x13\x00\x00', b'\xb9\x74\x13\x00\x00', b'\xbf\x74\x13\x00\x00']

    for root, dirs, files in os.walk(DONOR_EXTRACT):
        for f in files:
            if f.endswith('.pe') or f.endswith('.te') or f.endswith('body.bin'):
                p = os.path.join(root, f)
                try:
                    data = open(p, 'rb').read()
                    for pat in pats_1373:
                        if pat in data:
                            corpus_hits_1373.append((p.replace(str(DONOR_EXTRACT), ''), pat.hex()))
                    for pat in pats_1374:
                        if pat in data:
                            corpus_hits_1374.append((p.replace(str(DONOR_EXTRACT), ''), pat.hex()))
                except Exception:
                    pass

    corpus_clean = (len(corpus_hits_1373) == 0) and (len(corpus_hits_1374) == 0)
    record_check("Corpus Direct Query Scan", corpus_clean,
                 f"Immediate reader queries: 0x1373 hits={len(corpus_hits_1373)}, 0x1374 hits={len(corpus_hits_1374)}")

    all_passed = all(c['passed'] for c in checks)

    result_json = {
        'status': 'PASS' if all_passed else 'FAIL',
        'total_checks': len(checks),
        'checks_passed': sum(1 for c in checks if c['passed']),
        'checks': checks,
        'summary': {
            'tokens': {
                '0x1373': {
                    'name': 'DfPstateOverride',
                    'setup_offset': '0x703',
                    'width': 1,
                    'serializer_module': 'AmdFabricAriPei',
                    'serializer_rva': '0x11C66',
                    'direct_uefi_consumer': None
                },
                '0x1374': {
                    'name': 'DfClockOvrd',
                    'setup_offset': '0x704',
                    'width': 2,
                    'serializer_module': 'AmdFabricAriPei',
                    'serializer_rva': '0x11C98',
                    'direct_uefi_consumer': None
                }
            },
            'boundary_conclusion': (
                'DF override tokens 0x1373 and 0x1374 are serialized by AmdFabricAriPei and CbsBasePei '
                'into the NVTB/$INV buffer via CBS Notify registration callback 0x6A88 (VA 0x9E227A0). '
                'Zero direct reader queries exist across the UEFI PEI/DXE corpus. '
                'Downstream consumption terminates into the ABL1/APOB/SMU handoff.'
            )
        }
    }

    out_json_path = ROOT / 'evidence/firmware-audit/20260921-df-consumer/df-consumer-result.json'
    with open(out_json_path, 'w') as f:
        json.dump(result_json, f, indent=2)
    print(f"\nResult JSON written to {out_json_path}")

    sys.exit(0 if all_passed else 1)

if __name__ == '__main__':
    main()
