"""Byte-backed PLL-service boundary, not runtime or physical-clock verification."""

import hashlib
import json
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
D = Path(__file__).resolve().parent
P = (
    ROOT
    / "evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin"
)
b = P.read_bytes()
assert (
    hashlib.sha256(b).hexdigest()
    == "af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a"
)
obj = (
    ROOT
    / "evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/ABL1-exact.o"
)
commands = []
for start, end, label in [
    (0x5E68, 0x602C, "pll-body"),
    (0x463C, 0x4698, "fclk-override"),
    (0x7E30, 0x7E7C, "pll-caller"),
    (0x6C20, 0x6C5C, "topology-builder"),
]:
    cmd = [
        "llvm-objdump",
        "-D",
        "--triple=thumbv7m-none-eabi",
        f"--start-address={hex(start)}",
        f"--stop-address={hex(end)}",
        str(obj),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, check=False)
    commands.append(
        {
            "command": cmd,
            "exit": r.returncode,
            "stderr": r.stderr,
            "stdout_file": str(D / (label + ".txt")),
        }
    )
    (D / (label + ".txt")).write_text(r.stdout)
    assert r.returncode == 0 and not r.stderr
checks = {
    0x5E70: "0546",
    0x5E72: "8846",
    0x5E74: "1446",
    0x5F30: "4fea5408",
    0x5F9A: "6868",
    0x5F9C: "b0f89007",
    0x5FA0: "0628",
    0x5FA2: "41d0",
    0x5FA4: "40f2b040",
    0x5FA8: "0190",
    0x5FAA: "0f21",
    0x5FAC: "01a8",
    0x5FB2: "019b",
    0x5FBA: "a5f87830",
    0x5FC2: "0e20",
    0x5FC4: "0199",
    0x5FC6: "02aa",
    0x5FC8: "28df",
    0x5FF4: "0f20",
    0x5FF6: "4146",
    0x5FF8: "02aa",
    0x5FFA: "28df",
    0x6028: "fa20",
    0x602A: "bde7",
    0x4648: "0f29",
    0x464A: "1bd1",
    0x464E: "40f25f10",
    0x4670: "bdf80830",
    0x467E: "bdf80800",
    0x4682: "2860",
}
for off, h in checks.items():
    assert b[off : off + len(bytes.fromhex(h))] == bytes.fromhex(h), (
        hex(off),
        b[off : off + 4].hex(),
        h,
    )
strings = {}
for pc, expected in [
    (0x5FB6, b"Send PSPSMC_MSG_SetupFclkPll 0x%x\n"),
    (0x5FEC, b"Send PSPSMC_MSG_SetupUclkPll  0x%x\n"),
    (0x961A, b"\nAGESA MEM - Multi-Die - DRAM Speed Sync\n"),
]:
    half = struct.unpack_from("<H", b, pc)[0]
    assert half & 0xF800 == 0xA000
    target = ((pc + 4) & ~3) + 4 * (half & 255)
    value = b[target : b.index(0, target)]
    assert value == expected
    strings[hex(pc)] = {"target": hex(target), "text": value.decode()}
result = {
    "status": "PASS_STATIC_SERVICE_BOUNDARY",
    "payload_sha256": hashlib.sha256(b).hexdigest(),
    "commands": commands,
    "checked_instructions": len(checks),
    "strings": strings,
    "edges": {
        "FCLK": "post-463C [SP+4] -> STRH context+78 -> SVC28 R0=0E,R1=[SP+4],R2=SP+8",
        "UCLK": "entry R2 saved in R4;5F30 R8=R4 logical_shift_right1; SVC28 R0=0F,R1=R8,R2=SP+8 (callee-preserved register convention assumed)",
    },
    "default_before_override": {"nested_context_plus790_equals6": 250, "other": 1200},
    "override": "463C selector0F asks provider1FB4 using descriptor015F/0160; nonzero provider return replaces output with u16; zero return leaves default",
    "limits": [
        "Static code, no execution or physical clock/voltage proof",
        "SVC28 handler and message ID translation not resolved",
        "Do not treat SVC selector0E/0F as public SMU mailbox IDs",
        "Logging callbacks and external services remain unexecuted",
        "Override source is not yet joined to AmdSetup DF field",
    ],
}
(D / "result.json").write_text(json.dumps(result, indent=2) + "\n")
print(
    "PASS",
    len(checks),
    "instruction byte anchors;3 ADR strings;FCLK/UCLK SVC28 argument paths",
)
