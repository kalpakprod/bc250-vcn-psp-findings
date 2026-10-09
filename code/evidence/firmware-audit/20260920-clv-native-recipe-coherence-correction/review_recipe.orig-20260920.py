from pathlib import Path
import hashlib
import json

root = Path("/home/OWNER/orca/projects/bc250")
recipe = root / "docs/research/2026-09-20-clv-native-operator-recipe.md"
machine = root / "evidence/firmware-audit/20260920-clv-native-1to1-recipe/recipe-result.json"
canonical = root / "docs/research/2026-09-20-clv-native-menu-1to1-guide.md"
pointer = root / "docs/research/20260920-clv-abl1-r6-3c4-producer-trace.md"
uclk = root / "docs/research/2026-09-20-clv-uclk-discrimination-guide.md"
paths = [recipe, machine, canonical, pointer, uclk]
for path in paths:
    assert path.exists(), path
recipe_text = recipe.read_text()
canonical_text = canonical.read_text()
pointer_text = pointer.read_text()
uclk_text = uclk.read_text()
machine_obj = json.loads(machine.read_text())
checks = []


def check(name, ok, detail):
    checks.append({"name": name, "status": "PASS" if ok else "FAIL", "detail": detail})


check("memory_1330", all(x in recipe_text for x in ["1330 MHz", "0x1A", "QID 0x20F", "AmdSetup +0x316"]), "1330 enum/field mapping")
check("memory_1750", all(x in recipe_text for x in ["1750 MHz", "0x23", "QID 0x20F", "AmdSetup +0x316"]), "1750 enum/field mapping")
check("uclk", all(x in recipe_text for x in ["UclkDiv1M0 = Enabled", "QID 0x229", "AmdSetup +0x330", "value 0x01"]), "UclkDiv1M0 mapping")
check("memory_pstate", all(x in recipe_text for x in ["Memory P-state = Disabled", "QID 0x25E", "AmdSetup +0x36D", "value 0x00"]), "Memory P-state mapping")
check("fclk_dpm", all(x in recipe_text for x in ["FCLK_DPM = Disabled", "QID 0x7045", "AmdSetup +0x6A3", "value 0x00"]), "FCLK_DPM mapping")
check("df_control", all(x in recipe_text for x in ["DF Clock Override Control = Manual", "QID 0x37D", "AmdSetup +0x703", "value 0x01"]), "DF control mapping")
check("df_value", all(x in recipe_text for x in ["DF Clock Override         = same test number", "QID 0x37E", "+0x704"]), "DF numeric mapping")
for name, needle in [
    ("canonical_1330", "1330MHz=0x1A"),
    ("canonical_1750", "1750MHz=0x23"),
    ("canonical_uclk", "UclkDiv1M0"),
    ("canonical_memory_pstate", "Memory P-state"),
    ("canonical_fclk", "FCLK_DPM"),
    ("canonical_df", "DF Clock Override"),
]:
    check(name, needle in canonical_text, "canonical guide contains " + needle)
settings = {item["name"]: item for item in machine_obj["settings"]}
check("machine_status", machine_obj.get("status") == "STATIC_EXPERIMENTAL_MENU_HYPOTHESIS", str(machine_obj.get("status")))
check("machine_h1750", machine_obj.get("test_point") == "H1750-native-help", str(machine_obj.get("test_point")))
check("recipe_recommends_1330", "Recommended first test point" in recipe_text and "DF Clock Override          = 1330 decimal" in recipe_text, "current recipe recommendation is H1330")
check("machine_result_coherence", machine_obj.get("test_point") != "H1750-native-help", "machine result still names H1750 while recipe now recommends H1330; refresh or label result as historical H1750")
check(
    "machine_values",
    [
        settings["Memory Clock Speed"]["value"].startswith("0x23"),
        settings["UclkDiv1M0"]["value"].startswith("0x01"),
        settings["Memory P-state"]["value"].startswith("0x00"),
        settings["FCLK_DPM"]["value"].startswith("0x00"),
        settings["DF Clock Override Control"]["value"].startswith("0x01"),
        settings["DF Clock Override"]["value"].startswith("1750"),
    ]
    == [True] * 6,
    "machine H1750 values",
)
check("recipe_warns_alias", "Do not infer" in recipe_text and "MCLK=UCLK=FCLK" in recipe_text, "alias warning")
check("recipe_warns_ratio", "label alone does not decode the ratio" in recipe_text, "ratio warning")
check("recipe_warns_help_conflict", "FCLK > UCLK" in recipe_text and "not a guarantee" in recipe_text, "help conflict warning")
check("pointer_boundary_preserved", "runtime object identity unresolved" in pointer_text and "clock measurement" in pointer_text, "pointer boundary")
check("uclk_boundary_preserved", "cannot identify the divider ratio" in uclk_text and "physical clock" in uclk_text, "clock boundary")
failed = [item for item in checks if item["status"] != "PASS"]
result = {
    "status": "PASS" if not failed else "FAIL",
    "checks": len(checks),
    "failed": len(failed),
    "checks_detail": checks,
    "scope": "field/value consistency only; no firmware or hardware action",
    "inputs": {
        str(path.relative_to(root)): {
            "size": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for path in paths
    },
}
print(json.dumps(result, indent=2))
(root / "evidence/firmware-audit/20260920-clv-native-operator-recipe-review/review-result.json").write_text(
    json.dumps(result, indent=2) + "\n"
)
raise SystemExit(0 if not failed else 1)
