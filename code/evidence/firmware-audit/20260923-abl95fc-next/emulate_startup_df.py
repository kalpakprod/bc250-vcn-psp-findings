"""Observe later ABL4 startup-DF request with original code and explicit IO hooks."""

import hashlib, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE, UC_HOOK_INTR
from unicorn.arm_const import (
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_R2,
    UC_ARM_REG_SP,
    UC_ARM_REG_PC,
    UC_ARM_REG_LR,
)

D = Path(__file__).resolve().parent
b = (D / "ABL4.bin").read_bytes()
assert (
    hashlib.sha256(b).hexdigest()
    == "1d60a34f1641204423024857249781d9184b2c9c5342f4dd8dbc070df6c5150b"
)
assert b[0xD8AE:0xD8B2] == bytes.fromhex("40f20010")
results = []
for name, arg, stock in [
    ("stock_caller", 0x100, True),
    ("modified_argument", 0x101, False),
    ("restored_argument", 0x100, False),
]:
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0, 0x20000)
    u.mem_write(0, b)
    u.mem_map(0x300000, 0x10000)
    u.reg_write(UC_ARM_REG_SP, 0x308000)
    u.reg_write(UC_ARM_REG_R0, arg)
    u.reg_write(UC_ARM_REG_LR, 0x18001)
    e = {
        "case": name,
        "entry": "0xd8ae" if stock else "0x9564",
        "svc": [],
        "executed_topology_helpers": [],
        "instructions": 0,
    }

    def code(uc, a, size, _):
        e["instructions"] += 1
        if a in (0xA418, 0xA450):
            e["executed_topology_helpers"].append(hex(a))
        if a == 0x20F0:
            uc.reg_write(UC_ARM_REG_R0, 0)
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
        if a == 0x9A0C:
            raise AssertionError("Firmware assertion branch")

    def intr(uc, n, _):
        pc = uc.reg_read(UC_ARM_REG_PC)
        assert bytes(uc.mem_read(pc - 2, 2)) == b"\x28\xdf"
        e["svc"].append(
            {
                "pc": hex(pc - 2),
                "selector": uc.reg_read(UC_ARM_REG_R0),
                "argument": uc.reg_read(UC_ARM_REG_R1),
                "response_pointer": uc.reg_read(UC_ARM_REG_R2),
            }
        )
        uc.mem_write(uc.reg_read(UC_ARM_REG_R2), struct.pack("<I", 0))
        uc.reg_write(UC_ARM_REG_R0, 0)

    u.hook_add(UC_HOOK_CODE, code)
    u.hook_add(UC_HOOK_INTR, intr)
    end = 0xD8B6 if stock else 0x18000
    u.emu_start(0xD8AF if stock else 0x9565, end, timeout=500000, count=5000)
    assert u.reg_read(UC_ARM_REG_PC) == end
    assert [(s["selector"], s["argument"]) for s in e["svc"]] == [(7, arg)]
    assert e["executed_topology_helpers"] == ["0xa418", "0xa450"]
    assert bytes(u.mem_read(0, len(b))) == b
    e["code_unchanged"] = True
    results.append(e)
    print(name, "SVC28 selector7 argument", hex(arg), "instructions", e["instructions"])
(D / "startup-df-result.json").write_text(
    json.dumps(
        {
            "cases": results,
            "limits": [
                "No SVC28 hardware implementation modeled, success response fixture",
                "Phase ordering inferred from ABL module identities and exact callsites, not whole boot execution",
                "0x100 is packed raw argument, not frequency or proven pstate number",
                "Later software/firmware can change state again",
            ],
        },
        indent=2,
    )
    + "\n"
)
print("PASS3 native ABL4 transition cases")
