#!/usr/bin/env python3
"""Verify one conditional ABL1 +0x660 callback installation and consumer edge."""

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
BRANCH = (
    ROOT
    / "evidence/firmware-audit/20260920-clv-abl1-context-branch-consumer-xhigh/abl1-context-branch-consumer-result.json"
)
BASE_EVIDENCE = (
    ROOT
    / "evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-producer-trace-result.json"
)
EXPECTED = {
    "rom": "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8",
    "abl": "af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a",
    "dis": "b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65",
    "branch": "269049d9fb13f32dbf8c037f85ebfe695fd5099e37fe354e8b2a939d1c4cf671",
    "base": "d9b40965d4901df0544e460da7e16ac30b4ccd4cd97b07d2de2ec8b1afddf5f8",
}
BASE = 0x57100


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(checks: list[dict], name: str, got, expected) -> None:
    ok = got == expected
    checks.append({"check": name, "passed": ok, "got": got, "expected": expected})
    if not ok:
        raise AssertionError(f"{name}: got {got!r}, expected {expected!r}")


def line_at(text: str, offset: int) -> str:
    hits = re.findall(rf"^\s*{offset:x}:.*$", text, re.MULTILINE)
    if len(hits) != 1:
        raise AssertionError(f"listing {offset:#x}: expected one line, got {len(hits)}")
    return hits[0]


def main() -> None:
    checks: list[dict] = []
    paths = {
        "rom": ROM,
        "abl": ABL,
        "dis": DIS,
        "branch": BRANCH,
        "base": BASE_EVIDENCE,
    }
    for name, path in paths.items():
        check(checks, f"{name} exists", path.exists(), True)
        check(checks, f"{name} SHA-256", sha(path), EXPECTED[name])
    blob = ABL.read_bytes()
    listing = DIS.read_text(errors="replace")
    branch = json.loads(BRANCH.read_text())
    base_result = json.loads(BASE_EVIDENCE.read_text())
    check(checks, "prior branch result status", branch["status"], "PASS")
    check(checks, "prior branch checks reused by hash", branch["checks"], 89)
    check(checks, "prior base result status", base_result["status"], "PASS")
    check(
        checks,
        "prior conditional base",
        base_result["callback_boundary"]["candidate_runtime_base"],
        "0x57100",
    )
    check(
        checks,
        "prior independent base anchors",
        base_result["callback_boundary"]["independent_anchor_count"],
        4,
    )

    # Existing independent base anchors reproduce under the same conditional base.
    anchors = base_result["callback_boundary"]["anchors"]
    check(checks, "base anchor count", len(anchors), 4)
    for anchor in anchors:
        literal = int(anchor["literal"], 16)
        mapped = literal - BASE
        entry = mapped & ~1
        check(
            checks,
            f"base anchor {anchor['literal']} maps Thumb target",
            hex(mapped),
            anchor["mapped_thumb"].lower(),
        )
        check(
            checks,
            f"base anchor {anchor['literal']} maps entry",
            hex(entry),
            anchor["local_code_entry"].lower(),
        )

    raw = {
        0x7378: "2de9f043",  # function entry
        0x737C: "0546",  # R5 = arg0
        0x7384: "0e46",  # R6 = arg1
        0x738A: "1c46",  # R4 = arg3
        0x73AE: "d6f8c443",  # R4 = [R6+0x3c4], child context candidate
        0x73B2: "ac60",  # [R5+8] = R4
        0x74DE: "2846",  # R0 = R5 for initializer
        0x74E0: "03f056fd",  # BL 0xAF90
        0x7E72: "2046",  # later R0 = R4 consumer context
        0x7E74: "fdf7f8ff",  # BL 0x5E68
        0x8426: "2046",  # R0 = same R4
        0x8428: "07f0eafe",  # BL 0x10200
        0x7F4C: "04f53074",  # ADD.W R4,R4,#0x2C0 in parent span
        0x7FC2: "a4f53074",  # SUB.W R4,R4,#0x2C0 in parent span
        0xAF90: "2de9f047",  # initializer saves R4/R5
        0xAF94: "0446",  # initializer R4 = R0
        0xB0C2: "2948",  # literal load from B168
        0xB0C4: "c4f86006",  # [initializer object+0x660] = R0
        0xB168: "d90b0600",  # 0x00060BD9, conditional local candidate
        0xB16C: "557d0600",  # 0x00067D55
        0xB170: "310b0600",  # 0x00060B31
        0xB174: "8d0b0600",  # 0x00060B8D
        0xB178: "07920600",  # 0x00069207
        0xCABE: "c1f86006",  # second +0x660 writer through R1
        0xCE78: "40406d00",  # literal 0x006EC140 for second writer
        0x1081E: "2046",  # active child context passed to dispatcher
        0x10820: "00f09af8",  # BL 0x10958
        0x10958: "30b4",  # dispatcher prologue
        0x1095A: "d0f86046",  # R4 = [R0+0x660]
        0x1095E: "1346",  # R3 = incoming R2
        0x10960: "0a46",  # R2 = incoming R1
        0x10962: "a446",  # R12 = callback
        0x10964: "30bc",  # restore saved R4/R5
        0x10966: "0121",  # R1 = 1
        0x10968: "6047",  # BX R12
        0x9AD8: "2de9ff4f",  # conditional callback target prologue
        0x9ADE: "0546",  # R5 = callback context
        0x9AE2: "9b46",  # R11 = callback R3 (selected branch value)
        0x9AE8: "c2f30b00",  # R0 = low 12 bits of callback R2 token
        0x9BFA: "cdf814b0",  # selected R3 stored only in local stack
        0x9D20: "0bea0002",  # bitfield uses R11
        0x9D28: "0592",  # bitfield result written to local stack
        0x9D38: "fcf771ff",  # BL 0x6C1E
        0x9E6A: "0598",  # return value loaded from local stack
        0x9E6E: "bde8f08f",  # callback epilogue
        0x6C1E: "7047",  # BX LR stub target
        0x9C26: "05aa",  # callback output pointer SP+0x14 for 6DA4
        0x9C2A: "fdf7bbf8",  # BL 0x6DA4
        0x6DA4: "2de9f041",  # typed memory-copy helper
        0x6DAE: "1546",  # helper R5 = output pointer from R2
        0x6DD4: "04df",  # SVC #4 opaque map/read boundary
        0x6E06: "2b70",  # write byte to supplied R5 output
        0x6E0E: "2b80",  # write halfword to supplied R5 output
        0x6E1E: "2b60",  # write word to supplied R5 output
    }
    for offset, expected in raw.items():
        check(
            checks,
            f"raw bytes at {offset:#x}",
            blob[offset : offset + len(bytes.fromhex(expected))].hex(),
            expected,
        )

    # Direct pointer-table entries written by this same initializer corroborate
    # the candidate map, without claiming a loader/base readback.
    slots = [
        (0xB168, 0x60BD9, 0x9AD8, "2de9ff4f"),
        (0xB16C, 0x67D55, 0x10C54, "2de9f041"),
        (0xB170, 0x60B31, 0x9A30, "2de9f041"),
        (0xB174, 0x60B8D, 0x9A8C, "2de9f041"),
    ]
    for slot, literal, entry, sig in slots:
        got_literal = int.from_bytes(blob[slot : slot + 4], "little")
        mapped = got_literal - BASE
        check(checks, f"pointer at {slot:#x}", got_literal, literal)
        check(
            checks, f"pointer at {slot:#x} conditional Thumb mapping", mapped, entry | 1
        )
        check(
            checks,
            f"pointer at {slot:#x} target code anchor",
            blob[entry : entry + len(bytes.fromhex(sig))].hex(),
            sig,
        )

    # Exact stores show different pointer expressions at installer and use.
    ownership = {
        "initializer_call": "0x74DE R0=R5; 0x74E0 BL 0xAF90; 0xAF94 R4=R0; 0xB0C4 stores [initializer R4+0x660], so the slot base is parent R5",
        "active_dispatch": "0x73AE loads a child pointer candidate from [R6+0x3C4] into R4; 0x73B2 stores that pointer at [R5+8]. At 0x8426 the current R4 is passed to 0x10200, and 0x10958 later loads [current R0+0x660]. The exact current value at 0x8426 is not reconstructed here.",
        "intervening_register_fact": "raw instructions 0x7F4C and 0x7FC2 explicitly add/subtract 0x2C0 from R4 in the parent span; this verifier does not prove these adjustments restore the same child pointer on the path to 0x8426",
        "prior_context_alias_claim": "the prior 89-check result claimed the same R4 base at 0x7E74 and 0x8428 using a no-write scan; that scanner was malformed and the claim is withdrawn",
        "identity": "not proven: installer base is parent R5; active dispatcher receives the current R4 at 0x8426. R4 is set from an R6+0x3C4 child-pointer load at 0x73AE and has later explicit adjustments; no direct dataflow links that slot to the B0C4-installed +0x660, and BLX R1 at 0x74EA is unresolved.",
    }
    check(
        checks,
        "initializer/dispatcher ownership remains explicitly distinct",
        ownership["identity"].startswith("not proven"),
        True,
    )
    check(
        checks,
        "listing shows R4 adjustment at 0x7F4C",
        "add.w\tr4, r4, #0x2c0" in line_at(listing, 0x7F4C),
        True,
    )
    check(
        checks,
        "listing shows R4 adjustment at 0x7FC2",
        "sub.w\tr4, r4, #0x2c0" in line_at(listing, 0x7FC2),
        True,
    )
    # The exact candidate callback computes a local bitfield result. Its direct
    # stores are stack locals; helper SVC #4 copies through the caller buffer.
    target = (0x60BD9 - BASE) & ~1
    check(checks, "candidate callback local code entry", target, 0x9AD8)
    non_stack_stores = direct_store_destinations(listing, 0x9AD8, 0x9E70)
    check(checks, "candidate callback non-stack direct stores", non_stack_stores, [])
    check(
        checks,
        "candidate helper 6DA4 output is SP+0x14",
        "add\tr2, sp, #0x14" in line_at(listing, 0x9C26),
        True,
    )
    check(
        checks,
        "SVC #4 helper only writes through supplied output pointer",
        helper_copy_shape(listing),
        True,
    )

    result = {
        "status": "PASS",
        "checks": len(checks),
        "evidence_class": ["observed-bytes", "static-analysis"],
        "inputs": {name: str(path) for name, path in paths.items()},
        "hashes": {name: sha(path) for name, path in paths.items()},
        "pointer_map": {
            "literal_site": "0xB168",
            "pointer_literal": "0x00060BD9",
            "candidate_base": "0x57100 (conditional static mapping, not loader proof)",
            "thumb_target": "0x9AD9",
            "local_code_entry": "0x9AD8",
            "independent_prior_anchor_count": 4,
            "same_initializer_adjacent_anchors": [
                "0xB16C->0x10C54",
                "0xB170->0x9A30",
                "0xB174->0x9A8C",
            ],
        },
        "ownership": ownership,
        "candidate_callback_effect": {
            "input_mapping": "branch-selected incoming R2 at 0x10958 becomes callback R3; callback 0x9AD8 copies R3 into R11 at 0x9AE2",
            "token_mapping": "incoming dispatcher R1=0x61E becomes callback R2; 0x9AE8 extracts low 12 bits and indexes [R5+0x44]",
            "local_state": "R11 can be stored in [SP+0x14] at 0x9BFA and transformed by bitfield sequence 0x9D20..0x9D28; return path reloads [SP+0x14] into R0 at 0x9E6A",
            "helper_effect": "0x9D38 calls 0x6C1E, whose exact instruction is BX LR. Another path calls 0x6DA4 with R2=SP+0x14; the helper uses SVC #4 then copies byte/halfword/word into the supplied output pointer. SVC #4 mapping semantics remain opaque.",
            "direct_write_class": "candidate callback direct stores are to its stack frame; no direct MMIO or PLL write is present in this bounded callback body",
        },
        "second_660_writer": {
            "site": "0xCABE STR.W R0,[R1,#0x660]",
            "pointer_literal_site": "0xCE78",
            "literal": "0x006EC140",
            "conditional_base_mapping": "0x697040, not a local ABL1 file offset under base 0x57100; this does not establish an external address or target",
            "owner": "R1 ownership unresolved in this bounded trace",
        },
        "claim_boundary": "A candidate initializer literal maps to exact local callback code under the conditional 0x57100 base and has validating anchors. Exact identity between the installed parent-object slot and the active child-object [R4+0x660] dispatch slot is not proven. Therefore the callback candidate is not asserted to be the callback actually invoked for Fclk; neither callback hardware effect nor MCLK=UCLK=FCLK is established.",
        "checks_detail": checks,
    }
    (OUT / "abl1-context660-callback-result.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "checks": len(checks),
                "pointer_map": result["pointer_map"],
                "ownership": ownership,
                "callback_effect": result["candidate_callback_effect"],
                "claim_boundary": result["claim_boundary"],
            },
            separators=(",", ":"),
        )
    )


def direct_store_destinations(listing: str, start: int, stop: int) -> list[str]:
    out = []
    for line in listing.splitlines():
        m = re.match(r"\s*([0-9a-f]+):", line)
        if not m or not start <= int(m.group(1), 16) < stop:
            continue
        parts = line.split("\t")
        ins = (
            " ".join(x.strip() for x in parts[1:3]).split("@", 1)[0].strip()
            if len(parts) >= 3
            else ""
        )
        op, _, args = ins.partition(" ")
        if op.lower().startswith("str"):
            memory = re.search(r"\[([^\]]+)\]", args)
            if memory is None or not memory.group(1).strip().startswith("sp"):
                out.append(line.strip())
    return out


def helper_copy_shape(listing: str) -> bool:
    return all(
        fragment in line_at(listing, off)
        for off, fragment in [
            (0x6DAE, "mov\tr5, r2"),
            (0x6DD4, "svc\t#0x4"),
            (0x6E06, "strb\tr3, [r5]"),
            (0x6E0E, "strh\tr3, [r5]"),
            (0x6E1E, "str\tr3, [r5]"),
        ]
    )


if __name__ == "__main__":
    main()
