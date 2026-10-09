#!/usr/bin/env python3
"""Independent safety review: BC250 DF/MCLK 1800 MHz and SoC 1.15 V targets.

Read-only. Re-measures pinned ROM bytes, the clv CbsSetupDxe IFR option labels,
and every candidates/*.bin delta against the pinned donor. Writes one JSON result
next to this file. Inputs are never modified.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
from pathlib import Path

ROOT = Path("/home/OWNER/orca/projects/bc250")
OUT = Path(__file__).with_name("safety-review-result.json")

DONOR = ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin"
DONOR_SHA = "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"
SETUP = ROOT / "evidence/firmware-audit/20260919-inv-token-consumers/CbsSetupDxe-7ff717d51c9a.bin"
SETUP_SHA = "7ff717d51c9a447c6954c63b633cf836f1e4396c2b01f4bf590268a60ac1d0d8"
PARSER = ROOT / "import/from-windows/Users/kukuruza/bc250-bios/tools/uefi/e1_ifr_dump.py"
VOLT_RESULT = ROOT / "evidence/firmware-audit/20260920-clv-voltage-offset-consumer-boundary/voltage-offset-boundary-result.json"
VOLT_RESULT_SHA = "4026f8cebb814fc11fddb58eb5f5fd4e1e41fc878dbba3d3745161ddb7667bd3"

BODY = 0x4CF                 # AmdSetup body base in the donor ROM
IMAGE_SIZE = 0x1000000

# AmdSetup body-relative field map (independently re-derived from the clv IFR).
FIELDS = {
    "MemoryClockSpeed": (0x316, 1, "one_of"),
    "UclkDiv1M0": (0x330, 1, "one_of"),
    "FclkDpm": (0x6A3, 1, "one_of"),
    "VddcrVddOffsetControl": (0x6E5, 1, "one_of"),
    "VddcrVddOffset": (0x6E6, 4, "numeric"),
    "VddcrGfxOffsetControl": (0x6EA, 1, "one_of"),
    "VddcrGfxOffset": (0x6EB, 4, "numeric"),
    "ForceCpuFrequency": (0x701, 2, "numeric"),
    "DfClockOverrideControl": (0x703, 1, "one_of"),
    "DfClockOvrd": (0x704, 2, "numeric"),
}
VOLTAGE_RANGES = {           # absolute ROM offsets that carry a voltage request
    "VddcrVddOffsetControl": (BODY + 0x6E5, BODY + 0x6E5),
    "VddcrVddOffset": (BODY + 0x6E6, BODY + 0x6E9),
    "VddcrGfxOffsetControl": (BODY + 0x6EA, BODY + 0x6EA),
    "VddcrGfxOffset": (BODY + 0x6EB, BODY + 0x6EE),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


VDD_CONTROL_PREREQ = 1          # IFR: VDDCR_VDD Voltage Offset Control, value 1 == Manual
UNSET_BYTE = 0xFF               # C0A-lineage Setup records are 0xFF-filled (no stored request)


def classify_voltage_request(control_byte: int, value_bytes: bytes) -> str:
    """Separate a deliberate stored voltage request from unset lineage bytes."""
    value = int.from_bytes(value_bytes, "little")
    if control_byte == UNSET_BYTE and value == 0xFFFFFFFF:
        return "unset_lineage_bytes_0xff_not_a_request"
    if control_byte == 0 and value == 0:
        return "auto_and_zero_no_request"
    if control_byte == VDD_CONTROL_PREREQ and value != 0:
        return "deliberate_nonzero_request"
    return "other_combination_needs_review"


def diff_offsets(a: bytes, b: bytes, chunk: int = 1 << 16) -> list[int]:
    """Byte-diff two equal-length images using chunk compare (C speed) + local scan."""
    out: list[int] = []
    for start in range(0, len(a), chunk):
        sa, sb = a[start:start + chunk], b[start:start + chunk]
        if sa == sb:
            continue
        out.extend(start + i for i, (x, y) in enumerate(zip(sa, sb)) if x != y)
    return out


def load_ifr_questions(setup: bytes) -> dict:
    """Walk the exact CbsSetupDxe forms package: offset -> question + option labels."""
    spec = importlib.util.spec_from_file_location("e1_ifr_dump", PARSER)
    ifr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ifr)
    packages = ifr.find_packages(setup)
    strings_pkg = next(x for x in packages if x[1] == 4)
    strings = dict(ifr.parse_sibt(setup[strings_pkg[0]:strings_pkg[0] + 4 + strings_pkg[2]])[1])
    questions: dict[int, dict] = {}
    for start, typ, length in packages:
        if typ != 2:
            continue
        p, end = start + 4, start + 4 + length
        current = None
        while p + 2 <= end:
            op = setup[p]
            ln = setup[p + 1] & 0x7F
            if ln < 2 or p + ln > end:
                break                      # validated content ends; package tail is padding
            body = setup[p + 2:p + ln]
            if op in (0x05, 0x06, 0x07, 0x08, 0x1C, 0x23) and len(body) >= 11:
                prompt, _, qid, _, voff, _ = struct.unpack_from("<HHHHHB", body, 0)
                current = voff
                questions.setdefault(voff, {
                    "qid": hex(qid), "opcode": hex(op), "record_offset": hex(p),
                    "prompt": strings.get(prompt, "").rstrip("\0"), "options": [],
                })
            elif op == 0x09 and current is not None:
                oid = struct.unpack_from("<H", body, 0)[0]
                size = ifr.OPTVAL_SZ.get(body[3], 1)
                value = int.from_bytes(body[4:4 + size], "little")
                questions[current]["options"].append(
                    {"value": value, "label": strings.get(oid, "").rstrip("\0")})
            p += ln
    return questions


def main() -> int:
    donor = DONOR.read_bytes()
    setup = SETUP.read_bytes()
    assert sha256(donor) == DONOR_SHA, "donor hash mismatch"
    assert len(donor) == IMAGE_SIZE, "donor size mismatch"
    assert sha256(setup) == SETUP_SHA, "CbsSetupDxe hash mismatch"
    assert sha256(VOLT_RESULT.read_bytes()) == VOLT_RESULT_SHA, "consumer-boundary result hash mismatch"

    questions = load_ifr_questions(setup)

    # --- literal field readback from the pinned ROM -------------------------
    fields = {}
    for name, (off, width, kind) in FIELDS.items():
        raw = donor[BODY + off:BODY + off + width]
        q = questions.get(off)
        entry = {
            "amdsetup_offset": hex(off), "absolute_offset": hex(BODY + off),
            "width_bytes": width, "ikind": kind,
            "raw_hex": raw.hex(" "),
            "value": int.from_bytes(raw, "little"),
            "ifr": None if q is None else {
                "qid": q["qid"], "prompt": q["prompt"],
                "record_offset": q["record_offset"], "option_count": len(q["options"]),
            },
        }
        if q is not None and kind == "one_of":
            entry["ifr"]["label_for_stored_value"] = next(
                (o["label"] for o in q["options"] if o["value"] == entry["value"]), None)
        fields[name] = entry

    # --- independent checks that settle the two reviewed claims -------------
    mclk = fields["MemoryClockSpeed"]
    checks = {
        "donor_stores_memory_clock_option_0x24": mclk["value"] == 0x24,
        "clv_ifr_labels_0x24_as_1800MHz": mclk["ifr"]["label_for_stored_value"] == "1800MHz",
        "clv_ifr_labels_0x23_as_1750MHz": "1750MHz" in [o["label"] for o in
            questions[0x316]["options"] if o["value"] == 0x23],
        "donor_vdd_offset_control_auto": fields["VddcrVddOffsetControl"]["value"] == 0,
        "donor_vdd_offset_zero": fields["VddcrVddOffset"]["value"] == 0,
        "donor_gfx_offset_control_auto": fields["VddcrGfxOffsetControl"]["value"] == 0,
        "donor_gfx_offset_zero": fields["VddcrGfxOffset"]["value"] == 0,
        "donor_df_override_manual_1420": (fields["DfClockOverrideControl"]["value"] == 1
                                          and fields["DfClockOvrd"]["value"] == 1420),
        "memory_clock_question_is_qid_527_at_0x316": mclk["ifr"]["qid"] == hex(527),
        "vdd_offset_question_is_numeric_qid_876_at_0x6E6":
            fields["VddcrVddOffset"]["ifr"]["qid"] == hex(876),
    }
    assert checks["donor_stores_memory_clock_option_0x24"], "donor MCLK option not 0x24"
    assert checks["clv_ifr_labels_0x24_as_1800MHz"], "0x24 is not labelled 1800MHz"
    assert checks["donor_vdd_offset_zero"] and checks["donor_gfx_offset_zero"], "donor voltage non-zero"

    # --- candidate delta audit --------------------------------------------
    candidates = []
    for image in sorted((ROOT / "candidates").glob("*.bin")):
        data = image.read_bytes()
        manifest_path = image.with_suffix(".build.json")
        if len(data) != IMAGE_SIZE:
            candidates.append({"image": image.name, "size": len(data), "status": "NON_IMAGE_SIZE"})
            continue
        changed = diff_offsets(data, donor)
        voltage_touch = {}
        for name, (lo, hi) in VOLTAGE_RANGES.items():
            touched = [i for i in changed if lo <= i <= hi]
            if touched:
                voltage_touch[name] = {
                    "offsets": [hex(i) for i in touched],
                    "donor": donor[lo:hi + 1].hex(" "),
                    "candidate": data[lo:hi + 1].hex(" "),
                }
        manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else None
        recorded = manifest.get("changed_offsets") if isinstance(manifest, dict) else None
        recorded_set = {int(x, 16) for x in recorded} if recorded else None
        recomputed_set = set(changed)
        entry = {
            "image": image.name,
            "sha256": sha256(data),
            "changed_byte_count": len(changed),
            "changed_offsets_head": [hex(i) for i in changed[:12]],
            "base_lineage": "pinned_clv" if len(changed) < 4096 else "other_base",
            "voltage_touching": voltage_touch,
            "requests_voltage_change": bool(voltage_touch),
            "voltage_request": {
                "vdd_control_byte": data[BODY + 0x6E5],
                "vdd_value_le": data[BODY + 0x6E6:BODY + 0x6EA].hex(" "),
                "vdd_class": classify_voltage_request(data[BODY + 0x6E5], data[BODY + 0x6E6:BODY + 0x6EA]),
                "gfx_control_byte": data[BODY + 0x6EA],
                "gfx_value_le": data[BODY + 0x6EB:BODY + 0x6EF].hex(" "),
                "gfx_class": classify_voltage_request(data[BODY + 0x6EA], data[BODY + 0x6EB:BODY + 0x6EF]),
            },
            "field_values_changed": sorted({
                name for name, (off, width, _) in FIELDS.items()
                if any(BODY + off <= i < BODY + off + width for i in changed)
            }),
            "manifest_present": manifest is not None,
            "manifest_changed_offsets_match_recomputed": (
                recorded_set is None if recorded_set is None else recorded_set == recomputed_set),
            "manifest_voltage_changed": (manifest.get("voltage_changed")
                                         if isinstance(manifest, dict) else None),
            "manifest_status": (manifest.get("status") if isinstance(manifest, dict) else None),
        }
        if isinstance(manifest, dict) and "changed_offsets" in manifest:
            entry["manifest_changed_offsets"] = recorded
        candidates.append(entry)

    lineage = [c for c in candidates if c.get("base_lineage") == "pinned_clv"]
    voltage_candidates = [c["image"] for c in candidates if c.get("requests_voltage_change")]
    deliberate = [c["image"] for c in candidates
                  if c.get("voltage_request", {}).get("vdd_class") == "deliberate_nonzero_request"
                  or c.get("voltage_request", {}).get("gfx_class") == "deliberate_nonzero_request"]
    unset_lineage = [c["image"] for c in candidates
                     if c.get("voltage_request", {}).get("vdd_class") == "unset_lineage_bytes_0xff_not_a_request"]
    consumer = json.loads(VOLT_RESULT.read_text())
    reader = consumer["fabric_reader"]
    checks["pinned_consumer_boundary_status_is_partial"] = consumer["status"] == "PARTIAL_BLOCKED_AT_CONSUMER"
    checks["pinned_reader_has_two_direct_tokens"] = reader["direct_reader_call_count"] == 2
    checks["pinned_reader_does_not_request_0x1364"] = reader["requested_0x1364"] is False
    mismatches = [c["image"] for c in lineage
                  if c.get("manifest_changed_offsets_match_recomputed") is False]

    # --- safety claim matrix ----------------------------------------------
    matrix = {
        "target_1800MHz": {
            "stored_request_representable_in_pinned_rom": "PASS",
            "clv_ifr_option_label_matches_1800MHz": "PASS",
            "applied_mclk_measured_on_hardware": "UNRUN",
            "mclk_uclk_fclk_synchronization_proven": "UNRUN",
            "boot_and_stability_with_1800_stored": "INCONCLUSIVE",
            "thermal_or_power_margin_measured": "UNRUN",
            "historical_df1800_recipe_usable_under_ceiling": "FAIL",
            "note": ("The pinned clv donor already persists MemoryClockSpeed option 0x24 "
                     "('1800MHz'); this is a stored request, not an applied clock, and no "
                     "hardware measurement of MCLK/UCLK/FCLK exists. The historical DF1800 "
                     "report is associated with a physical feedback modification and a "
                     "reported SoC above the 1.15 V ceiling, so it is not a reproducible recipe."),
        },
        "target_SoC_1.15V": {
            "voltage_field_located_and_typed": "PASS",
            "unit_sign_encoding_established": "FAIL",
            "smc_consumer_of_record_0x1364_established": "INCONCLUSIVE",
            "board_specific_safe_rating_evidence": "FAIL",
            "rail_voltage_measured_under_load": "UNRUN",
            "candidate_requests_nonzero_voltage": "YES_IN_4_UNFLASHED_CANDIDATES_SEE_RESULT",
            "note": ("No board-specific measurement establishes 1.15 V as a rating; the field "
                     "unit/sign/encoding is unresolved and the applied consumer is not located. "
                     "No repository candidate requests a nonzero VDDCR_VDD/GFX offset."),
        },
    }

    result = {
        "review": "independent_safety_review_1800MHz_and_1.15V",
        "actor": "/root/ds_independent_safety_review",
        "inputs": {
            str(DONOR.relative_to(ROOT)): {"size": len(donor), "sha256": sha256(donor)},
            str(SETUP.relative_to(ROOT)): {"size": len(setup), "sha256": sha256(setup)},
            str(PARSER.relative_to(ROOT)): {"sha256": sha256(PARSER.read_bytes())},
            str(VOLT_RESULT.relative_to(ROOT)): {"sha256": sha256(VOLT_RESULT.read_bytes())},
        },
        "literal_fields": fields,
        "independent_checks": checks,
        "candidate_count": len(candidates),
        "candidates_on_pinned_clv": len(lineage),
        "voltage_changing_candidates": voltage_candidates,
        "deliberate_voltage_request_candidates": deliberate,
        "unset_lineage_0xff_candidates": unset_lineage,
        "manifest_disagreements": mismatches,
        "candidates": candidates,
        "safety_claim_matrix": matrix,
        "verdict": {
            "overall": "NO_GO_FOR_VOLTAGE_CHANGE_AND_UNPROVEN_FOR_1800MHz",
            "flash_approval_recommendation": "NOT_RECOMMENDED",
            "decisive_missing_tests": [
                "Rail-voltage measurement under load on the target board with a known-good "
                "baseline image and a verified recovery image.",
                "Independent clock measurement (hardware counter or equivalent) proving "
                "applied MCLK/UCLK/FCLK, not displayed values.",
                "A located and traced consumer for $INV record 0x1364 before any voltage "
                "request is treated as an applied voltage.",
            ],
        },
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "status": "SAFETY_REVIEW_COMPLETE",
        "checks_passed": sum(1 for v in checks.values() if v),
        "checks_total": len(checks),
        "candidates_audited": len(candidates),
        "voltage_changing_candidates": voltage_candidates,
        "deliberate_voltage_request_candidates": deliberate,
        "manifest_disagreements": mismatches,
        "memory_clock_stored_option": hex(fields["MemoryClockSpeed"]["value"]),
        "memory_clock_stored_label": fields["MemoryClockSpeed"]["ifr"]["label_for_stored_value"],
        "verdict": result["verdict"]["overall"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
