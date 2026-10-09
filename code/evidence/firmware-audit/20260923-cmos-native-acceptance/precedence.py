"""Test native CMOS versus item7 precedence, modeled item provider, no hardware."""

import hashlib
import json
import struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
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
ROOT = D.parents[2]
b = (
    ROOT
    / "evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin"
).read_bytes()
assert (
    hashlib.sha256(b).hexdigest()
    == "af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a"
)
CTX = 0x200000
NEST = 0x201000
END = 0x1F000
rows = []
for name, clock, valid, item, expect in [
    ("BASELINE", 1750, 1, None, 1750),
    ("MODIFIED_INPUT", 1650, 1, None, 1650),
    ("RESTORED_INPUT", 1750, 1, None, 1750),
    ("ITEM7_OVERRIDES_CMOS", 1650, 1, 0x24, 1800),
    ("ITEM7_1750", 1650, 1, 0x23, 1750),
    ("INVALID_CMOS", 1650, 0, None, 1200),
    ("SENTINEL_CMOS", 65535, 1, None, 1200),
]:
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0, 0x20000)
    u.mem_write(0, b)
    u.mem_map(CTX, 0x10000)
    u.mem_map(0x300000, 0x10000)
    u.mem_write(CTX + 4, struct.pack("<I", NEST))
    u.mem_write(CTX + 0x331, bytes([valid]))
    u.mem_write(CTX + 0x516, struct.pack("<H", clock))
    u.mem_write(NEST + 0x2C, struct.pack("<I", 1200))
    for reg, val in [
        (UC_ARM_REG_R0, CTX),
        (UC_ARM_REG_R1, 2),
        (UC_ARM_REG_SP, 0x308000),
        (UC_ARM_REG_LR, END | 1),
    ]:
        u.reg_write(reg, val)
    calls = []
    writes = []
    pcs = []

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
            if item is not None:
                mu.mem_write(mu.reg_read(UC_ARM_REG_R2), bytes([item]))
                mu.mem_write(mu.reg_read(UC_ARM_REG_R3), b"\x01")
            mu.reg_write(UC_ARM_REG_R0, int(item is not None))
        elif addr != 0x130C:
            return
        mu.reg_write(UC_ARM_REG_PC, mu.reg_read(UC_ARM_REG_LR))

    def write(mu, access, address, size, value, data):
        if address == NEST + 0x2C:
            writes.append(value)

    u.hook_add(UC_HOOK_CODE, code)
    u.hook_add(UC_HOOK_MEM_WRITE, write)
    u.emu_start(0x221D, END + 2, count=10000, timeout=1000000)
    value = struct.unpack("<I", u.mem_read(NEST + 0x2C, 4))[0]
    assert pcs[-1] == END and value == expect and calls == [[7, 2]], (
        name,
        value,
        hex(pcs[-1]),
    )
    if item is not None:
        assert writes == [clock, expect]
    rows.append(
        {
            "case": name,
            "cmos_clock": clock,
            "valid": valid,
            "item7": item,
            "result": value,
            "writes": writes,
            "provider_calls": calls,
        }
    )
    print(
        f"{name}: CMOS={clock} valid={valid} item7={item} writes={writes} final_policy={value}"
    )
(D / "precedence-result.json").write_text(
    json.dumps(
        {
            "scope": "native221C phase2; synthetic item7 provider; not applied clocks",
            "cases": rows,
        },
        indent=2,
    )
    + "\n"
)
print("PASS 7 native priority cases; present item7 can overwrite accepted CMOS clock")
