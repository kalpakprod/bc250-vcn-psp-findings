#!/usr/bin/env python3
"""Build a DF request experiment on hash-pinned 5.00 clv.

df1400 is a single-field DF request; h1330 applies the H1330 template
(DF request plus fixed AmdSetup byte writes). s2-ocv validates the S1-H1330
base and applies the arbitrated S2 template (S2A fixed-voltage verdict plus
S2B offset verdict; both no-change, so output is byte-identical to S1).
Stored requests are not measured clocks. Voltage and synchronization
profiles are deliberately unavailable until consumer semantics are
established.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from nvar_audit import parse_records

SOURCE_SHA256 = "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"
S1_SHA256 = "c5dc6424b3d836b0a262ed54d9c3e747f2c33d40cb614fac40e4ea46e7bfbf7c"
IMAGE_SIZE = 0x1000000
BUILDER_VERSION = "1.2.0"
# s2-ocv value is the S1 DF request asserted (never rewritten), not a new target.
PROFILES = {"df1400": 1400, "h1330": 0x0532, "s2-ocv": 0x0532}


def transform_s2(original: bytes) -> tuple[bytes, dict]:
    """Apply the arbitrated S2 template onto the S1-H1330 base.

    S2A returned no_change with an empty template and S2B returned
    closed=false (offset stays 0), so every S2-relevant byte is
    assert-only and the output is byte-identical to S1.
    """
    if len(original) != IMAGE_SIZE or hashlib.sha256(original).hexdigest() != S1_SHA256:
        raise ValueError("source is not the approved S1-H1330 image")
    records, _, _ = parse_records(original[:0x20000])
    amd = [r for r in records if r["name"] == "AmdSetup"]
    setup = [r for r in records if r["name"] == "Setup"]
    if len(amd) != 1 or len(setup) != 1:
        raise ValueError("expected exactly one AmdSetup and one Setup record")
    astart = int(amd[0]["absolute_offset"], 16)
    abody = original.index(b"\0", astart + 0x0B, astart + amd[0]["size"]) + 1
    sstart = int(setup[0]["absolute_offset"], 16)
    sbody = original.index(b"\0", sstart + 0x0B, sstart + setup[0]["size"]) + 1
    if astart != 0x4BB or abody != 0x4CF or abody + 0x706 > astart + amd[0]["size"]:
        raise ValueError("unexpected AmdSetup layout")
    if sstart != 0xD84 or sbody != 0xD95 or sbody + 0x1D3 > sstart + setup[0]["size"]:
        raise ValueError("unexpected Setup layout")
    # S1 bytes preserved (ROM offsets in comments; abody pinned to 0x4CF).
    if original[abody + 0x316] != 0x1A:  # 0x7E5
        raise ValueError("S1 byte not preserved at body+0x316")
    if original[abody + 0x330] != 0x01:  # 0x7FF
        raise ValueError("S1 byte not preserved at body+0x330")
    if original[abody + 0x36D] != 0xFF:  # 0x83C per S1C verdict 0xFF
        raise ValueError("S1 byte not preserved at body+0x36D")
    if original[abody + 0x703] != 1:  # 0xBD2 assert-only
        raise ValueError("unexpected S1 baseline at body+0x703")
    if int.from_bytes(original[abody + 0x704 : abody + 0x706], "little") != 0x0532:
        raise ValueError("S1 DF request not preserved")
    # S2A no-change asserts: donor fixed-voltage bytes untouched (sbody 0xD95).
    vcore = (
        original[sbody + 0x1C9],
        int.from_bytes(original[sbody + 0x1CA : sbody + 0x1CC], "little"),
        original[sbody + 0x1CC],
    )
    if vcore != (0, 900, 2):  # ROM 0xF5E..0xF61
        raise ValueError("unexpected S2A VCORE donor baseline")
    gfx = (
        original[sbody + 0x1CD],
        int.from_bytes(original[sbody + 0x1CE : sbody + 0x1D0], "little"),
        original[sbody + 0x1D0],
    )
    if gfx != (0, 900, 2):  # ROM 0xF62..0xF65
        raise ValueError("unexpected S2A GFX donor baseline")
    memio = (original[sbody + 0x1D1], original[sbody + 0x1D2])
    if memio != (0, 0x1E):  # ROM 0xF66..0xF67
        raise ValueError("unexpected S2A MEMIO donor baseline")
    # S2B stays-0 asserts: control byte plus u32 value untouched.
    if original[abody + 0x6E5] != 0:  # 0xBB4 VDDCR_VDD Offset Control (Auto)
        raise ValueError("unexpected S2B control baseline at body+0x6E5")
    if int.from_bytes(original[abody + 0x6E6 : abody + 0x6EA], "little") != 0:
        raise ValueError("unexpected S2B value baseline at body+0x6E6")  # 0xBB5 u32
    candidate = bytes(original)
    result = {
        "profile": "s2-ocv",
        "builder_version": BUILDER_VERSION,
        "source_sha256": S1_SHA256,
        "output_sha256": hashlib.sha256(candidate).hexdigest(),
        "size": len(candidate),
        "amdsetup_record": hex(astart),
        "amdsetup_body": hex(abody),
        "setup_record": hex(sstart),
        "setup_body": hex(sbody),
        "field": "none (S2A/S2B arbitrated no-change)",
        "s1_df_preserved": 1330,
        "changed_offsets": [],
        "changed_byte_count": 0,
        "byte_identical_to_source": True,
        "s2a_verdict": "no_change=true, template=[] (candidates/s2-ocv/S2A-verdict.json)",
        "s2b_verdict": "closed=false, offset stays 0 (candidates/s2-ocv/S2B-verdict.json)",
        "assert_only": [
            "0x7e5==0x1a, 0x7ff==0x01, 0x83c==0xff (S1 preserved)",
            "0xbd2==0x01, 0xbd3:0xbd4==0x0532 (S1 DF preserved)",
            "0xf5e..0xf67 donor fixed-voltage bytes untouched (S2A no-change)",
            "0xbb4==0x00 control, 0xbb5:0xbb8==0x00000000 value (S2B stays-0)",
        ],
        "voltage_changed": False,
        "hardware_written": False,
        "status": "EXPERIMENTAL_REQUEST_ONLY_NOT_FLASH_APPROVED",
        "unverified": ["applied clock", "synchronization", "boot", "stability"],
    }
    return candidate, result


def transform(original: bytes, profile: str) -> tuple[bytes, dict]:
    if profile == "s2-ocv":
        return transform_s2(original)
    if (
        len(original) != IMAGE_SIZE
        or hashlib.sha256(original).hexdigest() != SOURCE_SHA256
    ):
        raise ValueError("source is not the approved 5.00 clv image")
    if profile not in PROFILES:
        raise ValueError("unsupported experimental profile")
    records, _, _ = parse_records(original[:0x20000])
    selected = [r for r in records if r["name"] == "AmdSetup"]
    if len(selected) != 1:
        raise ValueError("expected exactly one AmdSetup record")
    record = selected[0]
    start = int(record["absolute_offset"], 16)
    end = start + record["size"]
    body = original.index(b"\0", start + 0x0B, end) + 1
    if start != 0x4BB or body != 0x4CF or body + 0x706 > end:
        raise ValueError("unexpected AmdSetup layout")
    offset = body + 0x704
    if (
        original[body + 0x703] != 1
        or int.from_bytes(original[offset : offset + 2], "little") != 1420
    ):
        raise ValueError("unexpected DF request baseline")
    target = PROFILES[profile]
    writes = [(offset, target.to_bytes(2, "little"))]
    extra = []
    if profile == "h1330":
        # H1330 template; ROM offsets in comments (body is pinned to 0x4CF).
        if original[body + 0x316] != 0x24:  # 0x7E5
            raise ValueError("unexpected H1330 baseline at body+0x316")
        if original[body + 0x330] != 0x01:  # 0x7FF
            raise ValueError("unexpected H1330 baseline at body+0x330")
        if original[body + 0x36D] != 0xFF:  # 0x83C: arbitration pending, never written
            raise ValueError("unexpected H1330 baseline at body+0x36D")
        writes += [(body + 0x316, b"\x1a"), (body + 0x330, b"\x01")]
        extra = [
            {"offset": hex(body + 0x316), "from": 0x24, "to": 0x1A},
            {
                "offset": hex(body + 0x330),
                "from": 0x01,
                "to": 0x01,
                "note": "already at target; template no-op",
            },
        ]
    candidate = bytearray(original)
    for at, blob in writes:
        candidate[at : at + len(blob)] = blob
    changed = [i for i, (a, b) in enumerate(zip(original, candidate)) if a != b]
    expected = sorted(
        {
            at + i
            for at, blob in writes
            for i in range(len(blob))
            if original[at + i] != blob[i]
        }
    )
    if not changed or changed != expected:
        raise ValueError("unexpected changed-byte set")
    result = {
        "profile": profile,
        "builder_version": BUILDER_VERSION,
        "source_sha256": SOURCE_SHA256,
        "output_sha256": hashlib.sha256(candidate).hexdigest(),
        "size": len(candidate),
        "amdsetup_record": hex(start),
        "amdsetup_body": hex(body),
        "field": "DfClockOvrd",
        "from": 1420,
        "to": target,
        "changed_offsets": [hex(i) for i in changed],
        "changed_byte_count": len(changed),
        "voltage_changed": False,
        "hardware_written": False,
        "status": "EXPERIMENTAL_REQUEST_ONLY_NOT_FLASH_APPROVED",
        "unverified": ["applied clock", "synchronization", "boot", "stability"],
    }
    if extra:
        result["extra_writes"] = extra
        result["assert_only"] = [
            "0xbd2==0x01 (never written)",
            "0x83c==0xff left untouched (S1-C arbitration pending)",
        ]
    return bytes(candidate), result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--profile", required=True, choices=sorted(PROFILES))
    args = ap.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    manifest = output.with_suffix(".build.json")
    if source in (output, manifest) or output == manifest:
        ap.error("source, output and manifest must be distinct")
    if output.exists() or manifest.exists():
        ap.error("refusing existing output or manifest")
    try:
        candidate, report = transform(source.read_bytes(), args.profile)
    except ValueError as error:
        ap.error(str(error))
    report.update(source=str(source), output=str(output))
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive opens also protect against files created after the preflight.
    with manifest.open("x", encoding="utf-8") as metadata:
        with output.open("xb") as image:
            image.write(candidate)
        if output.read_bytes() != candidate:
            raise RuntimeError("output readback mismatch")
        metadata.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
