#!/usr/bin/env python3
"""Build v003d: booted pre-dump + ONLY the v003c capsule window replaced.

Postmortem of the v003c no-boot: the full-image write factory-reset live
NVRAM and the APCB token block (0xAB1008..0xAB1B6F) to donor values, and
replaced the board's whole DXE volume with the donor's. v003d isolates
the capsule: every byte outside the capsule window is taken from the
FRESH PRE-WRITE DUMP (the image the board ran this morning), the capsule
window is v003c's (donor-DXE + driver before Bds). Diff vs the booted
dump is confined to the declared window: the corrected one-variable test.

Sources:
  base = evidence/programmer/reads/20260924-v003c/pre-v003c-read-a.bin
         (sha 64973ba364ae4417de10bd905d2cf8bad165af3b544d175b3cc315f0e28d621a)
  capsule donor = .../post-v003c-readback.bin (v003c, sha dafb323a…)
Output: candidates/SUPERSEDED-BC250_pre_dump_vcn_capsule_swap_v003d.bin (new, never overwrite)
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_vcn_o3_candidate import (  # noqa: E402
    OUTER_FV,
    OUTER_LEN,
    CAPSULE_GUID,
    decompress_inner,
    walk_inner_fv,
    guid_str,
    sha256,
)

REPO = Path(__file__).resolve().parent.parent
PRE = REPO / "evidence/programmer/reads/20260924-v003c/pre-v003c-read-a.bin"
POST = REPO / "evidence/programmer/reads/20260924-v003c/post-v003c-readback.bin"
OUT = REPO / "candidates/SUPERSEDED-BC250_pre_dump_vcn_capsule_swap_v003d.bin"
MANIFEST = (
    REPO / "candidates/SUPERSEDED-BC250_pre_dump_vcn_capsule_swap_v003d.build.json"
)

PRE_SHA = "64973ba364ae4417de10bd905d2cf8bad165af3b544d175b3cc315f0e28d621a"
POST_SHA = "dafb323a5d701f29b9c1b74f0a6bc728572590ced54a8389c01b20c0a4f828b0"
VCN_GUID = "B6250780-7E00-4203-900C-23443B1413FE"
BDS_GUID = bytes.fromhex("828f4b8f919b284086e6f4db7d4c1dff")


def main() -> int:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite existing output: {OUT}")
    pre = PRE.read_bytes()
    post = POST.read_bytes()
    assert len(pre) == len(post) == 0x1000000
    assert sha256(pre) == PRE_SHA, "pre-dump sha mismatch"
    assert sha256(post) == POST_SHA, "v003c readback sha mismatch"

    pre_clv = decompress_inner(pre)
    post_clv = decompress_inner(post)
    assert pre_clv["cpos"] == post_clv["cpos"], "capsule positions differ"
    cpos = pre_clv["cpos"]
    outer_end = OUTER_FV + OUTER_LEN
    pre_end = cpos + 24 + pre_clv["csz"]
    # the old capsule must be the LAST file of the outer FV (all FF after)
    assert all(b == 0xFF for b in pre[pre_end:outer_end]), "data after old capsule"
    for tag, img in (("pre", pre), ("post", post)):
        h = img[cpos : cpos + 24]
        assert img[cpos : cpos + 16] == CAPSULE_GUID, "capsule GUID missing"
        assert h[19] & 0x40 == 0, f"{tag}: capsule file checksum unsupported"

    new_total = 24 + post_clv["csz"]
    out = bytearray(pre)
    out[cpos : cpos + new_total] = post[cpos : cpos + new_total]
    out[cpos + new_total : pre_end] = b"\xff" * (pre_end - cpos - new_total)
    out_sha = sha256(bytes(out))

    # verification: re-walk the OUTPUT with real-DxeCore semantics
    chk = decompress_inner(bytes(out))
    inv, flen = walk_inner_fv(chk["fv"])
    assert chk["fv"].find(BDS_GUID) > 0 and chk["fv"].find(BDS_GUID) % 8 == 0
    newf = [f for f in inv if f["guid"] == VCN_GUID]
    assert len(newf) == 1, "driver not found / duplicated"
    assert len(inv) == 194, len(inv)
    bds = chk["fv"].find(BDS_GUID)
    assert newf[0]["off"] < bds, "driver must sit before Bds"
    diffs = [i for i in range(0x1000000) if out[i] != pre[i]]
    assert all(cpos <= i < pre_end for i in diffs), "diff outside declared window"
    assert all(out[i] == 0xFF for i in range(cpos + new_total, pre_end))

    OUT.write_bytes(bytes(out))
    MANIFEST.write_text(
        json.dumps(
            {
                "variant": "v003d",
                "what": "booted pre-dump + ONLY the v003c capsule window (donor DXE "
                "+ VCN driver before Bds); live NVRAM/APCB fully preserved",
                "base": {"path": str(PRE), "sha256": PRE_SHA},
                "capsule_source": {"path": str(POST), "sha256": POST_SHA},
                "output_sha256": out_sha,
                "capsule": {
                    "cpos": hex(cpos),
                    "old_csz": hex(pre_clv["csz"]),
                    "new_csz": hex(post_clv["csz"]),
                    "erased_after": hex(cpos + new_total),
                },
                "inner_fv": {"files": len(inv), "len": hex(flen)},
                "diff_window": {
                    "first": hex(min(diffs)),
                    "last": hex(max(diffs)),
                    "ndiff": len(diffs),
                },
                "hardware_written": False,
            },
            indent=2,
        )
        + "\n"
    )
    print(f"v003d OUT sha256: {out_sha}")
    print(
        f"capsule {hex(pre_clv['csz'])} -> {hex(post_clv['csz'])}, "
        f"inner FV {hex(flen)}/{len(inv)} files, diff bytes {len(diffs)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
