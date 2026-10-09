"""Bounded immediate-token scan, not a proof of absence of indirect consumers."""

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
C = ROOT / "evidence/firmware-audit/20260919-inv-token-consumers"
census = json.loads((C / "census.json").read_text())
records = {r["stem"]: r for r in census["records"]}
found = []
files = list(C.glob("*.instructions.json"))
for f in files:
    stem = f.name.removesuffix(".instructions.json")
    record = records[stem]
    b = (C / (stem + ".bin")).read_bytes()
    assert hashlib.sha256(b).hexdigest() == record["sha256"]
    data = json.loads(f.read_text())
    for i, r in enumerate(data):
        if not re.search(r"(?<![0-9a-f])0x123c\b", r.get("operands", "")):
            continue
        window = data[max(0, i - 8) : i + 12]
        for row in window:
            a = row["rva"]
            raw = bytes.fromhex(row["bytes"])
            sec = next(
                s
                for s in record["sections"]
                if s["rva"] <= a and a + len(raw) <= s["rva"] + s["size"]
            )
            off = sec["raw"] + a - sec["rva"]
            assert b[off : off + len(raw)] == raw
        if r["mnemonic"] == "mov" and r["operands"] == "edx,0x123c":
            assert data[i + 2]["operands"] == "WORD PTR [eax],dx"
            assert data[i + 10]["operands"] == "al,BYTE PTR [edx+0x36d]"
            assert data[i + 11]["operands"] == "BYTE PTR [ecx+0x3],al"
            kind = "record-producer"
        else:
            assert r["mnemonic"].startswith("j") or "[r" in r["operands"], r
            kind = "address/displacement-coincidence"
        found.append(
            {"module": stem, "instruction": r, "classification": kind, "window": window}
        )
assert len(found) == 20
assert sum(r["classification"] == "record-producer" for r in found) == 7
out = {
    "status": "BOUNDED_SCAN_COMPLETE",
    "modules": len(files),
    "scope": "decoded x86 UEFI corpus, immediate123C only. No computed/table/ARM/SMU coverage",
    "result": "7 serializer producers,13 address/displacement coincidences. No direct immediate requester identified. Not a no-consumer proof.",
    "candidates": found,
}
(OUT / "memory-pstate123c-candidates.json").write_text(json.dumps(out, indent=2) + "\n")
print(
    f"PASS {len(files)} module hashes;20 byte-backed candidates;7 producers,13 unrelated address uses"
)
