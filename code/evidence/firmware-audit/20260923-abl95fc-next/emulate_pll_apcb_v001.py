"""Run the real shipped FCLK-1800 candidate APCB bytes through the
preserved native ABL1 PLL builder (2026-09-24, O-F1 close attempt).

Same emulator contract as emulate_pll_apcb.py (read it first):
- ABL1-clv sha-pinned, clean clv ROM sha-pinned, Thumb, entry 0x63F9
  heap init then 0x5F1F..0x601A builder path.
- Only 0x130C/0x112A0 logging and SVC#0x28 intercepted (fixtures).
- Code bytes asserted unchanged; APCB asserted sum%256==0.

Difference: the APCB at modeled 0x7B000 is the ACTUAL candidate image
slice candidates/BC250_5.00_clv_FCLK1800_APCB_v001.bin[0xAB1000:0xAB1B9C]
for the candidate cases, written as-is (no in-memory patch), so a PASS
validates the exact shipped bytes, not a re-derivation.

Cases:
- control_clean:   clean base APCB as-is          -> expect FCLK arg 1420
- candidate_v001:  candidate v001 APCB as-is      -> expect FCLK arg 1800
- cand_gate_off:   candidate with gate 0 + chk    -> expect FCLK arg 1200
                   (gate still governs the record; token 0x160 not queried)
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
rom = (ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin").read_bytes()
assert (
    hashlib.sha256(rom).hexdigest()
    == "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"
)
apcb_clean = rom[0xAB1000:0xAB1B9C]
assert apcb_clean[:4] == b"APCB" and sum(apcb_clean) % 256 == 0
assert apcb_clean[0xB99:0xB9C] == bytes.fromhex("018c05")

cand_img = (
    ROOT / "candidates/BC250_5.00_clv_FCLK1800_APCB_v001.bin"
).read_bytes()
assert (
    hashlib.sha256(cand_img).hexdigest()
    == "3d6348c65a0c2ee500e13f3b1a5c9e9c64c57e36b570fbd1e85a19b9713871f8"
)
apcb_cand = cand_img[0xAB1000:0xAB1B9C]
assert apcb_cand[:4] == b"APCB" and sum(apcb_cand) % 256 == 0
assert apcb_cand[0xB99] == 0x01, "gate must stay 1 in the candidate"
assert struct.unpack_from("<H", apcb_cand, 0xB9A)[0] == 1800
# the candidate slice differs from clean ONLY at the value+checksum bytes
diff = [i for i in range(len(apcb_clean)) if apcb_clean[i] != apcb_cand[i]]
assert diff == [0x10, 0xB9A, 0xB9B], diff

CASES = [
    # name, input word, nested+0x790, expected FCLK service argument
    ("control_clean", 1800, 0, 1420),
    ("candidate_v001", 1800, 0, 1800),
    ("cand_gate_off", 1800, 0, 1200),
]

results = []
for name, value, chip, expected_fclk in CASES:
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0, 0x20000)
    u.mem_write(0, b)
    u.mem_map(CTX, 0x10000)
    u.mem_map(0x300000, 0x10000)
    u.mem_map(0x57000, 0x19000)
    u.mem_write(0x57100, b)
    u.mem_map(0x73000, 0xA000)
    if name == "control_clean":
        apcb = bytearray(apcb_clean)
        base_copy = apcb_clean
    elif name == "candidate_v001":
        apcb = bytearray(apcb_cand)
        base_copy = apcb_cand
    else:  # cand_gate_off: candidate bytes with gate forced 0 + checksum
        apcb = bytearray(apcb_cand)
        apcb[0xB99] = 0
        apcb[0x10] = 0
        apcb[0x10] = (-sum(apcb)) & 255
        assert sum(apcb) % 256 == 0
        base_copy = bytes(apcb)
    u.mem_write(0x7B000, bytes(apcb))
    u.reg_write(UC_ARM_REG_R0, CTX + 0x4000)
    u.reg_write(UC_ARM_REG_LR, 0x18001)
    u.emu_start(0x63F9, 0x18000, timeout=100000, count=100)
    assert u.reg_read(UC_ARM_REG_PC) == 0x18000
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
        "expected_fclk_arg": expected_fclk,
        "apcb_source_sha256": hashlib.sha256(base_copy).hexdigest(),
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
        if address == 0x4800:
            event["external_calls"].append(
                {
                    "address": "0x4800",
                    "r0": uc.reg_read(UC_ARM_REG_R0),
                    "native_executed": True,
                }
            )
        if address in (0x130C, 0x112A0):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            call = {"address": hex(address), "r0": r0, "r1": r1}
            event["external_calls"].append(call)
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
        u.emu_start(0x5F1F, 0x601A, timeout=2000000, count=150000)
        assert u.reg_read(UC_ARM_REG_PC) == 0x601A, hex(u.reg_read(UC_ARM_REG_PC))
        assert bytes(u.mem_read(0, len(b))) == b
        assert [(x["selector"], x["argument"]) for x in event["svc"]] == [
            (14, expected_fclk),
            (15, value >> 1),
        ], event
        event["context_78"] = struct.unpack("<H", bytes(u.mem_read(CTX + 0x78, 2)))[0]
        assert event["context_78"] == expected_fclk
        event["code_bytes_unchanged"] = True
        # for the as-is cases the emulator must not have altered the record
        run_apcb = bytes(u.mem_read(0x7B000, len(base_copy)))
        event["apcb_in_emulator_unchanged"] = run_apcb == base_copy
        assert run_apcb == base_copy
        token_calls = [
            x["r0"] for x in event["external_calls"] if x["address"] == "0x4800"
        ]
        assert token_calls == (
            [0x15F] if name == "cand_gate_off" else [0x15F, 0x160]
        ), token_calls
        event["token_calls"] = token_calls
        event["status"] = "PASS_BOUNDED_EMULATION"
    except Exception as ex:
        event["status"] = "ERROR"
        event["error"] = repr(ex)
        event["pc"] = hex(u.reg_read(UC_ARM_REG_PC))
        results.append(event)
        (D / "emulation-apcb-v001-result.json").write_text(
            json.dumps(results, indent=2) + "\n"
        )
        raise
    results.append(event)
    print(
        name,
        "input",
        value,
        "->",
        [(x["selector"], x["argument"]) for x in event["svc"]],
        "tokens",
        event["token_calls"],
        "instructions",
        event["instruction_count"],
    )

(D / "emulation-apcb-v001-result.json").write_text(
    json.dumps(
        {
            "candidate_image": "candidates/BC250_5.00_clv_FCLK1800_APCB_v001.bin",
            "candidate_image_sha256": hashlib.sha256(cand_img).hexdigest(),
            "abl1_sha256": hashlib.sha256(b).hexdigest(),
            "base_rom_sha256": hashlib.sha256(rom).hexdigest(),
            "cases": results,
            "limits": [
                "Start at 0x5F1F with synthetic frame, not full boot",
                "0x130C/0x112A0 logging and SVC28 intercepted with fixtures; no hardware",
                "APCB placed at modeled 0x7B000 per ABL0 SVC2D evidence; loader/overlay itself not executed",
                "No proof of physical MHz, SVC28 transport semantics, or 1:1:1",
                "Code bytes unchanged in every emulator instance",
            ],
        },
        indent=2,
    )
    + "\n"
)
print(
    "PASS3 candidate-bytes-to-PLL cases (control 1420, candidate 1800, gate-off 1200)"
)
