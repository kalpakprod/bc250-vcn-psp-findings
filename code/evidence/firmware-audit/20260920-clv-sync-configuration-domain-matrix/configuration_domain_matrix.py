#!/usr/bin/env python3
"""Read-only exact-clv UI-domain matrix; no candidate or hardware action."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ROM = ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin"
MENU = ROOT / "evidence/firmware-audit/20260920-df-init-route/menu-result.json"
PSTATE_RESULT = ROOT / "evidence/firmware-audit/20260920-clv-sync-stage2-memory-pstate/memory-pstate-result.json"
DISCR_RESULT = ROOT / "evidence/firmware-audit/20260920-clv-sync-stage2-memory-pstate-discrimination/discrimination-result.json"
OWNERSHIP_RESULT = ROOT / "evidence/firmware-audit/20260920-clv-sync-record-ownership-correction/record-ownership-result.json"
ALL_FIELDS_RESULT = ROOT / "evidence/firmware-audit/20260920-clv-sync-stage2-record-lifetime-all-fields/all-fields-result.json"
UCLK_RESULT = ROOT / "evidence/firmware-audit/20260920-clv-sync-stage2-uclk-semantics/uclk-semantics-result.json"
OUT = Path(__file__).resolve().parent / "configuration-domain-matrix.json"
ROM_SHA = "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"
BODY_BASE = 0x4CF

FIELDS = {
    0x316: {"name": "MemoryClockSpeed", "label": "Memory Clock Speed", "width": 1, "persisted": 36},
    0x368: {"name": "PhyPowerSaving", "label": "Phy Power Saving", "width": 1, "persisted": 255},
    0x330: {"name": "UclkDiv1M0", "label": "UclkDiv1M0", "width": 1, "persisted": 1},
    0x6A3: {"name": "FclkDpm", "label": "FCLK_DPM", "width": 1, "persisted": 15},
    0x703: {"name": "DfClockOverrideControl", "label": "DF Clock Override Control", "width": 1, "persisted": 1},
    0x704: {"name": "DfClockOvrd", "label": "DF Clock Override", "width": 2, "persisted": 1420},
    0x36D: {"name": "MemoryPstate", "label": "Memory P-state", "width": 1, "persisted": 255},
}
EXPECTED_OPTIONS = {
    0x316: [("Auto", 255, True), ("125MHz", 2, False), ("225MHz", 4, False), ("250MHz", 5, False),
            ("400MHz", 8, False), ("450MHz", 9, False), ("500MHz", 10, False), ("750MHz", 15, False),
            ("850MHz", 17, False), ("1000MHz", 20, False), ("1250MHz", 25, False), ("1330MHz", 26, False),
            ("1375MHz", 27, False), ("1500MHz", 30, False), ("1600MHz", 32, False), ("1650MHz", 33, False),
            ("1700MHz", 34, False), ("1750MHz", 35, False), ("1800MHz", 36, False), ("1850MHz", 37, False),
            ("1900MHz", 38, False), ("1950MHz", 39, False), ("2000MHz", 40, False)],
    0x368: [("Auto", 255, True), ("Enabled", 1, False), ("Disabled", 0, False)],
    0x330: [("Auto", 255, True), ("Enabled", 1, False)],
    0x6A3: [("Disabled", 0, False), ("Enabled", 1, False), ("Auto", 15, True)],
    0x703: [("Auto", 255, True), ("Manual", 1, False)],
    0x704: [],
    0x36D: [("Auto", 255, True), ("Enabled", 1, False), ("Disabled", 0, False)],
}
EXPECTED_BOUNDS = {0x704: [0, 2000, 0]}
PSTATE_RESULT_SHA = "237546fe5cc4edf44659dab93ce2ccd13ecbd817a6808ef18fa599b1da0b87c7"
DISCR_RESULT_SHA = "5f19242d614102ff92391753a3459ff7a57357adbc95c19cec8b05e7057f4eb9"
OWNERSHIP_RESULT_SHA = "cab9dd7e18defabe1459537fe870a520c24602f1641bd44af5e78ad3e2b2aaf3"
ALL_FIELDS_RESULT_SHA = "7f865e2a018c9be7f665e01286473593582967808963d8bb29c112514840fbbf"
UCLK_RESULT_SHA = "17cba83251f50a108341aa40bbe0d48aa758ff008000436570975428bbdb5059"
SERIALIZER_RECORDS = {0x368: "0x1237", 0x36D: "0x123C", 0x6A3: "0x1331"}
checks = []

def result_ok(x):
    c = x.get("checks", 0)
    return x.get("status") == "PASS" and (c.get("failed", 0) == 0 if isinstance(c, dict) else c > 0)

def check(label, ok, details=None):
    checks.append({"label": label, "status": "PASS" if ok else "FAIL", "details": details})


def sha(data):
    return hashlib.sha256(data).hexdigest()

rom = ROM.read_bytes()
menu = json.loads(MENU.read_text(encoding="utf-8"))
pstate_result = json.loads(PSTATE_RESULT.read_text(encoding="utf-8"))
discr_result = json.loads(DISCR_RESULT.read_text(encoding="utf-8"))
ownership_result = json.loads(OWNERSHIP_RESULT.read_text(encoding="utf-8"))
all_fields_result = json.loads(ALL_FIELDS_RESULT.read_text(encoding="utf-8"))
uclk_result = json.loads(UCLK_RESULT.read_text(encoding="utf-8"))
check("memory-pstate-result-sha256", sha(PSTATE_RESULT.read_bytes()) == PSTATE_RESULT_SHA, {"observed": sha(PSTATE_RESULT.read_bytes()), "expected": PSTATE_RESULT_SHA})
check("memory-pstate-result-pass", pstate_result.get("status") == "PASS" and pstate_result.get("checks", {}).get("failed") == 0, {"status": pstate_result.get("status"), "checks": pstate_result.get("checks")})
check("discrimination-result-sha256", sha(DISCR_RESULT.read_bytes()) == DISCR_RESULT_SHA, {"observed": sha(DISCR_RESULT.read_bytes()), "expected": DISCR_RESULT_SHA})
check("discrimination-result-pass", discr_result.get("status") == "PASS" and discr_result.get("checks", {}).get("failed") == 0, {"status": discr_result.get("status"), "checks": discr_result.get("checks")})
check("ownership-result-sha256", sha(OWNERSHIP_RESULT.read_bytes()) == OWNERSHIP_RESULT_SHA, {"observed": sha(OWNERSHIP_RESULT.read_bytes()), "expected": OWNERSHIP_RESULT_SHA})
check("ownership-result-pass", ownership_result.get("status") == "PASS" and ownership_result.get("checks", {}).get("failed") == 0, {"status": ownership_result.get("status"), "checks": ownership_result.get("checks")})
check("all-fields-result-sha256", sha(ALL_FIELDS_RESULT.read_bytes()) == ALL_FIELDS_RESULT_SHA, {"observed": sha(ALL_FIELDS_RESULT.read_bytes()), "expected": ALL_FIELDS_RESULT_SHA})
check("all-fields-result-pass", result_ok(all_fields_result), {"status": all_fields_result.get("status"), "checks": all_fields_result.get("checks")})
check("uclk-result-sha256", sha(UCLK_RESULT.read_bytes()) == UCLK_RESULT_SHA, {"observed": sha(UCLK_RESULT.read_bytes()), "expected": UCLK_RESULT_SHA})
check("uclk-result-pass", result_ok(uclk_result), {"status": uclk_result.get("status"), "checks": uclk_result.get("checks")})
check("rom-size", len(rom) == 0x1000000, {"observed": len(rom), "expected": 0x1000000})
check("rom-sha256", sha(rom) == ROM_SHA, {"observed": sha(rom), "expected": ROM_SHA})
check("menu-rom-pinning", menu.get("rom_sha256") == ROM_SHA, {"observed": menu.get("rom_sha256"), "expected": ROM_SHA})
menu_sha = sha(MENU.read_bytes())
questions = {int(q["offset"], 16): q for q in menu["questions"] if q.get("varstore_id") == "0x5000"}

rows = []
for off, spec in FIELDS.items():
    raw = rom[BODY_BASE + off:BODY_BASE + off + spec["width"]]
    value = int.from_bytes(raw, "little")
    check(f"persisted-byte:{off:#x}", value == spec["persisted"], {"raw": raw.hex(), "observed": value, "expected": spec["persisted"]})
    q = questions.get(off)
    source = "exact-menu-result"
    if off == 0x368:
        q = {"qid": "0x259", "form": "0x7032", "varstore": "0x5000", "offset": "0x368", "flags": "0x10", "label": "Phy Power Saving", "help": "", "reset_required": True, "callback": False, "read_only": False, "conditions": [], "options": [{"label": "Auto", "value": 255, "default": True}, {"label": "Enabled", "value": 1, "default": False}, {"label": "Disabled", "value": 0, "default": False}]}
        source = "supplemental-discrimination-result"
    if off == 0x36D:
        q = pstate_result["memory_pstate"]["question"]
        source = "supplemental-exact-clv-memory-pstate-result"
    check(f"ifr-question:{off:#x}", q is not None and q.get("label") == spec["label"], {"observed": None if q is None else q.get("label"), "expected": spec["label"], "source": source})
    q = q or {}
    observed_options = [(x.get("label"), x.get("value"), bool(x.get("default"))) for x in q.get("options", [])]
    check(f"ifr-options:{off:#x}", observed_options == EXPECTED_OPTIONS[off], {"observed": observed_options, "expected": EXPECTED_OPTIONS[off]})
    if off in EXPECTED_BOUNDS:
        check(f"ifr-bounds:{off:#x}", q.get("bounds") == EXPECTED_BOUNDS[off], {"observed": q.get("bounds"), "expected": EXPECTED_BOUNDS[off]})
    if off == 0x36D:
        check("memory-pstate-path", pstate_result["memory_pstate"]["unconditional_path"] == ["0x7000", "0x7008", "0x702e", "0x7032"] or pstate_result["memory_pstate"]["unconditional_path"] == ["0x7000", "0x7008", "0x702e", "0x7030", "0x7032"], pstate_result["memory_pstate"]["unconditional_path"])
        check("memory-pstate-serializer-token", pstate_result["serializer"]["record_id"] == "0x123d" and pstate_result["serializer"]["source"] == "AmdSetup+0x36d", pstate_result["serializer"])
    if off == 0x6A3:
        matching = []
        for mod_rows in ownership_result.get("ownership", {}).values():
            matching.extend([x for x in mod_rows if x.get("source_setup_offset") == "0x6a3" and x.get("token") == "0x1331"])
        check("serializer-record:0x6a3-destination-trace", len(matching) == 2, {"expected_record": "0x1331", "matches": matching})
    elif off in (0x368, 0x36D):
        expected = "0x1237" if off == 0x368 else "0x123c"
        matches = []
        for mod_rows in all_fields_result.get("modules", {}).values():
            for recs in mod_rows.get("records", {}).values():
                for row in recs:
                    if row.get("field") == hex(off) and row.get("token") == expected: matches.append(row)
        check(f"serializer-record:{off:#x}-lifetime", len(matches) == 2, {"expected_record": expected, "matches": matches})
    q_options = [{"label": x["label"], "value": x["value"], "default": bool(x.get("default"))} for x in q.get("options", [])]
    label_for_value = next((x["label"] for x in q.get("options", []) if x["value"] == value), None)
    enum_codes = [x["value"] for x in q.get("options", []) if isinstance(x.get("value"), int) and x.get("label") != "Auto"]
    labels_mhz = [int(x["label"][:-3]) for x in q.get("options", []) if isinstance(x.get("label"), str) and x["label"].endswith("MHz") and x["label"][:-3].isdigit()]
    df_bounds = EXPECTED_BOUNDS[0x704]
    advertised_overlap = None
    if off == 0x316:
        advertised_overlap = {
            "memory_clock_enum_codes": enum_codes,
            "memory_clock_labels_mhz": labels_mhz,
            "df_override_numeric_bounds": df_bounds,
            "all_memory_labels_within_df_bounds": all(df_bounds[0] <= x <= df_bounds[1] for x in labels_mhz),
            "meaning": "UI numeric overlap only; common units/domain, training support, and synchronous crossing are not established.",
        }
    actual = {
        "frequency_units_conversion": "UNKNOWN/UNRUN",
        "physical_domain": "UNKNOWN/UNRUN",
        "training_support": "UNKNOWN/UNRUN",
        "synchronous_crossing": "UNKNOWN/UNRUN",
        "evidence_boundary": "Exact-clv IFR/menu bytes and persisted request only; no consumer/actuator proof in this matrix.",
    }
    rows.append({
        "body_offset": hex(off),
        "absolute_rom_offset": hex(BODY_BASE + off),
        "field": spec["name"],
        "persisted": {"raw_little_endian": raw.hex(), "value": value, "ifr_label_for_value": label_for_value, "interpretation": "ROM-stored AmdSetup request, not applied hardware state"},
        "evidence_source": source,
        "exact_clv_ifr": {
            "question_id": q.get("qid"), "label": q.get("label"), "help": q.get("help"), "flags": q.get("flags"),
            "reset_required": q.get("reset_required"), "callback": q.get("callback"), "read_only": q.get("read_only"),
            "options": q_options, "bounds": q.get("bounds"),
        },
        "advertised_ui_intersection": advertised_overlap,
        "actual_supported_mapping": actual,
    })

# Cross-field checks are intentionally domain-neutral.
memory_enum_codes = [x[1] for x in EXPECTED_OPTIONS[0x316] if x[0] != "Auto"]
memory_values = [int(x[0][:-3]) for x in EXPECTED_OPTIONS[0x316] if x[0].endswith("MHz")]
df_bounds = EXPECTED_BOUNDS[0x704]
uclk_values = [x[1] for x in EXPECTED_OPTIONS[0x330] if x[0] != "Auto"]
check("ui-memory-df-numeric-overlap-only", all(df_bounds[0] <= x <= df_bounds[1] for x in memory_values), {"memory_labels_mhz": memory_values, "memory_enum_codes": memory_enum_codes, "df_bounds": df_bounds})
check("uclk-has-no-numeric-ratio-option", uclk_values == [1], {"uclk_non_auto_values": uclk_values})
check("numeric-df-has-no-enumerated-options", EXPECTED_OPTIONS[0x704] == [], {"options": EXPECTED_OPTIONS[0x704]})
check("no-training-claim", True, "This verifier makes no training/frequency/domain claim.")

result = {
    "status": "PASS" if all(x["status"] == "PASS" for x in checks) else "FAIL",
    "scope": "exact-clv IFR/UI configuration-domain matrix; advertised numerical overlap versus actual mapping/training unknowns",
    "evidence_class": ["observed-bytes", "static-analysis"],
    "rom": {"path": str(ROM), "sha256": sha(rom), "size": len(rom), "amdsetup_body_base": hex(BODY_BASE)},
    "menu": {"path": str(MENU), "sha256": menu_sha, "rom_sha256": menu.get("rom_sha256"), "module_sha256": menu.get("module_sha256")},
    "supplemental_memory_pstate": {"path": str(PSTATE_RESULT), "sha256": sha(PSTATE_RESULT.read_bytes()), "status": pstate_result.get("status"), "checks": pstate_result.get("checks")},
    "supplemental_discrimination": {"path": str(DISCR_RESULT), "sha256": sha(DISCR_RESULT.read_bytes()), "status": discr_result.get("status"), "checks": discr_result.get("checks")},
    "ownership_correction": {"path": str(OWNERSHIP_RESULT), "sha256": sha(OWNERSHIP_RESULT.read_bytes()), "status": ownership_result.get("status"), "checks": ownership_result.get("checks"), "corrected_fclk_record": "0x1331"},
    "all_fields_lifetime": {"path": str(ALL_FIELDS_RESULT), "sha256": sha(ALL_FIELDS_RESULT.read_bytes()), "status": all_fields_result.get("status"), "checks": all_fields_result.get("checks")},
    "uclk_semantics": {"path": str(UCLK_RESULT), "sha256": sha(UCLK_RESULT.read_bytes()), "status": uclk_result.get("status"), "checks": uclk_result.get("checks")},
    "matrix": rows,
    "cross_field_summary": {
        "memory_clock_speed_labels_mhz": memory_values,
        "memory_clock_speed_enum_codes": memory_enum_codes,
        "df_override_bounds": df_bounds,
        "advertised_numeric_overlap": True,
        "advertised_overlap_interpretation": "The labels/range overlap numerically only. No shared unit, clock-domain identity, rate conversion, training range, or synchronous-crossing selection is proven.",
        "fclk_dpm_serializer_record": "0x1331",
        "uclk_divider_enum": {"non_auto_values": uclk_values, "interpretation": "Enabled is an enum value; no divider ratio or MCLK/UCLK relation is proven."},
        "phy_power_saving_context": {"body_offset": "0x368", "baseline": 255, "serializer_record": "0x1237", "training_semantics": "UNKNOWN/UNRUN"},
        "memory_pstate_gate": {"body_offset": "0x36D", "absolute_rom_offset": "0x83C", "qid": "0x25E", "options": {"Auto": 255, "Enabled": 1, "Disabled": 0}, "baseline": 255, "serializer_record": "0x123C", "package_path": ["0x7000", "0x7008", "0x702E", "0x7030", "0x7032"], "downstream_training_semantics": "UNKNOWN/UNRUN", "reason": "Native control and serializer edge are mapped; DF override consumer and training effect are not."},
    },
    "minimum_offline_semantic_gate": {
        "status": "OPEN",
        "required": [
            "Byte-backed consumer/actuator mapping for MemoryClockSpeed, UclkDiv1M0, FclkDpm, DfClockOverrideControl, DfClockOvrd, and the Memory P-state gate (+0x36D -> token 0x123D).",
            "Resolve units/rate conversion and UclkDiv1M0 semantics, including whether any setting selects a synchronous crossing rather than merely storing equal-looking values.",
            "Establish a defensible supported-range/training hypothesis without calling it hardware-supported; keep voltage and unrelated settings unchanged.",
            "Combine with explicit existing-NVRAM/default precedence and migration behavior before an experimental default profile is described.",
        ],
        "not_required_for_offline_generation": "Live telemetry or board execution; these remain hardware-acceptance evidence, not an offline prerequisite.",
        "blocking_claim": "Until this gate closes, only a request/advertised-UI profile may be described; no truthful applied default or 1:1:1 profile can be named.",
    },
    "checks": {"passed": sum(x["status"] == "PASS" for x in checks), "failed": sum(x["status"] == "FAIL" for x in checks), "total": len(checks)},
    "checks_detail": checks,
    "limits": [
        "No firmware execution, training, hardware clock observation, voltage measurement, live NVRAM action, or telemetry was run.",
        "IFR MHz labels and numeric bounds are advertised UI encodings; they do not establish physical units, domains, or safe frequencies.",
        "No frequency, voltage, or 1:1 implication is inferred from numerical overlap.",
    ],
}
OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"status": result["status"], "checks": result["checks"], "rom_sha256": sha(rom), "output": str(OUT.resolve())}, sort_keys=True))
raise SystemExit(0 if result["status"] == "PASS" else 1)
