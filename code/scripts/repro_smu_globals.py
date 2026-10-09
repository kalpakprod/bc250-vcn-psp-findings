#!/usr/bin/env python3
"""Reproduce the SMU-firmware globals cited by the zero-day findings, from repo bytes.

Address convention, proven here: the PMFW type-0x08 file body maps 1:1 to SRAM,
i.e. file_offset == SRAM address.  Check: Ghidra's own DumpGlobals output for eight
addresses is reproduced 8/8 by a direct read at the same offset; the
file = SRAM -/+ 0x100 conventions reproduce 0/8.

Read-only; writes a JSON report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

BODY = Path(
    "archives/imported/vendor-upstream/legacy-tmp-bc250-upstream/"
    "amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5"
)
IMAGE = Path("evidence/donor/retroweb-20260916/BC250_5.00_clv.bin")

# values Ghidra's DumpGlobals printed in session (independent reference set)
GHIDRA = {
    0x17060: 0x00007AE0,
    0x1714C: 0x00008B18,
    0x177C4: 0x0001FFFF,
    0x17E68: 0x00008B08,
    0x17E6C: 0x01340000,
    0x17168: 0x01000000,
    0x1735C: 0x00001006,
    0x177FC: 0x000037B3,
}
# addresses cited by the findings, with the claim each supports
CITED = {
    0x17134: "ZD-3/ZD-4 mask applied to the polled domain register",
    0x17160: "ZD-3/ZD-4 window base added to the masked register",
    0x181B0: "ZD-1 ring-record base (asserted 0x000188A0; confirmed by direct read)",
    0x178B8: "FUN_000235c8 second-core window lower bound",
    0x178BC: "FUN_000235c8 second-core window upper bound",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("evidence/firmware-audit/20260919-zd/globals-repro.json"),
    )
    args = ap.parse_args()

    fw = BODY.read_bytes()
    img = IMAGE.read_bytes()
    payload = img[0x8FEE00 : 0x8FEE00 + 0x40200]
    report = {
        "tool": str(Path(__file__)),
        "smu_body_path": str(BODY),
        "smu_body_size": len(fw),
        "smu_body_sha256": hashlib.sha256(fw).hexdigest(),
        "image": str(IMAGE),
        "image_sha256": hashlib.sha256(img).hexdigest(),
        "psp_type_08_payload_equals_body_plus_0x100_prefix": payload[0x100:] == fw,
        "address_convention": None,
        "ghidra_reference_match": {},
        "cited_globals": {},
    }

    def at(off):
        return struct.unpack_from("<I", fw, off)[0] if 0 <= off + 4 <= len(fw) else None

    for label, delta in (
        ("file == SRAM", 0),
        ("file == SRAM - 0x100", 0x100),
        ("file == SRAM + 0x100", -0x100),
    ):
        hits = sum(1 for a, v in GHIDRA.items() if at(a - delta) == v)
        report["ghidra_reference_match"][label] = f"{hits}/{len(GHIDRA)}"

    best = max(report["ghidra_reference_match"].items(), key=lambda kv: kv[1])
    report["address_convention"] = (
        best[0] if best[1] == f"{len(GHIDRA)}/{len(GHIDRA)}" else "unresolved"
    )

    for addr, why in CITED.items():
        v = at(addr)
        report["cited_globals"][f"0x{addr:06X}"] = {
            "file_offset": f"0x{addr:06X}",
            "value": f"0x{v:08X}",
            "supports": why,
        }
    g = report["cited_globals"]
    report["derived_smn_base"] = {
        "formula": "(addr & DAT_17134) + DAT_17160 + 0x200",
        "DAT_17134": g["0x017134"]["value"],
        "DAT_17160": g["0x017160"]["value"],
        "base": hex((int(g["0x017160"]["value"], 16) + 0x200) & 0xFFFFFFFF),
    }
    report["assertions_checked"] = {
        "DAT_181B0 == 0x000188A0 (ZD-1 ring base)": g["0x0181B0"]["value"]
        == "0x000188A0",
        "DAT_17134 == 0x000FFFFF (ZD-3/4 mask)": g["0x017134"]["value"] == "0x000FFFFF",
        "DAT_17160 base derives 0x01100000 (ZD-3/4 window)": report["derived_smn_base"][
            "base"
        ]
        == "0x1100000",
        "DAT_178B8..DAT_178BC == 0x5B000..0x5B7FF (second-core window, D-R1 cross-check)": (
            g["0x0178B8"]["value"],
            g["0x0178BC"]["value"],
        )
        == ("0x0005AFFF", "0x0005B7FF"),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(
        f"convention: {report['address_convention']}  ref {report['ghidra_reference_match']}"
    )
    print(
        f"DAT_17134 = {g['0x017134']['value']}   DAT_17160 = {g['0x017160']['value']}   "
        f"derived SMN base = {report['derived_smn_base']['base']}"
    )
    print(
        f"DAT_181B0 = {g['0x0181B0']['value']}  (robin-5 body; per-version, see ring-base-per-version.json)"
    )
    print(
        f"DAT_178B8 = {g['0x0178B8']['value']}   DAT_178BC = {g['0x0178BC']['value']}"
    )
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
