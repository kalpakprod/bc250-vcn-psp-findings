#!/usr/bin/env python3
from pathlib import Path
import sys


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: {sys.argv[0]} KERNEL_SOURCE_ROOT")

    root = Path(sys.argv[1])
    amdgpu_vcn = root / "drivers/gpu/drm/amd/amdgpu/amdgpu_vcn.c"
    vcn_v2 = root / "drivers/gpu/drm/amd/amdgpu/vcn_v2_0.c"

    vcn_text = amdgpu_vcn.read_text(encoding="utf-8")
    helper = """static bool amdgpu_vcn_use_direct_fw(struct amdgpu_device *adev)\n{
\treturn amdgpu_bc250_vcn &&
\t       (adev->apu_flags & AMD_APU_IS_CYAN_SKILLFISH2) &&
\t       amdgpu_ip_version(adev, UVD_HWIP, 0) == IP_VERSION(2, 0, 3);
}\n\n"""
    anchor = """static void amdgpu_vcn_idle_work_handler(struct work_struct *work);\nstatic void amdgpu_vcn_reg_dump_fini(struct amdgpu_device *adev);\n\n"""
    if "static bool amdgpu_vcn_use_direct_fw" not in vcn_text:
        vcn_text = replace_once(vcn_text, anchor, anchor + helper,
                                "amdgpu_vcn helper anchor")

    vcn_text = replace_once(
        vcn_text,
        """\tif ((adev->firmware.load_type == AMDGPU_FW_LOAD_PSP) &&\n\t    (adev->pg_flags & AMD_PG_SUPPORT_VCN_DPG))\n""",
        """\tif ((adev->firmware.load_type == AMDGPU_FW_LOAD_PSP) &&\n\t    !amdgpu_vcn_use_direct_fw(adev) &&\n\t    (adev->pg_flags & AMD_PG_SUPPORT_VCN_DPG))\n""",
        "indirect SRAM condition",
    )
    vcn_text = replace_once(
        vcn_text,
        """\t\tif (adev->firmware.load_type != AMDGPU_FW_LOAD_PSP) {\n""",
        """\t\tif (adev->firmware.load_type != AMDGPU_FW_LOAD_PSP ||\n\t\t    amdgpu_vcn_use_direct_fw(adev)) {\n""",
        "VCN firmware copy condition",
    )
    vcn_text = replace_once(
        vcn_text,
        """\tif (adev->firmware.load_type == AMDGPU_FW_LOAD_PSP) {\n\t\tconst struct common_firmware_header *hdr;\n""",
        """\tif (adev->firmware.load_type == AMDGPU_FW_LOAD_PSP &&\n\t    !amdgpu_vcn_use_direct_fw(adev)) {\n\t\tconst struct common_firmware_header *hdr;\n""",
        "PSP VCN ucode registration condition",
    )
    amdgpu_vcn.write_text(vcn_text, encoding="utf-8", newline="\n")

    v2_text = vcn_v2.read_text(encoding="utf-8")
    v2_helper = """static bool vcn_v2_0_use_direct_fw(struct amdgpu_device *adev)\n{
\treturn amdgpu_bc250_vcn &&
\t       (adev->apu_flags & AMD_APU_IS_CYAN_SKILLFISH2) &&
\t       amdgpu_ip_version(adev, UVD_HWIP, 0) == IP_VERSION(2, 0, 3);
}\n\n"""
    v2_anchor = """static int vcn_v2_0_start_sriov(struct amdgpu_device *adev);\nstatic int vcn_v2_0_reset(struct amdgpu_vcn_inst *vinst);\n\n"""
    if "static bool vcn_v2_0_use_direct_fw" not in v2_text:
        v2_text = replace_once(v2_text, v2_anchor, v2_anchor + v2_helper,
                               "vcn_v2 helper anchor")

    condition = "if (adev->firmware.load_type == AMDGPU_FW_LOAD_PSP) {"
    replacement = """if (adev->firmware.load_type == AMDGPU_FW_LOAD_PSP &&
\t    !vcn_v2_0_use_direct_fw(adev)) {"""
    count = v2_text.count(condition)
    if count != 3:
        raise SystemExit(f"vcn_v2 PSP conditions: expected 3, found {count}")
    v2_text = v2_text.replace(condition, replacement)
    vcn_v2.write_text(v2_text, encoding="utf-8", newline="\n")

    print(f"updated {amdgpu_vcn}")
    print(f"updated {vcn_v2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
