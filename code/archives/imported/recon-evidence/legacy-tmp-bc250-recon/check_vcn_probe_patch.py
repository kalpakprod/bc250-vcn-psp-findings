#!/usr/bin/env python3
"""Mechanical source verifier for the BC-250 VCN probe patch."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import NoReturn

SUCCESS = "VCN_PROBE_PATCH_PASS files=7 helper_calls=7"


def fail(message: str) -> NoReturn:
    raise SystemExit(f"VCN_PROBE_PATCH_FAIL: {message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def source(root: Path, name: str) -> str:
    paths = list(root.rglob(name))
    require(len(paths) == 1, f"expected one {name}, found {len(paths)}")
    try:
        return paths[0].read_text(encoding="utf-8")
    except OSError as error:
        fail(f"cannot read {paths[0]}: {error}")


def source_at(root: Path, relative: str) -> str:
    path = root / relative
    require(path.is_file(), f"missing expected source file: {relative}")
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        fail(f"cannot read {path}: {error}")


def count(pattern: str, text: str) -> int:
    return len(re.findall(pattern, text, re.MULTILINE | re.DOTALL))


def function_body(text: str, name: str) -> str:
    match = re.search(rf"\b{name}\s*\([^;{{]*\)\s*\{{", text)
    require(match is not None, f"missing definition {name}")
    start = match.end()
    depth = 1
    for index in range(start, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if not depth:
                return text[start:index]
    fail(f"unterminated definition {name}")


def initializer_body(text: str, symbol: str) -> str:
    match = re.search(rf"\b{symbol}\s*=\s*\{{", text)
    require(match is not None, f"missing initializer {symbol}")
    start = match.end()
    depth = 1
    for index in range(start, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if not depth:
                return text[start:index]
    fail(f"unterminated initializer {symbol}")


def check_mode(drv: str, header: str) -> None:
    for symbol in ("AMDGPU_BC250_VCN_MODE_OFF", "AMDGPU_BC250_VCN_MODE_PROBE", "AMDGPU_BC250_VCN_MODE_HARDWARE"):
        require(re.search(rf"\b{symbol}\b", header) is not None, f"missing mode constant {symbol} in amdgpu.h")
    require(re.search(r"\bextern\s+int\s+amdgpu_bc250_vcn_mode\s*;", header) is not None,
            "amdgpu_bc250_vcn_mode is not exported by amdgpu.h")
    require(re.search(r"^\s*int\s+amdgpu_bc250_vcn_mode\s*(?:=|;)", drv, re.MULTILINE) is not None,
            "amdgpu_drv.c does not define amdgpu_bc250_vcn_mode")
    parameter = re.search(r"module_param(?:_named)?\s*\([^;]*amdgpu_bc250_vcn_mode[^;]*;", drv, re.DOTALL)
    require(parameter is not None, "missing amdgpu_bc250_vcn_mode module parameter")
    require(re.search(r"\b0(?:444|400)\b", parameter.group(0)) is not None,
            "amdgpu_bc250_vcn_mode parameter is not read-only")
    require(re.search(r"\bamdgpu_bc250_vcn\b", drv) is None, "obsolete standalone amdgpu_bc250_vcn remains")
    require(re.search(r"(?<!_)\bbc250_vcn\b(?!_mode)", drv) is None, "obsolete bare bc250_vcn remains")


def check_helper(vcn: str, header: str) -> None:
    declaration = count(r"\bamdgpu_vcn_fw_is_psp\s*\(", header)
    occurrences = count(r"\bamdgpu_vcn_fw_is_psp\s*\(", vcn)
    require(declaration == 1, "amdgpu_vcn_fw_is_psp must have one declaration")
    require(occurrences == 5, "amdgpu_vcn_fw_is_psp must have one definition and four call sites")
    body = function_body(vcn, "amdgpu_vcn_fw_is_psp")
    require("AMD_APU_IS_CYAN_SKILLFISH2" in body, "helper does not check Cyan Skillfish2 identity")
    require("0x13fe" in body, "helper does not check BC-250 device ID")
    require(re.search(r"\bIP_VERSION\s*\(\s*2\s*,\s*0\s*,\s*3\s*\)", body) is not None,
            "helper does not check VCN IP version 2.0.3")
    require("AMDGPU_BC250_VCN_MODE_PROBE" in body and "AMDGPU_BC250_VCN_MODE_HARDWARE" in body, "helper does not check probe and hardware modes")
    require(re.search(r"return\s+adev->firmware\.load_type\s*==\s*AMDGPU_FW_LOAD_PSP", body) is not None, "helper does not fall back to global PSP")
    require(re.search(r"firmware\.load_type\s*=(?!=)", body) is None, "helper assigns global firmware load_type")


def check_vcn_calls(vcn: str) -> None:
    calls = count(r"\bamdgpu_vcn_fw_is_psp\s*\(", vcn) - 1
    require(calls == 4, f"amdgpu_vcn.c needs four helper call sites, found {calls}")
    require(re.search(r"if\s*\(\s*!\s*amdgpu_vcn_fw_is_psp\s*\([^)]*\)\s*\).*?(?:bo_size|fw_size|alloc_size)", vcn, re.DOTALL) is not None, "BO size is not guarded by negated helper")
    require(re.search(r"if\s*\(\s*!\s*amdgpu_vcn_fw_is_psp\s*\([^)]*\)\s*\).*?(?:memcpy|cpu_addr|fw->data)", vcn, re.DOTALL) is not None, "resume copy is not guarded by negated helper")
    require(re.search(r"if\s*\(\s*amdgpu_vcn_fw_is_psp\s*\([^)]*\)\s*(?:&&\s*[^\n]+)?\)\s*\{?.*?(?:setup|amdgpu_vcn_setup)", vcn, re.DOTALL) is not None, "firmware setup is not guarded by positive helper")
    require(re.search(r"if\s*\(\s*amdgpu_vcn_fw_is_psp\s*\([^)]*\)\s*\).*?(?:sram|indirect)", vcn, re.DOTALL | re.IGNORECASE) is not None, "indirect SRAM path is not guarded by positive helper")


def check_v2(v2: str, header: str) -> None:
    calls = count(r"\bamdgpu_vcn_fw_is_psp\s*\(", v2)
    require(calls == 3, f"vcn_v2_0.c needs three helper call sites, found {calls}")
    require(re.search(r"firmware\.load_type\s*==\s*AMDGPU_FW_LOAD_PSP", v2) is None,
            "vcn_v2_0.c retains a direct PSP comparison")

    probe_early = function_body(v2, "vcn_v2_0_probe_early_init")
    require(re.search(r"num_enc_rings\s*=\s*0", probe_early) is not None,
            "probe early init does not disable encode rings")
    for forbidden in ("vcn_v2_0_set_dec_ring_funcs", "vcn_v2_0_set_enc_ring_funcs", "vcn_v2_0_set_irq_funcs"):
        require(forbidden not in probe_early, f"probe early init contains forbidden {forbidden}")

    probe_sw_init = function_body(v2, "vcn_v2_0_probe_sw_init")
    for required in ("amdgpu_vcn_sw_init", "amdgpu_vcn_setup_ucode", "amdgpu_vcn_resume"):
        require(required in probe_sw_init, f"probe sw init does not call {required}")
    for forbidden in ("amdgpu_irq_add_id", "amdgpu_ring_init", "vcn_doorbell_range", "RREG", "WREG", "ring_test", "vcn_v2_0_start"):
        require(forbidden not in probe_sw_init, f"probe sw init contains forbidden {forbidden}")

    probe_init = function_body(v2, "vcn_v2_0_probe_hw_init")
    for forbidden in ("sched.ready", "RREG", "WREG", "vcn_doorbell_range", "ring_test", "vcn_v2_0_start"):
        require(forbidden not in probe_init, f"probe hw init contains forbidden {forbidden}")

    funcs = initializer_body(v2, "vcn_v2_0_probe_ip_funcs")
    for forbidden in (
        "vcn_v2_0_sw_init", "vcn_v2_0_sw_fini", "vcn_v2_0_hw_init", "vcn_v2_0_hw_fini",
        "vcn_v2_0_suspend", "vcn_v2_0_resume", "vcn_v2_0_is_idle", "vcn_v2_0_wait_for_idle",
        "vcn_v2_0_dump_ip_state", "vcn_v2_0_set_clockgating_state", "vcn_v2_0_set_powergating_state",
    ):
        require(re.search(rf"=\s*{forbidden}\b", funcs) is None,
                f"probe funcs retains normal callback {forbidden}")
    for field, callback in (
        ("sw_init", r"vcn_v2_0_probe_sw_init"),
        ("sw_fini", r"vcn_v2_0_probe_sw_fini"),
        ("hw_init", r"vcn_v2_0_probe_hw_init"),
        ("is_idle", r"vcn_v2_0_probe_is_idle"),
        ("set_clockgating_state", r"vcn_v2_0_probe_set_clockgating_state"),
        ("set_powergating_state", r"vcn_v2_0_probe_set_powergating_state"),
    ):
        require(re.search(rf"\.{field}\s*=\s*{callback}\b", funcs) is not None,
                f"probe funcs does not assign {field} to its probe callback")
    require(re.search(r"=\s*(?:amdgpu_ip_block_noop|vcn_v2_0_probe_noop)\b", funcs) is not None,
            "probe funcs does not use a no-op callback")
    require(count(r"\b(?:const\s+)?struct\s+amdgpu_ip_block_version\s+vcn_v2_0_probe_ip_block\s*=", v2) == 1,
            "vcn_v2_0.c must define one vcn_v2_0_probe_ip_block")
    require(count(r"\bextern\s+(?:const\s+)?struct\s+amdgpu_ip_block_version\s+vcn_v2_0_probe_ip_block\s*;", header) == 1,
            "vcn_v2_0.h must declare one extern vcn_v2_0_probe_ip_block")


def braced_region(text: str, start: int, label: str) -> tuple[str, int]:
    opening = text.find("{", start)
    require(opening >= 0, f"missing opening brace for {label}")
    depth = 1
    for index in range(opening + 1, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if not depth:
                return text[opening + 1:index], index + 1
    fail(f"unterminated {label}")


def check_discovery(discovery: str) -> None:
    probe_match = re.search(
        r"\bif\s*\(\s*mode\s*==\s*AMDGPU_BC250_VCN_MODE_PROBE\s*\)",
        discovery,
    )
    require(probe_match is not None, "discovery lacks a BC-250 probe-mode branch")
    probe, after_probe = braced_region(discovery, probe_match.end(), "probe-mode branch")
    require("vcn_v2_0_probe_ip_block" in probe, "probe mode does not register probe IP block")
    require("jpeg_v2_0_ip_block" not in probe, "probe mode registers JPEG")

    hardware_match = re.match(
        r"\s*else\s+if\s*\(\s*mode\s*==\s*AMDGPU_BC250_VCN_MODE_HARDWARE\s*\)",
        discovery[after_probe:],
    )
    require(hardware_match is not None, "probe-mode branch is not followed by a hardware-mode branch")
    hardware, _ = braced_region(
        discovery,
        after_probe + hardware_match.end(),
        "hardware-mode branch",
    )
    require("vcn_v2_0_ip_block" in hardware and "jpeg_v2_0_ip_block" in hardware,
            "hardware mode does not register normal VCN and JPEG")


def main(argv: list[str]) -> None:
    require(len(argv) == 2, "usage: check_vcn_probe_patch.py PATH_TO_AMDGPU_DIR")
    root = Path(argv[1])
    require(root.is_dir(), f"not a directory: {root}")
    drv = source_at(root, "amdgpu_drv.c")
    amdgpu_header = source_at(root, "amdgpu.h")
    vcn = source_at(root, "amdgpu_vcn.c")
    vcn_header = source_at(root, "amdgpu_vcn.h")
    discovery = source_at(root, "amdgpu_discovery.c")
    v2 = source_at(root, "vcn_v2_0.c")
    v2_header = source_at(root, "vcn_v2_0.h")
    check_mode(drv, amdgpu_header)
    check_helper(vcn, vcn_header)
    check_vcn_calls(vcn)
    check_v2(v2, v2_header)
    check_discovery(discovery)
    print(SUCCESS)


if __name__ == "__main__":
    main(sys.argv)
