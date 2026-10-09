#!/usr/bin/env python3
"""Check the exact CLV memory-clock enum map and first opaque ABL callsite."""
from __future__ import annotations
import hashlib
import json
import re
import subprocess
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ROM = ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin"
PAY = ROOT / "evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin"
LISTING = OUT / "abl1-data-thumb-llvm.txt"
MENU = OUT / "menu-result.json"
ROM_SHA = "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"
PAY_SHA = "af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a"
MENU_SHA = "6e2d1978f7dcfdb4e780b220503d1a14401cb34c9d65104ca98840a47e2af14a"
LIST_SHA = "b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def check(checks, name, got, expected):
    passed = got == expected
    checks.append({"name": name, "status": "PASS" if passed else "FAIL",
                   "got": got, "expected": expected})
    if not passed:
        raise AssertionError(f"{name}: got {got!r}; expected {expected!r}")


def instruction(lines, address):
    return next((line for line in lines if re.match(rf"\s*{address:x}:", line)), "")


def has_instruction(lines, address, pattern):
    return bool(re.search(pattern, instruction(lines, address), re.I))


def occurrences(data: bytes, value: bytes):
    hits = []
    start = 0
    while True:
        offset = data.find(value, start)
        if offset < 0:
            return hits
        hits.append(offset)
        start = offset + 1


def main():
    checks = []
    rom = ROM.read_bytes()
    payload = PAY.read_bytes()
    listing_text = LISTING.read_text(errors="replace")
    listing_lines = listing_text.splitlines()
    menu = json.loads(MENU.read_text())

    check(checks, "pinned ROM hash", sha(ROM), ROM_SHA)
    check(checks, "exact ABL1 payload hash", sha(PAY), PAY_SHA)
    check(checks, "exact ABL1 payload length", len(payload), 0x171A0)
    check(checks, "Thumb listing hash", sha(LISTING), LIST_SHA)
    check(checks, "exact IFR report hash", sha(MENU), MENU_SHA)
    check(checks, "IFR report ROM identity", menu["rom_sha256"], ROM_SHA)
    memory_question = next(q for q in menu["questions"] if q["qid"] == "0x20f")
    check(checks, "IFR field offset", memory_question["offset"], "0x316")
    check(checks, "IFR field label", memory_question["label"], "Memory Clock Speed")
    option = next(o for o in memory_question["options"] if o["value"] == 36)
    check(checks, "IFR enum 0x24 label", option["label"], "1800MHz")
    # The immutable NVAR body base+field offset is independently mapped by prior NVAR evidence;
    # this direct byte recheck is only input identity, not a repeated serializer proof.
    check(checks, "current stored byte at ROM 0x7E5", rom[0x7E5], 0x24)

    # Reuse the existing 65-check exact-ABL1 producer verifier (not a second map implementation).
    reused = subprocess.run(
        ["python3", "-B", str(OUT / "prior_producer_input_verify.py")],
        capture_output=True, text=True, check=False)
    (OUT / "reused-producer.stdout").write_text(reused.stdout)
    (OUT / "reused-producer.stderr").write_text(reused.stderr)
    (OUT / "reused-producer.exit").write_text(f"{reused.returncode}\n")
    check(checks, "reused producer verifier exit", reused.returncode, 0)
    producer = json.loads((OUT / "abl1-producer-input-result.json").read_text())
    check(checks, "reused producer verifier status", producer["status"], "PASS")
    check(checks, "reused producer verifier check count", producer["checks"], 65)

    # This code emits a branch table target for enum 0x24. Resolve its actual target from bytes.
    check(checks, "selector token source", has_instruction(listing_lines, 0x2264,
          r"movs\s+r0, #0x7"), True)
    check(checks, "selector call", has_instruction(listing_lines, 0x2266,
          r"bl\s+0x1f2c\b"), True)
    check(checks, "TBB branch-table instruction", has_instruction(listing_lines, 0x2286,
          r"tbb\s+\[pc, r0\]"), True)
    table_base = 0x228A
    enum_code = 0x24
    table_index = enum_code - 2
    table_byte = payload[table_base + table_index]
    target = table_base + (2 * table_byte)
    check(checks, "TBB enum-0x24 target", target, 0x2318)
    check(checks, "TBB selected MOVW", has_instruction(listing_lines, target,
          r"movw\s+r0, #0x708"), True)
    check(checks, "MOVW emitted policy integer", 0x708, 1800)
    check(checks, "policy value store into context+0x2C",
          has_instruction(listing_lines, 0x22BA, r"str\s+r0, \[r1, #0x2c\]"), True)

    # The selector normalizes the branch mode to 2 before it returns to the caller.
    check(checks, "selector mode literal", has_instruction(listing_lines, 0x2238,
          r"movs\s+r6, #0x2"), True)
    check(checks, "selector mode store", has_instruction(listing_lines, 0x2332,
          r"str\s+r6, \[r0, #0x28\]"), True)

    # Follow the exact shared ABL context only through the memory-speed configuration path.
    for address, pattern in [
        (0x7DAE, r"bl\s+0x221c\b"),
        (0x7E00, r"bl\s+0xad58\b"),
        (0xADCC, r"ldr\s+r1, \[r0, #0x28\]"),
        (0xADD0, r"cmp\s+r1, #0x2"),
        (0xADF8, r"ldr\s+r6, \[r0, #0x2c\]"),
        (0xAE22, r"strh\s+r6, \[r0, #0x20\]"),
        (0x7E30, r"bl\s+0x10cc0\b"),
        (0x10E50, r"strh\s+r7, \[r0, #0x20\]"),
    ]:
        check(checks, f"instruction semantics at {address:#x}",
              has_instruction(listing_lines, address, pattern), True)

    # Stop at the following opaque service dispatch; item 0x17 is not an SMU queue/message ID.
    check(checks, "post-reducer service item", has_instruction(listing_lines, 0x7E36,
          r"movs\s+r1, #0x17"), True)
    check(checks, "post-reducer service context", has_instruction(listing_lines, 0x7E38,
          r"mov\s+r2, r4"), True)
    check(checks, "first unresolved service call", has_instruction(listing_lines, 0x7E3A,
          r"bl\s+0xc60\b"), True)

    string_bytes = [
        b"MemClkFreq = %d MHz",
        b"Read Memory Clock Speed     :  %04d MHz",
        b"Override Memory Clock Speed: %04dMHz",
        b"Program DRAM timing per memory clock",
        b"Highest Common MemClkFreq for all channels: %d",
    ]
    string_locations = {}
    for value in string_bytes:
        hits = occurrences(payload, value)
        check(checks, f"exact policy-unit string {value.decode('latin1')}", bool(hits), True)
        string_locations[value.decode("latin1")] = [hex(hit) for hit in hits]

    result = {
        "status": "PASS",
        "checks": len(checks),
        "evidence_class": ["observed-bytes", "static-analysis"],
        "input": {"rom": str(ROM), "rom_sha256": sha(ROM), "size": len(rom),
                  "abl1_payload": str(PAY), "abl1_sha256": sha(PAY),
                  "payload_size": len(payload)},
        "reused_verifier": {"path": str(OUT / "prior_producer_input_verify.py"),
                            "status": producer["status"], "checks": producer["checks"]},
        "enum_to_policy": {
            "field": "AmdSetup+0x316; IFR QID 0x20F",
            "stored_enum": "0x24",
            "IFR_label": "1800MHz",
            "ABL_lookup": "token 7 / timepoint 2 in existing ABL1 selector path; direct source identity with AmdSetup/$INV is not proven",
            "TBB_target": hex(target),
            "emitted_literal": "0x708",
            "decimal_policy_value": 1800,
            "unit_evidence": "Exact ABL1 strings name MemClkFreq and memory-clock values in MHz; this is a MHz-tagged policy integer, not proof of physical clock or GDDR6 data rate.",
            "string_offsets": string_locations,
        },
        "memory_policy_path": {
            "caller": "0x7DAE -> 0x221C with same context r4 and selector 2",
            "table": "0x228A + 2*(enum-2); enum 0x24 selects 0x2318 -> MOVW r0,#0x708",
            "config_context": "0x22BA stores numeric result to [r4+0x04]+0x2C; mode 2 is stored at 0x2332",
            "speed_writer": "0x7E00 -> 0xAD58; in branch mode==2, 0xADF8 loads context+0x2C; 0xAE22 writes selected halfword to channel+0x20",
            "reducer": "0x7E30 -> 0x10CC0; 0x10E50 writes reduced halfword to channel+0x20",
            "next_call": "0x7E34..0x7E3A passes ABL item 0x17 and context r4 to 0x0C60",
        },
        "first_missing_consumer_boundary": "ABL service item 0x17 called at payload 0x7E3A into 0x0C60. This track stops at the service boundary; the provider/consumer is unresolved and is owned by the separate APOB/ABL handoff track.",
        "limits": [
            "No direct AmdSetup+0x316/$INV 0x11ED -> ABL token-7 input edge is established.",
            "No PLL/register conversion, physical MCLK, GDDR6 edge/data-rate conversion, WCK, synchronous crossing, training acceptance or hardware result is established.",
            "No UCLK divider or DF override consumer was followed.",
            "No board, firmware execution, candidate, NVRAM, MMIO or hardware operation occurred.",
        ],
        "checks_detail": checks,
    }
    (OUT / "memory-clock-units-next-result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": "PASS", "checks": len(checks),
                      "enum_0x24_policy_integer": 1800,
                      "first_missing_consumer": "0x7E3A -> 0x0C60 item 0x17"}, indent=2))


if __name__ == "__main__":
    main()
