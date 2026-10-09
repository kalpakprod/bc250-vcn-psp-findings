"""Bounded native later UclkDiv1 phase bodies; typed provider deliberately modeled."""

import hashlib, json, struct
from pathlib import Path
from unicorn import (
    Uc,
    UC_ARCH_ARM,
    UC_MODE_THUMB,
    UC_HOOK_CODE,
    UC_HOOK_MEM_WRITE,
    UC_HOOK_INTR,
)
from unicorn.arm_const import (
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_R2,
    UC_ARM_REG_R3,
    UC_ARM_REG_SP,
    UC_ARM_REG_LR,
    UC_ARM_REG_PC,
)

D = Path(__file__).resolve().parent
rows = []
for module, sha, entry, provider, logger, epilogue in [
    (
        "ABL3",
        "3f5890b3a830725a11e169861fcfa208fa3f5fab37a38fc7f994a221a1f213be",
        0x32B4,
        0x2634,
        0x1BE4,
        0x4B30,
    ),
    (
        "ABL4",
        "1d60a34f1641204423024857249781d9184b2c9c5342f4dd8dbc070df6c5150b",
        0x5CE4,
        0x2894,
        0x20F0,
        0x7560,
    ),
]:
    b = (D / f"{module}.bin").read_bytes()
    assert hashlib.sha256(b).hexdigest() == sha
    for name, value in [("BASELINE", 1), ("MODIFIED", 0), ("RESTORED", 1)]:
        u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        u.mem_map(0, 0x100000)
        u.mem_write(0, b)
        u.mem_map(0x200000, 0x10000)
        u.mem_map(0x300000, 0x10000)
        for reg, val in [
            (UC_ARM_REG_R0, 0x200000),
            (UC_ARM_REG_R1, 2),
            (UC_ARM_REG_SP, 0x308000),
            (UC_ARM_REG_LR, 0x1F001),
        ]:
            u.reg_write(reg, val)
        pcs = []
        calls = []
        logs = []

        def code(mu, a, size, data):
            pcs.append(a)
            if a == 0x1F000:
                mu.emu_stop()
                return
            if a == provider:
                descriptor = struct.unpack(
                    "<HHH", mu.mem_read(mu.reg_read(UC_ARM_REG_R0), 6)
                )
                assert (
                    descriptor[0] == 0x20
                    and 0x21 <= descriptor[1] <= 0x24
                    and descriptor[2] == 0
                )
                assert mu.reg_read(UC_ARM_REG_R1) == 2
                calls.append(list(descriptor))
                mu.mem_write(mu.reg_read(UC_ARM_REG_R2), bytes([value]))
                mu.mem_write(mu.reg_read(UC_ARM_REG_R3), b"\x01")
                mu.reg_write(UC_ARM_REG_R0, 1)
            elif a == logger:
                ptr = mu.reg_read(UC_ARM_REG_R2)
                txt = bytes(mu.mem_read(ptr, 80)).split(b"\0")[0].decode()
                assert "Override UclkDiv1 M" in txt
                logs.append([txt, mu.reg_read(UC_ARM_REG_R3)])
                mu.reg_write(UC_ARM_REG_R0, 0)
            else:
                return
            mu.reg_write(UC_ARM_REG_PC, mu.reg_read(UC_ARM_REG_LR))

        def write(mu, access, a, size, value, data):
            assert 0x300000 <= a < 0x310000, hex(a)

        def intr(mu, num, data):
            raise AssertionError(("unexpected service", num))

        u.hook_add(UC_HOOK_CODE, code)
        u.hook_add(UC_HOOK_MEM_WRITE, write)
        u.hook_add(UC_HOOK_INTR, intr)
        u.emu_start(entry | 1, 0x1F002, count=3000, timeout=1000000)
        assert (
            pcs[-1] == 0x1F000
            and epilogue in pcs
            and len(calls) == 4
            and [x[1] for x in logs] == [value] * 4
        )
        assert bytes(u.mem_read(0, len(b))) == b
        rows.append(
            {
                "module": module,
                "sha256": sha,
                "case": name,
                "value": value,
                "provider_modeled": True,
                "descriptors": calls,
                "logs": logs,
                "instructions": len(pcs),
                "only_stack_writes": True,
                "services": 0,
            }
        )
        print(
            f"{module} {name}: four_logs={value} only_stack_writes=True services=0 returned=True"
        )
(D / "later-result.json").write_text(json.dumps(rows, indent=2) + "\n")
print("PASS 6 later-ABL branch cases; modeled provider, unchanged branch bodies")
