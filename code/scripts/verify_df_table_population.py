#!/usr/bin/env python3
import struct
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM_PATH = ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin"
SMU_PATH = (
    ROOT
    / "archives/imported/vendor-upstream/legacy-tmp-bc250-upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5"
)

EXPECTED_ROM_SHA = "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"
EXPECTED_SMU_SHA = "cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37"
SMU_OFFSET = 0x8FEF00
SMU_SIZE = 262400


def main():
    rom_data = ROM_PATH.read_bytes()
    rom_sha = hashlib.sha256(rom_data).hexdigest()
    assert rom_sha == EXPECTED_ROM_SHA
    smu_from_rom = rom_data[SMU_OFFSET : SMU_OFFSET + SMU_SIZE]
    smu_data = SMU_PATH.read_bytes()
    smu_sha = hashlib.sha256(smu_data).hexdigest()
    assert smu_sha == EXPECTED_SMU_SHA
    assert smu_from_rom == smu_data

    expected_rates = [
        (250.0, 225.0, 112.5),
        (250.0, 225.0, 112.5),
        (750.0, 425.0, 106.25),
        (1200.0, 875.0, 109.375),
        (150.0, 125.0, 125.0),
    ]

    for pstate, (exp_fclk, exp_uclk, exp_soc) in enumerate(expected_rates):
        row_offset = 0xCF0C + pstate * 40
        row = smu_data[row_offset : row_offset + 40]
        fclk = struct.unpack("<f", row[4:8])[0]
        uclk = struct.unpack("<f", row[16:20])[0]
        soc = struct.unpack("<f", row[20:24])[0]
        assert fclk == exp_fclk
        assert uclk == exp_uclk
        assert soc == exp_soc

    header = smu_data[0xCEE0:0xCF0C]
    assert header == b"\x00" * 0x2C

    idx_cf80 = smu_data[0xCF80:0xCF84]
    idx_cfd0 = smu_data[0xCFD0:0xCFD4]
    assert idx_cf80 == bytes([3, 2, 1, 0])
    assert idx_cfd0 == bytes([0, 255, 255, 255])

    ptrs = [0xCF0C + idx * 40 for idx in idx_cf80]
    assert ptrs == [0xCF84, 0xCF5C, 0xCF34, 0xCF0C]

    lit_171ec = struct.unpack("<I", smu_data[0x171EC:0x171F0])[0]
    assert lit_171ec == 0xCEE0

    callback_bytes = smu_data[0x1BC80:0x1BCE0]
    assert b"\x1c\xed" in callback_bytes

    print(
        "VERIFIER_RESULT: BOUNDED_STATIC_CHECKS_PASSED (static binary coverage only, does not prove runtime/indirect/DMA write isolation)"
    )


if __name__ == "__main__":
    main()
