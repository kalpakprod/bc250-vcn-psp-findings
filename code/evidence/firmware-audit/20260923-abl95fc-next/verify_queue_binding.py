"""Resolve index versus human queue labels, retain unproven PSP transport edge."""

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
text = (D / "smu-mailbox-accessors.txt").read_text()
n = 0
for m in re.finditer(r"^([0-9a-f]{8}) ([0-9a-f]+) (.+)$", text, re.M):
    a = int(m[1], 16)
    raw = bytes.fromhex(m[2])
    assert b[a : a + len(raw)] == raw
    n += 1
assert n == 16, n
base = struct.unpack_from("<I", b, 0xBA0)[0]
assert base == 0x7000
vectors = list(struct.unpack_from("<8I", b, 0x7A94))
assert vectors[3] == vectors[4] == 0x746C and vectors[5] == 0x79B4
rows = []
for index, table in enumerate(vectors):
    end = min(x for x in set(vectors + [0x7A94]) if x > table)
    entries = {
        hex(msg): (
            hex(struct.unpack_from("<I", b, table + msg * 8)[0])
            if table + msg * 8 + 4 <= end - 4
            else "OUTSIDE_BOUNDED_TABLE"
        )
        for msg in (7, 14, 15)
    }
    arg, rsp, cmd = struct.unpack_from("<III", b, base + 12 + index * 12)
    rows.append(
        {
            "index": index,
            "table_pointer": hex(table),
            "arg_register": hex(arg),
            "response_register": hex(rsp),
            "command_register": hex(cmd),
            "handlers": entries,
        }
    )
assert rows[5]["handlers"] == {"0x7": "0x1e720", "0xe": "0x1f218", "0xf": "0x1f2f0"}
assert (
    rows[5]["arg_register"] == "0x3010700"
    and rows[5]["response_register"] == "0x3010704"
)
result = {
    "status": "PASS_STATIC_INDEX_MAP",
    "source_sha256": hashlib.sha256(b).hexdigest(),
    "accessor_instruction_checks": n,
    "rows": rows,
    "finding": "Retained unique-table label Queue4 is physical index5 because indices3 and4 share a table.",
    "limits": [
        "Pointer vector is read from firmware data; its selection in live dispatcher not executed",
        "ARG/RSP semantics verified by originalFFC/FA8 accessors; CMD field interpretation from retained descriptor layout, dispatcher not re-proven",
        "SVC28 to this queue still unproven",
        "Internal SMN addresses are not host commands; no IO executed",
    ],
}
(D / "queue-binding-result.json").write_text(json.dumps(result, indent=2) + "\n")
print("PASS8 index entries,16 exact accessor instructions; PLL family index5, not4")
