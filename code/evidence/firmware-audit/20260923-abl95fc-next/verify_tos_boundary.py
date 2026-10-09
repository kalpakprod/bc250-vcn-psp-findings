"""Reject false attribution of early ABL service28 to retained TOS dispatcher."""

import hashlib, json, struct, subprocess
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB
from unicorn.arm_const import (
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_SP,
    UC_ARM_REG_LR,
    UC_ARM_REG_PC,
)

D = Path(__file__).resolve().parent
b = (D / "psp-type2.bin").read_bytes()
assert (
    hashlib.sha256(b).hexdigest()
    == "259a31d52ec847df23596ae1c7e736212ff6bab7793af741b83fa62e439ade68"
)
checks = {
    0x8: "8c0000ea",
    0x284: "40419fe5",
    0x288: "34ff2fe1",
    0x46B0: "5139",
    0x46C2: "8029",
    0x46D4: "f6e3",
    0x501A: "0924",
}
for o, v in checks.items():
    assert b[o : o + len(bytes.fromhex(v))] == bytes.fromhex(v), (hex(o), v)
assert struct.unpack_from("<I", b, 0x3CC)[0] == 0x4545
results = []
for svc in [0x28, 0x2D]:
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0, 0x20000)
    u.mem_write(0, b)
    u.mem_map(0x200000, 0x1000)
    u.mem_map(0x300000, 0x10000)
    # Synthetic saved-register frame for the dispatcher, no exception/ROM handler emulation.
    u.mem_write(0x6010, struct.pack("<I", 0x200000))
    for reg, val in [
        (UC_ARM_REG_R0, 0),
        (UC_ARM_REG_R1, svc),
        (UC_ARM_REG_SP, 0x308000),
        (UC_ARM_REG_LR, 0x18001),
    ]:
        u.reg_write(reg, val)
    u.emu_start(0x46A1, 0x18000, timeout=100000, count=500)
    assert u.reg_read(UC_ARM_REG_PC) == 0x18000 and u.reg_read(UC_ARM_REG_R0) == 9
    assert bytes(u.mem_read(0, 0x6000)) == b[:0x6000]
    results.append(
        {
            "service": svc,
            "return": 9,
            "entry": "0x46a0",
            "exception_prologue_not_executed": True,
            "code_0_to6000_unchanged": True,
        }
    )
    print("TOS dispatcher service", hex(svc), "->9")
(D / "tos-boundary-result.json").write_text(
    json.dumps(
        {
            "cases": results,
            "source_sha256": hashlib.sha256(b).hexdigest(),
            "finding": "This native TOS dispatcher route does not implement early ABL28/2D services; both take default9. Do not infer TOS was active during ABL.",
            "limits": [
                "Synthetic supervisor frame, not live TOS exception",
                "Other runtime dispatch paths not excluded",
                "Type1 header not recognized, not proven encrypted",
                "ROM/earlier bootloader implementation remains missing",
            ],
        },
        indent=2,
    )
    + "\n"
)
print("PASS2 TOS dispatcher cases; no hardware IO, no firmware patch")
