"""Actual ABL0 APCB load caller/validation, ROM service explicitly mocked."""

import hashlib, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_INTR
from unicorn.arm_const import (
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_R2,
    UC_ARM_REG_R3,
    UC_ARM_REG_SP,
    UC_ARM_REG_PC,
    UC_ARM_REG_LR,
)

ROOT = Path(__file__).resolve().parents[3]
D = Path(__file__).resolve().parent
b = (D / "ABL0.bin").read_bytes()
assert (
    hashlib.sha256(b).hexdigest()
    == "3405551617c13dc7b1db464edd74e0f7a4240a80b37ed068c7650ccfe2d19e29"
)
rom = (ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin").read_bytes()
assert (
    hashlib.sha256(rom).hexdigest()
    == "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"
)
apcb = rom[0xAB1000:0xAB1B9C]
results = []
for name in ["baseline", "bad_checksum", "service_failure", "restored"]:
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0, 0x20000)
    u.mem_write(0, b)
    u.mem_map(0x7B000, 0x2000)
    u.mem_map(0x200000, 0x10000)
    u.mem_map(0x300000, 0x10000)
    for reg, value in [
        (UC_ARM_REG_R0, 0x200000),
        (UC_ARM_REG_R1, 0),
        (UC_ARM_REG_SP, 0x308000),
        (UC_ARM_REG_LR, 0x18001),
    ]:
        u.reg_write(reg, value)
    event = {"case": name, "svcs": []}

    def intr(uc, number, _):
        pc = uc.reg_read(UC_ARM_REG_PC)
        op = bytes(uc.mem_read(pc - 2, 2))
        assert op[1] == 0xDF
        n = op[0]
        entry = {"pc": hex(pc - 2), "svc": n}
        event["svcs"].append(entry)
        if n == 0x2D:
            typ = uc.reg_read(UC_ARM_REG_R0)
            dest = uc.reg_read(UC_ARM_REG_R1)
            szptr = uc.reg_read(UC_ARM_REG_R2)
            cap = struct.unpack("<I", bytes(uc.mem_read(szptr, 4)))[0]
            assert (typ, dest, cap) == (0x60, 0x7B000, 0x2000)
            entry.update(
                type=typ, destination=hex(dest), capacity=cap, service_is_fixture=True
            )
            if name == "service_failure":
                uc.reg_write(UC_ARM_REG_R0, 1)
            else:
                data = bytearray(apcb)
                if name == "bad_checksum":
                    data[-1] ^= 1
                uc.mem_write(dest, bytes(data))
                uc.mem_write(szptr, struct.pack("<I", len(data)))
                uc.reg_write(UC_ARM_REG_R0, 0)
        elif n == 6:
            pass  # Log-only SVC contract is a model assumption, preserve registers.
        elif n == 0:
            event["fatal_code"] = uc.reg_read(UC_ARM_REG_R0)
            uc.emu_stop()
        else:
            raise AssertionError(entry)

    u.hook_add(UC_HOOK_INTR, intr)
    u.emu_start(0x31, 0x18000, timeout=1000000, count=50000)
    event["pc"] = hex(u.reg_read(UC_ARM_REG_PC))
    event["return"] = u.reg_read(UC_ARM_REG_R0)
    event["code_unchanged"] = bytes(u.mem_read(0, len(b))) == b
    assert event["code_unchanged"]
    if name in ("baseline", "restored"):
        assert u.reg_read(UC_ARM_REG_PC) == 0x18000 and event["return"] == 0
        assert bytes(u.mem_read(0x7B000, len(apcb))) == apcb
        event["loaded_sha256"] = hashlib.sha256(
            bytes(u.mem_read(0x7B000, len(apcb)))
        ).hexdigest()
    else:
        assert event["fatal_code"] == 16
    results.append(event)
    print(
        name,
        "return",
        event["return"],
        "fatal",
        event.get("fatal_code"),
        "pc",
        event["pc"],
    )
assert results[0]["loaded_sha256"] == results[3]["loaded_sha256"]
(D / "abl0-load-result.json").write_text(
    json.dumps(
        {
            "cases": results,
            "limits": [
                "SVC2D handler mocked; actual selected flash region or runtime overlay not proven",
                "SVC6 treated as logging without register mutation",
                "Synthetic context/stack, not full boot",
            ],
        },
        indent=2,
    )
    + "\n"
)
print("PASS4 ABL0 load-request/validation cases")
