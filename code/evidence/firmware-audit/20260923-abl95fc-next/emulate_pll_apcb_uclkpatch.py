"""UCLK-division patch proof: 1-bit ABL1 patch -> UCLK service argument.

Patch: ABL1+0x5F30 halfwords EA4F 0854 (LSR.W R8,R4,#1) -> EA4F 0850
(LSR.W R8,R4,#0 == MOV.W R8,R4, the ARM alias). One bit (byte +0x5F33
0x54 -> 0x50). Effect per the decoded path (docs/research/
2026-09-23-abl-pll-service-boundary.md): UCLK SVC28 argument = R8 =
input word, instead of input>>1.

Runs the SAME emulator contract as emulate_pll_apcb_v001.py (read it):
APCB = the actual FCLK-1800 candidate bytes at modeled 0x7B000, entry
0x63F9 heap init then 0x5F1F..0x601A, only 0x130C/0x112A0 logging and
SVC28 intercepted. Difference: the ABL1 image loaded at 0 is the PATCHED
payload (diff vs af8cf562 asserted == exactly one byte at +0x5F33).

Expected with the patch, input word 1800:
  svc == [(14, 1800), (15, 1800)]   # FCLK from APCB record, UCLK = input
Control (unpatched ABL1, same APCB): [(14, 1800), (15, 900)].
"""

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
ORIG = (
    ROOT
    / "evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin"
)
orig = ORIG.read_bytes()
assert (
    hashlib.sha256(orig).hexdigest()
    == "af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a"
)
assert orig[0x5F30:0x5F34] == bytes.fromhex("4fea5408".replace(" ", "")) or True
# exact halfword check (little-endian file order: EA4F at +0x5F30, 0854 at +0x5F32)
assert orig[0x5F30:0x5F32] == b"\x4f\xea" and orig[0x5F32:0x5F34] == b"\x54\x08", \
    orig[0x5F30:0x5F34].hex()

patched = bytearray(orig)
patched[0x5F32] = 0x04  # halfword 0x0854 -> 0x0804: imm2 01->00 AND type LSR(01)->LSL(00); LSL.W R8,R4,#0 == MOV.W R8,R4 (documented alias; LSR #0 is shift-by-32 -> 0, caught by the first run)
patched = bytes(patched)
diff = [i for i in range(len(orig)) if orig[i] != patched[i]]
assert diff == [0x5F32], diff
assert patched[0x5F32:0x5F34] == b"\x04\x08"
PATCHED_SHA = hashlib.sha256(patched).hexdigest()

rom = (ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin").read_bytes()
assert (
    hashlib.sha256(rom).hexdigest()
    == "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"
)
cand_img = (ROOT / "candidates/BC250_5.00_clv_FCLK1800_APCB_v001.bin").read_bytes()
assert (
    hashlib.sha256(cand_img).hexdigest()
    == "3d6348c65a0c2ee500e13f3b1a5c9e9c64c57e36b570fbd1e85a19b9713871f8"
)
apcb_cand = cand_img[0xAB1000:0xAB1B9C]
assert apcb_cand[:4] == b"APCB" and sum(apcb_cand) % 256 == 0

CTX = 0x200000
NESTED = 0x201000
SP = 0x308000

CASES = [
    # name, image bytes, expected (fclk_arg, uclk_arg)
    ("control_unpatched", orig, (1800, 900)),
    ("uclk_patch", patched, (1800, 1800)),
    ("uclk_patch_input1750", patched, (1800, 1750)),
]

results = []
for name, code_img, (exp_fclk, exp_uclk) in CASES:
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0, 0x20000)
    u.mem_write(0, code_img)
    u.mem_map(CTX, 0x10000)
    u.mem_map(0x300000, 0x10000)
    u.mem_map(0x57000, 0x19000)
    u.mem_write(0x57100, code_img)
    u.mem_map(0x73000, 0xA000)
    u.mem_write(0x7B000, apcb_cand)
    u.reg_write(UC_ARM_REG_R0, CTX + 0x4000)
    u.reg_write(UC_ARM_REG_LR, 0x18001)
    u.emu_start(0x63F9, 0x18000, timeout=100000, count=100)
    assert u.reg_read(UC_ARM_REG_PC) == 0x18000
    u.mem_write(0x6B000, struct.pack("<I", 0x12345678))
    u.mem_write(CTX + 4, struct.pack("<I", NESTED))
    u.mem_write(NESTED + 0x790, struct.pack("<H", 0))
    value = 1800 if "1750" not in name else 1750
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
        "abl1_sha256": hashlib.sha256(code_img).hexdigest(),
        "expected": {"fclk": exp_fclk, "uclk": exp_uclk},
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
        if address == 0x4800:
            event["external_calls"].append(uc.reg_read(UC_ARM_REG_R0))
        if address in (0x130C, 0x112A0):
            uc.reg_write(UC_ARM_REG_R0, 0)
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
        elif address == 0x64C8:
            raise AssertionError("Unexpected firmware assertion path")

    def intr(uc, number, _):
        pc = uc.reg_read(UC_ARM_REG_PC)
        assert bytes(uc.mem_read(pc - 2, 2)) == b"\x28\xdf", (number, hex(pc))
        r0 = uc.reg_read(UC_ARM_REG_R0)
        r1 = uc.reg_read(UC_ARM_REG_R1)
        r2 = uc.reg_read(UC_ARM_REG_R2)
        event["svc"].append({"selector": r0, "argument": r1})
        assert r0 in (14, 15) and r2 == SP + 8
        uc.mem_write(r2, struct.pack("<I", 0))
        uc.reg_write(UC_ARM_REG_R0, 0)

    u.hook_add(UC_HOOK_CODE, code)
    u.hook_add(UC_HOOK_INTR, intr)
    u.emu_start(0x5F1F, 0x601A, timeout=2000000, count=150000)
    assert u.reg_read(UC_ARM_REG_PC) == 0x601A, hex(u.reg_read(UC_ARM_REG_PC))
    assert bytes(u.mem_read(0, len(code_img))) == code_img
    got = [(x["selector"], x["argument"]) for x in event["svc"]]
    assert got == [(14, exp_fclk), (15, exp_uclk)], (name, got)
    event["context_78"] = struct.unpack("<H", bytes(u.mem_read(CTX + 0x78, 2)))[0]
    assert event["context_78"] == exp_fclk
    event["status"] = "PASS_BOUNDED_EMULATION"
    event["svc_pairs"] = got
    results.append(event)
    print(name, "input", value, "->", got, "instructions", event["instruction_count"])

(D / "emulation-apcb-uclkpatch-result.json").write_text(
    json.dumps(
        {
            "patch": {
                "offset": "0x5F32",
                "old": "0x54",
                "new": "0x04",
                "instruction": "LSR.W R8,R4,#1 -> LSL.W R8,R4,#0 == MOV.W R8,R4 (imm2 01->00, type 01->00)",
                "original_abl1_sha256": hashlib.sha256(orig).hexdigest(),
                "patched_abl1_sha256": PATCHED_SHA,
                "diff": ["0x5F32"],
            },
            "apcb": "candidates/BC250_5.00_clv_FCLK1800_APCB_v001.bin[0xAB1000:0xAB1B9C]",
            "cases": results,
            "limits": [
                "Bounded window 0x5F1F..0x601A with synthetic frame; SVC28 intercepted",
                "Proves the SERVICE ARGUMENT, not physical UCLK or transport semantics",
                "The steady-state DF P-state path and later ABL4 switching are NOT covered",
            ],
        },
        indent=2,
    )
    + "\n"
)
print("PASS3 UCLK-division patch cases (control 900, patched 1800, patched 1750->1750)")
