#!/usr/bin/env python3
"""Bounded static check of the exact CLV $INV parser/sign boundary."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ROM = ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin"
CODE = ROOT / "evidence/firmware-audit/20260919-inv-token-consumers/AmdFabricAriPei-c5b99650a442-0.code"
ASM = ROOT / "evidence/firmware-audit/20260919-inv-token-consumers/AmdFabricAriPei-c5b99650a442-0.asm"
ROWS = ROOT / "evidence/firmware-audit/20260919-inv-token-consumers/AmdFabricAriPei-c5b99650a442.instructions.json"
OUT = Path(__file__).resolve().parent / "offset-consumer-next-result.json"
EXPECTED_ROM = "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"
# The retained .code section begins at image RVA 0x240; its file offset is RVA-0x240.
CODE_RVA_BASE = 0x240

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def fail(msg: str):
    raise AssertionError(msg)

def get_code(rva: int, n: int) -> bytes:
    off = rva - CODE_RVA_BASE
    if off < 0 or off + n > len(code):
        fail(f"RVA outside code section: {rva:#x}+{n:#x}")
    return code[off:off+n]

def find_row(rva: int):
    for row in rows:
        if row.get("rva") == rva:
            return row
    fail(f"instruction row not found: {rva:#x}")

def u32_parser(value: int) -> tuple[int, int]:
    """Model exact type-2 branch: mov eax,[payload]; xor output high dword."""
    low = value & 0xffffffff
    high = 0
    return low, high

def u8_or_u16_parser(value: int, width: int) -> tuple[int, int]:
    """Model exact MOVZX + CDQ branch; MOVZX makes EAX non-negative."""
    low = value & ((1 << (width * 8)) - 1)
    high = 0
    return low, high

rom = ROM.read_bytes()
code = CODE.read_bytes()
rows = json.loads(ROWS.read_text(encoding="utf-8"))
checks = []
def check(name, actual, expected):
    ok = actual == expected
    checks.append({"name": name, "ok": ok, "actual": actual, "expected": expected})
    if not ok:
        fail(f"{name}: {actual!r} != {expected!r}")

check("rom_size", len(rom), 0x1000000)
check("rom_sha256", sha(ROM), EXPECTED_ROM)
check("amd_fabric_code_size", len(code), 92512)
check("amd_fabric_code_sha256", sha(CODE), "2a32fef056825e8f201db78402e0303f9541aa90013df2e56c78550c5a3f2db9")
check("amd_fabric_assembly_sha256", sha(ASM), "9c4744e1129052c965828694995bc60b250ce4bdb66d858584d090ea092b9f95")
check("amd_fabric_instruction_rows_sha256", sha(ROWS), "77b1d4be4393fbbf920847398ae5667c42b3841066d40c2aaace1b49036c81e1")

# Producer boundary: 0x1364 is a type-2 (four-byte) record copied from +0x6E6.
check("producer_0x1364_mov", get_code(0x11956, 5).hex(), "ba64130000")
check("producer_0x1364_type_flag", get_code(0x1196a, 3).hex(), "80ca02")
check("producer_0x1364_payload_load", get_code(0x11979, 6).hex(), "8b82e6060000")
check("producer_0x1364_payload_store", get_code(0x1197f, 3).hex(), "894103")
check("producer_0x1363_control_mov", get_code(0x11924, 5).hex(), "ba63130000")
check("producer_0x1363_control_load", get_code(0x11944, 6).hex(), "8a82e5060000")

# Generic reader byte window. The switch is driven by record[2] & 3. Type 2
# loads four bytes at record+3 and explicitly clears the output high dword;
# type 0/1 execute MOVZX before CDQ, so those paths also cannot sign extend.
check("reader_entry", get_code(0x1d3c, 6).hex(), "558bec83ec24")
check("reader_nvtb_magic_load", get_code(0x1d4d, 5).hex(), "bb4e565442")
check("reader_inv_magic_check", get_code(0x1dfc, 6).hex(), "813e24494e56")
check("reader_type_load", get_code(0x1e16, 7).hex(), "0fb6460283e003")
check("reader_type2_load", get_code(0x1e47, 7).hex(), "8b460383670400")
check("reader_type2_stride", get_code(0x1e4e, 2).hex(), "6a07")
check("reader_type1_movzx", get_code(0x1e52, 6).hex(), "0fb746036a05")
check("reader_type0_movzx_cdq", get_code(0x1e5a, 12).hex(), "0fb646036a04998957048907")
check("reader_type1_shared_cdq_store", get_code(0x1e60, 6).hex(), "998957048907")
check("reader_token_compare", get_code(0x1e67, 9).hex(), "668b06663b4508740c")

# Focused local caller windows only: these are the two calls to this reader in
# AmdFabricAriPei, not a repeated corpus-wide token census.
check("caller_1_requested_id", get_code(0x1eb0, 5).hex(), "68ff100000")
check("caller_1_reader_call", get_code(0x1ebd, 5).hex(), "e87afeffff")
check("caller_2_requested_id", get_code(0x1f8b, 5).hex(), "6804110000")
check("caller_2_reader_call", get_code(0x1f94, 5).hex(), "e8a3fdffff")
reader_call_sites = sorted(
    row["rva"] for row in rows
    if row.get("mnemonic") == "call" and row.get("operands", "").lower() == "0x1d3c"
)
check("module_local_direct_reader_calls", reader_call_sites, [0x1ebd, 0x1f94])

# Host-only model of the exact operations, with high-bit controls. This is a
# semantic check of decoded instructions, not an execution of firmware.
check("type2_zero_extension_high_bit", u32_parser(0x80000000), (0x80000000, 0))
check("type2_zero_extension_all_ones", u32_parser(0xffffffff), (0xffffffff, 0))
check("type1_movzx_high_bit", u8_or_u16_parser(0x8000, 2), (0x8000, 0))
check("type0_movzx_high_bit", u8_or_u16_parser(0x80, 1), (0x80, 0))

result = {
    "status": "STATIC_PARSER_BOUNDARY_ONLY",
    "checks": checks,
    "check_count": len(checks),
    "target": {
        "rom": str(ROM),
        "rom_size": len(rom),
        "rom_sha256": sha(ROM),
        "code": str(CODE),
        "code_sha256": sha(CODE),
        "code_rva_base": hex(CODE_RVA_BASE),
        "assembly": str(ASM),
        "instruction_rows": str(ROWS),
    },
    "producer": {
        "control_field": "AmdSetup+0x6E5",
        "control_record": "0x1363",
        "value_field": "AmdSetup+0x6E6",
        "value_record": "0x1364",
        "value_record_type_low_bits": 2,
        "value_payload_width": 4,
        "copy_is_unchanged": True,
    },
    "reader": {
        "module": "AmdFabricAriPei",
        "entry_rva": "0x1d3c",
        "record_marker": "$INV",
        "type2_operation": "mov eax,[record+3]; mov [out+0],eax; and dword ptr [out+4],0",
        "type01_operation": "movzx eax,[record+3]; cdq; mov [out+4],edx",
        "1364_signed_conversion": False,
        "direct_callers": [
            {"caller_rva": "0x1eb0", "requested_record": "0x10ff", "call_rva": "0x1ebd"},
            {"caller_rva": "0x1f8b", "requested_record": "0x1104", "call_rva": "0x1f94"},
        ],
        "local_direct_1364_call": False,
    },
    "interpretation": {
        "observed": "The exact generic parser's type-2 branch zero-extends the 32-bit payload into its 64-bit output pair; the two direct callers pass 0x10FF and 0x1104, not 0x1364.",
        "not_observed": "No final voltage consumer, rail selection, mV/sign convention at the actuator, or hardware application.",
        "rail_scope": "AmdSetup+0x6E6 is retained as VDDCR_VDD-labelled offset field; no SoC or GFX equivalence is inferred. AmdSetup+0x6EA/+0x6EB remains the separate GFX-labelled pair.",
    },
}
OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"status": result["status"], "checks": len(checks), "output": str(OUT)}, sort_keys=True))
