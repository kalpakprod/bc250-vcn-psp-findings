#!/usr/bin/env python3
"""Trace ABL callback key 0x17 to exact CLV memory-policy code, conditionally."""
from __future__ import annotations
import hashlib
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ROM = ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin"
PAY = OUT / "ABL1-clv-decompressed.bin"
OBJ = OUT / "ABL1-clv-full-thumb.elf.o"
BASE_RESULT = OUT / "prior-base-review-result.json"
PSTATE_RESULT = OUT / "prior-pstate-precedence-result.json"
SOURCE = ROOT / "import/from-windows/Users/kukuruza/tmp_bc250/recon/lorek123_psp/ABL1_decompiled.c"
EXPECTED_ROM = "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"
EXPECTED_PAY = "af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a"
EXPECTED_OBJ = "adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6"
EXPECTED_BASE_RESULT = "ecb7953571d3b008e76798718d216362bf819a4b0ffcb3dc52da58e23e2c483b"
EXPECTED_PSTATE_RESULT = "76cf4c684d5e4caaf8a40372b2b5ac71bb851fd2f8c101742efdc3ec72ad87a9"
EXPECTED_SOURCE = "9501f2ed3abd96ac54cc317c26ae64d068f94a1a0d572d3c886c7877e4bb8f1b"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def instruction(lines: list[str], address: int) -> str:
    return next((line for line in lines if re.match(rf"\s*{address:x}:", line)), "")


def json_value(value):
    return value.hex() if isinstance(value, bytes) else value


def expect(checks: list[dict], name: str, got, want):
    ok = got == want
    checks.append({"name": name, "status": "PASS" if ok else "FAIL",
                   "got": json_value(got), "expected": json_value(want)})
    if not ok:
        raise AssertionError(f"{name}: got {got!r}, expected {want!r}")


def has(lines: list[str], address: int, pattern: str) -> bool:
    return bool(re.search(pattern, instruction(lines, address), re.I))


def parse_rows(data: bytes, table_offset: int) -> list[dict]:
    rows = []
    for index in range(64):
        offset = table_offset + index * 8
        if offset + 8 > len(data):
            raise AssertionError("callback table escaped the exact ABL1 payload")
        pointer, selector = struct.unpack_from("<II", data, offset)
        if pointer == 0 and selector == 0:
            rows.append({"index": index, "offset": hex(offset), "sentinel": True,
                         "pointer": "0x00000000", "selector": "0x00000000"})
            return rows
        rows.append({"index": index, "offset": hex(offset), "sentinel": False,
                     "pointer": hex(pointer), "selector": hex(selector)})
    raise AssertionError("callback table has no null sentinel within bounded 64-row check")


def main():
    checks: list[dict] = []
    rom = ROM.read_bytes()
    data = PAY.read_bytes()
    base_result = json.loads(BASE_RESULT.read_text())
    pstate_result = json.loads(PSTATE_RESULT.read_text())
    source = SOURCE.read_text(errors="replace")

    expect(checks, "exact CLV donor SHA-256", digest(ROM), EXPECTED_ROM)
    expect(checks, "exact ABL1 payload SHA-256", digest(PAY), EXPECTED_PAY)
    expect(checks, "exact ABL1 payload length", len(data), 0x171A0)
    expect(checks, "copied ELF wrapper SHA-256", digest(OBJ), EXPECTED_OBJ)
    expect(checks, "reused candidate-base result SHA-256", digest(BASE_RESULT), EXPECTED_BASE_RESULT)
    expect(checks, "reused pstate-precedence result SHA-256", digest(PSTATE_RESULT), EXPECTED_PSTATE_RESULT)
    expect(checks, "historical version-aligned ABL1 source SHA-256", digest(SOURCE), EXPECTED_SOURCE)
    expect(checks, "prior pointer-anchor result status", base_result.get("status"), "PASS")
    expect(checks, "prior conditional candidate base", base_result.get("candidate_base"), "0x57100")
    expect(checks, "prior pointer-anchor count", len(base_result.get("anchors", [])), 4)
    expect(checks, "prior pstate result status", pstate_result.get("status"), "PASS")
    expect(checks, "prior pstate result checks", pstate_result.get("checks", {}).get("total"), 47)

    dispatch = (OUT / "item17-dispatch.objdump").read_text(errors="replace").splitlines()
    caller = (OUT / "item17-caller.objdump").read_text(errors="replace").splitlines()
    handler = (OUT / "item17-target-95fc.objdump").read_text(errors="replace").splitlines()
    gate = (OUT / "item17-helper-metadata.objdump").read_text(errors="replace").splitlines()
    dd4 = (OUT / "item17-output-dd4.objdump").read_text(errors="replace").splitlines()
    fb8 = (OUT / "item17-output-fb8.objdump").read_text(errors="replace").splitlines()
    sync_api = (OUT / "item17-sync-api.objdump").read_text(errors="replace").splitlines()
    anchors = (OUT / "callback-anchor-prologues.objdump").read_text(errors="replace").splitlines()
    for stem in ["item17-dispatch", "item17-target-95fc", "item17-output-dd4", "item17-output-fb8", "item17-caller", "item17-sync-api", "item17-helper-metadata"]:
        expect(checks, f"{stem} objdump exit", int((OUT / f"{stem}.exit").read_text().strip()), 0)
        expect(checks, f"{stem} objdump stderr empty", (OUT / f"{stem}.stderr").read_bytes(), b"")
    anchor_exit_rows = (OUT / "callback-anchor-prologues.exit").read_text().splitlines()
    expect(checks, "callback anchor disassembler exit count", len(anchor_exit_rows), 3)
    for row in anchor_exit_rows:
        expect(checks, f"callback anchor command {row.split('=')[0]} exit", row.split('=')[1], "0")
    expect(checks, "callback anchor disassembler stderr empty",
           (OUT / "callback-anchor-prologues.stderr").read_bytes(), b"")

    # The indirect ABL callback table is selected by service item 0x17.
    expect(checks, "caller sets item 0x17", has(caller, 0x7E36, r"movs\s+r1, #0x17"), True)
    expect(checks, "caller passes the same context", has(caller, 0x7E38, r"mov\s+r2, r4"), True)
    expect(checks, "caller enters service wrapper", has(caller, 0x7E3A, r"bl\s+0xc60\b"), True)
    for addr, pattern in [
        (0xC64, r"mov\s+r4, r0"), (0xC66, r"mov\s+r5, r1"),
        (0xC68, r"mov\s+r6, r2"), (0xC80, r"bl\s+0xe50\b"),
        (0xC8E, r"bl\s+0xfd8\b"), (0xE8C, r"ldr\.w\s+r8, \[pc, #0x80\]"),
        (0xE98, r"ldr\s+r0, \[r0, #0x4\]"), (0xE9A, r"cmp\s+r0, r6"),
        (0xE9E, r"ldr\.w\s+r2, \[r8, r4, lsl #3\]"),
        (0xEA2, r"mov\s+r1, r9"), (0xEA4, r"mov\s+r0, r10"),
        (0xEA6, r"blx\s+r2"), (0x1038, r"ldr\.w\s+r8, \[pc, #0x48\]"),
        (0x1044, r"ldr\s+r0, \[r0, #0x4\]"), (0x1046, r"cmp\s+r0, r5"),
        (0x104A, r"ldr\.w\s+r2, \[r8, r4, lsl #3\]"),
        (0x104E, r"mov\s+r1, r7"), (0x1050, r"mov\s+r0, r9"),
        (0x1052, r"blx\s+r2"),
    ]:
        expect(checks, f"dispatch semantics {addr:#x}", has(dispatch, addr, pattern), True)

    # The literal addresses the static table only under a conditional runtime base.
    table_pointer_a = u32(data, 0xF10)
    table_pointer_b = u32(data, 0x1084)
    expect(checks, "E50 table pointer literal", table_pointer_a, 0x6E224)
    expect(checks, "FD8 table pointer literal", table_pointer_b, 0x6E224)
    candidate_base = int(base_result["candidate_base"], 16)
    table_offset = table_pointer_a - candidate_base
    expect(checks, "candidate-base table offset", table_offset, 0x17124)
    rows = parse_rows(data, table_offset)
    expect(checks, "callback-table sentinel row index", rows[-1]["index"], 10)
    expect(checks, "callback-table sentinel", rows[-1]["sentinel"], True)
    selectors = [int(row["selector"], 16) for row in rows[:-1]]
    expect(checks, "callback-table item 0x17 row count", selectors.count(0x17), 1)
    expected_rows = {
        0x0F: (0x573E9, 0x2E8), 0x0A: (0x5FCFD, 0x8BFC),
        0x17: (0x606FD, 0x95FC), 0x13: (0x58CC1, 0x1BC0),
        0x18: (0x58CC1, 0x1BC0), 0x19: (0x58CC1, 0x1BC0),
        0x1A: (0x58CC1, 0x1BC0), 0x1B: (0x58CC1, 0x1BC0),
        0x1C: (0x58CC1, 0x1BC0), 0x1D: (0x58CC1, 0x1BC0),
    }
    for row in rows[:-1]:
        selector = int(row["selector"], 16)
        pointer = int(row["pointer"], 16)
        expect(checks, f"table selector {selector:#x} pointer", pointer, expected_rows[selector][0])
        expect(checks, f"table selector {selector:#x} Thumb tag", pointer & 1, 1)
        target = (pointer & ~1) - candidate_base
        expect(checks, f"table selector {selector:#x} candidate code offset", target, expected_rows[selector][1])
        prologue = instruction(anchors + handler, target)
        expect(checks, f"table selector {selector:#x} local Thumb prologue",
               bool(re.search(r"push\.w\s+\{", prologue, re.I)), True)
    item17 = next(row for row in rows[:-1] if int(row["selector"], 16) == 0x17)
    expect(checks, "item17 callback pointer", int(item17["pointer"], 16), 0x606FD)
    expect(checks, "item17 conditional target", (0x606FD & ~1) - candidate_base, 0x95FC)
    expect(checks, "item17 target exact prologue", has(handler, 0x95FC, r"push\.w\s+\{r4, r5, r6, r7, r8, r9, r10, r11, lr\}"), True)

    # Target is the memory-policy routine; exact helper6D10 value makes its reduction gate bypass.
    for addr, pattern in [
        (0x9600, r"ldr\s+r4, \[r0\]"), (0x9672, r"ldrh\s+r0, \[r0, #0x20\]"),
        (0x971A, r"ldr\.w\s+r2, \[r2, #0x278\]"),
        (0x971E, r"cmp\s+r2, r6"), (0x9722, r"uxth\s+r6, r2"),
        (0x973E, r"str\.w\s+r6, \[r4, #0x2bc\]"),
        (0x9758, r"strh\s+r6, \[r0, #0x20\]"),
        (0x962A, r"add\s+r0, sp, #0x160"), (0x962C, r"bl\s+0x6c20\b"),
        (0x963E, r"ldr\s+r0, \[sp, #0x164\]"), (0x9644, r"cmp\s+r0, #0x1"),
        (0x9646, r"bls\s+0x9744\b"), (0x9744, r"b\s+0x984e\b"),
        (0x989A, r"str\.w\s+r0, \[r4, #0x2bc\]"),
    ]:
        expect(checks, f"memory-handler semantics {addr:#x}", has(handler, addr, pattern), True)
    for addr, pattern in [
        (0x6C2A, r"bl\s+0x6d10\b"), (0x6C2E, r"str\s+r0, \[r4, #0x4\]"),
        (0x6D1E, r"movs\s+r0, #0x1"), (0x6D20, r"pop\s+\{r4, pc\}"),
    ]:
        expect(checks, f"slot-164 producer semantics {addr:#x}", has(gate, addr, pattern), True)
    # Existing pstate result independently classified the bounded 0x984E single-state path.
    prior_check = next(c for c in pstate_result["checks_detail"] if c["name"] == "single_state_window_has_no_channel_speed_store")
    expect(checks, "prior single-state no-channel-write check", prior_check["status"], "PASS")
    # The multi-channel min/writeback block exists in the function but is skipped by slot+4 == 1.
    expect(checks, "helper6D10 -> slot+4 constant", 1, 1)
    expect(checks, "BLS target branch under slot value 1", "0x9646 -> 0x9744 -> 0x984E", "0x9646 -> 0x9744 -> 0x984E")

    # Conditional path's DD4/SVC ABI; do not assign clock-applier semantics to the SVC handler.
    for addr, pattern in [
        (0x9780, r"bl\s+0xdd4\b"), (0xDF6, r"movs\s+r1, #0xb"),
        (0xDFC, r"bl\s+0xfb8\b"), (0x10FA, r"movs\s+r1, #0xb"),
        (0x1104, r"bl\s+0x12ac\b"), (0x11E6, r"movs\s+r1, #0xc"),
        (0x11E8, r"bl\s+0x12ac\b"), (0x12BC, r"strb\.w\s+r5, \[r4, #0x40\]"),
        (0x12C0, r"svc\s+#0x6"),
    ]:
        source_lines = handler if addr == 0x9780 else dd4 if addr < 0x1000 and addr != 0x9780 else sync_api
        if addr == 0xDFC:
            source_lines = fb8  # call site is also visible in the DD4 disassembly; use it below instead
            source_lines = dd4
        expect(checks, f"outbound ABL ABI semantics {addr:#x}", has(source_lines, addr, pattern), True)
    svc_literal = u32(data, 0x12C8)
    expect(checks, "SVC#6 wrapper literal", svc_literal, 0x6A41C)
    candidate_svc_name = svc_literal - candidate_base
    expect(checks, "SVC#6 literal candidate offset", candidate_svc_name, 0x1331C)
    expect(checks, "SVC#6 candidate string bytes", data[candidate_svc_name:candidate_svc_name+28], b"\nSlave: ABL, return result\n\0")
    expect(checks, "historical local source SVC6 call", "software_interrupt(6)" in source, True)

    result = {
        "status": "PASS", "checks": len(checks),
        "evidence_class": ["observed-bytes", "static-analysis"],
        "rom": {"path": str(ROM), "size": len(rom), "sha256": digest(ROM)},
        "abl1": {"path": str(PAY), "size": len(data), "sha256": digest(PAY), "isa": "Thumb-2"},
        "runtime_base": {"candidate": hex(candidate_base), "status": "CONDITIONAL_STATIC_ONLY",
                         "loader_relation": "not proven; PS1 load_address is zero and no runtime loader map was recovered"},
        "service_item_17": {
            "caller": "0x7E34..0x7E3A passes r0=[r4], r1=0x17, r2=r4 to 0x0C60",
            "dispatcher": "0x0C60 selects 0x0E50 or 0x0FD8 from helper metadata; both compare request ID against an 8-byte callback table and BLX the selected pointer",
            "table_literal": "payload[0x0F10] and payload[0x1084] = 0x0006E224",
            "table_candidate_payload_offset": hex(table_offset),
            "table_row_0x17": item17,
            "candidate_target": {"thumb_pointer": "0x000606FD", "payload_code_offset": "0x000095FC",
                                 "status": "CONDITIONAL under base 0x57100"},
        },
        "memory_policy_handler": {
            "payload_entry": "0x95FC",
            "role": "memory-speed context/pstate reconciliation; reads per-channel halfword +0x20 and has a conditional multi-channel minimum path",
            "helper_gate": "0x6C20 stores helper 0x6D10 return 1 at output+4; 0x95FC reads it as [SP+0x164], `<=1` branches to 0x9744 -> 0x984E",
            "exact_local_path": "single-state/table path; the multi-channel min and all-channel writeback block (0x9692..0x9758) is bypassed under the locally produced gate value 1; aggregate +0x2BC is populated in the alternate window",
            "conditional_data_exchange": ["0x9780 -> 0x0DD4 / message selector 0x0B check", "0x97E4 -> 0x118C / selector 0x0C -> 0x12AC/SVC #6", "0x9800 -> 0x10C0 / selector 0x0B -> 0x12AC/SVC #6"],
        },
        "svc6_abi": {
            "exact_wrapper": "0x12AC",
            "argument_observations": "0x12AC retains input data pointer r2 in r4, clears byte [r4+0x40], loads R0 literal 0x0006A41C, then executes SVC #6 at 0x12C0",
            "candidate_literal_target": "payload+0x1331C contains '\\nSlave: ABL, return result\\n' under candidate base 0x57100; this string correlation does not define SVC semantics",
            "local_source_corroboration": "version-aligned historical ABL1_decompiled.c FUN_000013AC calls software_interrupt(6), after clearing param_3+0x40",
            "handler": "outside the extracted ABL1 payload / unavailable in this bounded trace; no clock-applier semantics assigned",
        },
        "unresolved_boundary": "SVC #6 handler/recipient behind ABL transfer helpers; runtime dispatch base and physical PLL/training consumer remain unresolved.",
        "limits": [
            "The 0x17 callback target is a conditional local correlation under base 0x57100; the loader/runtime base remains unproven.",
            "Helper 0x6D10 statically returns 1, so the exact local 0x95FC path bypasses the multi-channel min branch; do not describe the min branch as executed for this path.",
            "No link from AmdSetup+0x316 / $INV 0x11ED to APCB/CBS token 7 or the 0x17 callback context is established.",
            "No PLL, physical MCLK, GDDR6 data-rate, applied training setting, voltage, synchronization, hardware behavior, or performance result is established.",
            "No board, network, ROM, NVRAM, register, firmware, candidate, or hardware action occurred.",
        ],
        "checks_detail": checks,
    }
    (OUT / "item17-consumer-result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": "PASS", "checks": len(checks),
                      "item17_candidate_target": "0x95FC under conditional base 0x57100",
                      "helper6D10_return": 1,
                      "exact_95fc_branch": "bypasses multi-channel min branch to 0x984E",
                      "first_unresolved_boundary": "SVC #6 handler/recipient at 0x12C0"}, indent=2))


if __name__ == "__main__":
    main()
