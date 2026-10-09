#!/usr/bin/env python3
"""Byte-backed stage-2 check for clv AmdSetup defaults and precedence."""
from __future__ import annotations
import hashlib, json, struct, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ROM = ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin"
STAGE1 = ROOT / "evidence/firmware-audit/20260920-clv-sync-stage1/stage1-report.json"
MENU = ROOT / "evidence/firmware-audit/20260920-df-init-route/menu-result.json"
EDK_META = OUT / "edk2-HiiConfigAccess.metadata.json"
GATE_META = OUT / "edk2-SetupBrowser-callback-gate.metadata.json"
GATE_SETUP_SNIP = OUT / "edk2-SetupBrowser-Setup-snippet.txt"
GATE_PRESENTATION_SNIP = OUT / "edk2-SetupBrowser-Presentation-snippet.txt"
SETUP_BIN = ROOT / "evidence/firmware-audit/20260919-inv-token-consumers/CbsSetupDxe-7ff717d51c9a.bin"
SETUP_INS = ROOT / "evidence/firmware-audit/20260919-inv-token-consumers/CbsSetupDxe-7ff717d51c9a.instructions.json"
BASE_BIN = ROOT / "evidence/firmware-audit/20260919-inv-token-consumers/CbsBasePei-6ff112922ad8.bin"
BASE_INS = ROOT / "evidence/firmware-audit/20260919-inv-token-consumers/CbsBasePei-6ff112922ad8.instructions.json"

EXPECTED = {
    str(ROM): "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8",
    str(SETUP_BIN): "7ff717d51c9a447c6954c63b633cf836f1e4396c2b01f4bf590268a60ac1d0d8",
    str(BASE_BIN): "6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77",
}
FIELDS = {
    "0x316": {"name": "MemoryClockSpeed", "width": 1, "existing": 36, "fallback": 0xff, "init_rva": "0x3c80", "init_bytes": "c68116030000ff"},
    "0x330": {"name": "UclkDiv1M0", "width": 1, "existing": 1, "fallback": 0xff, "init_rva": "0x3d22", "init_bytes": "c68130030000ff"},
    "0x6A3": {"name": "FclkDpm", "width": 1, "existing": 15, "fallback": 0x0f, "init_rva": "0x4561", "init_bytes": "c681a30600000f"},
    "0x703": {"name": "DfClockOverrideControl", "width": 1, "existing": 1, "fallback": 0xff, "init_rva": "0x4741", "init_bytes": "c68103070000ff"},
    "0x704": {"name": "DfClockOvrd", "width": 2, "existing": 1420, "fallback": 1000, "init_rva": "0x474d", "init_bytes": "66898104070000"},
}

def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def load_ins(p: Path):
    return {int(x["rva"]): x for x in json.loads(p.read_text())}

def check(cond, label, details=None):
    checks.append({"label": label, "status": "PASS" if cond else "FAIL", "details": details})
    return cond

checks = []
for p, want in EXPECTED.items():
    pp = Path(p)
    check(pp.exists(), f"exists:{pp}")
    if pp.exists():
        check(sha256(pp) == want, f"sha256:{pp}", {"observed": sha256(pp), "expected": want})

rom = ROM.read_bytes()
check(len(rom) == 0x1000000, "clv-size-16MiB", len(rom))
body_base = 0x4CF
nvar_raw = {}
for off, spec in FIELDS.items():
    o = int(off, 16)
    raw = rom[body_base + o: body_base + o + spec["width"]]
    val = int.from_bytes(raw, "little")
    nvar_raw[off] = {"absolute": hex(body_base + o), "raw": raw.hex(), "value": val}
    check(val == spec["existing"], f"existing-nvar:{off}", nvar_raw[off])

setup = load_ins(SETUP_INS)
base = load_ins(BASE_INS)
# Semantic labels for the callback action values are pinned in own metadata
# from the external-primary EDK II header; the firmware bytes remain local.
edk_meta = json.loads(EDK_META.read_text())
check(edk_meta["observed_definitions"]["EFI_BROWSER_ACTION_RETRIEVE"] == 2, "EDK2-action-retrieve-2")
check(edk_meta["observed_definitions"]["EFI_BROWSER_ACTION_DEFAULT_STANDARD"] == "0x1000", "EDK2-action-default-standard-0x1000")
gate_meta = json.loads(GATE_META.read_text())
check(sha256(GATE_META) == "6b48c5c5b2b71b34b90c1efd58cb878dfd386bdaba3ba345bd6e52c1de6c2398", "EDK2-browser-gate-metadata-hash")
check(sha256(GATE_SETUP_SNIP) == "9b899844cf050edd11183d5a4e6849a801369414449876cabc85351ad61402a0", "EDK2-SetupBrowser-Setup-snippet-hash")
check(sha256(GATE_PRESENTATION_SNIP) == "b948159d421aba1e9c31d16cc1ffe11e446a30e5eb0a077a8b75b00ce35ff51b", "EDK2-SetupBrowser-Presentation-snippet-hash")
check(gate_meta["sources"][0]["sha256"] == "183743078ef483db5c800080cd338a7ec8108014f801f5c617ee6e884e80df9a", "EDK2-SetupBrowser-Setup-source-hash")
check(gate_meta["sources"][1]["sha256"] == "525002bfdac874432e5d6d46b014be7551bd4d3813a383eb37a6394fa7bf47ab", "EDK2-SetupBrowser-Presentation-source-hash")
# CbsSetupDxe's concrete default helper at RVA 0x2fe4, called by three callers.
for rva, expected in {
    0x3c80: "c68116030000ff", 0x3d22: "c68130030000ff",
    0x4561: "c681a30600000f", 0x4741: "c68103070000ff",
    0x4748: "b8e8030000", 0x474d: "66898104070000",
}.items():
    d = setup.get(rva)
    check(d is not None and d["bytes"] == expected, f"CbsSetupDxe-default-byte:{rva:#x}", {"observed": d, "expected": expected})
for rva, target in [(0x653, 0x2fe4), (0xa11, 0x2fe4), (0xb86, 0x2fe4)]:
    d = setup.get(rva)
    got = None
    if d and d["bytes"].startswith("e8"):
        got = rva + 5 + int.from_bytes(bytes.fromhex(d["bytes"])[1:5], "little", signed=True)
    check(got == target, f"CbsSetupDxe-default-call:{rva:#x}->{target:#x}", {"observed_target": None if got is None else hex(got), "instruction": d})
# Exact CbsSetupDxe callback registration: interface+0x48 = Callback RVA 0x950.
for rva, expected in {0xaf6: "488d0553feffff", 0xb03: "48894748"}.items():
    d = setup.get(rva)
    check(d is not None and d["bytes"] == expected, f"CbsSetupDxe-callback-registration:{rva:#x}", {"observed": d, "expected": expected})
# Callback RVA 0x950: action in RDX; action 2=RETRIEVE branches to 0xa1d,
# while 0x1000=DEFAULT_STANDARD falls through to helper 0x2fe4.
for rva, expected in {
    0x979: "4883fa03", 0x983: "4883fa04", 0x9fb: "ba02000000",
    0xa03: "483bda", 0xa06: "7415", 0xa08: "4881fb00100000", 0xa0f: "7537", 0xa11: "e8ce250000",
}.items():
    d = setup.get(rva)
    check(d is not None and d["bytes"] == expected, f"CbsSetupDxe-callback-default-branch:{rva:#x}", {"observed": d, "expected": expected})
callback_default_target = 0xa11 + 5 + int.from_bytes(bytes.fromhex(setup[0xa11]["bytes"])[1:5], "little", signed=True)
check(callback_default_target == 0x2fe4, "CbsSetupDxe-callback-default-target-0x2fe4", hex(callback_default_target))
# Standard-default branch does not consume r14/QID; invocation is browser-gated.
std_window = [d for d in setup.values() if 0x9f3 <= d["rva"] <= 0xa16]
check(not any("r14" in (d.get("operands") or "") for d in std_window), "CbsSetupDxe-standard-default-no-QID-use", [d["operands"] for d in std_window if "r14" in (d.get("operands") or "")])
# The concrete existing-variable path uses EFI_RUNTIME_SERVICES.GetVariable (+0x48),
# requires EFI_BUFFER_TOO_SMALL and size 0x8b5, then performs a second GetVariable;
# failure at either gate reaches 0x2fe4.
for rva, expected in {
    0x5fe: "ff5048", 0x601: "48b90500000000000080", 0x610: "4881bc2480000000b5080000",
    0x647: "ff5048", 0x64a: "483bc3", 0x64d: "7d09",
}.items():
    d = setup.get(rva)
    check(d is not None and d["bytes"] == expected, f"CbsSetupDxe-GetVariable-gate:{rva:#x}", {"observed": d, "expected": expected})
# Independent CbsBasePei fallback has three failure branches in each of two read paths.
for rva in (0x333, 0x344, 0x355, 0x5b4, 0x5c5, 0x5d6):
    d = base.get(rva)
    got = None
    if d and d["bytes"].startswith("e8"):
        got = rva + 5 + int.from_bytes(bytes.fromhex(d["bytes"])[1:5], "little", signed=True)
    check(got == 0x650, f"CbsBasePei-missing-variable-fallback:{rva:#x}->0x650", {"observed_target": None if got is None else hex(got), "instruction": d})
# CbsBasePei fallback initializer exact bytes (same selected fields).
base_init = {0x1a4b: "c68216030000ff", 0x1b3d: "c68130030000ff", 0x294b: "c682a30600000f", 0x2c0f: "c68203070000ff", 0x2c1e: "66898104070000"}
for rva, expected in base_init.items():
    d = base.get(rva)
    check(d is not None and d["bytes"] == expected, f"CbsBasePei-default-byte:{rva:#x}", {"observed": d, "expected": expected})

menu = json.loads(MENU.read_text())
menu_map = {int(q["offset"], 16): q for q in menu["questions"] if q.get("varstore_id") == "0x5000"}
question_gate_expectations = {
    0x316: {"qid": "0x20f", "callback": False},
    0x330: {"qid": "0x229", "callback": False},
    0x6A3: {"qid": "0x7045", "callback": True},
    0x703: {"qid": "0x37d", "callback": False},
    0x704: {"qid": "0x37e", "callback": False},
}
question_gates = {}
load_defaults = {}
for off, spec in FIELDS.items():
    o = int(off, 16)
    q = menu_map.get(o)
    check(q is not None, f"IFR-question-present:{off}")
    expected_gate = question_gate_expectations[o]
    observed_gate = {"qid": (q or {}).get("qid"), "callback": (q or {}).get("callback")}
    question_gates[off] = observed_gate
    check(observed_gate == expected_gate, f"IFR-callback-gate:{off}", {"observed": observed_gate, "expected": expected_gate})
    defaults = [x["value"] for x in (q or {}).get("options", []) if x.get("default")]
    if defaults:
        check(len(defaults) == 1 and defaults[0] == spec["fallback"], f"IFR-default:{off}", {"default": defaults, "expected": spec["fallback"]})
        load_defaults[off] = {"status": "STATIC_DEFAULT_PRESENT", "value": defaults[0]}
    else:
        load_defaults[off] = {"status": "NO_IFR_DEFAULT_OPCODE_OBSERVED", "value": None}
        check(o == 0x704, f"IFR-no-default-only-numeric:{off}", {"options": (q or {}).get("options", []), "bounds": (q or {}).get("bounds")})

# A host-only byte-backed model deliberately leaves +0x704 Load Defaults unresolved:
# the menu has no default opcode for the numeric question, while the initializer has 1000.
model = {
    "existing_variable_success": {off: x["existing"] for off, x in FIELDS.items()},
    "missing_variable_fallback": {off: x["fallback"] for off, x in FIELDS.items()},
    "load_defaults_ifr_observed": load_defaults,
    "no_hardware_execution": True,
}
passed = sum(x["status"] == "PASS" for x in checks)
failed = len(checks) - passed
result = {
    "status": "PASS" if failed == 0 else "FAIL",
    "checks": {"passed": passed, "failed": failed, "total": len(checks)},
    "evidence_class": ["observed-bytes", "static-analysis", "emulated-or-host-tested"],
    "rom": {"path": str(ROM), "sha256": sha256(ROM), "size": len(rom), "amdsetup_body_base": hex(body_base), "raw_fields": nvar_raw},
    "modules": {"CbsSetupDxe": {"path": str(SETUP_BIN), "sha256": sha256(SETUP_BIN)}, "CbsBasePei": {"path": str(BASE_BIN), "sha256": sha256(BASE_BIN)}},
    "default_sources": {"CbsSetupDxe_helper_rva": "0x2fe4", "CbsBasePei_helper_rva": "0x4c0 (Rizin) / 0x650 (instruction RVA)", "get_variable_method_offset": "0x48", "required_size": "0x8b5", "efi_buffer_too_small": "0x80000005"},
    "fields": FIELDS,
    "precedence_model": model,
    "callback_default_action": {
        "callback_rva": "0x950",
        "registration": "EFI_HII_CONFIG_ACCESS_PROTOCOL interface+0x48",
        "action_2": "EFI_BROWSER_ACTION_RETRIEVE -> callback path 0xA1D (not helper 0x2FE4)",
        "action_0x1000": "EFI_BROWSER_ACTION_DEFAULT_STANDARD",
        "branch_target": "0x2fe4",
        "numeric_0x704": 1000,
        "question_gates": question_gates,
        "execution_status": "STATIC_ONLY_CALLBACK_NOT_EXECUTED",
    },
    "checks_detail": checks,
    "limitations": [
        "No firmware code executed; GetVariable branch behavior is static control-flow evidence.",
        "No live NVRAM reset or Load Optimized Defaults action was run.",
        "The numeric +0x704 question has no IFR default option and no CALLBACK flag; the standard-default callback is browser-gated by callback questions and is statically traced to 1000 as a side effect of the selected callback path. Live browser/reset persistence is unrun.",
        "A same-session hardware clock/training result is not established.",
    ],
}
(OUT / "stage2-defaults-result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({"status": result["status"], "checks": result["checks"], "existing_nvar": model["existing_variable_success"], "missing_variable_fallback": model["missing_variable_fallback"], "load_defaults_ifr_declared": load_defaults, "callback_default_action": result["callback_default_action"]}, sort_keys=True))
sys.exit(0 if failed == 0 else 1)
