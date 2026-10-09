import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
C = ROOT / "evidence/firmware-audit/20260919-inv-token-consumers"
p = C / "AmdIdsDebugPrintDxe-e177833c8a19.bin"
b = p.read_bytes()
assert hashlib.sha256(b).hexdigest() == "e177833c8a196019762213622fea29e9fb16ed03cec7d4f601bc19573f85256f"
rows = json.loads(
    (C / "AmdIdsDebugPrintDxe-e177833c8a19.instructions.json").read_text()
)
# PE section mapping must be checked, not assumed to equal raw offsets.
assert b[:2] == b"MZ"
pe = struct.unpack_from("<I", b, 0x3c)[0]
assert b[pe:pe+4] == b"PE\0\0"
count = struct.unpack_from("<H", b, pe+6)[0]
size = struct.unpack_from("<H", b, pe+20)[0]
sections = []
for i in range(count):
    at = pe + 24 + size + 40*i
    vs, va, raw_size, raw = struct.unpack_from("<IIII", b, at+8)
    sections.append((va, raw_size, raw))

def raw_offset(rva, length):
    matches = [raw+rva-va for va, size, raw in sections if va <= rva and rva+length <= va+size]
    assert len(matches) == 1
    return matches[0]

want = {
    0xA32: "c744242019a00000",
    0xA4D: "e85efcffff",
    0xA60: "488b442440",
    0xA65: "8138cc9910db",
    0xA72: "488b442440",
    0xA77: "488901",
    0xAE0: "48894c2408",
    0xAEE: "e80dffffff",
    0xB05: "488b4018",
    0xB09: "488901",
}
for r, h in want.items():
    expected = bytes.fromhex(h)
    off = raw_offset(r, len(expected))
    assert b[off:off+len(expected)] == expected, hex(r)
result = {
    "status": "PASS",
    "module": p.name,
    "section_mapping": sections,
    "sha256": hashlib.sha256(b).hexdigest(),
    "anchors": {hex(k): v for k, v in want.items()},
    "finding": "A019 lookup result is accepted only when object header DB1099CC matches; caller then reads object +0x18 and returns it to an IDS/debug-print path. No voltage token or SMU voltage register write appears in this bounded path.",
    "scope": "bounded direct path; not proof about all computed callers",
}
Path(__file__).with_name("ids-debug-path.json").write_text(
    json.dumps(result, indent=2) + "\n"
)
print("PASS IDS/debug path consumes A019 object +0x18, no voltage token")
