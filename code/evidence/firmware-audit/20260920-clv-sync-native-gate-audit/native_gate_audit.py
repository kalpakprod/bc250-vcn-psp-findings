#!/usr/bin/env python3
"""Read-only offline semantic gate audit for the conditional CLV native-sync template."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ROM = ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin"
MENU = ROOT / "evidence/firmware-audit/20260920-df-init-route/menu-result.json"
SPEC = ROOT / "docs/research/20260920-clv-sync-conditional-candidate-spec.md"
PLAN = ROOT / "specs/2026-09-20-clv-sync-development-plan.md"
DEFAULTS = ROOT / "evidence/firmware-audit/20260920-clv-sync-stage2-defaults/stage2-defaults-result.json"
MATRIX = ROOT / "evidence/firmware-audit/20260920-clv-sync-configuration-domain-matrix/configuration-domain-matrix.json"
PSTATE = ROOT / "evidence/firmware-audit/20260920-clv-sync-stage2-memory-pstate/memory-pstate-result.json"
UCLK = ROOT / "evidence/firmware-audit/20260920-clv-sync-stage2-uclk-semantics/uclk-semantics-result.json"
TOKEN = ROOT / "evidence/firmware-audit/20260920-clv-sync-stage2-token-matrix/token-matrix-result.json"
OWNERSHIP = ROOT / "evidence/firmware-audit/20260920-clv-sync-record-ownership-correction/record-ownership-result.json"
ROM_SHA = "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"
MENU_SHA = "6e2d1978f7dcfdb4e780b220503d1a14401cb34c9d65104ca98840a47e2af14a"
BODY = 0x4CF
FIELDS = {
    "MemoryClockSpeed": (0x316, 1, 0x7E5, "0x11ED"),
    "UclkDiv1M0": (0x330, 1, 0x7FF, "0x1204"),
    "MemoryPstate": (0x36D, 1, 0x83C, "0x123D"),
    "FclkDpm": (0x6A3, 1, 0xB72, "0x1331"),
    "DfClockOverrideControl": (0x703, 1, 0xBD2, "0x1373"),
    "DfClockOvrd": (0x704, 2, 0xBD3, "0x1374"),
}

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def result_ok(obj: dict) -> bool:
    checks = obj.get("checks")
    if isinstance(checks, dict):
        return obj.get("status") == "PASS" and checks.get("failed") == 0
    return obj.get("status") == "PASS"

def row(gate, requirement, status, evidence_class, command, observed, consequence):
    return {
        "gate": gate,
        "requirement": requirement,
        "status": status,
        "evidence_class": evidence_class,
        "command": command,
        "observed": observed,
        "consequence": consequence,
    }

rom = ROM.read_bytes()
menu = json.loads(MENU.read_text())
spec_text = SPEC.read_text()
plan_text = PLAN.read_text()
defaults = json.loads(DEFAULTS.read_text())
matrix = json.loads(MATRIX.read_text())
pstate = json.loads(PSTATE.read_text())
uclk = json.loads(UCLK.read_text())
token = json.loads(TOKEN.read_text())
ownership = json.loads(OWNERSHIP.read_text())
questions = {int(q["offset"], 16): q for q in menu["questions"] if q.get("varstore_id") == "0x5000"}

def value(name):
    off, width, _, _ = FIELDS[name]
    return int.from_bytes(rom[BODY + off:BODY + off + width], "little")

field_state = {}
for name, (off, width, absolute, record) in FIELDS.items():
    q = questions.get(off)
    raw = rom[BODY + off:BODY + off + width]
    field_state[name] = {
        "body_offset": hex(off),
        "absolute_offset": hex(absolute),
        "width": width,
        "raw": raw.hex(),
        "value": int.from_bytes(raw, "little"),
        "record": record,
        "ifr": {
            "label": None if q is None else q.get("label"),
            "qid": None if q is None else q.get("qid"),
            "help": None if q is None else q.get("help"),
            "conditions": None if q is None else q.get("conditions"),
            "options": None if q is None else q.get("options", []),
            "callback": None if q is None else q.get("callback"),
        },
    }

# The spec's proposed minimum is checked as a literal template, not inferred from filename.
template_strings_present = all(x in spec_text for x in [
    "0x7E5", "0x7FF", "0xBD3", "0xBD4", "0x36D", "0x6A3", "four changed bytes",
])
help_text = questions[0x703]["help"]
help_requires_pstate_disabled = "Memory P-state is disabled" in help_text
pstate_question = pstate["memory_pstate"]["question"]
pstate_disabled_option = next((x["value"] for x in pstate_question["options"] if x["label"] == "Disabled"), None)
template_leaves_pstate = "0x36D" in spec_text and "Hold unchanged" in spec_text
# Existing exact evidence says callback/registration are static only.
consumer_unresolved = "final consumer" in SPEC.read_text().lower() or "requester/consumer" in SPEC.read_text().lower()

matrix_rows = [
    row("G0", "Pinned source identity", "PASS" if len(rom) == 0x1000000 and sha(ROM) == ROM_SHA else "FAIL",
         ["observed-bytes"], "sha256sum evidence/donor/retroweb-20260916/BC250_5.00_clv.bin",
         {"size": len(rom), "sha256": sha(ROM)}, "The audit is bound to one immutable 16 MiB donor."),
    row("G1", "Native IFR fields/defaults/help reopened", "PASS" if sha(MENU) == MENU_SHA and menu.get("rom_sha256") == ROM_SHA and template_strings_present else "PARTIAL",
         ["observed-bytes", "static-analysis"], "python3 evidence/.../configuration_domain_matrix.py; python3 evidence/.../stage2_defaults_verify.py",
         {"menu_sha256": sha(MENU), "fields": field_state, "template_strings_present": template_strings_present},
         "Native metadata is exact, but IFR help/conditions are not proof of runtime enforcement."),
    row("G2", "Serializer ownership for all candidate fields", "PASS" if result_ok(token) and result_ok(ownership) else "FAIL",
         ["observed-bytes", "static-analysis"], "python3 evidence/.../token_matrix_verify.py; python3 evidence/.../record_ownership_verify.py",
         {"token_status": token.get("status"), "token_checks": token.get("checks"), "ownership_status": ownership.get("status"), "ownership_checks": ownership.get("checks")},
         "Serializer handoffs are mapped; this is not final divider/training consumption."),
    row("G3", "0x1204 requester/consumer/final actuator", "BLOCKED" if consumer_unresolved else "UNRESOLVED",
         ["static-analysis", "emulated-or-host-tested"], "python3 evidence/.../uclk_semantics_verify.py; python3 evidence/.../configuration_domain_matrix.py",
         {"uclk_status": uclk.get("status"), "uclk_conclusion": uclk.get("conclusion"), "matrix_gate": matrix.get("minimum_offline_semantic_gate", {}).get("status")},
         "The first static edge is an INV adapter/registration candidate; installed/invoked dispatcher and final actuator are not joined."),
    row("G4", "Units/rate conversion and supported shared range", "BLOCKED",
         ["static-analysis"], "python3 evidence/.../configuration_domain_matrix.py; python3 evidence/.../token_matrix_verify.py",
         {"ui_overlap": matrix.get("cross_field_summary", {}).get("advertised_numeric_overlap"), "interpretation": matrix.get("cross_field_summary", {}).get("advertised_overlap_interpretation")},
         "MHz labels and 0..2000 numeric bounds overlap only; enum bytes and numeric DF value are not proven to share units."),
    row("G5", "UclkDiv1M0 ratio and synchronous crossing", "BLOCKED",
         ["static-analysis", "emulated-or-host-tested"], "python3 evidence/.../uclk_semantics_verify.py",
         {"field": field_state["UclkDiv1M0"], "conclusion": uclk.get("conclusion"), "ratio_arithmetic_in_serializer": uclk.get("new_discriminant", {}).get("ratio_arithmetic_in_serializer")},
         "Enabled=1 is preserved as a byte; no ratio, crossing selector, or independent clock relation is established."),
    row("G6", "Memory-P-state/training relation and native override precondition", "BLOCKED",
         ["observed-bytes", "static-analysis"], "python3 evidence/.../memory_pstate_verify.py; python3 evidence/.../configuration_domain_matrix.py",
         {"help": help_text, "help_requires_disabled": help_requires_pstate_disabled, "baseline_memory_pstate": value("MemoryPstate"), "disabled_option": pstate_disabled_option, "template_leaves_pstate": template_leaves_pstate, "pstate_record": field_state["MemoryPstate"]["record"], "pstate_static_result": pstate.get("status")},
         "New contradiction: the four-byte template changes/uses DF override while leaving Memory P-state Auto (0xFF), but native help names Disabled (0x00) as the required precondition. No static proof shows Auto resolves to Disabled before the override consumer; adding 0x83C=00 would raise the minimum to five changed bytes, and still would not prove training."),
    row("G7", "FclkDpm/override precedence", "BLOCKED",
         ["observed-bytes", "static-analysis"], "python3 evidence/.../record_ownership_verify.py; python3 evidence/.../stage2_defaults_verify.py",
         {"fclk_dpm": field_state["FclkDpm"], "defaults": defaults.get("callback_default_action"), "serializer_owner": ownership.get("correction")},
         "+0x6A3 is callback-bearing and serializes to 0x1331, but its downstream precedence relative to manual DF override is unknown; leaving Auto is not justified as irrelevant."),
    row("G8", "Existing-NVRAM/default/fallback/migration precedence", "PARTIAL",
         ["observed-bytes", "static-analysis"], "python3 evidence/.../stage2_defaults_verify.py",
         {"defaults_status": defaults.get("status"), "callback_execution_status": defaults.get("callback_default_action", {}).get("execution_status"), "existing_nvar": defaults.get("existing_nvar"), "fallback": defaults.get("missing_variable_fallback"), "ifr": defaults.get("load_defaults_ifr_declared")},
         "Existing-variable and fallback values are statically mapped; browser invocation, reset and post-reset readback are unrun."),
    row("G9", "Conditional template internally coherent", "BLOCKED",
         ["observed-bytes", "static-analysis"], "python3 native_gate_audit.py",
         {"template_changed_absolute_offsets": ["0x7E5", "0x7FF", "0xBD3", "0xBD4"], "template_asserts": ["0x703=1", "0x36D unchanged", "0x6A3 unchanged"], "native_help_precondition": "0x703=Manual + 0x704 override => FCLK>UCLK and MemoryPstate=Disabled", "baseline_pstate": "0xFF Auto"},
         "The four-byte set remains a conditional template only; the explicit native precondition is not met and semantic consumer/units/crossing gates remain open."),
    row("G10", "Four-role native-sync candidate transaction/build", "UNRUN",
         ["emulated-or-host-tested", "unrun"], "PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test_clv_oc_builder.py' -v",
         {"builder_regression": "7/7 PASS", "unsupported_sync_rejected": True, "sync_candidate_built": False, "four_roles": "UNRUN", "tests_output_path": str(OUT / "builder-tests.stderr")}, "Only the supported df1400 regression was exercised; sync refusal is tested. No native-sync candidate or four-role transaction was created."),
    row("G11", "Hardware acceptance", "UNRUN",
         ["unrun"], "No hardware/settings/flash command (by task constraint)",
         {"hardware": "UNRUN", "physical_clocks": "UNRUN", "training": "UNRUN", "recovery_readback": "UNRUN"}, "No physical clock, divider, crossing, training, performance or stability claim follows."),
]

result = {
    "status": "BLOCKED",
    "artifact_class": "offline_native_sync_semantic_gate_audit",
    "evidence_class": ["observed-bytes", "static-analysis", "emulated-or-host-tested", "unrun-hardware"],
    "source": {"path": str(ROM), "size": len(rom), "sha256": sha(ROM), "amdsetup_body": hex(BODY)},
    "inputs": {"menu": {"path": str(MENU), "sha256": sha(MENU)}, "spec": {"path": str(SPEC), "sha256": sha(SPEC)}, "plan": {"path": str(PLAN), "sha256": sha(PLAN)}},
    "native_fields": field_state,
    "gate_matrix": matrix_rows,
    "new_finding": {
        "id": "F1",
        "title": "Four-byte template omits native Memory-P-state precondition",
        "observed": "Exact DF override help says FCLK > UCLK and Memory P-state disabled; baseline +0x36D=0xFF Auto; exact IFR Disabled option is 0x00; template holds +0x36D unchanged while changing +0x704 and asserting +0x703=Manual.",
        "classification": "offline semantic contradiction / closure condition, not runtime rejection",
        "minimum_change_if_help_is_treated_as_required": "Add AmdSetup+0x36D=0x00 at absolute ROM offset 0x83C, making at least five changed bytes (0x7E5, 0x7FF, 0x83C, 0xBD3, 0xBD4).",
        "qualification": "Because exact IFR has no conditions and retained evidence calls help guidance, this does not prove the firmware will reject Auto; it proves the current four-byte template cannot claim that the documented native precondition is satisfied without an additional proof that Auto resolves to Disabled.",
        "remaining_blockers": ["0x1204 final consumer/actuator", "units and GDDR6 rate conversion", "UclkDiv1M0 ratio/crossing", "FclkDpm precedence", "training semantics", "default/migration execution"],
    },
    "decision": "Do not build a sync candidate. Keep existing df1400-only builder unchanged. The conditional four-byte template is BLOCKED and not internally closed; 1:1:1 remains disallowed.",
    "checks": {"passed": sum(x["status"] == "PASS" for x in matrix_rows), "partial": sum(x["status"] == "PARTIAL" for x in matrix_rows), "blocked": sum(x["status"] == "BLOCKED" for x in matrix_rows), "unrun": sum(x["status"] == "UNRUN" for x in matrix_rows), "total": len(matrix_rows)},
}
OUT.joinpath("gate-matrix.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({"status": result["status"], "checks": result["checks"], "finding": result["new_finding"]["id"], "output": str(OUT.joinpath("gate-matrix.json").resolve())}, sort_keys=True))
