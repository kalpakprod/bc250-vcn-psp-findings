"""Verify candidate query handlers and initial table numbers; no live-state claim."""

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
assert struct.unpack_from("<I", b, 0x79B4 + 10 * 8)[0] == 0x1E7D8
assert struct.unpack_from("<I", b, 0x79B4 + 13 * 8)[0] == 0x1E650
n = 0
for filename in ("smu-df-query.txt", "smu-df-count.txt"):
    text = (D / filename).read_text()
    # Ignore guessed1E994 entry: not a table-proven function start.
    if filename == "smu-df-query.txt":
        text = text.split("===== 0001e994")[0]
    for m in re.finditer(r"^([0-9a-f]{8}) ([0-9a-f]+) (.+)$", text, re.M):
        off = int(m[1], 16)
        raw = bytes.fromhex(m[2])
        assert b[off : off + len(raw)] == raw
        n += 1
rows = []
for off in (0xCF0C, 0xCF34, 0xCF5C, 0xCF84, 0xCFAC):
    rows.append(
        {
            "address": hex(off),
            "raw_coefficients0_3": b[off : off + 4].hex(),
            "float4": struct.unpack_from("<f", b, off + 4)[0],
            "query_float18": struct.unpack_from("<f", b, off + 0x18)[0],
        }
    )
assert [r["query_float18"] for r in rows] == [450.0, 450.0, 850.0, 1750.0, 250.0]
result = {
    "status": "PASS_STATIC_QUERY_SOURCE",
    "instructions_checked": n,
    "query_handler": "0x1e7d8",
    "set_state_handler": "0x1e650",
    "initial_rows": rows,
    "limits": [
        "Input index selects runtime pointer table atCEE0+1C, not necessarily image default row",
        "Service transport still candidate",
        "Query returns stored float converted to integer, not PLL readback",
        "1750 is stored initial value, not actual MCLK or confirmed limit",
        "Entry1E994 guessed during exploration discarded, no inference from it",
    ],
}
(D / "df-rows-result.json").write_text(json.dumps(result, indent=2) + "\n")
print(
    "PASS",
    n,
    "query/set-state instruction bytes,5 initial row values; runtime provenance remains open",
)
