#!/usr/bin/env python3
"""Offline source/ROM discriminator for the ATOM SMU-clock-info candidate.

This script reads only the pinned CLV ROM and retained source files. It never
opens sysfs, connects to hardware/network, writes registers, or invokes the
project's workstation/board clock probe. Its JSON output is a result record.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ROM = ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin"
DRIVER = ROOT / "import/from-windows/Users/kukuruza/tmp_bc250/recon/smu_v11_0.c"
OUT = Path(__file__).resolve().parent / "clock-observability-source-result.json"
EXPECTED_ROM = "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"
EXPECTED_DRIVER = "3d4a62199f4b2dfea021b9c36f473fb161f10bd3aed89bcdc99f0d5eb2a5ccb1"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

rom = ROM.read_bytes()
driver = DRIVER.read_text(encoding="utf-8", errors="replace")
checks: list[dict[str, object]] = []

def check(name: str, ok: bool, observed: object, expected: object) -> None:
    checks.append({"name": name, "status": "PASS" if ok else "FAIL",
                   "observed": observed, "expected": expected})

rom_sha = sha(rom)
driver_sha = sha(DRIVER.read_bytes())
check("clv-size", len(rom) == 0x1000000, len(rom), 0x1000000)
check("clv-pinned-sha256", rom_sha == EXPECTED_ROM, rom_sha, EXPECTED_ROM)
check("retained-driver-source-sha256", driver_sha == EXPECTED_DRIVER,
      driver_sha, EXPECTED_DRIVER)

# Preserve/check the exact donor's request byte. 0x4CF + 0x316 = 0x7E5.
request_byte = rom[0x7E5]
check("native-memory-request-byte", request_byte == 0x24,
      {"offset": "0x7E5", "value": f"0x{request_byte:02X}"},
      {"offset": "0x7E5", "value": "0x24", "exact-CLV-IFR-label": "1800MHz"})

# Direct source slice: the helper passes a clock ID/syspll ID to an ATOM BIOS
# command interpreter and converts the command's output field from Hz/10000.
helper_start = driver.index("static int smu_v11_0_atom_get_smu_clockinfo(")
helper_end = driver.index("\nint smu_v11_0_get_vbios_bootup_values(", helper_start)
helper = driver[helper_start:helper_end]
boot_start = helper_end + 1
after_boot = driver.find("\nint ", boot_start)
boot_fn = driver[boot_start:after_boot if after_boot >= 0 else len(driver)]
check("helper-inputs-clock-and-syspll-identifiers",
      "input.clk_id = clk_id;" in helper and "input.syspll_id = syspll_id;" in helper,
      [line.strip() for line in helper.splitlines() if "input.clk_id" in line or "input.syspll_id" in line],
      ["input.clk_id = clk_id;", "input.syspll_id = syspll_id;"])
check("helper-selects-atom-clock-frequency-command",
      "GET_SMU_CLOCK_INFO_V3_1_GET_CLOCK_FREQ" in helper and "getsmuclockinfo" in helper,
      ["GET_SMU_CLOCK_INFO_V3_1_GET_CLOCK_FREQ" in helper, "getsmuclockinfo" in helper],
      [True, True])
check("helper-runs-atom-table-not-direct-register-read",
      "amdgpu_atom_execute_table(" in helper and "RREG32" not in helper and "WREG32" not in helper and "SMN" not in helper,
      {"atom_execute_table": "amdgpu_atom_execute_table(" in helper,
       "direct_RREG32": "RREG32" in helper, "direct_WREG32": "WREG32" in helper,
       "direct_SMN": "SMN" in helper},
      {"atom_execute_table": True, "direct_RREG32": False,
       "direct_WREG32": False, "direct_SMN": False})
check("helper-returns-atom-output-frequency-hz-div-10000",
      "atom_smu_outputclkfreq.smu_clock_freq_hz" in helper and "/ 10000" in helper,
      [line.strip() for line in helper.splitlines() if "smu_clock_freq_hz" in line],
      "le32_to_cpu(output...smu_clock_freq_hz) / 10000")
check("mclk-uclk-seed-is-firmwareinfo-bootup-mclk",
      "smu->smu_table.boot_values.uclk = v_3_3->bootup_mclk_in10khz;" in boot_fn and
      "smu->smu_table.boot_values.uclk = v_3_1->bootup_mclk_in10khz;" in boot_fn,
      {"v3_1": "v_3_1->bootup_mclk_in10khz" in boot_fn,
       "v3_3": "v_3_3->bootup_mclk_in10khz" in boot_fn},
      {"v3_1": True, "v3_3": True})
check("fclk-atom-result-stored-as-boot-value",
      "SMU11_SYSPLL1_0_FCLK_ID" in boot_fn and
      "SMU11_SYSPLL1_2_ID" in boot_fn and
      "&smu->smu_table.boot_values.fclk" in boot_fn and
      "boot_values.format_revision == 3" in boot_fn and
      "boot_values.content_revision >= 2" in boot_fn,
      {"syspll_fclk_id": "SMU11_SYSPLL1_0_FCLK_ID" in boot_fn,
       "output_destination": "&smu->smu_table.boot_values.fclk" in boot_fn,
       "revision_guard": "boot_values.format_revision == 3" in boot_fn and "boot_values.content_revision >= 2" in boot_fn},
      {"syspll_fclk_id": True, "output_destination": True, "revision_guard": True})
check("path-does-not-claim-live-counter-in-driver-body",
      "boot_values" in helper + boot_fn and "RLC_CLK_COUNT_" not in helper + boot_fn,
      {"boot_values_context": "boot_values" in helper + boot_fn,
       "RLC_counter_symbol": "RLC_CLK_COUNT_" in helper + boot_fn},
      {"boot_values_context": True, "RLC_counter_symbol": False})

# Parse standard 55AA / +0x48 -> ATOM headers. This is an offline ROM check,
# not a broad search for the text token ATOM.
atom_headers: list[dict[str, str]] = []
pos = 0
while True:
    pos = rom.find(b"\x55\xAA", pos)
    if pos < 0:
        break
    if pos + 0x4A <= len(rom):
        ptr = int.from_bytes(rom[pos + 0x48:pos + 0x4A], "little")
        if ptr and pos + ptr + 4 <= len(rom) and rom[pos + ptr:pos + ptr + 4] == b"ATOM":
            atom_headers.append({"rom_offset": f"0x{pos:X}", "atom_header": f"0x{pos + ptr:X}"})
    pos += 1
check("exact-clv-has-no-55aa-atombios-rom-header", len(atom_headers) == 0,
      atom_headers, [])

passed = sum(c["status"] == "PASS" for c in checks)
failed = len(checks) - passed
result = {
    "status": "PASS" if failed == 0 else "FAIL",
    "evidence_class": ["observed-bytes", "static-analysis"],
    "scope": "offline-only; no board, network, sysfs, register write, firmware write, or probe invocation",
    "inputs": {
        "rom": str(ROM), "rom_size": len(rom), "rom_sha256": rom_sha,
        "driver_source": str(DRIVER), "driver_source_sha256": driver_sha,
    },
    "request_preservation": {
        "absolute_offset": "0x7E5", "AmdSetup_relative_offset": "+0x316",
        "value": f"0x{request_byte:02X}", "ifr_label": "1800MHz",
        "meaning": "stored request only; not a measured frequency",
    },
    "candidate_path": {
        "driver_helper": "smu_v11_0_atom_get_smu_clockinfo",
        "command_surface": "ATOM GET_SMU_CLOCK_INFO v3.1 / GET_CLOCK_FREQ",
        "fclk_destination": "smu_table.boot_values.fclk (revision-gated)",
        "mclk_uclk_source": "ATOM firmware-info bootup_mclk_in10khz -> smu_table.boot_values.uclk",
        "output_field": "atom_smu_outputclkfreq.smu_clock_freq_hz / 10000",
        "classification": "API-reported boot/PLL frequency candidate; not proven physical counter, current live frequency, or exact-CLV path",
        "reason_not_accepted": [
            "retained helper delegates semantics to an ATOM command table; this check found no standard 55AA/+0x48 ATOM VBIOS header in exact CLV, and the table instructions/live-PLL semantics are not recovered",
            "exact CLV contains no standard 55AA/+0x48 ATOM VBIOS header, so this generic ATOM path is not bound to this firmware",
            "driver source is an imported source file pinned by hash, not a revision-identified or installed BC-250 driver build",
            "no exact-CLV MCLK/UCLK independent counters, PLL/divider fields, common reference, units, or sync/crossing status are established here",
        ],
    },
    "future_hardware_acceptance_procedure": None,
    "stop_reason": "No semantically defensible exact-board, read-only physical MCLK/UCLK/FCLK counter-or-divider path was found; do not fabricate a probe or treat model/boot clock values as physical readback.",
    "checks": {"passed": passed, "failed": failed, "total": len(checks)},
    "checks_detail": checks,
}
OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"status": result["status"], "checks": result["checks"],
                  "request": result["request_preservation"],
                  "candidate_path": result["candidate_path"]["classification"],
                  "atom_vbios_headers": atom_headers,
                  "output": str(OUT.resolve())}, sort_keys=True))
raise SystemExit(0 if failed == 0 else 1)
