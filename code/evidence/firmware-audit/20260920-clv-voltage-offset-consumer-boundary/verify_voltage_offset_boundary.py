from pathlib import Path
import hashlib
import importlib.util
import json
import re
import struct

ROOT = Path("/home/OWNER/orca/projects/bc250")
ROM = ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin"
SETUP = ROOT / "evidence/firmware-audit/20260919-inv-token-consumers/CbsSetupDxe-7ff717d51c9a.bin"
CB = ROOT / "evidence/firmware-audit/20260919-inv-token-consumers/CbsBasePei-6ff112922ad8.bin"
CB_ASM = ROOT / "evidence/firmware-audit/20260919-inv-token-consumers/CbsBasePei-6ff112922ad8-0.asm"
NBIO = ROOT / "evidence/firmware-audit/20260919-inv-token-consumers/AmdNbioSmuV10Pei-905b8be68afd-0.asm"
FABRIC = ROOT / "evidence/firmware-audit/20260919-inv-token-consumers/AmdFabricAriPei-c5b99650a442-0.asm"
PARSER = ROOT / "import/from-windows/Users/kukuruza/bc250-bios/tools/uefi/e1_ifr_dump.py"
EDK = ROOT / "import/from-windows/Users/kukuruza/tmp_bc250/upstream/edk2/MdePkg/Include/Uefi/UefiInternalFormRepresentation.h"

EXPECTED = {
    ROM: ("ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8", 16777216),
    SETUP: ("7ff717d51c9a447c6954c63b633cf836f1e4396c2b01f4bf590268a60ac1d0d8", 264160),
    CB: ("6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77", 81520),
    CB_ASM: ("667dcb547b12ac6d545757270ddada1d282c8f070be57d4897a9f4b4060d72ff", 0),
    Path(NBIO): ("1c74e94c6637ef7dfabcc9f03e85fffc698d730da512d61cbfe2cbaafb4186da", 0),
    Path(FABRIC): ("9c4744e1129052c965828694995bc60b250ce4bdb66d858584d090ea092b9f95", 0),
}
inputs = {}
for path, (digest, size) in EXPECTED.items():
    data = path.read_bytes()
    got = hashlib.sha256(data).hexdigest()
    assert got == digest, f"hash mismatch {path}: {got}"
    if size:
        assert len(data) == size, f"size mismatch {path}: {len(data)}"
    inputs[str(path.relative_to(ROOT))] = {"size": len(data), "sha256": got}

spec = importlib.util.spec_from_file_location("e1_ifr_dump", PARSER)
ifr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ifr)
setup = SETUP.read_bytes()
packages = ifr.find_packages(setup)
forms = next((x for x in packages if x[1] == 2), None)
strings_pkg = next((x for x in packages if x[1] == 4), None)
assert forms and strings_pkg
strings = ifr.parse_sibt(setup[strings_pkg[0]:strings_pkg[0] + 4 + strings_pkg[2]])[1]

records = []
scope = []
p = forms[0] + 4
end = forms[0] + 4 + forms[2]
while p + 2 <= end:
    op = setup[p]
    ln = setup[p + 1] & 0x7F
    scoped = bool(setup[p + 1] & 0x80)
    if ln < 2 or p + ln > end:
        break
    body = setup[p + 2:p + ln]
    if op == 0x0A and scoped:
        scope.append("SUPPRESS_IF")
    elif op == 0x29 and scope:
        scope.pop()
    elif op in (0x05, 0x07) and len(body) >= 11:
        prompt, help_id, qid, vid, voff, qflags = struct.unpack_from("<HHHHHB", body, 0)
        if qid in (0x36B, 0x36C):
            row = {
                "qid": hex(qid),
                "offset": hex(voff),
                "opcode": hex(op),
                "record_offset": hex(p),
                "question_flags": hex(qflags),
                "suppressed_by_scope": bool(scope),
                "prompt_id": prompt,
                "prompt": next((s for i, s in strings if i == prompt), ""),
                "scope": list(scope),
            }
            if op == 0x07:
                nflags = body[11]
                width = (1, 2, 4, 8)[nflags & 3]
                row.update({
                    "numeric_flags": hex(nflags),
                    "width_bytes": width,
                    "display_bits": hex(nflags & 0x30),
                    "min_max_step": [
                        int.from_bytes(body[12 + i * width:12 + (i + 1) * width], "little")
                        for i in range(3)
                    ],
                })
            records.append(row)
    p += ln

control = next(x for x in records if int(x["qid"], 16) == 0x36B and not x["suppressed_by_scope"])
value = next(x for x in records if int(x["qid"], 16) == 0x36C)
assert control["offset"] == "0x6e5"
assert value["offset"] == "0x6e6"
assert value["width_bytes"] == 4
assert value["min_max_step"] == [0, 0xFFFFFFFF, 0]
assert value["display_bits"] == "0x10"

cb_text = CB_ASM.read_text(errors="strict")
nbio_text = NBIO.read_text(errors="strict")
fabric_text = FABRIC.read_text(errors="strict")
serializer_assertions = {
    "CbsBasePei_control_load": "e3e4:" in cb_text and "8a 82 e5 06 00 00" in cb_text,
    "CbsBasePei_control_record": "e3c4:" in cb_text and "ba 63 13 00 00" in cb_text,
    "CbsBasePei_value_load": "e419:" in cb_text and "8b 82 e6 06 00 00" in cb_text,
    "CbsBasePei_value_record": "e3f6:" in cb_text and "ba 64 13 00 00" in cb_text,
    "AmdNbioSmuV10Pei_control_load": "10464:" in nbio_text and "8a 82 e5 06 00 00" in nbio_text,
    "AmdNbioSmuV10Pei_value_load": "10499:" in nbio_text and "8b 82 e6 06 00 00" in nbio_text,
    "AmdNbioSmuV10Pei_control_record": "10444:" in nbio_text and "ba 63 13 00 00" in nbio_text,
    "AmdNbioSmuV10Pei_value_record": "10476:" in nbio_text and "ba 64 13 00 00" in nbio_text,
    "AmdNbioSmuV10Pei_value_width_copy": "1049f:" in nbio_text and "89 41 03" in nbio_text,
}
assert all(serializer_assertions.values()), serializer_assertions
assert "1048a:" in nbio_text and "80 ca 02" in nbio_text
assert "e407:" in cb_text and "80 e2 fc" in cb_text

reader_calls = []
for line in fabric_text.splitlines():
    if re.search(r"\bcall\s+0x1d3c\b", line):
        reader_calls.append(line)
tokens = []
for line in fabric_text.splitlines():
    m = re.search(r"\bpush\s+0x([0-9a-f]+)\b", line)
    if m and int(m.group(1), 16) in (0x10FF, 0x1104, 0x1204, 0x1364):
        tokens.append({"line": line, "token": hex(int(m.group(1), 16))})
assert len(reader_calls) == 2, reader_calls
assert [x["token"] for x in tokens if x["token"] in ("0x10ff", "0x1104")] == ["0x10ff", "0x1104"]
assert not [x for x in tokens if x["token"] in ("0x1204", "0x1364")]

result = {
    "status": "PARTIAL_BLOCKED_AT_CONSUMER",
    "inputs": inputs,
    "ifr": {
        "packages": [(hex(o), hex(t), hex(n)) for o, t, n in packages],
        "control_qid_0x36b": control,
        "value_qid_0x36c": value,
        "interpretation": "QID 0x36C is a numeric u32 with unsigned display flag and bounds 0..0xFFFFFFFF; the existing IFR text labels it HIDDEN under SUPPRESS_IF, while this bounded raw parser does not decode that extended construct. No physical sign, mV, VID, or rail meaning follows.",
    },
    "serializer": {
        "checks": serializer_assertions,
        "record_0x1363": "u8 control +0x6e5, flags low bits 0",
        "record_0x1364": "u32 value +0x6e6, flags low bits 2 / 4-byte copy",
        "raw_transform": "value copied unchanged into the $INV record; no numeric conversion",
    },
    "fabric_reader": {
        "reader_entry": "0x1d3c / generic reader 0x1dfc",
        "direct_reader_call_count": len(reader_calls),
        "direct_immediate_tokens": [x["token"] for x in tokens],
        "requested_tokens": ["0x10ff", "0x1104"],
        "requested_0x1364": False,
        "boundary": "no direct 0x1364 requester in this exact AmdFabricAriPei inventory; computed/indirect/HOB/runtime later consumer remains unresolved",
    },
    "verdict": "The signed-offset interpretation is established only as a hidden native Setup u32 request serialized unchanged as $INV 0x1364 paired with control 0x1363. Actual consumer, physical rail identity, numeric conversion, SoC target voltage, and applied hardware effect are not established.",
    "limits": [
        "No +150=>1.15V interpretation.",
        "No SoC/GFX rail identity from driver labels.",
        "No firmware, NVRAM, register, hardware, or candidate mutation.",
        "No global absence claim beyond the bounded exact AmdFabric direct-reader inventory.",
    ],
}
out = ROOT / "evidence/firmware-audit/20260920-clv-voltage-offset-consumer-boundary"
(out / "voltage-offset-boundary-result.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
