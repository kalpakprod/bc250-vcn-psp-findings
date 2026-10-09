#!/usr/bin/env python3
"""Independently compare exact ABL1 enum dispatch with exact CLV IFR options."""
from __future__ import annotations

import hashlib
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PAY = ROOT / "evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin"
IFR = ROOT / "evidence/firmware-audit/20260920-df-init-route/menu-result.json"
LISTING = ROOT / "evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-data-thumb-llvm.txt"
EXPECTED_PAYLOAD = "af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a"
EXPECTED_IFR_MODULE = "7ff717d51c9a447c6954c63b633cf836f1e4396c2b01f4bf590268a60ac1d0d8"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def u16(data: bytes, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def movw_r0_imm(data: bytes, offset: int) -> int | None:
    """Decode the Thumb-2 MOVW r0,#imm16 form used by this table."""
    first, second = u16(data, offset), u16(data, offset + 2)
    if (first & 0xFBF0) != 0xF240 or ((second >> 8) & 0xF) != 0x0:
        return None
    i = (first >> 10) & 1
    imm4 = first & 0xF
    imm3 = (second >> 12) & 0x7
    imm8 = second & 0xFF
    return (i << 11) | (imm4 << 12) | (imm3 << 8) | imm8


def mov_r0_imm(data: bytes, offset: int) -> int | None:
    half = u16(data, offset)
    if (half & 0xF800) == 0x2000:
        return half & 0xFF
    return movw_r0_imm(data, offset)


def parse_mhz(label: str) -> int | None:
    match = re.fullmatch(r"(\d+)MHz", label)
    return int(match.group(1)) if match else None


def main() -> int:
    payload = PAY.read_bytes()
    ifr = json.loads(IFR.read_text())
    checks: list[dict] = []

    def check(name: str, got, expected) -> None:
        checks.append(
            {
                "name": name,
                "status": "PASS" if got == expected else "FAIL",
                "got": got,
                "expected": expected,
            }
        )

    check("payload_sha256", sha256(payload), EXPECTED_PAYLOAD)
    check("payload_length", len(payload), 94624)
    check("exact_ifr_module_sha256", ifr["module_sha256"], EXPECTED_IFR_MODULE)
    check("exact_ifr_parser_status", ifr["status"], "PASS")
    check("listing_exists", LISTING.exists(), True)

    # The exact TBB dispatch at 0x2286 is based at 0x228A. Each byte is a
    # halfword displacement; the range guard at 0x2284 rejects selector bytes
    # outside 2..40 before this table is consulted.
    check("tbb_opcode", payload[0x2286:0x228A].hex(), "dfe800f0")
    check("range_guard_bytes", payload[0x2280:0x2286].hex(), "801e272851d2")
    tbb = payload[0x228A:0x228A + 39]
    check("tbb_length", len(tbb), 39)

    dispatch: dict[int, dict] = {}
    for selector in range(256):
        if selector < 2 or selector > 40:
            dispatch[selector] = {
                "kind": "invalid-range",
                "target": "0x232A",
                "direct_writes": ["diagnostic helper at 0x64C8", "[r4+0x04]+0x28 <- 2"],
            }
            continue
        index = selector - 2
        target = 0x228A + tbb[index] * 2
        if target == 0x232A:
            dispatch[selector] = {
                "kind": "invalid-table-gap",
                "target": "0x232A",
                "direct_writes": ["diagnostic helper at 0x64C8", "[r4+0x04]+0x28 <- 2"],
            }
            continue
        value = mov_r0_imm(payload, target)
        if value is None:
            dispatch[selector] = {
                "kind": "unexpected-target",
                "target": hex(target),
            }
        else:
            dispatch[selector] = {
                "kind": "mapped",
                "target": hex(target),
                "policy_value": value,
                "direct_writes": ["[r4+0x04]+0x2C <- policy_value", "[r4+0x04]+0x28 <- 2"],
            }

    expected_mapped = {
        2: 125, 4: 225, 5: 250, 8: 400, 9: 450, 10: 500,
        15: 750, 17: 850, 20: 1000, 25: 1250, 26: 1330,
        27: 1375, 30: 1500, 32: 1600, 33: 1650, 34: 1700,
        35: 1750, 36: 1800, 37: 1850, 40: 2000,
    }
    got_mapped = {
        selector: item["policy_value"]
        for selector, item in dispatch.items()
        if item["kind"] == "mapped"
    }
    check("all_20_abl_mappings", got_mapped, expected_mapped)
    check("mapped_count", len(got_mapped), 20)
    check("auto_0xFF_is_invalid_range", dispatch[0xFF]["kind"], "invalid-range")
    check("ifr_1900_code_38_is_invalid_gap", dispatch[38]["kind"], "invalid-table-gap")
    check("ifr_1950_code_39_is_invalid_gap", dispatch[39]["kind"], "invalid-table-gap")
    check("invalid_path_target", payload[0x232A:0x2334].hex(), "c44804f0ccf860688662")
    check("invalid_path_no_direct_speed_write", "[r4+0x04]+0x2C <- policy_value" not in dispatch[38].get("direct_writes", []), True)

    questions = [q for q in ifr["questions"] if q.get("label") == "Memory Clock Speed"]
    check("one_memory_clock_question", len(questions), 1)
    question = questions[0]
    ifr_options = {
        int(option["value"]): {
            "label": option["label"],
            "default": bool(option.get("default", False)),
            "numeric_mhz": parse_mhz(option["label"]),
        }
        for option in question["options"]
    }
    check("ifr_question_offset", question["offset"], "0x316")
    check("ifr_auto_default", ifr_options[0xFF], {"label": "Auto", "default": True, "numeric_mhz": None})

    comparisons = []
    for selector, value in sorted(got_mapped.items()):
        option = ifr_options.get(selector)
        comparisons.append(
            {
                "code": selector,
                "abl_policy_value": value,
                "ifr_label": option["label"] if option else None,
                "ifr_numeric_mhz": option["numeric_mhz"] if option else None,
                "numeric_agreement": bool(option and option["numeric_mhz"] == value),
                "namespace_identity_proven": False,
            }
        )
    check("all_20_codes_have_ifr_options", all(row["ifr_label"] for row in comparisons), True)
    check("all_20_numeric_labels_agree", all(row["numeric_agreement"] for row in comparisons), True)

    ifr_only = []
    for code, option in sorted(ifr_options.items()):
        if code not in got_mapped:
            ifr_only.append(
                {
                    "code": code,
                    "label": option["label"],
                    "default": option["default"],
                    "numeric_mhz": option["numeric_mhz"],
                    "abl_outcome": dispatch[code]["kind"],
                    "abl_target": dispatch[code]["target"],
                }
            )
    expected_ifr_only = [
        {"code": 38, "label": "1900MHz", "default": False, "numeric_mhz": 1900, "abl_outcome": "invalid-table-gap", "abl_target": "0x232A"},
        {"code": 39, "label": "1950MHz", "default": False, "numeric_mhz": 1950, "abl_outcome": "invalid-table-gap", "abl_target": "0x232A"},
        {"code": 0xFF, "label": "Auto", "default": True, "numeric_mhz": None, "abl_outcome": "invalid-range", "abl_target": "0x232A"},
    ]
    check("ifr_only_entries_and_invalid_outcomes", ifr_only, expected_ifr_only)

    result = {
        "status": "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL",
        "checks": {
            "passed": sum(item["status"] == "PASS" for item in checks),
            "failed": sum(item["status"] == "FAIL" for item in checks),
            "total": len(checks),
        },
        "evidence_class": ["observed-bytes", "static-analysis"],
        "inputs": {
            "abl1_payload": str(PAY),
            "abl1_payload_sha256": sha256(payload),
            "ifr_result": str(IFR),
            "ifr_module_sha256": ifr["module_sha256"],
            "abl1_listing": str(LISTING),
        },
        "abl1_dispatch": {
            "selector_range_guard": "selector 2..40 enters TBB; all other byte values branch to 0x232A",
            "tbb_offset": "0x228A",
            "invalid_target": "0x232A",
            "invalid_path": "diagnostic helper call 0x64C8, then direct mode write [r4+0x04]+0x28 <- 2; no direct +0x2C policy write in this function",
            "mapped": {hex(code): value for code, value in sorted(got_mapped.items())},
        },
        "comparison": {
            "exact_code_and_numeric_agreement_count": sum(row["numeric_agreement"] for row in comparisons),
            "exact_code_and_numeric_agreement_total": len(comparisons),
            "mapped_entries": comparisons,
            "ifr_only_entries": ifr_only,
            "same_namespace_proven": False,
            "interpretation": "All 20 ABL-recognized input codes have exact IFR option-code matches and their decoded numeric policy values equal the IFR MHz labels. IFR Auto/default 0xFF and 1900/1950 codes 0x26/0x27 are not accepted by this ABL TBB path: they take the invalid diagnostic path. This is a strong bounded correlation, not proof that token 7, the IFR field, or the numeric values share one runtime namespace or physical-MHz unit.",
        },
        "checks_detail": checks,
    }
    output = OUT / "abl1-ifr-enum-compare-result.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "checks": result["checks"], "output": str(output)}, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
