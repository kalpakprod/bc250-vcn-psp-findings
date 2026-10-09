#!/usr/bin/env python3
"""
Dynamic SMN Security Gasket unclamp for AMD BC-250 VCN (Bank 12).
Applies the 56 reference writes derived from Cezanne/Renoir SEC_GASKET to SMN
space (0x0900c000..0x0900cb80) using SMU privileged SMN access, then verifies
MMIO liveness.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# SMU unlock library path
SMU_LIB = Path(
    os.environ.get(
        "BC250_SMU_PATH",
        "/home/OWNER/vcn_unlock/bc250-smu-unlock",
    )
)
sys.path.insert(0, str(SMU_LIB))

import unlock  # noqa: E402
from bc250_smu import Bc250Smu, SmuError  # noqa: E402

# Daveconde enable_vcn for MMIO reading
VCN_SRC = Path(
    os.environ.get(
        "BC250_VCN_SOURCE",
        "/home/OWNER/vcn_unlock/daveconde-bc250-vcn-enable",
    )
)
sys.path.insert(0, str(VCN_SRC))

import enable_vcn  # noqa: E402

# 56 writes from working_vcn_gasket_template.json
GASKET_WRITES = [
    ("0x201", 0x0900c234, 0x00000000),
    ("0x201", 0x0900c830, 0x00fffffb),
    ("0x201", 0x0900c834, 0x00ffffff),
    ("0x201", 0x0900c838, 0x00ffffff),
    ("0x201", 0x0900c920, 0x000003ff),
    ("0x201", 0x0900c92c, 0x00000000),
    ("0x201", 0x0900c930, 0x00000036),
    ("0x201", 0x0900c944, 0x00000307),
    ("0x201", 0x0900c950, 0x00000000),
    ("0x201", 0x0900c954, 0x00000036),
    ("0x201", 0x0900c934, 0x00021800),
    ("0x201", 0x0900c938, 0x000218ff),
    ("0x201", 0x0900c968, 0x00000307),
    ("0x201", 0x0900c974, 0x00000000),
    ("0x201", 0x0900c978, 0x00000036),
    ("0x201", 0x0900c958, 0x00020300),
    ("0x201", 0x0900c95c, 0x000206ff),
    ("0x201", 0x0900c98c, 0x00000307),
    ("0x201", 0x0900c998, 0x00000000),
    ("0x201", 0x0900c99c, 0x00000036),
    ("0x201", 0x0900c97c, 0x0001f844),
    ("0x201", 0x0900c980, 0x0001f84f),
    ("0x201", 0x0900c9b0, 0x00000307),
    ("0x201", 0x0900c9bc, 0x00000000),
    ("0x201", 0x0900c9c0, 0x00000036),
    ("0x201", 0x0900c9a0, 0x00020180),
    ("0x201", 0x0900c9a4, 0x00020183),
    ("0x201", 0x0900c9d4, 0x00000307),
    ("0x201", 0x0900c9e0, 0x00000000),
    ("0x201", 0x0900c9e4, 0x00000036),
    ("0x201", 0x0900c9c4, 0x00020108),
    ("0x201", 0x0900c9c8, 0x00020117),
    ("0x201", 0x0900c9f8, 0x00000307),
    ("0x201", 0x0900ca04, 0x00000000),
    ("0x201", 0x0900ca08, 0x00000036),
    ("0x201", 0x0900c9e8, 0x00021078),
    ("0x201", 0x0900c9ec, 0x0002107f),
    ("0x201", 0x0900ca1c, 0x00000307),
    ("0x201", 0x0900ca28, 0x00000000),
    ("0x201", 0x0900ca2c, 0x00000036),
    ("0x201", 0x0900ca0c, 0x00020eb0),
    ("0x201", 0x0900ca10, 0x00020eb7),
    ("0x201", 0x0900ca40, 0x00000307),
    ("0x201", 0x0900ca4c, 0x00000000),
    ("0x201", 0x0900ca50, 0x00000036),
    ("0x201", 0x0900ca30, 0x0001f860),
    ("0x201", 0x0900ca34, 0x0001f863),
    ("0x201", 0x0900cb80, 0x000000ff),
    ("0x201", 0x0900c910, 0x00497fff),
    ("0x201", 0x0900c914, 0x00007fff),
    ("0x201", 0x0900c234, 0x00000001),
    ("0x280", 0x0900c234, 0x00000000),
    ("0x280", 0x0900c914, 0x00000000),
    ("0x280", 0x0900c930, 0x00000000),
    ("0x280", 0x0900cb80, 0x00000000),
    ("0x280", 0x0900c234, 0x00000001),
]

MMIO_PROBES = (
    ("UVD_PGFSM_CONFIG", 0x0000, 1),
    ("UVD_PGFSM_STATUS", 0x0001, 1),
    ("UVD_POWER_STATUS", 0x0004, 1),
    ("CC_UVD_HARVESTING", 0x0007, 1),
    ("UVD_JPEG_POWER_STATUS", 0x000A, 1),
    ("UVD_MASTINT_EN", 0x0200, 1),
    ("UVD_STATUS", 0x026F, 1),
    ("UVD_VERSION", 0x05C9, 1),
    ("UVD_NO_OP", 0x05BF, 1),
    ("UVD_JPEG_CNTL", 0x0080, 0),
    ("UVD_JRBC_STATUS", 0x0109, 0),
)


def read_mmio_ladder(direct: enable_vcn.VcnDirect) -> dict[str, int]:
    out = {}
    for name, offset, segment in MMIO_PROBES:
        mmio = (
            (enable_vcn.VCN_SEG1_DW if segment else enable_vcn.VCN_SEG0_DW)
            + offset
        ) * 4
        val = direct.rd(mmio)
        out[name] = val
    return out


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=("control", "full"),
        default="control",
        help="control toggles only Bank-12 enable; full replays all 56 writes",
    )
    args = parser.parse_args()

    writes = (
        [GASKET_WRITES[0], GASKET_WRITES[50]]
        if args.mode == "control"
        else GASKET_WRITES
    )
    print(f"=== SMN VCN Gasket Dynamic Unclamp mode={args.mode} ===", flush=True)
    smu = Bc250Smu()
    direct = None
    try:
        if not smu.alive():
            print("ERROR: SMU is not alive", file=sys.stderr)
            return 1
        print("[*] SMU alive verified", flush=True)

        if not smu.secure_access_enabled():
            print("[*] Unlocking SMU secure access path...", flush=True)
            unlock.smu = smu
            unlock.unlock(smu)
        if not smu.secure_access_enabled():
            print("ERROR: secure SMU path did not open", file=sys.stderr)
            return 1
        print("[*] Secure access open", flush=True)

        direct = enable_vcn.VcnDirect()
        mmio_before = read_mmio_ladder(direct)
        all_ones_before = all(v == 0xFFFFFFFF for v in mmio_before.values())
        print(f"[*] MMIO before: uniform_all_ones={all_ones_before}", flush=True)

        control_before = smu.smn_read32(0x0900C234)
        print(f"[*] Bank-12 control before=0x{control_before:08x}", flush=True)

        write_results = []
        for idx, (group, address, value) in enumerate(writes):
            print(
                f"[*] write[{idx:02d}/{len(writes):02d}] {group} "
                f"0x{address:08x} <= 0x{value:08x}",
                flush=True,
            )
            try:
                smu.smn_write32(address, value)
            except Exception as error:
                print(f"ERROR: write failed: {error}", file=sys.stderr, flush=True)
                return 3
            if not smu.alive():
                print("ERROR: SMU stopped responding after write", file=sys.stderr, flush=True)
                return 4
            write_results.append(
                {
                    "idx": idx,
                    "group": group,
                    "address": f"0x{address:08x}",
                    "value": f"0x{value:08x}",
                }
            )

        control_after = smu.smn_read32(0x0900C234)
        print(f"[*] Bank-12 control after=0x{control_after:08x}", flush=True)

        mmio_after = read_mmio_ladder(direct)
        all_ones_after = all(v == 0xFFFFFFFF for v in mmio_after.values())
        print(f"[*] MMIO after: uniform_all_ones={all_ones_after}", flush=True)
        for name, value in mmio_after.items():
            marker = " changed" if value != mmio_before[name] else ""
            print(f"    {name:22s}=0x{value:08x}{marker}", flush=True)

        summary = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "mode": args.mode,
            "control_before": f"0x{control_before:08x}",
            "control_after": f"0x{control_after:08x}",
            "all_ones_before": all_ones_before,
            "all_ones_after": all_ones_after,
            "mmio_before": {name: f"0x{value:08x}" for name, value in mmio_before.items()},
            "mmio_after": {name: f"0x{value:08x}" for name, value in mmio_after.items()},
            "writes": write_results,
        }
        output = Path(
            f"/home/OWNER/vcn_unlock/smn_vcn_gasket_{args.mode}.json"
        )
        output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"[*] summary={output}", flush=True)
        return 0 if not all_ones_after else 2
    finally:
        if direct is not None:
            try:
                direct.rf.close()
                os.close(direct.vram_fd)
            except Exception:
                pass
        smu.close()


if __name__ == "__main__":
    raise SystemExit(main())
