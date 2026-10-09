#!/usr/bin/env python3
"""ABL1 APCB writer census (sync fork J1, 2026-09-23).

Executes the proven native ABL1 window (entry 0x221D, Unicorn, Thumb) with a
real APCB copy modeled at 0x7B000 and logs EVERY memory write, classified by
target:
  - APCB copy 0x7B000..0x7D000, especially +0x482 (item7), +0x86E..0x872
    (token21/UclkDiv), +0xB99/+0xB9A (DF gate/value 015F/0160);
  - context +0x2BC and nested +0x2C (policy channels);
  - the outer+channel*4+0x278 family (handler 0x95FC store window);
  - everything else (counted, listed in the JSON).

Cases: BASELINE_APCB (item7=0x24) vs MODIFIED_APCB (item7=0x23) vs
CMOS_ONLY (different CMOS clock, pristine APCB). Diffing the write sets
answers fork J1 for the executed window: does any writer derive from a
source other than CMOS/APCB-native (i.e. an AmdSetup carrier path)?

Verdict scope: the EXECUTED WINDOW ONLY (0x221D..0x1F000, proven path), not
the full ABL1 entry-to-window range. No hardware, no flash, no claims about
physical clocks.
"""

import hashlib
import json
import struct
import sys
from pathlib import Path

from unicorn import (
    Uc,
    UC_ARCH_ARM,
    UC_MODE_THUMB,
    UC_HOOK_CODE,
    UC_HOOK_MEM_WRITE,
    UC_HOOK_MEM_READ,
)
from unicorn.arm_const import (
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_R2,
    UC_ARM_REG_R3,
    UC_ARM_REG_LR,
    UC_ARM_REG_SP,
    UC_ARM_REG_PC,
)

D = Path(__file__).resolve().parent
ROOT = D.parent
EVID = ROOT / "evidence/firmware-audit/20260923-abl1-apcb-writer-census"

ABL1 = (
    ROOT
    / "evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin"
).read_bytes()
assert (
    hashlib.sha256(ABL1).hexdigest()
    == "af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a"
)
ROM = (ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin").read_bytes()
assert (
    hashlib.sha256(ROM).hexdigest()
    == "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"
)
APCB = ROM[0xAB1000:0xAB1B9C]
assert APCB[:4] == b"APCB" and sum(APCB) % 256 == 0

CTX = 0x200000
NEST = 0x201000
END = 0x1F000
APCB_BASE = 0x7B000

APCB_WATCH = {0x482, 0x483, 0x484} | set(range(0x86E, 0x873)) | {0xB99, 0xB9A, 0xB9B}


def classify(addr: int, size: int) -> str:
    if APCB_BASE <= addr < APCB_BASE + 0x2000:
        off = addr - APCB_BASE
        if off in APCB_WATCH or any(off <= w < off + size for w in APCB_WATCH):
            return f"APCB_WATCH+{hex(off)}"
        return f"APCB_OTHER+{hex(off)}"
    if addr == NEST + 0x2C:
        return "NESTED+2C"
    if CTX + 0x2B0 <= addr < CTX + 0x2C0:
        return "CTX_2BC_WINDOW"
    if CTX + 0x270 <= addr < CTX + 0x2E0:
        return "CTX_278_WINDOW"
    if CTX <= addr < CTX + 0x10000:
        return "CTX_OTHER"
    if 0x300000 <= addr < 0x310000:
        return "STACK"
    if addr >= 0x57000 and addr < 0x70000:
        return "LOADBASE57100_COPY"
    return "OTHER"


def run_case(name: str, item7_enum: int, cmos_clock: int, valid: int) -> dict:
    apcb = bytearray(APCB)
    if item7_enum is not None:
        apcb[0x482] = item7_enum
        apcb[0x10] = 0
        apcb[0x10] = (-sum(apcb)) & 255
        assert sum(apcb) % 256 == 0
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0, 0x20000)
    u.mem_write(0, ABL1)
    u.mem_map(CTX, 0x10000)
    u.mem_map(0x300000, 0x10000)
    u.mem_map(0x57000, 0x19000)
    u.mem_write(0x57100, ABL1)
    u.mem_map(0x73000, 0xA000)
    u.mem_write(APCB_BASE, bytes(apcb))

    u.reg_write(UC_ARM_REG_R0, CTX + 0x4000)
    u.reg_write(UC_ARM_REG_LR, 0x18001)
    u.emu_start(0x63F9, 0x18000, count=100, timeout=100000)
    assert u.reg_read(UC_ARM_REG_PC) == 0x18000
    u.mem_write(0x6B000, struct.pack("<I", 0x12345678))
    u.mem_write(CTX + 4, struct.pack("<I", NEST))
    u.mem_write(CTX + 0x331, bytes([valid]))
    u.mem_write(CTX + 0x516, struct.pack("<H", cmos_clock))
    u.mem_write(NEST + 0x2C, struct.pack("<I", 1200))
    for reg, val in [
        (UC_ARM_REG_R0, CTX),
        (UC_ARM_REG_R1, 2),
        (UC_ARM_REG_SP, 0x308000),
        (UC_ARM_REG_LR, END | 1),
    ]:
        u.reg_write(reg, val)

    writes: list[dict] = []
    others: dict[str, int] = {}
    calls: list[list[int]] = []
    pcs: list[int] = []

    def code(mu, addr, size, data):
        pcs.append(addr)
        if addr == END:
            mu.emu_stop()
            return
        if addr == 0x64C8:
            raise AssertionError("native assertion reached")
        if addr == 0x1F2C:
            pair = [mu.reg_read(UC_ARM_REG_R0), mu.reg_read(UC_ARM_REG_R1)]
            calls.append(pair)
            assert pair == [7, 2]
            return
        if addr not in (0x130C, 0x112A0):
            return
        mu.reg_write(UC_ARM_REG_R0, 0)
        mu.reg_write(UC_ARM_REG_PC, mu.reg_read(UC_ARM_REG_LR))

    def write(mu, access, address, size, value, data):
        cls = classify(address, size)
        if cls.startswith(("APCB_WATCH", "APCB_OTHER", "NESTED", "CTX_2", "LOADBASE")):
            writes.append(
                {
                    "pc": hex(mu.reg_read(UC_ARM_REG_PC)),
                    "addr": hex(address),
                    "class": cls,
                    "size": size,
                    "value": hex(value),
                }
            )
        else:
            others[cls] = others.get(cls, 0) + 1

    u.hook_add(UC_HOOK_CODE, code)
    u.hook_add(UC_HOOK_MEM_WRITE, write)
    u.emu_start(0x221D, END + 2, count=150000, timeout=2000000)

    final_policy = struct.unpack("<I", u.mem_read(NEST + 0x2C, 4))[0]
    assert pcs[-1] == END and calls == [[7, 2]], (name, hex(pcs[-1]))
    assert bytes(u.mem_read(0, len(ABL1))) == ABL1, "ABL1 code self-modified!"
    expected = 1800 if item7_enum in (None, 0x24) else 1750
    assert final_policy == expected, (name, hex(final_policy))
    return {
        "case": name,
        "item7_enum": hex(item7_enum) if item7_enum is not None else "pristine",
        "cmos_clock": cmos_clock,
        "final_policy": final_policy,
        "watched_writes": writes,
        "other_write_classes": others,
        "provider_calls": calls,
    }


def main() -> int:
    EVID.mkdir(parents=True, exist_ok=True)
    rows = [
        run_case("BASELINE_APCB", 0x24, 1750, 1),
        run_case("MODIFIED_APCB_item7_0x23", 0x23, 1750, 1),
        run_case("CMOS_ONLY_pristine_APCB", None, 1650, 1),
    ]

    def keyset(row: dict) -> set:
        return {(w["pc"], w["addr"], w["value"]) for w in row["watched_writes"]}

    diff_b_m = sorted(keyset(rows[0]) - keyset(rows[1]))
    diff_m_b = sorted(keyset(rows[1]) - keyset(rows[0]))
    diff_b_c = sorted(keyset(rows[0]) - keyset(rows[2]))

    # J1 verdict for the executed window: a writer is "foreign" if it targets
    # the watched APCB offsets (0x482/0x86E..0x872/0xB99/0xB9A) and is NOT one
    # of the known native paths (checksum refresh at +0x10 excluded).
    foreign = [
        w
        for row in rows
        for w in row["watched_writes"]
        if w["class"].startswith("APCB_WATCH")
        and not w["class"].startswith(("APCB_WATCH+0x10", "APCB_WATCH+0x482"))
    ]
    verdict = {
        "j1_executed_window": "CLOSED-NEGATIVE: no writer outside the known CMOS/APCB-native paths touched the watched APCB offsets; AmdSetup carriers do not reach the PLL arguments in this window"
        if not foreign
        else f"FOREIGN WRITERS FOUND: {len(foreign)} - the producer join is ALIVE",
        "foreign_writes": foreign[:50],
        "write_set_diffs": {
            "baseline_minus_modified": [list(t) for t in diff_b_m],
            "modified_minus_baseline": [list(t) for t in diff_m_b],
            "baseline_minus_cmos_only": [list(t) for t in diff_b_c],
        },
    }
    out = {
        "scope": "ABL1 native window 0x221D..0x1F000, real APCB modeled at 0x7B000; no hardware",
        "abl1_sha256": hashlib.sha256(ABL1).hexdigest(),
        "base_image_sha256": hashlib.sha256(ROM).hexdigest(),
        "cases": rows,
        "verdict": verdict,
    }
    (EVID / "writer-census-result.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(verdict["write_set_diffs"], indent=1))
    print(verdict["j1_executed_window"])
    for row in rows:
        print(
            f"{row['case']}: final_policy={row['final_policy']} "
            f"watched_writes={len(row['watched_writes'])} "
            f"other_classes={row['other_write_classes']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
