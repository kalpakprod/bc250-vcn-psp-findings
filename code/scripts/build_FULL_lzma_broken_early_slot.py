#!/usr/bin/env python3
"""Build BC250_vcn-driver-FULL_lzma-BROKEN_early-slot.bin (alias v004): booted pre-dump + full VCN driver WITH a Depex section, LZMA header left broken (unknown size).

The SUPERSEDED v003e build (no Depex) hung early DXE: the driver poked PCI
0xB8/0xBC before the NBIO host bridge was ready. This BROKEN build injects
the same driver but the FFS now
carries a real DEPEX section (TRUE, 06 00 00 13 06 08) so the dispatcher
schedules it in the normal dependency queue, after PCI is published, instead
of the earliest no-DEPEX pool. Everything else is identical to the
SUPERSEDED v003e build: base =
the board's own booted image, diff confined to the capsule window.

Blob: candidates/vcn-unlock-driver-v000-DRAFT/bin/Bc250VcnUnlockDxe-final.ffs
      (PE32 section + DEPEX TRUE section, 12322 B, type 0x07, state 0x07 ->
      normalized 0xF8 in-image)
Base: evidence/programmer/reads/20260924-v003c/pre-v003c-read-a.bin
      (sha 64973ba364ae4417de10bd905d2cf8bad165af3b544d175b3cc315f0e28d621a)
Output: candidates/BC250_vcn-driver-FULL_lzma-BROKEN_early-slot.bin (new, never overwrite)
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
BLOB = REPO / "candidates/vcn-unlock-driver-v000-DRAFT/bin/Bc250VcnUnlockDxe-final.ffs"
OUT = REPO / "candidates/BC250_vcn-driver-FULL_lzma-BROKEN_early-slot.bin"
MANIFEST = REPO / "candidates/BC250_vcn-driver-FULL_lzma-BROKEN_early-slot.build.json"

PRE_SHA = "64973ba364ae4417de10bd905d2cf8bad165af3b544d175b3cc315f0e28d621a"
VCN_GUID = "B6250780-7E00-4203-900C-23443B1413FE"
BDS_GUID = bytes.fromhex("828f4b8f919b284086e6f4db7d4c1dff")
STATE_IN_IMAGE = 0xF8
DEPEX_SEC_TYPE = 0x13
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


def sections_of(ffs: bytes) -> list[tuple[int, int]]:
    """Return [(type, size)] of the FFS body sections (best-effort walk)."""
    body = ffs[24:]
    out, o = [], 0
    while o + 4 <= len(body):
        sz = int.from_bytes(body[o : o + 3], "little")
        t = body[o + 3]
        if sz < 4 or o + sz > len(body):
            break
        out.append((t, sz))
        o += sz
    return out


def main() -> int:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite existing output: {OUT}")
    pre = PRE.read_bytes()
    assert len(pre) == 0x1000000 and sha256(pre) == PRE_SHA

    blob = bytearray(BLOB.read_bytes())
    blob_sha = sha256(bytes(blob))
    assert blob[18] == 0x07, f"FFS type {blob[18]:#x} != DRIVER"
    assert guid_str(blob) == VCN_GUID, guid_str(blob)
    assert (sum(blob[:17]) + sum(blob[18:23])) & 0xFF == 0, "header checksum"
    secs = sections_of(bytes(blob))
    types = [t for t, _ in secs]
    assert 0x10 in types, f"no PE32 in blob: {secs}"
    assert DEPEX_SEC_TYPE in types, f"no DEPEX section in blob: {secs}"
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
    assert (prev["off"] + prev["size"] + 7) & ~7 == bds_pos

    pad = (8 - (len(blob) % 8)) % 8
    new_fv = (
        bytearray(clv["fv"][:bds_pos]) + blob + b"\xff" * pad + clv["fv"][bds_pos:flen]
    )
    new_flen = (len(new_fv) + blk - 1) & ~(blk - 1)
    assert new_flen - len(new_fv) < blk, "unexpected growth"
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

    # verification
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
    # the embedded FFS in the output must still carry the DEPEX section
    embedded = chk["fv"][bds_pos : bds_pos + len(blob)]
    assert DEPEX_SEC_TYPE in [t for t, _ in sections_of(embedded)], (
        "depsex lost in-image"
    )
    diffs = [i for i in range(0x1000000) if out[i] != pre[i]]
    assert all(cpos <= i < outer_end for i in diffs), "diff escaped capsule"

    OUT.write_bytes(bytes(out))
    MANIFEST.write_text(
        json.dumps(
            {
                "plain_name": "BC250_vcn-driver-FULL_lzma-BROKEN_early-slot.bin",
                "alias": "v004",
                "builder": "scripts/build_FULL_lzma_broken_early_slot.py",
                "variant": "v004",
                "what": "board's own booted BIOS + VCN driver (WITH DEPEX TRUE section) "
                "before Bds.ffs; diff confined to capsule; live NVRAM/APCB intact",
                "depex_fix_vs_superseded_v003e": "driver FFS now carries a DEPEX section (TRUE) so "
                "DxeCore does not dispatch it in the earliest no-DEPEX pool",
                "base": {"path": str(PRE), "sha256": PRE_SHA},
                "blob": {
                    "path": str(BLOB),
                    "sha256": blob_sha,
                    "sections": [[hex(t), s] for t, s in sections_of(bytes(blob))],
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
                    "fv_off": hex(bds_pos),
                    "size": hex(len(blob)),
                    "depex_section_present": True,
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
    print(f"BROKEN_early-slot OUT sha256: {out_sha}")
    print(
        f"inner FV {hex(flen)} -> {hex(new_flen)}, {len(inv)} -> {len(chk_inv)} files"
    )
    print(f"driver @{hex(bds_pos)} (DEPEX present) before Bds -> {hex(chk_bds)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
