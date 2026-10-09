"""Bounded candidate classification, not global absence-of-writer proof."""

import hashlib, json, re, struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
D = Path(__file__).resolve().parent
b = (
    ROOT
    / "import/from-windows/Users/kukuruza/tmp_bc250/upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5"
).read_bytes()
assert (
    hashlib.sha256(b).hexdigest()
    == "cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37"
)
files = ["row-writers.txt", "df-row-candidate-setters.txt", "df-domain-queries.txt"]
count = 0
for name in files:
    s = (D / name).read_text()
    assert s.startswith("PASS: entire loaded program memory equals")
    for m in re.finditer(r"^([0-9a-f]{8}) ([0-9a-f]+) (.+)$", s, re.M):
        a = int(m[1], 16)
        raw = bytes.fromhex(m[2])
        assert b[a : a + len(raw)] == raw
        count += 1
pools = {
    hex(p): hex(struct.unpack_from("<I", b, p)[0])
    for p in [0x1711C, 0x1778C, 0x171EC, 0x17470, 0x17474, 0x17478, 0x1747C]
}
assert pools["0x1778c"] == "0xf104" and pools["0x171ec"] == "0xcee0"
assert pools["0x17474"] == "0xcf78"
r = {
    "status": "BOUNDED_CANDIDATES_CLASSIFIED",
    "instruction_bytes_checked": count,
    "literal_pools": pools,
    "classifications": {
        "21E8C": "direct float outputF104..F120, not selected DF row18; callees not globally excluded",
        "1E038": "rowpointer/index metadata initialization; no direct row18 assignment in shown function",
        "1F3F4/1F52C": "measurement accumulators/counter initialization",
        "1F098": "reads selected-row4/10/14, returns numeric state, not writer",
        "1F120": "copies changed register53A60 across mask-selected channels and commits last value atCF78+8*i+80",
        "1F198": "writes handshake53A58, polls53A5C",
        "22D6C": "broad CPU initialization; direct stores not to requested row, transitive effects unresolved",
    },
    "limits": [
        "53 raw l32r candidates not complete disassembly/CFG",
        "Existing Ghidra listing-only scan had insufficient coverage and is not an absence proof",
        "No physical clocks, field effect, stable profile or hardware claims",
        "Requested runtime row18 writer remains unresolved",
    ],
}
(D / "row-writer-result.json").write_text(json.dumps(r, indent=2) + "\n")
print(
    "PASS",
    count,
    "instruction byte records; bounded candidates classified; writer unresolved",
)
