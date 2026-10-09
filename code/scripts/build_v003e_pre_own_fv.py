#!/usr/bin/env python3
"""SUPERSEDED (v003e): builds SUPERSEDED-BC250_pre_dump_vcn_own_fv_v003e.bin — the board's OWN live BIOS + VCN driver, kept for history only.

v003c replaced the board's whole DXE volume with the FD donor's volume
(postmortem finding). v003e injects the SAME driver into the inner FV the
board actually ran this morning (0x43D000, 193 files), placed BEFORE
Bds.ffs (the v003c placement class: contiguous, 8-aligned, no erased gap),
FV grown by whole blocks, capsule recompressed. Everything outside the
capsule window = the booted dump, byte for byte (live NVRAM/APCB intact).

DEVIATION from the plan-mandated base ("community 3.00 MeiMeiDXE
boot-proven"): the base here is the board's own running image, because
the v003c postmortem showed the FD base was never equal to what the board
runs. Requires operator decision; build is offline and writes nothing
but a new candidate file.

Sources:
  base = evidence/programmer/reads/20260924-v003c/pre-v003c-read-a.bin
         (sha 64973ba364ae4417de10bd905d2cf8bad165af3b544d175b3cc315f0e28d621a)
  blob = candidates/vcn-unlock-driver-v000-DRAFT/bin/Bc250VcnUnlockDxe.ffs
Output: candidates/SUPERSEDED-BC250_pre_dump_vcn_own_fv_v003e.bin (new, never overwrite)
"""

from __future__ import annotations

import json
import lzma
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_vcn_o3_candidate import (  # noqa: E402
    OUTER_FV,
    OUTER_LEN,
    CAPSULE_GUID,
    decompress_inner,
    walk_inner_fv,
    fv_header_checksum,
    ffs_header_checksum,
    guid_str,
    sha256,
)

REPO = Path(__file__).resolve().parent.parent
PRE = REPO / "evidence/programmer/reads/20260924-v003c/pre-v003c-read-a.bin"
BLOB = REPO / "candidates/vcn-unlock-driver-v000-DRAFT/bin/Bc250VcnUnlockDxe.ffs"
OUT = REPO / "candidates/SUPERSEDED-BC250_pre_dump_vcn_own_fv_v003e.bin"
MANIFEST = REPO / "candidates/SUPERSEDED-BC250_pre_dump_vcn_own_fv_v003e.build.json"

PRE_SHA = "64973ba364ae4417de10bd905d2cf8bad165af3b544d175b3cc315f0e28d621a"
BLOB_SHA = "e8b2a62c15688191cb9e8e9271aef18ac1b5fc2bd727adea3eb569639ddbbcb0"
VCN_GUID = "B6250780-7E00-4203-900C-23443B1413FE"
BDS_GUID = bytes.fromhex("828f4b8f919b284086e6f4db7d4c1dff")
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
    pre = PRE.read_bytes()
    assert len(pre) == 0x1000000 and sha256(pre) == PRE_SHA

    blob = bytearray(BLOB.read_bytes())
    assert sha256(bytes(blob)) == BLOB_SHA
    assert blob[18] == 0x07 and guid_str(blob) == VCN_GUID
    assert (sum(blob[:17]) + sum(blob[18:23])) & 0xFF == 0
    blob[23] = STATE_IN_IMAGE
    blob = bytes(blob)

    clv = decompress_inner(pre)
    flen = struct.unpack_from("<Q", clv["fv"], 0x20)[0]
    num, blk = struct.unpack_from("<II", clv["fv"], 0x38)
    assert num * blk == flen, (hex(num), hex(blk), hex(flen))
    inv, _ = walk_inner_fv(clv["fv"])
    assert not any(f["guid"] == VCN_GUID for f in inv)

    bds_pos = clv["fv"].find(BDS_GUID)
    assert bds_pos > 0 and bds_pos % 8 == 0, hex(bds_pos)
    prev = max((f for f in inv if f["off"] < bds_pos), key=lambda f: f["off"])
    prev_end = (prev["off"] + prev["size"] + 7) & ~7
    assert prev_end == bds_pos, (hex(prev_end), hex(bds_pos))  # no gap before Bds

    pad = (8 - (len(blob) % 8)) % 8
    new_fv = (
        bytearray(clv["fv"][:bds_pos]) + blob + b"\xff" * pad + clv["fv"][bds_pos:flen]
    )
    new_flen = (len(new_fv) + blk - 1) & ~(blk - 1)
    new_fv += b"\xff" * (new_flen - len(new_fv))
    struct.pack_into("<Q", new_fv, 0x20, new_flen)
    struct.pack_into("<I", new_fv, 0x38, new_flen // blk)
    fv_header_checksum(new_fv, 0x48)
    new_fv = bytes(new_fv)

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
    assert all(b == 0xFF for b in pre[cpos + old_csz : outer_end])
    assert cpos + new_csz <= outer_end
    cap_hdr = bytearray(pre[cpos : cpos + 24])
    assert cap_hdr[19] & 0x40 == 0
    cap_hdr[20:23] = int.to_bytes(new_csz, 3, "little")
    ffs_header_checksum(cap_hdr)

    out = bytearray(pre)
    out[cpos : cpos + 24] = cap_hdr
    out[cpos + 24 : cpos + new_csz] = bytes(guided) + compressed
    out[cpos + new_csz : outer_end] = b"\xff" * (outer_end - cpos - new_csz)
    out_sha = sha256(bytes(out))

    # verification (real-DxeCore semantics walk of the OUTPUT)
    chk = decompress_inner(bytes(out))
    chk_flen = struct.unpack_from("<Q", chk["fv"], 0x20)[0]
    assert chk_flen == new_flen
    chk_inv, _ = walk_inner_fv(chk["fv"])
    assert len(chk_inv) == len(inv) + 1
    newf = [f for f in chk_inv if f["guid"] == VCN_GUID]
    assert len(newf) == 1 and newf[0]["off"] == bds_pos
    assert newf[0]["sha"] == sha256(blob[24:])
    orig_shas = {f["sha"] for f in inv}
    assert orig_shas <= {f["sha"] for f in chk_inv}
    chk_bds = chk["fv"].find(BDS_GUID)
    assert chk_bds == bds_pos + len(blob) + pad
    diffs = [i for i in range(0x1000000) if out[i] != pre[i]]
    assert all(cpos <= i < outer_end for i in diffs), "diff escaped the capsule"

    OUT.write_bytes(bytes(out))
    MANIFEST.write_text(
        json.dumps(
            {
                "variant": "v003e",
                "what": "board's own live BIOS (booted pre-dump) + VCN driver before "
                "Bds.ffs in its OWN inner FV (no donor DXE); live NVRAM/APCB "
                "intact; diff confined to the capsule window",
                "note": "DEVIATES from the plan-mandated community-3.00-MeiMeiDXE base; "
                "operator decision required before any flash",
                "base": {"path": str(PRE), "sha256": PRE_SHA},
                "blob": {"path": str(BLOB), "sha256": BLOB_SHA},
                "output_sha256": out_sha,
                "inner_fv": {
                    "old_len": hex(flen),
                    "new_len": hex(new_flen),
                    "old_files": len(inv),
                    "new_files": len(chk_inv),
                },
                "injected": {
                    "guid": VCN_GUID,
                    "fv_off": hex(bds_pos),
                    "size": hex(len(blob)),
                },
                "bds_shifted_to": hex(chk_bds),
                "diff_window": {
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
    print(f"v003e OUT sha256: {out_sha}")
    print(
        f"inner FV {hex(flen)} -> {hex(new_flen)}, {len(inv)} -> {len(chk_inv)} files"
    )
    print(
        f"driver @{hex(bds_pos)} before Bds, capsule {hex(old_csz)} -> {hex(new_csz)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
