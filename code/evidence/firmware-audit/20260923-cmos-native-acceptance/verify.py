"""Native CLV CMOS acceptance slice, synthetic IO. Never accesses hardware."""

import hashlib
import json
import struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import (
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_R2,
    UC_ARM_REG_R4,
    UC_ARM_REG_R9,
    UC_ARM_REG_R10,
    UC_ARM_REG_LR,
    UC_ARM_REG_SP,
    UC_ARM_REG_PC,
)

ROOT = Path(__file__).resolve().parents[3]
D = Path(__file__).resolve().parent
source = (
    ROOT
    / "evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin"
)
b = source.read_bytes()
assert (
    hashlib.sha256(b).hexdigest()
    == "af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a"
)
CTX = 0x200000
rows = []
for name, clock, signature, bad_sum, expected in [
    ("BASELINE", 1750, 0x42435041, False, 1),
    ("MODIFIED_INPUT", 1650, 0x42435041, False, 1),
    ("RESTORED_INPUT", 1750, 0x42435041, False, 1),
    ("BAD_CHECKSUM", 1650, 0x42435041, True, 0),
    ("BAD_SIGNATURE", 1650, 0, False, 0),
    ("ABL_SIGNATURE", 1750, 0x4C424124, False, 1),
]:
    cmos = bytearray(256)
    struct.pack_into("<I", cmos, 0x90, signature)
    struct.pack_into("<H", cmos, 0x96, clock)
    cmos[0x98:0xA4] = bytes(range(12, 24))  # marker fixture, not recommended timings
    struct.pack_into("<HHHH", cmos, 0xA4, 4096, 120, 240, 512)
    struct.pack_into("<H", cmos, 0x94, sum(cmos[0x96:0xAC]) + int(bad_sum))
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0, 0x20000)
    u.mem_write(0, b)
    u.mem_map(CTX, 0x10000)
    u.mem_map(0x300000, 0x10000)
    u.mem_write(CTX + 0x510, bytes(cmos[0x90:0x94]))
    for reg, val in [
        (UC_ARM_REG_R4, CTX),
        (UC_ARM_REG_R9, 0),
        (UC_ARM_REG_R10, 1),
        (UC_ARM_REG_SP, 0x308000),
    ]:
        u.reg_write(reg, val)
    reads = []
    writes = []
    checksum_calls = []
    visited = []

    def hook(mu, addr, size, data):
        visited.append(addr)
        if addr == 0x7DBE:
            mu.emu_stop()
            return
        if addr == 0x5534:
            checksum_calls.append(
                [mu.reg_read(UC_ARM_REG_R0), mu.reg_read(UC_ARM_REG_R1)]
            )
        if addr in (0x113FC, 0x1145A):
            port = mu.reg_read(UC_ARM_REG_R0)
            idx = mu.reg_read(UC_ARM_REG_R1)
            width = 2 if addr == 0x113FC else 1
            assert port == 0x72 and 0x94 <= idx <= 0xAA
            val = int.from_bytes(cmos[idx : idx + width], "little")
            reads.append([idx, width, val])
            mu.reg_write(UC_ARM_REG_R0, val)
        elif addr == 0x11D00:
            writes.append(
                [
                    mu.reg_read(UC_ARM_REG_R0),
                    mu.reg_read(UC_ARM_REG_R1),
                    mu.reg_read(UC_ARM_REG_R2),
                ]
            )
        elif addr != 0x130C:
            return
        mu.reg_write(UC_ARM_REG_PC, mu.reg_read(UC_ARM_REG_LR))

    u.hook_add(UC_HOOK_CODE, hook)
    u.emu_start(0x77B3, 0x1F000, count=20000, timeout=1000000)
    assert visited[-1] == 0x7DBE, (name, hex(visited[-1]))
    accepted = u.mem_read(CTX + 0x331, 1)[0]
    loaded = bytes(u.mem_read(CTX + 0x516, 22))
    assert accepted == expected
    if signature:
        assert loaded == cmos[0x96:0xAC]
        assert checksum_calls == [[CTX + 0x516, 22]]
    else:
        assert not reads and not checksum_calls
    if bad_sum:
        assert writes == [[0x72, 0x90, 0x454B4843]]
    else:
        assert not writes
    row = {
        "case": name,
        "input_clock": clock,
        "accepted_flag": accepted,
        "loaded_clock": int.from_bytes(loaded[:2], "little"),
        "reads": reads,
        "writes": writes,
        "instructions": len(visited),
        "native_checksum_calls": checksum_calls,
        "cmos_sha256": hashlib.sha256(cmos).hexdigest(),
    }
    rows.append(row)
    print(
        f"{name}: input={clock} loaded={row['loaded_clock']} accepted={accepted} writes={writes}"
    )
assert rows[0]["cmos_sha256"] == rows[2]["cmos_sha256"]
(D / "result.json").write_text(
    json.dumps(
        {
            "scope": "native acceptance slice, modeled IO and entry context; not whole boot, PLL or hardware",
            "source_sha256": hashlib.sha256(b).hexdigest(),
            "cases": rows,
        },
        indent=2,
    )
    + "\n"
)
print("PASS 6 native CMOS acceptance cases; original firmware unchanged")
