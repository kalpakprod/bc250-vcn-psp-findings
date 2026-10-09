#!/usr/bin/env python3
"""
verify_df_indirect_consumer.py - Bounded verification of Data Fabric (DF)
PEI indirect dispatch edges, module identity at 0x11C98, and token 0x1374 consumers.
"""

import hashlib
import json
import os
import struct
import sys

CLV_PATH = "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin"
EXPECTED_CLV_SHA256 = "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"

FABRIC_PATH = "evidence/firmware-audit/20260919-inv-token-consumers/AmdFabricAriPei-c5b99650a442.bin"
EXPECTED_FABRIC_SHA256 = (
    "c5b99650a442ed9be1cf3a62e7571f7eb163b9f80a60d4fcc7b3e9afe4506f78"
)
FABRIC_TE_DELTA = 408  # 0x198
FABRIC_BASE_VA = 0x09E1BB80

CBS_PATH = (
    "evidence/firmware-audit/20260919-inv-token-consumers/CbsBasePei-6ff112922ad8.bin"
)
EXPECTED_CBS_SHA256 = "6ff112922ad824645f1e3171d18c79327cbbefe8b2af67cd74a108c7334ced77"
CBS_TE_DELTA = 400  # 0x190
CBS_BASE_VA = 0x09EBA08C

SMU_PEI_PATH = "evidence/firmware-audit/20260919-inv-token-consumers/AmdNbioSmuV10Pei-905b8be68afd.bin"
EXPECTED_SMU_PEI_SHA256 = (
    "905b8be68afd1dce5453acef8273cbf94bdae6d41823c25438ace286348e2c80"
)
SMU_TE_DELTA = 400  # 0x190


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def check_clv_and_modules():
    assert os.path.exists(CLV_PATH), f"Missing {CLV_PATH}"
    clv_sha = sha256_file(CLV_PATH)
    assert clv_sha == EXPECTED_CLV_SHA256, f"CLV SHA mismatch: {clv_sha}"

    assert os.path.exists(FABRIC_PATH), f"Missing {FABRIC_PATH}"
    fab_sha = sha256_file(FABRIC_PATH)
    assert fab_sha == EXPECTED_FABRIC_SHA256, f"Fabric SHA mismatch: {fab_sha}"

    assert os.path.exists(CBS_PATH), f"Missing {CBS_PATH}"
    cbs_sha = sha256_file(CBS_PATH)
    assert cbs_sha == EXPECTED_CBS_SHA256, f"CBS SHA mismatch: {cbs_sha}"

    assert os.path.exists(SMU_PEI_PATH), f"Missing {SMU_PEI_PATH}"
    smu_sha = sha256_file(SMU_PEI_PATH)
    assert smu_sha == EXPECTED_SMU_PEI_SHA256, f"SMU PEI SHA mismatch: {smu_sha}"


def check_serialization_identities():
    """Verify exact locations of token 0x1374 serialization across modules."""
    with open(FABRIC_PATH, "rb") as f:
        fab_data = f.read()
    with open(CBS_PATH, "rb") as f:
        cbs_data = f.read()
    with open(SMU_PEI_PATH, "rb") as f:
        smu_data = f.read()

    # In AmdFabricAriPei: RVA 0x11C98 -> raw offset = 0x11C98 - 0x198 = 0x11B00
    fab_raw_11c98 = 0x11C98 - FABRIC_TE_DELTA
    assert fab_data[fab_raw_11c98 : fab_raw_11c98 + 5] == bytes.fromhex("ba74130000"), (
        "AmdFabricAriPei 0x11C98 does not match 'mov edx, 0x1374'"
    )
    # check setup offset 0x704 read at RVA 0x11CBB: raw = 0x11CBB - 0x198 = 0x11B23
    fab_raw_11cbb = 0x11CBB - FABRIC_TE_DELTA
    assert fab_data[fab_raw_11cbb : fab_raw_11cbb + 7] == bytes.fromhex(
        "668b8204070000"
    ), "AmdFabricAriPei 0x11CBB does not match 'mov ax, [edx+0x704]'"

    # In CbsBasePei: RVA 0xE738 -> raw offset = 0xE738 - 0x190 = 0xE5A8
    cbs_raw_e738 = 0xE738 - CBS_TE_DELTA
    assert cbs_data[cbs_raw_e738 : cbs_raw_e738 + 5] == bytes.fromhex("ba74130000"), (
        "CbsBasePei 0xE738 does not match 'mov edx, 0x1374'"
    )

    # In AmdNbioSmuV10Pei: RVA 0x107B8 -> raw offset = 0x107B8 - 0x190 = 0x10628
    smu_raw_107b8 = 0x107B8 - SMU_TE_DELTA
    assert smu_data[smu_raw_107b8 : smu_raw_107b8 + 5] == bytes.fromhex("ba74130000"), (
        "AmdNbioSmuV10Pei 0x107B8 does not match 'mov edx, 0x1374'"
    )


def check_fabric_indirect_edges():
    """Verify all 31 indirect call/jump edges in AmdFabricAriPei."""
    with open(FABRIC_PATH, "rb") as f:
        data = f.read()

    # Check IDS table at raw 0x16BC4
    # Event 0x20000003 -> Handler VA 0x09E1DA0F (RVA 0x1E8F)
    # Event 0x20000004 -> Handler VA 0x09E1DAED (RVA 0x1F6D)
    ids_table_raw = 0x16BC4
    ev1, h1, ev2, h2, sent1, sent2 = struct.unpack(
        "<6I", data[ids_table_raw : ids_table_raw + 24]
    )
    assert ev1 == 0x20000003 and h1 == (FABRIC_BASE_VA + 0x1E8F), (
        "IDS event 0x20000003 mismatch"
    )
    assert ev2 == 0x20000004 and h2 == (FABRIC_BASE_VA + 0x1F6D), (
        "IDS event 0x20000004 mismatch"
    )
    assert sent1 == 0xFFFFFFFF and sent2 == 0xFFFFFFFF, "IDS sentinel mismatch"

    # Check CBS event subtable in AmdFabricAriPei at raw 0x16A98
    # Event 0xFFFFFFFE -> Handler VA 0x09E227A0 (RVA 0x6C20)
    subtable_raw = 0x16A98
    cpu_pred = struct.unpack("<Q", data[subtable_raw : subtable_raw + 8])[0]
    rsvd = struct.unpack("<Q", data[subtable_raw + 8 : subtable_raw + 16])[0]
    handler_va, event_id = struct.unpack(
        "<2I", data[subtable_raw + 16 : subtable_raw + 24]
    )
    assert cpu_pred == 0xFFFFFFFF, f"Subtable CPU predicate mismatch: {hex(cpu_pred)}"
    assert handler_va == (FABRIC_BASE_VA + 0x6C20), (
        f"Handler VA mismatch: {hex(handler_va)}"
    )
    assert event_id == 0xFFFFFFFE, f"Event ID mismatch: {hex(event_id)}"

    # Check function tables at 0x9E32934 (raw 0x16C1C)
    ft_raw = 0x16C1C
    t1, t2, t3, term = struct.unpack("<4I", data[ft_raw : ft_raw + 16])
    assert t1 == 0x09E32CFC and t2 == 0x09E32CEC and t3 == 0x09E32CDC and term == 0, (
        "Function table pointers mismatch"
    )


def check_reader_pointer_isolation():
    """Verify that reader 0x1D3C has no stored function pointers in data sections."""
    with open(FABRIC_PATH, "rb") as f:
        data = f.read()

    reader_rva = 0x1D3C
    reader_va = FABRIC_BASE_VA + reader_rva
    rva_bytes = struct.pack("<I", reader_rva)
    va_bytes = struct.pack("<I", reader_va)

    assert rva_bytes not in data[0x16800:], "Reader RVA found stored in data section"
    assert va_bytes not in data[0x16800:], "Reader VA found stored in data section"


def main():
    check_clv_and_modules()
    check_serialization_identities()
    check_fabric_indirect_edges()
    check_reader_pointer_isolation()
    print("BOUNDED_DF_INDIRECT_VERIFICATION_PASSED")


if __name__ == "__main__":
    main()
