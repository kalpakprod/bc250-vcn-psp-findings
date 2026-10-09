"""Execute original VCORE/GFX enable branch and staging, with two IO stop hooks."""

import hashlib
import json
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
SOURCE = (
    ROOT
    / "evidence/firmware-audit/20260919-inv-token-consumers/ISL69247-3e1f753a6279.bin"
)
rom = ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin"
rom_sha = hashlib.sha256(rom.read_bytes()).hexdigest()
assert rom_sha == "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"
b = SOURCE.read_bytes()
assert (
    hashlib.sha256(b).hexdigest()
    == "3e1f753a627922d16e5a638a527e39f4dd26242144edae25b0ac849db6421e34"
)
assert rom.read_bytes()[0xED2C74 : 0xED2C74 + len(b)] == b
src = (OUT.parent / "staging.s").read_text()
assert " mov $payload,%edi\n push $0x21\n mov $0x09ed31c9,%eax\n call *%eax" in src
log = []
for rail, entry, enableoff, valueoff in [
    ("VCORE_label", 0x30A, 0x1C9, 0x1CA),
    ("GFX_label", 0x3A8, 0x1CD, 0x1CE),
]:
    for case, enabled, value, expected in [
        ("baseline", 0, 0x123, 900),
        ("modified", 1, 0x123, 0x123),
        ("changed_word", 1, 0x456, 0x456),
        ("disabled_changed_word", 0, 0x456, 900),
        ("restored", 0, 0x123, 900),
    ]:
        d = OUT / rail / case
        d.mkdir(parents=True, exist_ok=True)
        init = f" mov $setup+0x178,%ebp\n xor %ebx,%ebx\n mov $900,%esi\n movb ${enabled},setup+{enableoff}\n movw ${value},setup+{valueoff}\n mov ${hex(0x09ED2ADC + entry)},%eax\n jmp *%eax"
        asm = src.replace(
            " mov $payload,%edi\n push $0x21\n mov $0x09ed31c9,%eax\n call *%eax", init
        ).replace("payload: .long VALUE", "setup: .space 0x300")
        (d / "test.s").write_text(asm)
        commands = [
            ["as", "--32", str(d / "test.s"), "-o", str(d / "test.o")],
            [
                "ld",
                "-m",
                "elf_i386",
                "--section-start=.instrumented=0x09ed2c74",
                "-o",
                str(d / "test.elf"),
                str(d / "test.o"),
            ],
            [
                "objcopy",
                "--dump-section",
                ".instrumented=" + str(d / "module.bin"),
                str(d / "test.elf"),
            ],
            ["timeout", "3", str(d / "test.elf")],
        ]
        e = {
            "rail_label": rail,
            "case": case,
            "enable": enabled,
            "word": value,
            "entry_rva": hex(entry),
            "commands": [],
        }
        log.append(e)
        for cmd in commands:
            r = subprocess.run(cmd, cwd=ROOT, capture_output=True, check=False)
            e["commands"].append(
                {
                    "command": cmd,
                    "exit": r.returncode,
                    "stdout_hex": r.stdout.hex(),
                    "stderr": r.stderr.decode(errors="replace"),
                }
            )
            (OUT / "result.json").write_text(json.dumps(log, indent=2) + "\n")
            assert r.returncode == 0 and not r.stderr, e
        emitted = (d / "module.bin").read_bytes()
        assert len(emitted) == len(b)
        patches = set(range(0x3CD, 0x3D2)) | set(range(0x59B, 0x5A0))
        assert all(
            x == y for i, (x, y) in enumerate(zip(b, emitted)) if i not in patches
        )
        assert emitted[0x3CD] == emitted[0x59B] == 0xE9
        assert len(r.stdout) == 48
        trace = list(struct.iter_unpack("<II", r.stdout))
        assert trace == [
            (0x65, 0xC0),
            (0x66, 0x21),
            (0x70, expected & 255),
            (0x71, expected >> 8),
            (0x63, 3),
            (0x60, 0xC0),
        ], trace
        e["trace"] = trace
        e["noninstrumented_bytes_exact"] = True
        print(
            rail,
            case,
            "enable=" + str(enabled),
            "input=" + hex(value),
            "staged=" + hex(expected),
            "exit0 stderr empty",
        )
    assert log[-5]["trace"] == log[-1]["trace"]
assert hashlib.sha256(rom.read_bytes()).hexdigest() == rom_sha
(OUT / "result.json").write_text(json.dumps(log, indent=2) + "\n")
print(
    "PASS10 caller cases; synthetic setup frame; stops before hardware; physical rail/voltage not proven"
)
