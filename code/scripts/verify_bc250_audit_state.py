#!/usr/bin/env python3
"""Verify the current BC-250 readback/candidate evidence state.

This verifier only reads existing artifacts. It does not call a programmer,
open hardware devices, write firmware, or mutate Cutter/Rizin state.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = "83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0"
APCB_SHA = "6b1fe8ef504142d5d5273a85b6c9febdf0b1fb8fc08ebab2593281c320cb9d70"
MEM_SHA = "63cd074197ce26bafe7d2f943eeceb69b331cdba94f12662820de710fc193fee"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def map_refs_ok(path: Path) -> tuple[bool, list[str]]:
    obj = load(path)
    errors: list[str] = []
    for key, item in obj.get("artifacts", {}).items():
        target = Path(item["path"])
        if not target.is_absolute():
            target = ROOT / target
        if not target.is_file():
            errors.append(f"{key}: missing {target}")
        elif sha256(target) != item.get("sha256"):
            errors.append(f"{key}: hash mismatch")
    return not errors, errors


def diff_positions(a: bytes, b: bytes) -> list[int]:
    if len(a) != len(b):
        return [-1]
    return [i for i, (x, y) in enumerate(zip(a, b)) if x != y]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/firmware-audit/audit-state-verification-20260911.json")
    args = parser.parse_args()
    output = args.output.resolve()

    base = ROOT / "evidence/programmer/reads/20260911/read-a.bin"
    read_b = ROOT / "evidence/programmer/reads/20260911/read-b.bin"
    dump = ROOT / "dump/2.bin"
    apcb_candidate = ROOT / "candidates/BC250_APCB_DFG_only_v001_from_read-a.bin"
    mem_candidate = ROOT / "candidates/BC250_MemoryClock_1750_only_v001_from_read-a.bin"
    apcb_manifest_path = ROOT / "evidence/candidates/BC250_APCB_DFG_only_v001/build-manifest.json"
    mem_manifest_path = ROOT / "evidence/candidates/BC250_MemoryClock_1750_only_v001/build-manifest.json"
    fresh_inv = ROOT / "evidence/programmer/reads/20260911/firmware-audit/inventory.json"
    fresh_ext = ROOT / "evidence/programmer/reads/20260911/firmware-audit/read-a-inventory-with-extract.json"
    fresh_nvar = ROOT / "evidence/programmer/reads/20260911/firmware-audit/read-a-nvar-primary.json"
    apcb_report = ROOT / "evidence/candidates/BC250_APCB_DFG_only_v001/apcb-detail.json"
    apcb_fw = ROOT / "evidence/candidates/BC250_APCB_DFG_only_v001/firmware-audit.json"
    mem_nvar = ROOT / "evidence/candidates/BC250_MemoryClock_1750_only_v001/nvar-primary.json"
    mem_fw = ROOT / "evidence/candidates/BC250_MemoryClock_1750_only_v001/firmware-audit.json"
    apcb_review = ROOT / "evidence/candidates/BC250_APCB_DFG_only_v001/independent-review-gemini.md"
    mem_review = ROOT / "evidence/candidates/BC250_MemoryClock_1750_only_v001/independent-review-gemini.md"
    vcn_map = ROOT / "evidence/firmware-audit/vcn-evidence-map.json"
    mem_map = ROOT / "evidence/firmware-audit/memory-soc-voltage-evidence-map.json"
    matrix = ROOT / "evidence/firmware-audit/completion-matrix-20260911.json"

    checks: dict[str, dict[str, Any]] = {}
    checks["baseline_hash"] = {"pass": all(sha256(p) == BASE_SHA for p in (base, read_b, dump)), "expected": BASE_SHA, "paths": [str(p) for p in (base, read_b, dump)]}
    base_bytes = base.read_bytes()
    checks["reads_byte_identical"] = {"pass": base_bytes == read_b.read_bytes() == dump.read_bytes()}
    apcb_bytes = apcb_candidate.read_bytes()
    mem_bytes = mem_candidate.read_bytes()
    apcb_diff = diff_positions(base_bytes, apcb_bytes)
    mem_diff = diff_positions(base_bytes, mem_bytes)
    checks["apcb_exact_diff"] = {"pass": apcb_diff == [0xAB1010, 0xAB1132, 0xAB116E], "offsets": [hex(x) for x in apcb_diff]}
    checks["memory_exact_diff"] = {"pass": mem_diff == [0x7E5], "offsets": [hex(x) for x in mem_diff]}
    checks["candidate_hashes"] = {"pass": sha256(apcb_candidate) == APCB_SHA and sha256(mem_candidate) == MEM_SHA, "apcb": sha256(apcb_candidate), "memory": sha256(mem_candidate)}

    inv = load(fresh_inv)
    checks["fresh_inventory"] = {"pass": all(i["size"] == 0x1000000 and i["psp"]["checksum_match"] and i["bhd"]["checksum_match"] and i["apcb"]["checksum_match"] for i in inv["images"]), "images": len(inv["images"])}
    ext = load(fresh_ext)["images"][0]["extraction"]
    checks["fresh_extraction"] = {"pass": ext["module_count"] == 234 and ext["unique_module_files"] == 234, "module_count": ext["module_count"], "unique": ext["unique_module_files"]}
    nv = load(fresh_nvar)
    checks["fresh_nvar"] = {"pass": nv["record_count"] == 683 and nv["selected_count"] == 1 and nv["selected_fields"][0]["value"] == 255, "warnings": len(nv["errors"])}

    ar = load(apcb_report)["images"]
    checks["apcb_parser"] = {"pass": ar[1]["apcb"]["checksum_match"] and ar[1]["apcb"]["dfg_words"] == {"0x130": "0x007FFF00", "0x16C": "0x007FFF00"}}
    af = load(apcb_fw)["images"][0]
    checks["apcb_firmware_parser"] = {"pass": af["psp"]["checksum_match"] and af["bhd"]["checksum_match"] and af["apcb"]["checksum_match"] and len(af["firmware_volumes"]) == 4}
    mn = load(mem_nvar)["selected_fields"]
    mf = load(mem_fw)["images"][0]
    checks["memory_parser"] = {"pass": any(f["name"] == "MemoryClockSpeed" and f["value"] == 35 for f in mn) and mf["psp"]["checksum_match"] and mf["bhd"]["checksum_match"] and mf["apcb"]["checksum_match"]}
    checks["review_hashes"] = {"pass": sha256(apcb_review) == "90e15006a3093c8ba484fa702d4dab12225d522878892e6bba01d39666db7905" and sha256(mem_review) == "47a9b6a7be4628861ac04031e959a6ea76b1b67bfe7f724c8ba0b66b330123fb"}
    v_ok, v_err = map_refs_ok(vcn_map); m_ok, m_err = map_refs_ok(mem_map)
    checks["map_references"] = {"pass": v_ok and m_ok, "vcn_errors": v_err, "memory_errors": m_err}
    matrix_obj = load(matrix)
    checks["completion_matrix_current"] = {"pass": matrix_obj.get("overall_status") == "ACTIVE_INCOMPLETE", "status": matrix_obj.get("overall_status")}

    pass_count = sum(bool(value.get("pass")) for value in checks.values())
    result = {"generated_at": datetime.now(timezone.utc).isoformat(), "tool": "scripts/verify_bc250_audit_state.py", "checks": checks, "passed_checks": pass_count, "total_checks": len(checks), "all_exercised_checks_pass": pass_count == len(checks), "hardware_mutation": False, "open_gates": matrix_obj.get("goal_completion_blockers", [])}
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing output: {output}")
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "passed_checks": pass_count, "total_checks": len(checks), "all_exercised_checks_pass": result["all_exercised_checks_pass"]}))
    return 0 if result["all_exercised_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
