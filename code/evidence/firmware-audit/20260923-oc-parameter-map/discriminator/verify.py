"""Discriminate adjacent serializer records with unequal in-memory markers. No IO."""

import hashlib
import json
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
CORPUS = ROOT / "evidence/firmware-audit/20260919-inv-token-consumers"
SOURCE = ROOT / "evidence/firmware-audit/20260923-native-cbs-inv/test.s"
ROM = ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin"
ROM_SHA = "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"
assert hashlib.sha256(ROM.read_bytes()).hexdigest() == ROM_SHA
modules = {
    "nvram": (
        "NvramPei-cbc1def3ce53.bin",
        "cbc1def3ce53e947091d3bf1e950d78a4e78afbc69c67369124979736ab2116f",
    ),
    "cbs": (
        "CbsBasePei-6ff112922ad8.bin",
        "6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77",
    ),
}
for name, digest in modules.values():
    assert hashlib.sha256((CORPUS / name).read_bytes()).hexdigest() == digest
source = SOURCE.read_text()
source = source.replace("mode: .long MODE", "mode: .long 0")
old_path = "/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260923-chat-case/nvar/oc_profiles_03.bin"
assert old_path in source
source = source.replace(old_path, str(ROM))
source = source.replace("widths: .long 1,1,1,1,4,1,2", "widths: .long 1,1,1,1,1,1,1")
source = source.replace(
    "tokens: .long 0x11ed,0x1204,0x1331,0x1363,0x1364,0x1373,0x1374",
    "tokens: .long 0x1330,0x1331,0x1332,0x123b,0x123c,0x123d,0x11ed",
)
offsets = [0x6A2, 0x6A3, 0x6A4, 0x36C, 0x36D, 0x36E, 0x316]
tokens = [0x1330, 0x1331, 0x1332, 0x123B, 0x123C, 0x123D, 0x11ED]
cases = [
    ("baseline", [0xA1, 0xB2, 0xC3, 0x31, 0x42, 0x53, 0x24]),
    ("modified", [0xC3, 0xA1, 0xB2, 0x53, 0x31, 0x42, 0x23]),
    ("restored", [0xA1, 0xB2, 0xC3, 0x31, 0x42, 0x53, 0x24]),
]
ledger = []
for label, markers in cases:
    dest = OUT / label
    dest.mkdir(exist_ok=True)
    insertion = "\n".join(
        f" movb ${value},acquired+{offset}" for offset, value in zip(offsets, markers)
    )
    assert source.count(" rep movsb\n push $invsize") == 1
    asm = source.replace(
        " rep movsb\n push $invsize", " rep movsb\n" + insertion + "\n push $invsize"
    )
    (dest / "test.s").write_text(asm)
    commands = [
        ["as", "--32", str(dest / "test.s"), "-o", str(dest / "test.o")],
        [
            "ld",
            "-m",
            "elf_i386",
            "--section-start=.nvram=0x09ed7764",
            "--section-start=.cbs=0x09eba21c",
            "-o",
            str(dest / "test.elf"),
            str(dest / "test.o"),
        ],
    ]
    for section in modules:
        commands.append(
            [
                "objcopy",
                "--dump-section",
                f".{section}={dest / section}",
                str(dest / "test.elf"),
            ]
        )
    commands.append(["timeout", "3", str(dest / "test.elf")])
    entry = {
        "case": label,
        "input": dict(zip(map(hex, offsets), markers)),
        "commands": [],
    }
    ledger.append(entry)
    for command in commands:
        run = subprocess.run(command, cwd=ROOT, capture_output=True)
        entry["commands"].append(
            {
                "command": command,
                "exit": run.returncode,
                "stdout_hex": run.stdout.hex(),
                "stderr": run.stderr.decode(errors="replace"),
            }
        )
        (OUT / "result.json").write_text(json.dumps(ledger, indent=2) + "\n")
        assert run.returncode == 0 and not run.stderr, entry
    for section, (filename, _) in modules.items():
        assert (dest / section).read_bytes() == (CORPUS / filename).read_bytes()
    assert len(run.stdout) == 64
    words = struct.unpack("<16I", run.stdout)
    entry["output"] = dict(zip(map(hex, tokens), words[6:13]))
    assert list(words[6:13]) == markers, entry
    assert words[13:] == (1122, 127, 5628), words
    entry["module_sections_exact"] = True
    print(label, entry["input"], "->", entry["output"], "exit=0 stderr=empty")
assert ledger[0]["output"] == ledger[2]["output"]
assert hashlib.sha256(ROM.read_bytes()).hexdigest() == ROM_SHA
(OUT / "result.json").write_text(json.dumps(ledger, indent=2) + "\n")
print("PASS unequal-marker serializer discrimination; no hardware meaning inferred")
