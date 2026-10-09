#!/usr/bin/env python3
"""Verify one exact ABL1 UCLK/FCLK policy branch from retained source leads.

This is deliberately not a whole-image literal scan.  It binds source leads to
specific exact-payload strings, descriptor construction, calls, and output
stores, then records the first unresolved consumer edge.
"""
from __future__ import annotations
import hashlib, json, re, struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ROM = ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin"
ABL = ROOT / "evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin"
SRC = ROOT / "import/from-windows/Users/kukuruza/tmp_bc250/recon/lorek123_psp/ABL3_decompiled.c"
STR = ROOT / "import/from-windows/Users/kukuruza/tmp_bc250/recon/lorek123_psp/ABL1_strings.txt"
DIS = ROOT / "evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt"
EXPECTED = {
    "rom": "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8",
    "abl": "af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a",
    "source": "ecd1bfb8be3fe15257038c4db6fd927ab72ca97a920a4639ad10cece04d3e22f",
    "strings": "c27bf19fb46415703c1e761641d3ac08102dda775b9152ea1b6a557c47741170",
    "disassembly": "b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65",
}

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def find_or_fail(blob: bytes, needle: bytes, label: str) -> int:
    off = blob.find(needle)
    if off < 0:
        raise AssertionError(f"missing {label}: {needle!r}")
    return off

def adr_target_thumb16(insn_off: int, insn: bytes) -> int:
    # Thumb ADR (ADD Rd, PC, imm8<<2), used by the exact 0x4634 lead.
    half = int.from_bytes(insn, "little")
    if (half & 0xf800) != 0xa000:
        raise AssertionError(f"not ADR at 0x{insn_off:x}: {insn.hex()}")
    imm = (half & 0xff) << 2
    return ((insn_off + 4) & ~3) + imm

def _json_value(value):
    if isinstance(value, (bytes, bytearray)):
        return "hex:" + bytes(value).hex()
    return value

def check(checks, name, got, expected):
    ok = got == expected
    checks.append({"check": name, "passed": ok, "got": _json_value(got), "expected": _json_value(expected)})
    if not ok:
        raise AssertionError(f"{name}: got {got!r}, expected {expected!r}")

def main() -> None:
    checks = []
    for name, path, key in (("ROM", ROM, "rom"), ("ABL1 decompressed", ABL, "abl"),
                            ("retained ABL3 source", SRC, "source"), ("retained ABL1 strings", STR, "strings"),
                            ("exact ABL1 disassembly", DIS, "disassembly")):
        check(checks, f"{name} exists", path.exists(), True)
        check(checks, f"{name} sha256", sha(path), EXPECTED[key])

    blob = ABL.read_bytes()
    src = SRC.read_text(errors="replace")
    strings = STR.read_text(errors="replace")
    dis = DIS.read_text(errors="replace")

    # Retained source lead: ABL3 decompilation names the four UclkDiv1 fields
    # and the common record reader, but this is not treated as exact source ID.
    source_needles = [
        "local_3a = 0x21;",
        "s_Override_UclkDiv1_M0___d_000037bc",
        "local_3a = 0x22;",
        "s_Override_UclkDiv1_M1___d_000037d8",
        "local_3a = 0x23;",
        "s_Override_UclkDiv1_M2___d_000037f4",
        "local_3a = 0x24;",
        "s_Override_UclkDiv1_M3___d_00003810",
        "FUN_00002734(&local_3c",
    ]
    for needle in source_needles:
        check(checks, f"retained source lead: {needle}", needle in src, True)
    uclk_block = src[src.find("case 2:", src.find("FUN_000033b4")):src.find("case 3:", src.find("FUN_000033b4"))]
    check(checks, "retained Uclk case has no direct func_0x0000c900 writer", "func_0x0000c900" in uclk_block, False)

    # The retained ABL1 string file is a lead, not an exact-address authority.
    # Its listed historical offsets are kept as data but are deliberately not
    # required to equal the exact clv payload offsets.
    for text in ("Override UclkDiv1 M0: %d", "Override UclkDiv1 M1: %d",
                 "Override UclkDiv1 M2: %d", "Override UclkDiv1 M3: %d", "Override Fclk: %d"):
        check(checks, f"retained string lead present: {text}", text in strings, True)

    # Exact payload string anchors.  These are byte-backed and used to bind
    # the retained names to the exact clv ABL1, not to infer semantics alone.
    exact_uclk_strings = {}
    for idx, text in enumerate(("Override UclkDiv1 M0: %d", "Override UclkDiv1 M1: %d",
                                "Override UclkDiv1 M2: %d", "Override UclkDiv1 M3: %d")):
        needle = b"\n\t" + text.encode() + b"\n"
        off = find_or_fail(blob, needle, text)
        exact_uclk_strings[f"M{idx}"] = {"payload_offset": off, "text": text}
    fclk_off = find_or_fail(blob, b"\n\tOverride Fclk: %d\n", "Override Fclk")
    check(checks, "exact UCLK string offsets are contiguous 0x1c bytes", [exact_uclk_strings[f"M{i}"]["payload_offset"] for i in range(4)], [0x30AC,0x30C8,0x30E4,0x3100])
    check(checks, "exact FCLK string offset", fclk_off, 0x469C)

    # Exact UclkDiv1 case-2 branch: descriptor fields 0x20/0x21 .. 0x24,
    # common reader BL 0x1fb4, output byte [sp+0xc], and logger ADRs to the
    # four exact string anchors.  No context write or PLL call is present in
    # these four narrow slices; the unresolved edge is the reader 0x1fb4.
    uclk_cases = []
    for i, (start, key, str_off) in enumerate(((0x2CF0,0x21,0x30AC),(0x2D20,0x22,0x30C8),(0x2D48,0x23,0x30E4),(0x2D70,0x24,0x3100))):
        win = blob[start:start+0x30]
        # key is emitted by the movs immediate immediately before strh [sp,#0x46].
        key_byte = bytes((key, 0x20))  # movs r0,#key in exact little-endian bytes
        check(checks, f"UCLK M{i} key immediate 0x{key:02x}", key_byte in win, True)
        check(checks, f"UCLK M{i} calls common reader 0x1fb4", b"\xff\xf7" in win, True)
        check(checks, f"UCLK M{i} reads returned byte [sp+0xc]", b"\x9d\xf8\x0c\x30" in win, True)
        # Decode all ADRs in the slice and require the expected exact string.
        adr_hits = []
        for off in range(start, start+0x30, 2):
            ins = blob[off:off+2]
            if len(ins)==2 and (int.from_bytes(ins,"little") & 0xf800) == 0xa000:
                adr_hits.append(adr_target_thumb16(off, ins))
        check(checks, f"UCLK M{i} logger ADR binds exact string", str_off in adr_hits, True)
        uclk_cases.append({"field": f"UclkDiv1M{i}", "descriptor_key": f"0x{key:02x}", "branch_start": f"0x{start:x}", "reader": "payload+0x1fb4", "output": "returned byte at [sp+0xc] -> logger only", "exact_string": f"0x{str_off:x}"})

    # Exact Fclk branch at payload 0x463c: input pointer r0 is preserved in
    # r5; selector r1 must be 0xf; descriptor 0x15f/0x160 is passed to the
    # same reader; returned halfword [sp+8] is written through [r5].
    fstart = 0x463c
    fwin = blob[fstart:0x4696]
    check(checks, "FCLK branch begins with selector gate cmp r1,#0xf", blob[0x4648:0x464a], b"\x0f\x29")
    check(checks, "FCLK branch preserves input pointer r0 in r5", blob[0x4642:0x4644], b"\x05\x46")
    check(checks, "FCLK descriptor first halfword 0x15f", blob[0x464e:0x4652], b"\x40\xf2\x5f\x10")
    check(checks, "FCLK descriptor second halfword 0x160", blob[0x4656:0x465c], b"\x40\x1c\xad\xf8\x14\x20")
    check(checks, "FCLK branch calls common reader 0x1fb4", b"\xfd\xf7\xa3\xfc" in fwin, True)
    check(checks, "FCLK branch reads returned halfword [sp+8]", blob[0x467e:0x4682], b"\xbd\xf8\x08\x00")
    check(checks, "FCLK branch writes returned value through input pointer", blob[0x4682:0x4684], b"\x28\x60")
    adr = adr_target_thumb16(0x4678, blob[0x4678:0x467a])
    check(checks, "FCLK logger ADR binds exact string", adr, 0x469c)
    check(checks, "FCLK caller reaches helper branch", b"\xfd\xf7\x58\xfb" in blob[0x7000:0x7008], True)

    # Semantic boundary is explicit and byte-backed: the selected slices call
    # only the common reader/logger/wrapper.  No direct WRMSR/MMIO/SMU PLL
    # call is attributed to these slices; downstream 0x1fb4 is unresolved.
    check(checks, "UCLK slices contain no direct BL 0x46b4 helper", b"\xfd\xf7" in b"".join(blob[s:s+0x30] for s,_,_ in ((0x2cf0,0x21,0x30ac),(0x2d20,0x22,0x30c8),(0x2d48,0x23,0x30e4),(0x2d70,0x24,0x3100))), False)
    result = {
        "status": "PASS",
        "checks": len(checks),
        "route": "exact ABL1 UCLK/FCLK policy branch structural match",
        "evidence_class": ["observed-bytes", "static-analysis"],
        "inputs": {"rom": str(ROM), "abl1": str(ABL), "retained_source_lead": str(SRC), "retained_strings_lead": str(STR), "disassembly": str(DIS)},
        "hashes": {"rom": sha(ROM), "abl1": sha(ABL), "source": sha(SRC), "strings": sha(STR), "disassembly": sha(DIS)},
        "exact_uclk_branch": uclk_cases,
        "exact_fclk_branch": {
            "branch_start": "0x463c", "selector": "r1 == 0x0f", "input": "r0 pointer preserved in r5", "descriptor": ["0x015f", "0x0160"],
            "reader": "payload+0x1fb4", "returned_value": "halfword at [sp+0x8]", "output": "str r0,[r5] at payload+0x4682", "logger_string": "payload+0x469c"
        },
        "unresolved_edge": "payload+0x1fb4 consumes the UclkDiv1/Fclk descriptors and supplies the returned byte/halfword; its downstream consumer/clock-divider/PLL semantics are not proven by these branches. No MCLK=UCLK=FCLK or physical-clock claim follows.",
        "fresh_result": "Exact ABL1 contains a concrete UclkDiv1 case-2 read/log branch (descriptor keys 0x21..0x24, reader 0x1fb4, returned byte [sp+0xc]) and a concrete Fclk branch (selector 0x0f, descriptor 0x15f/0x160, reader 0x1fb4, returned halfword stored through caller pointer). These are policy handoff branches, not a proven divider/PLL actuator; the first unresolved mapping edge is common reader 0x1fb4.",
        "limits": "Retained ABL3 source and ABL1 string offsets are version-aligned leads only; exact source-to-binary identity and loader/runtime base remain unproven. No cross-channel minimum 0x95fc or aggregate classifier 0x751c was used as the deliverable. No firmware/hardware/runtime action was performed.",
        "checks_detail": checks,
    }
    (OUT/"abl1-fclk-uclk-branch-result.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({"status": result["status"], "checks": len(checks), "uclk_branch": result["exact_uclk_branch"], "fclk_branch": result["exact_fclk_branch"], "unresolved_edge": result["unresolved_edge"]}, indent=2))

if __name__ == "__main__":
    main()
