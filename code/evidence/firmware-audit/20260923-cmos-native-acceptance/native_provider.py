"""Execute native221C with pristine APCB and modeled CMOS context, no hardware."""

import hashlib
import json
import struct
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
rom = (ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin").read_bytes()
assert (
    hashlib.sha256(rom).hexdigest()
    == "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"
)
apcb = rom[0xAB1000:0xAB1B9C]
assert apcb[:4] == b"APCB" and sum(apcb) % 256 == 0
for name, clock, valid, enum, expected in [
    ("BASELINE", 1750, 1, 0x24, 1800),
    ("MODIFIED_INPUT", 1650, 1, 0x24, 1800),
    ("RESTORED_INPUT", 1750, 1, 0x24, 1800),
    ("INVALID_CMOS", 1650, 0, 0x24, 1800),
    ("MODIFIED_APCB", 1650, 1, 0x23, 1750),
    ("RESTORED_APCB", 1650, 1, 0x24, 1800),
]:
    active_apcb = bytearray(apcb)
    active_apcb[0x482] = enum
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
    source_reads = []

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
        if address == NEST + 0x2C:
            writes.append(value)

    def read(mu, access, address, size, value, data):
        if 0x7B000 <= address < 0x7BB9C:
            source_reads.append(
                [
                    hex(mu.reg_read(UC_ARM_REG_PC)),
                    hex(address - 0x7B000),
                    size,
                    bytes(mu.mem_read(address, size)).hex(),
                ]
            )

    u.hook_add(UC_HOOK_MEM_READ, read)
    u.hook_add(UC_HOOK_CODE, code)
    u.hook_add(UC_HOOK_MEM_WRITE, write)
    u.emu_start(0x221D, END + 2, count=150000, timeout=2000000)
    value = struct.unpack("<I", u.mem_read(NEST + 0x2C, 4))[0]
    assert pcs[-1] == END and calls == [[7, 2]], (name, value, hex(pcs[-1]))
    assert bytes(u.mem_read(0, len(b))) == b
    assert value == expected and writes == ([clock, expected] if valid else [expected])
    rows.append(
        {
            "case": name,
            "cmos_clock": clock,
            "valid": valid,
            "provider": "native APCB",
            "apcb_enum": enum,
            "apcb_changed_offsets": [
                hex(i) for i, (x, y) in enumerate(zip(apcb, active_apcb)) if x != y
            ],
            "result": value,
            "writes": writes,
            "provider_calls": calls,
            "source_reads": source_reads,
        }
    )
    print(
        f"{name}: CMOS={clock} valid={valid} native_provider=APCB enum={enum} writes={writes} final_policy={value}"
    )
(D / "native-provider-result.json").write_text(
    json.dumps(
        {
            "scope": "native221C phase2; pristine APCB in modeled memory; no hardware",
            "cases": rows,
        },
        indent=2,
    )
    + "\n"
)
assert rows[0]["result"] == rows[2]["result"]
print(
    "PASS 6 native APCB provider cases; APCB+482 overrides CMOS clock; code unchanged"
)
