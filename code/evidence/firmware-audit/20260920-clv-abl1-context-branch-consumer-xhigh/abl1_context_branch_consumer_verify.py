#!/usr/bin/env python3
"""Verify exact ABL1 field-branch consequences and the first indirect dispatcher."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ABL = (
    ROOT
    / "evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin"
)
DIS = (
    ROOT
    / "evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt"
)
PRIOR = (
    ROOT
    / "evidence/firmware-audit/20260920-clv-abl1-reader-output-context-xhigh/abl1-reader-output-context-result.json"
)
EXPECTED = {
    "abl": "af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a",
    "dis": "b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65",
    "prior": "6abae87817c9aa5baf8565524b071f5fae6d19ad5e478d140e22fdea0da42c21",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(checks: list[dict], name: str, got, expected) -> None:
    passed = got == expected
    checks.append({"check": name, "passed": passed, "got": got, "expected": expected})
    if not passed:
        raise AssertionError(f"{name}: got {got!r}, expected {expected!r}")


def line_at(text: str, offset: int) -> str:
    hits = re.findall(rf"^\s*{offset:x}:.*$", text, re.MULTILINE)
    if len(hits) != 1:
        raise AssertionError(f"listing {offset:#x}: expected 1 line, got {len(hits)}")
    return hits[0]


def main() -> None:
    checks: list[dict] = []
    for name, path, expected in (
        ("exact ABL1", ABL, EXPECTED["abl"]),
        ("exact listing", DIS, EXPECTED["dis"]),
        ("prior result", PRIOR, EXPECTED["prior"]),
    ):
        check(checks, f"{name} exists", path.exists(), True)
        check(checks, f"{name} SHA-256", sha(path), expected)
    blob = ABL.read_bytes()
    listing = DIS.read_text(errors="replace")
    prior = json.loads(PRIOR.read_text())
    check(checks, "prior result status", prior["status"], "PASS")
    check(checks, "prior result checks reused by hash only", prior["checks"], 59)

    raw = {
        0x10496: "40f21869",  # r9 = 0x618 before the consequent block
        0x107DC: "4946",  # mov r1,r9
        0x107E0: "00f0baf8",  # first call to 0x10958
        0x107E4: "b4f87800",  # ldrh r0,[r4,#0x78]
        0x107E8: "40f21e61",  # r1 = 0x61e before dispatch
        0x107EC: "b0f57a7f",  # cmp r0,#0x3e8
        0x107F2: "b0f5966f",  # cmp r0,#0x4b0
        0x107F8: "10e0",  # default branch 0x1081c
        0x107FA: "b542",  # cmp r5,r6
        0x107FE: "40f26422",  # r2=0x264
        0x10804: "bd42",  # cmp r5,r7
        0x10808: "40f26442",  # r2=0x464
        0x1080E: "bd42",  # cmp r5,r7
        0x10812: "b542",  # cmp r5,r6
        0x10816: "40f26022",  # r2=0x260
        0x1081C: "0022",  # default r2=0
        0x1081E: "204600f09af8",  # r0=r4; BL 0x10958
        0x10824: "0122",  # r2=1
        0x10826: "40f20521",  # r1=0x205
        0x1082C: "00f094f8",  # BL 0x10958
        0x10830: "0022",  # r2=0
        0x10832: "40f2f711",  # r1=0x1f7
        0x10838: "00f08ef8",  # BL 0x10958
        0x1083C: "1822",  # r2=0x18
        0x1083E: "40f21e21",  # r1=0x21e
        0x10844: "00f088f8",  # BL 0x10958
        0x10848: "424a",  # load literal pointer argument
        0x1084A: "40f22261",  # r1=0x622
        0x10850: "00f082f8",  # BL 0x10958
        0x10854: "04f53174",  # R4 = prior R4 + context offset 0x2C4
        0x1085A: "2168",  # R1 = child pointer stored at [R4]
        0x1085C: "c880",  # STRH R0,[R1,#6]
        0x10862: "2168",  # reload same child pointer
        0x10864: "a1f84400",  # STRH R0,[R1,#0x44]
        0x1086C: "2168",  # reload same child pointer
        0x1086E: "a1f84600",  # STRH R0,[R1,#0x46]
        0x10876: "2168",  # reload same child pointer
        0x10878: "a1f84c00",  # STRH R0,[R1,#0x4c]
        0x1087E: "a4f53174",  # restore R4 context base
        0x10890: "00f062f8",  # BL 0x10958 token 0x2ba
        0x108A0: "00f05af8",  # BL 0x10958 token 0x2bb
        0x108B8: "00f04ef8",  # BL 0x10958 token 0x2bc
        0x108CA: "00f045f8",  # BL 0x10958 token 0x2bd
        0x108D6: "faf71ffa",  # BL 0xad18 helper 0x2be
        0x108FC: "00f02cf8",  # BL 0x10958 derived value
        0x10946: "00f007f8",  # final BL 0x10958
        0x10958: "30b4",  # dispatcher prologue
        0x1095A: "d0f86046",  # LDR r4,[r0,#0x660]; mov r3,r2
        0x1095E: "13460a46",  # mov r2,r1; mov r12,r4
        0x10962: "a44630bc",  # mov r12,r4; restore saved r4/r5
        0x10966: "0121",  # R1 = 1
        0x10968: "6047",  # BX r12
    }
    for offset, expected in raw.items():
        check(
            checks,
            f"raw bytes at {offset:#x}",
            blob[offset : offset + len(bytes.fromhex(expected))].hex(),
            expected,
        )

    expected_lines = {
        0x107EC: "cmp.w\tr0, #0x3e8",
        0x107F2: "cmp.w\tr0, #0x4b0",
        0x107F8: "b\t0x1081c",
        0x107FA: "cmp\tr5, r6",
        0x107FE: "movw\tr2, #0x264",
        0x10808: "movw\tr2, #0x464",
        0x10816: "movw\tr2, #0x260",
        0x1081E: "mov\tr0, r4",
        0x10820: "bl\t0x10958",
        0x1082C: "bl\t0x10958",
        0x10838: "bl\t0x10958",
        0x10844: "bl\t0x10958",
        0x10850: "bl\t0x10958",
        0x10854: "add.w\tr4, r4, #0x2c4",
        0x1085A: "ldr\tr1, [r4]",
        0x1085C: "strh\tr0, [r1, #0x6]",
        0x10864: "strh.w\tr0, [r1, #0x44]",
        0x1086E: "strh.w\tr0, [r1, #0x46]",
        0x10878: "strh.w\tr0, [r1, #0x4c]",
        0x1087E: "sub.w\tr4, r4, #0x2c4",
        0x108D6: "bl\t0xad18",
        0x10958: "push\t{r4, r5}",
        0x1095A: "ldr.w\tr4, [r0, #0x660]",
        0x1095E: "mov\tr3, r2",
        0x10960: "mov\tr2, r1",
        0x10962: "mov\tr12, r4",
        0x10966: "movs\tr1, #0x1",
        0x10968: "bx\tr12",
    }
    for offset, fragment in expected_lines.items():
        check(
            checks,
            f"listing instruction at {offset:#x}",
            fragment in line_at(listing, offset),
            True,
        )

    # r9 is overwritten exactly once after entry and before the branch use;
    # no guessed loader/base mapping is needed for this register fact.
    segment = listing.splitlines()
    r9writes = []
    for line in segment:
        m = re.match(r"\s*([0-9a-f]+):", line)
        if not m:
            continue
        off = int(m.group(1), 16)
        parts = line.split("\t")
        ins = "\t".join(parts[1:3]).strip() if len(parts) >= 3 else ""
        if 0x1021C <= off <= 0x107DC and re.match(r"(?:movw|mov\.w|mov)\s+r9,", ins):
            r9writes.append(line.strip())
    check(
        checks,
        "r9 assignments through branch use",
        r9writes,
        [line_at(listing, 0x1021C).strip(), line_at(listing, 0x10496).strip()],
    )

    result = {
        "status": "PASS",
        "checks": len(checks),
        "evidence_class": ["observed-bytes", "static-analysis"],
        "inputs": {
            "abl1": str(ABL),
            "disassembly": str(DIS),
            "prior_result": str(PRIOR),
        },
        "hashes": {
            "abl1": sha(ABL),
            "disassembly": sha(DIS),
            "prior_result": sha(PRIOR),
        },
        "branch": {
            "field_load": "0x107E4 LDRH R0,[R4,#0x78]",
            "compare_0x3e8": "taken path 0x107FA -> 0x107FE -> 0x10802 -> 0x1081E; selects R2=0x264 or R2=0x464 after R5 comparisons",
            "compare_0x4b0": "taken path 0x1080E -> 0x10816 -> 0x1081E; selects R2=0x260 when R5 matches R7 or R6",
            "default": "0x107F8 -> 0x1081C -> 0x1081E; selects R2=0",
            "first_dispatch_arguments": "R0=context; prior R1=0x61E; branch-selected prior R2 in {0,0x260,0x264,0x464}; dispatcher 0x10958 presents R1=1, R2=0x61E, R3=branch-selected prior R2 to BX R12 target",
            "convergent_calls": [
                "0x10820",
                "0x1082C",
                "0x10838",
                "0x10844",
                "0x10850",
                "0x10890",
                "0x108A0",
                "0x108B8",
                "0x108CA",
                "0x108FC",
                "0x10946",
            ],
            "context_data_writes": {
                "pointer_source": "R4 = context + 0x2C4 at 0x10854; R1 = [R4] at 0x1085A",
                "stores": [
                    "STRH R0,[R1+0x06] at 0x1085C",
                    "STRH R0,[R1+0x44] at 0x10864",
                    "STRH R0,[R1+0x46] at 0x1086E",
                    "STRH R0,[R1+0x4C] at 0x10878",
                ],
                "classification": "stores through the pointer stored at context+0x2C4 into an in-memory child object; exact semantics/address mapping unknown; not direct MMIO evidence",
                "context_base_restored": "R4 -= 0x2C4 at 0x1087E",
            },
            "indirect_dispatcher": "0x10958 loads callback [R0+0x660], maps incoming R1 -> R2 and R2 -> R3, sets R1=1, and BX R12; no direct MMIO/register write is present in this callee",
            "classification": "configuration/timing-selection values are passed through an indirect callback and written to a child data object; no direct hardware-register programming is present in this bounded path. Callback target/effect remains unresolved because the context object's [R0+0x660] value is not bound to this call site.",
        },
        "checks_detail": checks,
    }
    (OUT / "abl1-context-branch-consumer-result.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "checks": len(checks),
                "branch": result["branch"],
            },
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
