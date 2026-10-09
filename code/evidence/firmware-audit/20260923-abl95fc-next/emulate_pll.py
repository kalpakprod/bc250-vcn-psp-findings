"""Execute original Thumb PLL argument builder, intercept external effects explicitly."""

import hashlib
import json
import struct
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE, UC_HOOK_INTR
from unicorn.arm_const import (
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_R2,
    UC_ARM_REG_R4,
    UC_ARM_REG_R5,
    UC_ARM_REG_R6,
    UC_ARM_REG_SP,
    UC_ARM_REG_LR,
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
NESTED = 0x201000
SP = 0x308000
cases = [
    ("baseline", 1800, 0, None),
    ("modified_input", 1750, 0, None),
    ("restored_input", 1800, 0, None),
    ("chip6", 1800, 6, None),
    ("provider_override", 1800, 0, 1420),
    ("provider_zero", 1800, 0, 0),
    ("provider_max_u16", 1800, 0, 65535),
]
results = []
for name, value, chip, override in cases:
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0, 0x20000)
    u.mem_write(0, b)
    u.mem_map(CTX, 0x10000)
    u.mem_map(0x300000, 0x10000)
    u.mem_map(0x6B000, 0x1000)
    u.mem_write(0x6B000, struct.pack("<I", 0x12345678))
    u.mem_write(CTX + 4, struct.pack("<I", NESTED))
    u.mem_write(NESTED + 0x790, struct.pack("<H", chip))
    for reg, val in [
        (UC_ARM_REG_R4, value),
        (UC_ARM_REG_R5, CTX),
        (UC_ARM_REG_R6, 0x100000),
        (UC_ARM_REG_SP, SP),
    ]:
        u.reg_write(reg, val)
    event = {
        "case": name,
        "input_word": value,
        "nested_790": chip,
        "provider_response_fixture": override,
        "external_calls": [],
        "svc": [],
        "instruction_count": 0,
    }

    def code(uc, address, size, _):
        event["instruction_count"] += 1
        if address == 0x463C:
            assert (
                uc.reg_read(UC_ARM_REG_R0) == SP + 4
                and uc.reg_read(UC_ARM_REG_R1) == 15
            )
            event["default_before_provider"] = struct.unpack(
                "<I", bytes(uc.mem_read(SP + 4, 4))
            )[0]
        if address in (0x130C, 0x1FB4):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            call = {"address": hex(address), "r0": r0, "r1": r1}
            returned = 0
            if address == 0x1FB4:
                descriptor = bytes(uc.mem_read(r0, 6))
                assert descriptor == struct.pack("<HHH", 0x15F, 0x160, 0), (
                    descriptor.hex()
                )
                outptr = uc.reg_read(UC_ARM_REG_R2)
                call["descriptor_hex"] = descriptor.hex()
                call["fixture_status"] = 0 if override is None else 1
                if override is not None:
                    uc.mem_write(outptr, struct.pack("<H", override))
                    returned = 1
                call["fixture_value"] = override
            event["external_calls"].append(call)
            uc.reg_write(UC_ARM_REG_R0, returned)
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
        elif address == 0x64C8:
            raise AssertionError("Unexpected firmware assertion path")

    def intr(uc, number, _):
        pc = uc.reg_read(UC_ARM_REG_PC)
        assert bytes(uc.mem_read(pc - 2, 2)) == b"\x28\xdf", (number, hex(pc))
        r0 = uc.reg_read(UC_ARM_REG_R0)
        r1 = uc.reg_read(UC_ARM_REG_R1)
        r2 = uc.reg_read(UC_ARM_REG_R2)
        event["svc"].append(
            {
                "pc": hex(pc - 2),
                "service": 0x28,
                "selector": r0,
                "argument": r1,
                "response_pointer": r2,
                "fixture_return": 0,
            }
        )
        assert r0 in (14, 15) and r2 == SP + 8
        uc.mem_write(r2, struct.pack("<I", 0))
        uc.reg_write(UC_ARM_REG_R0, 0)

    u.hook_add(UC_HOOK_CODE, code)
    u.hook_add(UC_HOOK_INTR, intr)
    try:
        u.emu_start(0x5F1F, 0x601A, timeout=1000000, count=20000)
        assert u.reg_read(UC_ARM_REG_PC) == 0x601A, hex(u.reg_read(UC_ARM_REG_PC))
        assert bytes(u.mem_read(0, len(b))) == b
        expected_fclk = (
            override if override is not None else (250 if chip == 6 else 1200)
        )
        assert [(x["selector"], x["argument"]) for x in event["svc"]] == [
            (14, expected_fclk),
            (15, value >> 1),
        ], event
        event["context_78"] = struct.unpack("<H", bytes(u.mem_read(CTX + 0x78, 2)))[0]
        assert event["context_78"] == expected_fclk
        event["code_bytes_unchanged"] = True
        event["status"] = "PASS_BOUNDED_EMULATION"
    except Exception as ex:
        event["status"] = "ERROR"
        event["error"] = repr(ex)
        event["pc"] = hex(u.reg_read(UC_ARM_REG_PC))
        results.append(event)
        (D / "emulation-result.json").write_text(json.dumps(results, indent=2) + "\n")
        raise
    results.append(event)
    print(
        name,
        "input",
        value,
        "->",
        [(x["selector"], x["argument"]) for x in event["svc"]],
        "instructions",
        event["instruction_count"],
    )
assert results[0]["svc"] == results[2]["svc"]
(D / "emulation-result.json").write_text(
    json.dumps(
        {
            "source_sha256": hashlib.sha256(b).hexdigest(),
            "cases": results,
            "limits": [
                "Start at5F1E with synthetic frame, not full boot or full function",
                "130C logging skipped;original463C executed;only1FB4 provider return/value simulated explicitly",
                "SVC28 intercepted, successful return/response fixtures, no hardware",
                "No proof of physical MHz or1:1:1",
                "Code bytes unchanged in every emulator instance",
            ],
        },
        indent=2,
    )
    + "\n"
)
print("PASS7 native Thumb cases, unchanged code, only declared external-effect hooks")
