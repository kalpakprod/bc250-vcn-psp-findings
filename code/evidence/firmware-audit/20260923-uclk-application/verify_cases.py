"""Observe original UclkDiv1 phase with native APCB lookup, no hardware."""

import hashlib, json, struct
from pathlib import Path
from unicorn import (
    Uc,
    UC_ARCH_ARM,
    UC_MODE_THUMB,
    UC_HOOK_CODE,
    UC_HOOK_MEM_READ,
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
ROOT = D.parents[2]
b = (
    ROOT
    / "evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin"
).read_bytes()
rom = (ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin").read_bytes()
assert (
    hashlib.sha256(b).hexdigest()
    == "af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a"
)
assert (
    hashlib.sha256(rom).hexdigest()
    == "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"
)
apcb = rom[0xAB1000:0xAB1B9C]
CTX = 0x200000
END = 0x1F000
results = []
for name, gate, value, expected in [
    ("BASELINE", 1, 1, [1]),
    ("MODIFIED_M0", 1, 0, [0]),
    ("RESTORED_M0", 1, 1, [1]),
    ("AUTO_FF", 1, 255, []),
    ("GATE_OFF", 0, 1, []),
]:
    active_apcb = bytearray(apcb)
    active_apcb[0x86E] = gate
    active_apcb[0x86F] = value
    active_apcb[0x10] = 0
    active_apcb[0x10] = (-sum(active_apcb)) & 255
    assert sum(active_apcb) % 256 == 0
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0, 0x20000)
    u.mem_write(0, b)
    u.mem_map(CTX, 0x10000)
    u.mem_map(0x300000, 0x10000)
    u.mem_map(0x57000, 0x19000)
    u.mem_write(0x57100, b)
    u.mem_map(0x73000, 0xA000)
    u.mem_write(0x7B000, bytes(active_apcb))
    u.reg_write(UC_ARM_REG_R0, CTX + 0x4000)
    u.reg_write(UC_ARM_REG_LR, 0x18001)
    u.emu_start(0x63F9, 0x18000, count=100, timeout=100000)
    assert u.reg_read(UC_ARM_REG_PC) == 0x18000
    u.mem_write(0x6B000, struct.pack("<I", 0x12345678))
    for reg, val in [
        (UC_ARM_REG_R0, CTX),
        (UC_ARM_REG_R1, 2),
        (UC_ARM_REG_SP, 0x308000),
        (UC_ARM_REG_LR, END | 1),
    ]:
        u.reg_write(reg, val)
    pcs = []
    reads = []
    writes = []
    logs = []
    tokens = []

    def code(mu, a, size, data):
        pcs.append(a)
        if a == END:
            mu.emu_stop()
            return
        if a in (0x64C8, 0x10958):
            raise AssertionError(("unexpected assertion/actuator", hex(a)))
        if a == 0x4800:
            tokens.append(mu.reg_read(UC_ARM_REG_R0))
        if a == 0x130C:
            ptr = mu.reg_read(UC_ARM_REG_R2)
            raw = bytes(mu.mem_read(ptr, 100)).split(b"\0")[0]
            logs.append(
                [
                    hex(ptr),
                    raw.decode("ascii", errors="replace"),
                    mu.reg_read(UC_ARM_REG_R3),
                ]
            )
        if a in (0x130C, 0x112A0):
            mu.reg_write(UC_ARM_REG_R0, 0)
            mu.reg_write(UC_ARM_REG_PC, mu.reg_read(UC_ARM_REG_LR))

    def read(mu, access, a, size, value, data):
        if 0x7B000 <= a < 0x7BB9C:
            reads.append(
                [
                    hex(mu.reg_read(UC_ARM_REG_PC)),
                    hex(a - 0x7B000),
                    size,
                    bytes(mu.mem_read(a, size)).hex(),
                ]
            )

    def write(mu, access, a, size, value, data):
        if CTX <= a < CTX + 0x10000:
            writes.append([hex(a - CTX), size, value])

    def intr(mu, number, data):
        raise AssertionError(("unexpected hardware service", number))

    u.hook_add(UC_HOOK_CODE, code)
    u.hook_add(UC_HOOK_MEM_READ, read)
    u.hook_add(UC_HOOK_MEM_WRITE, write)
    u.hook_add(UC_HOOK_INTR, intr)
    u.emu_start(0x2CA5, END + 2, count=200000, timeout=2000000)
    assert pcs[-1] == END, hex(pcs[-1])
    assert bytes(u.mem_read(0, len(b))) == b
    assert not writes
    actual = [x[2] for x in logs if "Override UclkDiv1 M0" in x[1]]
    assert actual == expected, (name, actual, expected)
    r = {
        "case": name,
        "changed_apcb_offsets": [
            hex(i) for i, (a, z) in enumerate(zip(apcb, active_apcb)) if a != z
        ],
        "m0_log": actual,
        "instructions": len(pcs),
        "tokens": tokens,
        "source_reads": reads,
        "context_writes": writes,
        "logs": logs,
        "code_unchanged": True,
        "scope": "native phase2 with modeled context/APCB placement, logging intercepted, no hardware",
    }
    results.append(r)
    print(
        f"{name}: M0_log={actual} context_writes={len(writes)} actuator_callbacks=0 services=0 returned=True"
    )
(D / "cases-result.json").write_text(json.dumps(results, indent=2) + "\n")
print("PASS 5 native UclkDiv1 phase cases; no divider actuation on this path")
