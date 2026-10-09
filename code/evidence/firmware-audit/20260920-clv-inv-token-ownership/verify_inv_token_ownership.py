#!/usr/bin/env python3
"""Bounded $INV token-ownership census for the pinned CLV 5.00 image.

Question: does any module of the exact 233-module CLV UEFI extraction request or
compare $INV record 0x1364 (and its six sibling AmdSetup field records), and does
the 32-bit token encoding occur anywhere else in the 16 MiB pinned image?

Method class is changed from the prior single-body immediate-caller inventory:
corpus-wide instruction-row census plus a raw ROM-wide byte census with an
explicit positive control. Inputs and the extraction route are reused, not
re-derived: census.json (FFS/section map), per-module .instructions.json rows and
.bin bodies live under evidence/firmware-audit/20260919-inv-token-consumers/.

Read-only. No ROM, NVRAM, register, hardware, source-input or candidate mutation.
"""

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

PROJECT = Path("/home/OWNER/orca/projects/bc250")
CORPUS = PROJECT / "evidence/firmware-audit/20260919-inv-token-consumers"
OUT = Path(__file__).resolve().parent

# $INV record -> AmdSetup field offset, as established by the accepted prior trace.
FIELD_TOKENS = {
    0x11ED: 0x316,
    0x1204: 0x330,
    0x1331: 0x6A3,
    0x1363: 0x6E5,
    0x1364: 0x6E6,
    0x1373: 0x703,
    0x1374: 0x704,
}
EXPECTED_PRODUCERS = {
    "AmdFabricAriPei-c5b99650a442",
    "AmdNbioBaseARIPei-51d96c1e5a5e",
    "AmdNbioGfxARIPei-63413be2ac29",
    "AmdNbioPcieARIPei-62b1398c4ba9",
    "AmdNbioSmuV10Pei-905b8be68afd",
    "AmdSocBl5AriPei-79e13211d5ae",
    "CbsBasePei-6ff112922ad8",
}
CONTROL_TOKENS = {0x1000: 14, 0x1388: 11, 0x10FF: 1, 0x1104: 1}
PRE_IMM_PREFIX = "83c104894df8ba"  # add ecx,4 ; mov [ebp-0x8],ecx ; mov edx,imm16
POST_IMM_PREFIX = "8b45f8"  # mov eax,[ebp-0x8]

checks = []


def check(label, condition):
    checks.append({"check": label, "passed": bool(condition)})
    if not condition:
        raise AssertionError(label)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def token_immediate(row, token):
    """True when the row carries the token as a bare immediate operand."""
    if row["mnemonic"] not in {"mov", "push", "cmp", "test", "add", "sub"}:
        return False
    want = hex(token)
    return any(part.strip().lower() == want for part in row["operands"].split(","))


def main():
    census = json.loads((CORPUS / "census.json").read_text())
    rom = Path(census["input"])
    if not rom.is_absolute():
        rom = PROJECT / rom
    body = rom.read_bytes()

    # ---- C1 pinned image ------------------------------------------------
    check("ROM size 16777216", len(body) == 16777216)
    check("ROM sha256", sha256(body) == census["sha256"])

    # ---- C2 corpus integrity -------------------------------------------
    records = census["records"]
    check("233 extraction records", len(records) == 233)
    check(
        "233 distinct body digests",
        len({r["sha256"] for r in records}) == 233,
    )
    manifest = subprocess.run(
        [
            "sha256sum",
            "-c",
            "evidence/firmware-audit/20260919-inv-token-consumers/SHA256SUMS",
        ],
        cwd=PROJECT,
        capture_output=True,
        text=True,
    )
    ok_lines = [ln for ln in manifest.stdout.splitlines() if ln.endswith(": OK")]
    failed_lines = [ln.split(":")[0] for ln in manifest.stdout.splitlines() if ln.endswith(": FAILED")]
    check("archive SHA256SUMS covers 953 files", len(ok_lines) + len(failed_lines) == 953)
    check(
        "archive manifest failures are documentation-only, never extraction inputs",
        all(path.startswith("docs/") for path in failed_lines),
    )
    check("no extraction module body failed", not any(path.endswith(".bin") for path in failed_lines))

    rows_by_stem = {}
    bodies = {}
    for rec in records:
        stem = rec["stem"]
        bin_path = CORPUS / (stem + ".bin")
        rows_path = CORPUS / (stem + ".instructions.json")
        b = bin_path.read_bytes()
        check("body digest " + stem, sha256(b) == rec["sha256"])
        check("instruction rows present " + stem, rows_path.is_file())
        bodies[stem] = b
        rows_by_stem[stem] = json.loads(rows_path.read_text())

    # ---- C3 producer census --------------------------------------------
    producers = {t: {} for t in FIELD_TOKENS}
    address_mentions = {t: [] for t in FIELD_TOKENS}
    hexre = re.compile(r"0x[0-9a-f]+")
    for stem, rows in rows_by_stem.items():
        for row in rows:
            operands = row["operands"].lower()
            if "0x11" not in operands and "0x12" not in operands and "0x13" not in operands:
                continue
            for part in hexre.findall(operands):
                token = int(part, 16)
                if token not in FIELD_TOKENS:
                    continue
                if token_immediate(row, token):
                    check(
                        "only mov edx immediate form for " + hex(token),
                        row["mnemonic"] == "mov" and row["operands"].strip() == "edx," + hex(token),
                    )
                    producers[token].setdefault(stem, []).append(row["rva"])
                else:
                    address_mentions[token].append(
                        {"module": stem, "rva": row["rva"], "mnemonic": row["mnemonic"], "operands": row["operands"]}
                    )

    producer_map = {}
    for token, sites in producers.items():
        check(
            "exactly seven producer modules for " + hex(token),
            set(sites) == EXPECTED_PRODUCERS,
        )
        check(
            "one producer site per module for " + hex(token),
            all(len(v) == 1 for v in sites.values()),
        )
        producer_map[hex(token)] = {
            "amdsetup_offset": hex(FIELD_TOKENS[token]),
            "sites": {stem: hex(sites[stem][0]) for stem in sorted(sites)},
        }
    check(
        "identical producer module set for all seven field tokens",
        len({frozenset(p) for p in producers.values()}) == 1,
    )

    # ---- C4 producer store structure for 0x1363 / 0x1364 ---------------
    structure = {}
    want = {
        0x1363: {"imm": "ba63130000", "payload": "8a82e5060000"},
        0x1364: {"imm": "ba64130000", "payload": "8b82e6060000"},
    }
    for token, forms in want.items():
        structure[hex(token)] = {}
        for stem, rvas in producers[token].items():
            rva = rvas[0]
            rows = rows_by_stem[stem]
            window = [r for r in rows if rva <= r["rva"] <= rva + 0x40]
            bytes_rows = {r["bytes"] for r in window}
            check("producer immediate bytes " + stem + " " + hex(token), forms["imm"] in bytes_rows)
            check("producer word store " + stem + " " + hex(token), "668910" in bytes_rows)
            check("producer payload copy " + stem + " " + hex(token), forms["payload"] in bytes_rows)
            if token == 0x1364:
                check("producer width flag or-2 " + stem, "80ca02" in bytes_rows)
            structure[hex(token)][stem] = hex(rva)

    # ---- C5 request census with positive control -----------------------
    push_census = {}
    for stem, rows in rows_by_stem.items():
        for row in rows:
            if row["mnemonic"] == "push" and re.fullmatch(r"0x[0-9a-f]+", row["operands"].strip()):
                value = int(row["operands"].strip(), 16)
                push_census.setdefault(value, []).append({"module": stem, "rva": hex(row["rva"])})
    request_census = {hex(t): len(push_census.get(t, [])) for t in FIELD_TOKENS}
    for token in FIELD_TOKENS:
        check("no immediate request site for " + hex(token), len(push_census.get(token, [])) == 0)
    control_census = {}
    for token, expected in CONTROL_TOKENS.items():
        observed = len(push_census.get(token, []))
        control_census[hex(token)] = observed
        check("positive control request sites for " + hex(token), observed >= expected)

    # ---- C6 raw ROM census --------------------------------------------
    rom_census = {}
    for token in (0x1363, 0x1364):
        pattern = token.to_bytes(4, "little")
        offsets = []
        start = 0
        while True:
            idx = body.find(pattern, start)
            if idx < 0:
                break
            offsets.append(idx)
            start = idx + 1
        check("exactly seven ROM occurrences of " + hex(token), len(offsets) == 7)
        entries = []
        for idx in offsets:
            check(
                "ROM producer prefix " + hex(token) + " @" + hex(idx),
                body[idx - 7: idx].hex() == PRE_IMM_PREFIX,
            )
            check(
                "ROM producer suffix " + hex(token) + " @" + hex(idx),
                body[idx + 4: idx + 7].hex() == POST_IMM_PREFIX,
            )
            entries.append({"offset": hex(idx), "prefix": body[idx - 7: idx].hex(), "suffix": body[idx + 4: idx + 7].hex()})
        rom_census[hex(token)] = entries

    # ---- C7 ROM occurrence -> module attribution -----------------------
    ordered = sorted(
        (r for r in records if r["stem"] in EXPECTED_PRODUCERS),
        key=lambda r: r["ffs_offset"],
    )
    check("seven producer records carry ffs offsets", len(ordered) == 7)
    attribution = {}
    for token in (0x1363, 0x1364):
        mapped = []
        for entry in rom_census[hex(token)]:
            offset = int(entry["offset"], 16)
            owners = [
                r["stem"]
                for r in ordered
                if r["ffs_offset"] <= offset < r["ffs_offset"] + r["size"]
            ]
            check("single FFS owner for " + hex(token) + " @" + entry["offset"], len(owners) == 1)
            mapped.append({"offset": entry["offset"], "module": owners[0]})
        check(
            "ROM occurrences map one-to-one onto the seven producer modules " + hex(token),
            sorted(m["module"] for m in mapped) == sorted(EXPECTED_PRODUCERS),
        )
        attribution[hex(token)] = mapped

    # ---- result --------------------------------------------------------
    result = {
        "status": "PRODUCER_ONLY_IN_MODULE_SET",
        "question": "consumer/requester of $INV record 0x1364 in the pinned CLV UEFI module set",
        "inputs": {
            "rom": {"path": str(rom.relative_to(PROJECT)), "size": len(body), "sha256": sha256(body)},
            "corpus": {
                "path": str(CORPUS.relative_to(PROJECT)),
                "records": len(records),
                "manifest_file": "SHA256SUMS",
                "manifest_ok_lines": len(ok_lines),
                "manifest_failed_lines": len(failed_lines),
                "manifest_failed_paths": failed_lines,
            },
        },
        "producer_census": producer_map,
        "producer_structure": structure,
        "request_census": request_census,
        "request_census_positive_control": control_census,
        "address_mentions_not_tokens": {hex(t): address_mentions[t] for t in FIELD_TOKENS},
        "rom_raw_census": rom_census,
        "rom_attribution": attribution,
        "verdict": (
            "Every one of the seven AmdSetup-to-$INV field records is emitted by seven identical "
            "inline serializer copies and is never passed as an immediate token argument anywhere in "
            "the 233-module CLV UEFI extraction; the 32-bit token encodings occur exactly seven times "
            "each in the whole 16 MiB image, all at those producer stores. No UEFI consumer of record "
            "0x1364 is present in this image."
        ),
        "limits": [
            "No immediate token argument and no 32-bit little-endian token encoding elsewhere does not exclude a computed/indirect or 16-bit-encoded consumer.",
            "Non-UEFI firmware (PSP/$PS1, ABL1, SMU/TOS) was not searched in this bounded trace.",
            "No voltage, rail, clock, unit, synchronization or hardware effect is established.",
            "Read-only: no ROM, NVRAM, register, hardware or candidate mutation.",
        ],
        "checks_passed": len(checks),
        "checks": checks,
    }
    text = json.dumps(result, indent=2) + "\n"
    (OUT / "inv-token-ownership-result.json").write_text(text)
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
