#!/usr/bin/env python3
"""Build v003c: route-B VCN driver injected BEFORE Bds.ffs (fixed placement).

The staged v003b appended the driver FFS at inner-FV offset 0x432000, i.e.
AFTER the base's trailing 0xFF free space. The real DxeCore FV walker
(MdeModulePkg/Core/Dxe/FwVol.c, FwGetNextFile) treats the first erased
buffer as "free space so we are done" and STOPS: a file after a 0xFF gap is
never dispatched. v003b would boot but the driver would never run.

v003c uses the placement proven on hardware by the W9 series (its injected
driver executed: 8-core unlock observed): insert the FFS strictly before
Bds.ffs (GUID 8f4b8f82-9b91-4028-86e6-f4db7d4c1dff), 8-byte aligned, pad
with 0xFF to alignment, grow the inner FV by whole blocks, recompute the
FV header checksum, LZMA-recompress the capsule. NO PSP directory changes
(one variable per flash, same as v003b intended).

Base:  evidence/donor/fd-v22-20260923/BC250_3.00_MeiMeiDXEv3 (606a7a7f…)
Blob:  candidates/vcn-unlock-driver-v000-DRAFT/bin/Bc250VcnUnlockDxe.ffs
       (12316 B, type 0x07 DRIVER, state 0x07 -> normalized 0xF8 in-image)
Output: candidates/BC250_3.00_MeiMeiDXEv3_vcn_v003c.bin (never overwrite)
"""

from __future__ import annotations

import hashlib
import json
import lzma
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_vcn_o3_candidate import (  # noqa: E402
    OUTER_FV,
    OUTER_LEN,
    decompress_inner,
    walk_inner_fv,
    fv_header_checksum,
    ffs_header_checksum,
    guid_str,
    sha256,
)

REPO = Path(__file__).resolve().parent.parent
BASE = REPO / "evidence/donor/fd-v22-20260923/BC250_3.00_MeiMeiDXEv3"
BLOB = REPO / "candidates/vcn-unlock-driver-v000-DRAFT/bin/Bc250VcnUnlockDxe.ffs"
OUT = REPO / "candidates/BC250_3.00_MeiMeiDXEv3_vcn_v003c.bin"
MANIFEST = REPO / "candidates/BC250_3.00_MeiMeiDXEv3_vcn_v003c.build.json"

BASE_SHA = "606a7a7f9ef8fb1c445d8ccfa9640de0339bfec5ab52969135a9e87d62028182"
BLOB_SHA = "e8b2a62c15688191cb9e8e9271aef18ac1b5fc2bd727adea3eb569639ddbbcb0"
VCN_GUID = "B6250780-7E00-4203-900C-23443B1413FE"
BDS_GUID = bytes.fromhex("828f4b8f919b284086e6f4db7d4c1dff")  # LE, 8f4b8f82-…
STATE_IN_IMAGE = 0xF8
LZMA_FILTERS = [
    {
        "id": lzma.FILTER_LZMA1,
        "dict_size": 16 * 1024 * 1024,
        "lc": 3,
        "lp": 0,
        "pb": 2,
        "mode": lzma.MODE_NORMAL,
        "nice_len": 64,
        "mf": lzma.MF_BT4,
    }
]


def main() -> int:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite existing output: {OUT}")
    base = BASE.read_bytes()
    assert len(base) == 0x1000000 and sha256(base) == BASE_SHA
    blob = bytearray(BLOB.read_bytes())
    assert sha256(bytes(blob)) == BLOB_SHA
    assert blob[18] == 0x07, f"expected FFS type 0x07 DRIVER, got {blob[18]:#x}"
    assert guid_str(blob) == VCN_GUID, guid_str(blob)
    assert (sum(blob[:17]) + sum(blob[18:23])) & 0xFF == 0, "header checksum bad"
    blob[23] = STATE_IN_IMAGE
    blob = bytes(blob)
    blob_sha = sha256(blob)

    # 1. unpack the capsule
    clv = decompress_inner(base)
    fv, flen = clv["fv"], 0
    flen = struct.unpack_from("<Q", clv["fv"], 0x20)[0]
    inv, _ = walk_inner_fv(clv["fv"])
    assert not any(f["guid"] == VCN_GUID for f in inv), "VCN GUID already present"

    # 2. insertion point: the Bds.ffs file start (must be a real inventory file)
    bds_pos = clv["fv"].find(BDS_GUID)
    assert bds_pos > 0 and bds_pos % 8 == 0, hex(bds_pos)
    bds_entry = [f for f in inv if f["off"] == bds_pos]
    assert bds_entry and bds_entry[0]["guid"] == guid_str(BDS_GUID), (
        "Bds not in inventory"
    )
    prev = max((f for f in inv if f["off"] < bds_pos), key=lambda f: f["off"])
    prev_end = (prev["off"] + prev["size"] + 7) & ~7
    assert prev_end == bds_pos, (hex(prev_end), hex(bds_pos))  # no gap before Bds

    # 3. insert BEFORE Bds; pad to 8; grow the FV by whole blocks
    pad = (8 - (len(blob) % 8)) % 8
    new_fv = (
        bytearray(clv["fv"][:bds_pos]) + blob + b"\xff" * pad + clv["fv"][bds_pos:flen]
    )
    num, blk = struct.unpack_from("<II", new_fv, 0x38)
    assert num * blk == flen, (hex(num), hex(blk), hex(flen))
    new_flen = (len(new_fv) + blk - 1) & ~(blk - 1)
    new_fv += b"\xff" * (new_flen - len(new_fv))
    struct.pack_into("<Q", new_fv, 0x20, new_flen)
    struct.pack_into("<I", new_fv, 0x38, new_flen // blk)
    fv_header_checksum(new_fv, 0x48)
    new_fv = bytes(new_fv)

    # 4. capsule rebuild (same as the o3/v003b machinery)
    fvim = int.to_bytes(len(new_fv) + 4, 3, "little") + b"\x17" + new_fv
    stream = clv["raw"] + b"\x00" * clv["raw_pad"] + fvim
    compressed = lzma.compress(stream, format=lzma.FORMAT_ALONE, filters=LZMA_FILTERS)
    guided = bytearray(clv["guided_hdr"])
    new_gsz = len(guided) + len(compressed)
    assert new_gsz < 0xFFFFFF
    guided[0:3] = int.to_bytes(new_gsz, 3, "little")
    new_csz = 24 + len(guided) + len(compressed)
    cpos, old_csz = clv["cpos"], clv["csz"]
    outer_end = OUTER_FV + OUTER_LEN
    assert all(b == 0xFF for b in base[cpos + old_csz : outer_end]), (
        "non-FF after capsule"
    )
    assert cpos + new_csz <= outer_end, (hex(cpos + new_csz), hex(outer_end))
    cap_hdr = bytearray(base[cpos : cpos + 24])
    assert cap_hdr[19] & 0x40 == 0, "capsule has file checksum; unsupported"
    cap_hdr[20:23] = int.to_bytes(new_csz, 3, "little")
    ffs_header_checksum(cap_hdr)

    out = bytearray(base)
    out[cpos : cpos + 24] = cap_hdr
    out[cpos + 24 : cpos + new_csz] = bytes(guided) + compressed
    out[cpos + new_csz : outer_end] = b"\xff" * (outer_end - cpos - new_csz)
    out_sha = sha256(bytes(out))

    # 5. verification: re-walk the OUTPUT with real-DxeCore semantics
    chk = decompress_inner(bytes(out))
    chk_flen = struct.unpack_from("<Q", chk["fv"], 0x20)[0]
    assert chk_flen == new_flen, (hex(chk_flen), hex(new_flen))
    chk_inv, _ = walk_inner_fv(chk["fv"])  # stops at erased space, like DxeCore
    assert len(chk_inv) == len(inv) + 1, (len(chk_inv), len(inv))
    newf = [f for f in chk_inv if f["guid"] == VCN_GUID]
    assert len(newf) == 1 and newf[0]["off"] == bds_pos, newf
    assert newf[0]["sha"] == sha256(blob[24:])
    assert chk["fv"][newf[0]["off"] + 23] == STATE_IN_IMAGE, "in-image state"
    # every original file survived (shas), Bds shifted but intact
    orig_shas = {f["sha"] for f in inv}
    assert orig_shas <= {f["sha"] for f in chk_inv}
    bds_new = [f for f in chk_inv if f["guid"] == guid_str(BDS_GUID)]
    assert len(bds_new) == 1 and bds_new[0]["off"] == bds_pos + len(blob) + pad
    # no erased gap before the new file: previous file still ends right at it
    chk_prev = max((f for f in chk_inv if f["off"] < bds_pos), key=lambda f: f["off"])
    assert (chk_prev["off"] + chk_prev["size"] + 7) & ~7 == bds_pos
    # diff confined to the capsule window
    diffs = [i for i in range(0x1000000) if base[i] != out[i]]
    assert all(OUTER_FV + 0x88 <= i <= 0xC2654B for i in diffs), "diff outside capsule"

    OUT.write_bytes(bytes(out))
    MANIFEST.write_text(
        json.dumps(
            {
                "variant": "v003c",
                "fix": "driver inserted BEFORE Bds.ffs (v003b placed it after the 0xFF "
                "free tail at 0x432000 where DxeCore's FV walk stops: never dispatched)",
                "base": {"path": str(BASE), "sha256": BASE_SHA},
                "blob": {
                    "path": str(BLOB),
                    "sha256": BLOB_SHA,
                    "in_image_sha256": blob_sha,
                },
                "output_sha256": out_sha,
                "inner_fv": {
                    "old_len": hex(flen),
                    "new_len": hex(new_flen),
                    "old_files": len(inv),
                    "new_files": len(chk_inv),
                },
                "injected": {
                    "guid": VCN_GUID,
                    "name": "Bc250VcnUnlockDxe",
                    "fv_off": hex(bds_pos),
                    "size": hex(len(blob)),
                    "placement": "before Bds.ffs, contiguous, 8-aligned",
                },
                "bds_shifted_to": hex(bds_pos + len(blob) + pad),
                "changed_range": {
                    "first": hex(min(diffs)),
                    "last": hex(max(diffs)),
                    "ndiff": len(diffs),
                },
                "capsule": {"old_csz": hex(old_csz), "new_csz": hex(new_csz)},
                "hardware_written": False,
            },
            indent=2,
        )
        + "\n"
    )
    print(f"Base SHA256:       {BASE_SHA[:16]}…")
    print(f"B lob SHA256:      {blob_sha[:16]}…")
    print(f"Candidate SHA256:  {out_sha}")
    print(
        f"inner FV: {len(inv)} -> {len(chk_inv)} files, len {hex(flen)} -> {hex(new_flen)}"
    )
    print(
        f"driver at {hex(bds_pos)} (before Bds), Bds -> {hex(bds_pos + len(blob) + pad)}"
    )
    print(f"capsule {hex(old_csz)} -> {hex(new_csz)}, diff bytes {len(diffs)}")
    print(f"OUT: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
