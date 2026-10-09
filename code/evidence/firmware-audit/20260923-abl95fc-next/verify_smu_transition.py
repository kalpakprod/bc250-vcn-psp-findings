"""Verify retained SMU dispatch entries and fresh exact instruction listings."""

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
rom = (ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin").read_bytes()
assert rom[0x8FEF00 : 0x8FEF00 + len(b)] == b
checked = []
for file in ["smu-pll-handlers.txt", "smu-transition-helpers.txt"]:
    text = (D / file).read_text()
    assert text.startswith("PASS: entire loaded program memory equals")
    lines = []
    for m in re.finditer(r"^([0-9a-f]{8}) ([0-9a-f]+) (.+)$", text, re.M):
        a = int(m[1], 16)
        raw = bytes.fromhex(m[2])
        assert b[a : a + len(raw)] == raw
        lines.append({"address": m[1], "bytes": m[2], "instruction": m[3]})
    assert lines
    checked.append(
        {
            "file": file,
            "instructions": len(lines),
            "sha256": hashlib.sha256(text.encode()).hexdigest(),
        }
    )
entries = {}
for msg, off, target in [
    (7, 0x79E8, 0x1E720),
    (14, 0x7A20, 0x1F218),
    (15, 0x7A28, 0x1F2F0),
]:
    flags, addr = struct.unpack_from("<II", b, off)
    assert flags == 6 and addr == target
    entries[hex(msg)] = {"entry": hex(off), "handler": hex(addr), "flags": flags}
scale = struct.unpack_from("<f", b, 0x170AC)[0]
assert 0.00099999 < scale < 0.00100001
result = {
    "source_sha256": hashlib.sha256(b).hexdigest(),
    "entries": entries,
    "listings": checked,
    "scale170ac": scale,
    "conclusions": [
        "1E720 uses high byte1 and low byte index, calls1E448 and storesFF to state+F6",
        "1F218 and1F2F0 reject when state+F6==FF and reject zero argument",
        "1F218 selects domain0E;1F2F0 domains0F/11 plus10/12",
        "Both scale unsigned integer by float0.001 before downstream helper",
    ],
    "limits": [
        "Static Xtensa analysis, not emulation",
        "SVC28 transport to these dispatch entries remains unproven",
        "Numeric scale does not independently prove physical clock units",
        "Rows may be rewritten at runtime; initial image table not final hardware state",
    ],
}
(D / "smu-transition-result.json").write_text(json.dumps(result, indent=2) + "\n")
print(
    "PASS dispatch entries and",
    sum(x["instructions"] for x in checked),
    "SMU instruction bytes; exact ROM slice",
)
