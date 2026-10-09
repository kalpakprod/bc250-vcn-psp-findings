"""Locate first external dependency of unchanged4800->49CC lookup. Not boot."""

import hashlib
import json
import struct
from pathlib import Path
from unicorn import (
    Uc,
    UcError,
    UC_ARCH_ARM,
    UC_MODE_THUMB,
    UC_HOOK_CODE,
    UC_HOOK_INTR,
    UC_HOOK_MEM_INVALID,
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

ROOT = Path(__file__).resolve().parents[3]
D = Path(__file__).resolve().parent
b = (
    ROOT
    / "evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin"
).read_bytes()
assert (
    hashlib.sha256(b).hexdigest()
    == "af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a"
)
u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
u.mem_map(0, 0x20000)
u.mem_write(0, b)
# Separate read image for embedded absolute data pointers. Conditional base, not loader proof.
u.mem_map(0x57000, 0x19000)
u.mem_write(0x57100, b)
u.mem_map(0x73000, 0xA000)
# Execute native empty-arena initializer rather than invent its layout.
rom = (ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin").read_bytes()
assert (
    hashlib.sha256(rom).hexdigest()
    == "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"
)
apcb = rom[0xAB1000:0xAB3000]
assert apcb[:4] == b"APCB"
u.mem_write(0x7B000, apcb)
u.mem_map(0x300000, 0x10000)
u.mem_map(0x200000, 0x10000)
SP = 0x308000
u.reg_write(UC_ARM_REG_R0, 0x200200)
u.reg_write(UC_ARM_REG_LR, 0x18001)
u.emu_start(0x63F9, 0x18000, timeout=100000, count=100)
assert u.reg_read(UC_ARM_REG_PC) == 0x18000
for reg, val in [
    (UC_ARM_REG_R0, 0x15F),
    (UC_ARM_REG_R1, 15),
    (UC_ARM_REG_R2, 0x200000),
    (UC_ARM_REG_R3, 0x200100),
    (UC_ARM_REG_SP, SP),
    (UC_ARM_REG_LR, 0x18001),
]:
    u.reg_write(reg, val)
u.mem_write(SP, struct.pack("<I", 0))
e = {
    "assumptions": [
        "raw instruction execution at0, separate data image alias at conditional57100",
        "synthetic output pointers and stack, no whole-boot state",
    ],
    "events": [],
    "instructions": 0,
    "last_pcs": [],
}


def code(uc, a, size, _):
    e["instructions"] += 1
    e["last_pcs"] = (e["last_pcs"] + [hex(a)])[-25:]
    if a in (0x4800, 0x49CC, 0x6374, 0x6238, 0x1270, 0x4E4C):
        e["events"].append({"entered": hex(a)})
    if a == 0x4C0E:
        e["events"].append(
            {
                "value_source_base": hex(uc.reg_read(UC_ARM_REG_R0)),
                "value_source_offset": uc.reg_read(UC_ARM_REG_R2),
            }
        )
    if a in (0x130C, 0x112A0):
        uc.reg_write(UC_ARM_REG_R0, 0)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
    if a == 0x64C8:
        e["boundary"] = {"kind": "firmware-assertion", "pc": hex(a)}
        uc.emu_stop()


def intr(uc, n, _):
    pc = uc.reg_read(UC_ARM_REG_PC)
    e["boundary"] = {
        "kind": "svc-unmodeled",
        "pc": hex(pc - 2),
        "opcode": bytes(uc.mem_read(pc - 2, 2)).hex(),
    }
    uc.emu_stop()


def invalid(uc, access, a, size, value, _):
    e["boundary"] = {
        "kind": "unmapped-memory",
        "access": access,
        "address": hex(a),
        "size": size,
        "pc": hex(uc.reg_read(UC_ARM_REG_PC)),
    }
    return False


u.hook_add(UC_HOOK_CODE, code)
u.hook_add(UC_HOOK_INTR, intr)
u.hook_add(UC_HOOK_MEM_INVALID, invalid)
try:
    u.emu_start(0x4801, 0x18000, timeout=2000000, count=150000)
except UcError as err:
    e["emulator_error"] = str(err)
e["first_lookup"] = {
    "token": "0x15f",
    "status": u.reg_read(UC_ARM_REG_R0),
    "value_hex": bytes(u.mem_read(0x200000, 8)).hex(),
}
if u.reg_read(UC_ARM_REG_PC) == 0x18000:
    for reg, val in [
        (UC_ARM_REG_R0, 0x160),
        (UC_ARM_REG_R1, 15),
        (UC_ARM_REG_R2, 0x200000),
        (UC_ARM_REG_R3, 0x200100),
        (UC_ARM_REG_SP, SP),
        (UC_ARM_REG_LR, 0x18001),
    ]:
        u.reg_write(reg, val)
    u.mem_write(0x200000, b"\x00" * 8)
    u.emu_start(0x4801, 0x18000, timeout=2000000, count=150000)
    e["second_lookup"] = {
        "token": "0x160",
        "status": u.reg_read(UC_ARM_REG_R0),
        "value_hex": bytes(u.mem_read(0x200000, 8)).hex(),
    }
e["pc"] = hex(u.reg_read(UC_ARM_REG_PC))
e["returned_r0"] = u.reg_read(UC_ARM_REG_R0)
e["apcb_source"] = "clean ROM0xAB1000 copied to modeled runtime7B000"
e["output_hex"] = bytes(u.mem_read(0x200000, 8)).hex()
e["original_instruction_image_unchanged"] = bytes(u.mem_read(0, len(b))) == b
assert e["original_instruction_image_unchanged"]
if "boundary" not in e:
    e["boundary"] = {
        "kind": "return" if u.reg_read(UC_ARM_REG_PC) == 0x18000 else "budget-stop"
    }
(D / "cold-provider-result.json").write_text(json.dumps(e, indent=2) + "\n")
print(json.dumps({k: v for k, v in e.items() if k != "events"}, indent=2))
print("events", e["events"][:20])
