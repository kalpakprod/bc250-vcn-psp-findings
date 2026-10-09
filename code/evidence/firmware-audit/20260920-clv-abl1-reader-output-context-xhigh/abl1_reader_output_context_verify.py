#!/usr/bin/env python3
"""Trace one exact ABL1 Fclk reader result into and out of its context field."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ROM = ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin"
ABL = (
    ROOT
    / "evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin"
)
DIS = (
    ROOT
    / "evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt"
)
READER = (
    ROOT
    / "evidence/firmware-audit/20260920-clv-abl1-apcb-reader-boundary-resume/abl1-apcb-reader-boundary-result.json"
)
BRANCH = (
    ROOT
    / "evidence/firmware-audit/20260920-clv-abl1-fclk-uclk-branch-xhigh/abl1-fclk-uclk-branch-result.json"
)
EXPECTED = {
    "rom": "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8",
    "abl": "af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a",
    "dis": "b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65",
    "reader": "537f987266057865bd7f278939304f2f40dcc5db4e57c6048ca0905ce2dac128",
    "branch": "d6d053b5e4a74a5b4fe0526e4d4659d22a500601074baad751977ab21e2ecdfa",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(checks: list[dict], name: str, got, expected) -> None:
    passed = got == expected
    checks.append({"check": name, "passed": passed, "got": got, "expected": expected})
    if not passed:
        raise AssertionError(f"{name}: got {got!r}, expected {expected!r}")


def listing_line(text: str, offset: int) -> str:
    pattern = re.compile(rf"^\s*{offset:x}:.*$", re.MULTILINE)
    matches = pattern.findall(text)
    if len(matches) != 1:
        raise AssertionError(
            f"listing offset {offset:#x}: expected one line, found {len(matches)}"
        )
    return matches[0]


def main() -> None:
    checks: list[dict] = []
    paths = {"rom": ROM, "abl": ABL, "dis": DIS, "reader": READER, "branch": BRANCH}
    for name, path in paths.items():
        check(checks, f"{name} exists", path.exists(), True)
        check(checks, f"{name} sha256", sha(path), EXPECTED[name])

    blob = ABL.read_bytes()
    listing = DIS.read_text(errors="replace")
    reader = json.loads(READER.read_text())
    branch = json.loads(BRANCH.read_text())
    check(checks, "prior reader result status", reader.get("status"), "PASS")
    check(
        checks,
        "prior reader descriptors",
        reader["reader"]["descriptor_pairs"],
        {
            "UclkDiv1M0": ["0x20", "0x21"],
            "UclkDiv1M1": ["0x20", "0x22"],
            "UclkDiv1M2": ["0x20", "0x23"],
            "UclkDiv1M3": ["0x20", "0x24"],
            "Fclk": ["0x15f", "0x160"],
        },
    )
    check(checks, "prior branch result status", branch.get("status"), "PASS")
    check(
        checks,
        "prior Fclk descriptors",
        branch["exact_fclk_branch"]["descriptor"],
        ["0x015f", "0x0160"],
    )

    raw = [
        (0x1FC4, "1646", "reader output argument R2 copied to R6"),
        (0x2042, "9af80000", "reader loads type byte from caller type pointer"),
        (0x2070, "3080", "type-2 reader store is STRH R0,[R6]"),
        (0x4662, "04a8", "Fclk caller passes its local descriptor at SP+0x10"),
        (0x4668, "02aa", "Fclk caller passes its result slot at SP+0x08"),
        (0x466A, "fdf7a3fc", "Fclk caller BLs to reader 0x1FB4"),
        (0x467E, "bdf80800", "Fclk branch first loads returned halfword from SP+0x08"),
        (0x4682, "2860", "Fclk branch stores through its caller-provided pointer"),
        (0x5E68, "2de9ff47", "Fclk receiving routine saves R4-R10 and LR"),
        (0x5E70, "0546", "Fclk receiving routine copies context argument R0 to R5"),
        (0x5FA4, "40f2b040", "caller seeds its output local with immediate 0x4B0"),
        (0x5FAC, "01a8fef745fb", "caller passes SP+0x04 and BLs Fclk routine 0x463C"),
        (0x5FB2, "019b", "caller reads the output local after Fclk routine returns"),
        (0x5FBA, "a5f87830", "caller stores returned halfword at context+0x78"),
        (0x6024, "bde8ff87", "Fclk receiving routine restores saved R4 before return"),
        (0x7E72, "2046", "outer routine passes its R4 context pointer in R0"),
        (
            0x7E74,
            "fdf7f8ff",
            "outer routine directly calls Fclk receiving routine 0x5E68",
        ),
        (0x8426, "2046", "same outer routine later passes R4 in R0 again"),
        (
            0x8428,
            "07f0eafe",
            "same outer routine directly calls context reader 0x10200",
        ),
        (0x10200, "2de9f043", "context reader saves R4-R9 and LR"),
        (0x10208, "0446", "context reader copies R0 context argument into R4"),
        (0x104B2, "6ed1", "conditional path to downstream Fclk consumer block"),
        (0x10592, "22e1", "branch to downstream block 0x107DA"),
        (
            0x107E0,
            "00f0baf8",
            "downstream block calls local helper before reading field",
        ),
        (0x107E4, "b4f87800", "first identified downstream load is LDRH R0,[R4,#0x78]"),
        (0x107EC, "b0f57a7f", "first downstream comparison against immediate 0x3E8"),
        (0x107F2, "b0f5966f", "next downstream comparison against immediate 0x4B0"),
    ]
    for offset, expected, label in raw:
        check(
            checks,
            f"raw {offset:#x}: {label}",
            blob[offset : offset + len(bytes.fromhex(expected))].hex(),
            expected,
        )

    expected_lines = {
        0x2D0C: "bl\t0x1fb4",
        0x2D12: "ldrb.w\tr3, [sp, #0xc]",
        0x466A: "bl\t0x1fb4",
        0x467E: "ldrh.w\tr0, [sp, #0x8]",
        0x4682: "str\tr0, [r5]",
        0x5FAE: "bl\t0x463c",
        0x5FB2: "ldr\tr3, [sp, #0x4]",
        0x5FBA: "strh.w\tr3, [r5, #0x78]",
        0x7E74: "bl\t0x5e68",
        0x8428: "bl\t0x10200",
        0x10208: "mov\tr4, r0",
        0x104B2: "bne\t0x10592",
        0x10592: "b\t0x107da",
        0x107E4: "ldrh.w\tr0, [r4, #0x78]",
    }
    for offset, fragment in expected_lines.items():
        line = listing_line(listing, offset)
        check(checks, f"listing {offset:#x} instruction", fragment in line, True)

    # Demonstrate the exact context register stays the argument base across the
    # two relevant direct calls and inside the consumer routine before the load.
    write_ops = {
        "add",
        "add.w",
        "adds",
        "adr",
        "and",
        "ands",
        "asr",
        "asrs",
        "bfi",
        "eor",
        "eors",
        "ldr",
        "ldr.w",
        "ldrb",
        "ldrb.w",
        "ldrh",
        "ldrh.w",
        "ldrsb",
        "ldrsb.w",
        "ldrd",
        "lsl",
        "lsls",
        "lsr",
        "lsrs",
        "mov",
        "mov.w",
        "movs",
        "movt",
        "movw",
        "mvn",
        "mvns",
        "mul",
        "muls",
        "orr",
        "orr.w",
        "orrs",
        "pop",
        "rsb",
        "rsbs",
        "sxtb",
        "uxtb",
        "uxth",
        "sub",
        "sub.w",
        "subs",
    }

    def writes_r4(start: int, stop: int) -> list[str]:
        found = []
        for line in listing.splitlines():
            m = re.match(r"\s*([0-9a-f]+):\s+\S+\s+([^\t]+)", line)
            if not m or not start <= int(m.group(1), 16) < stop:
                continue
            ins = m.group(2).strip().split("@", 1)[0].strip()
            op, _, operands = ins.partition(" ")
            if op.lower() in write_ops and operands.split(",", 1)[0].strip() == "r4":
                found.append(line.strip())
        return found

    check(
        checks,
        "outer context R4 has no explicit write between the two direct calls",
        writes_r4(0x7E74, 0x8428),
        [],
    )
    check(
        checks,
        "consumer context R4 has no explicit write before offset load",
        writes_r4(0x10208, 0x107E4),
        [],
    )
    loads = [
        line.strip()
        for line in listing.splitlines()
        if re.search(r"\bldrh\.w\s+r0, \[r4, #0x78\]", line)
    ]
    check(checks, "full listing count for direct LDRH R0,[R4,#0x78]", len(loads), 1)
    check(
        checks,
        "unique field load is at 0x107E4",
        listing_line(listing, 0x107E4).strip(),
        loads[0],
    )

    result = {
        "status": "PASS",
        "checks": len(checks),
        "evidence_class": ["observed-bytes", "static-analysis"],
        "inputs": {name: str(path) for name, path in paths.items()},
        "hashes": {name: sha(path) for name, path in paths.items()},
        "result": {
            "reader_typed_store": "type 2 executes STRH R0,[R6] at payload+0x2070; R6 receives caller R2",
            "uclk_output_boundary": "the exact UclkDiv1 M0..M3 callers pass SP+0x0C as output; first post-return byte load at 0x2D12 is then sent to logger; no persistent context store is established in these four slices",
            "fclk_output_path": [
                "Fclk descriptor [0x015F,0x0160] is supplied at 0x4662; output pointer is SP+0x08 at 0x4668; reader call is 0x466A.",
                "Returned halfword is loaded from SP+0x08 at 0x467E and stored through the handler's output pointer at 0x4682.",
                "Direct caller 0x5E68 is called at 0x7E74 with R0=R4; its Fclk subcall at 0x5FAE receives R0=SP+0x04, then caller loads that local at 0x5FB2 and stores its low halfword at [context+0x78] at 0x5FBA.",
                "The same outer R4 base is passed at 0x8428 to 0x10200. That routine copies R0 into R4 at 0x10208; its reachable branch 0x104B2 -> 0x10592 -> 0x107DA reaches the first identified load [R4+0x78] at 0x107E4, followed by comparisons to immediates 0x3E8 and 0x4B0.",
            ],
            "claim_boundary": "Static ABL1 dataflow only. The comparisons and selected branch constants are observed, but units, value meaning, loader/runtime invocation, MCLK-UCLK-FCLK equality, divider/PLL application, memory training, and physical clocks are not established. The conditional 0x57100 mapping is not used as loader proof.",
        },
        "checks_detail": checks,
    }
    target = OUT / "abl1-reader-output-context-result.json"
    target.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "status": result["status"],
                "checks": len(checks),
                "context_store": "0x5FBA [R5+0x78]",
                "first_downstream_load": "0x107E4 LDRH R0,[R4,#0x78]",
                "claim_boundary": result["result"]["claim_boundary"],
            },
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
