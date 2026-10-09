#!/usr/bin/env python3
"""S3 driver candidate builder: inject the 6 S3A-arbitrated DXE drivers into S2 base.

Credit: FV/FFS/LZMA logic copied from scripts/build_fd_drivers_clv.py
(FD v2.2 -> clv port, output 0968a70c) and parameterized by S3A/S3B verdicts.
Original file is kept intact; this script does not import or modify it.

Method: append 6 whole FFS blobs (byte-exact, headers/checksums preserved) to
the end of the S2 inner FV, grow FV length by whole 0x1000 blocks, optionally
apply S3B-arbitrated Setup-unhide byte change(s) at inner-FV level (same-size
only, pre-recompression), recompute FV header checksum, rebuild the FV_IMAGE +
GUIDED(LZMA) + capsule FFS layers with the proven d-series LZMA parameters.
Everything outside 0xAE0000-0xE00000 stays byte-identical to S2 (S1 NVRAM
bytes asserted). Immediate structural self-validation; exits nonzero on any
failure. BLOCKS (builds nothing) unless S3A replay_go is true.
"""

from __future__ import annotations
import argparse, hashlib, json, lzma, struct, sys
from pathlib import Path

OUTER_FV = 0xAE0000
OUTER_LEN = 0x320000
CAPSULE_GUID = bytes.fromhex("93fd219e729c154c8c4be77f1db2d792")
EXPECTED_S2_SHA256 = "c5dc6424b3d836b0a262ed54d9c3e747f2c33d40cb614fac40e4ea46e7bfbf7c"
# S1 NVRAM bytes that must survive (from S2 build.json assert_only).
S1_ASSERTS = [
    (0x7E5, 0x1A),
    (0x7FF, 0x01),
    (0x83C, 0xFF),
    (0xBD2, 0x01),
    (0xBD3, 0x32),
    (0xBD4, 0x05),
]
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
FFS_TYPES = set(
    [
        0x01,
        0x02,
        0x03,
        0x04,
        0x05,
        0x06,
        0x07,
        0x08,
        0x09,
        0x0A,
        0x0B,
        0x0C,
        0x0D,
        0x0E,
        0x0F,
        0xF0,
    ]
)


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def ffs_header_checksum(header: bytearray) -> None:
    header[16] = 0
    header[16] = (-(sum(header[:16]) + sum(header[18:23]))) & 0xFF


def fv_header_checksum(hdr: bytearray, hdrlen: int) -> None:
    struct.pack_into("<H", hdr, 0x32, 0)
    s = sum(struct.unpack_from(f"<{hdrlen // 2}H", hdr, 0)) & 0xFFFF
    struct.pack_into("<H", hdr, 0x32, (-s) & 0xFFFF)


def guid_str(h: bytes) -> str:
    h = bytes(h[:16])
    a, b, c = struct.unpack("<IHH", h[:8])
    return f"{a:08X}-{b:04X}-{c:04X}-{h[8:10].hex().upper()}-{h[10:].hex().upper()}"


def guid_to_bytes(g: str) -> bytes:
    g = g.replace("-", "")
    raw = bytes.fromhex(g)
    a, b, c = struct.unpack(">IHH", raw[:8])
    return struct.pack("<IHH", a, b, c) + raw[8:]


def walk_inner_fv(fv: bytes):
    assert fv[0x28:0x2C] == b"_FVH"
    flen = struct.unpack_from("<Q", fv, 0x20)[0]
    hdrlen = struct.unpack_from("<H", fv, 0x30)[0]
    assert flen <= len(fv)
    inv, pos = [], 0x48
    assert hdrlen == 0x48, hex(hdrlen)
    while pos + 24 <= flen:
        h = bytes(fv[pos : pos + 24])
        typ = h[18]
        if typ in FFS_TYPES:
            sz = int.from_bytes(h[20:23], "little")
            if (
                sz >= 24
                and pos + sz <= flen
                and (sum(h[:17]) + sum(h[18:23])) & 0xFF == 0
            ):
                inv.append(
                    {
                        "guid": guid_str(h),
                        "type": typ,
                        "size": sz,
                        "off": pos,
                        "sha": sha256(bytes(fv[pos + 24 : pos + sz])),
                    }
                )
                pos = (pos + sz + 7) & ~7
                continue
        if bytes(fv[pos : pos + 8]) == b"\xff" * 8:
            pos += 8
            continue
        raise ValueError(f"FFS walk stops at {pos:#x}: {h.hex()}")
    return inv, flen


def decompress_inner(img: bytes):
    cpos = img.find(CAPSULE_GUID, OUTER_FV, OUTER_FV + 0x1000)
    assert cpos > 0 and cpos % 8 == 0
    assert img[cpos + 18] == 0x0B
    csz = int.from_bytes(img[cpos + 20 : cpos + 23], "little")
    data = img[cpos + 24 : cpos + csz]
    assert data[3] == 0x02  # GUID_DEFINED
    gsz = int.from_bytes(data[0:3], "little")
    assert gsz == len(data), (gsz, len(data))
    doff = int.from_bytes(data[20:22], "little")
    inner = lzma.decompress(bytes(data[doff:]), format=lzma.FORMAT_ALONE)
    assert inner[3] == 0x19  # RAW
    rsz = int.from_bytes(inner[0:3], "little")
    p = (rsz + 3) & ~3
    assert inner[p + 3] == 0x17  # FV_IMAGE
    fsz = int.from_bytes(inner[p : p + 3], "little")
    return {
        "cpos": cpos,
        "csz": csz,
        "guided_hdr": bytes(data[:doff]),
        "raw": bytes(inner[:rsz]),
        "raw_pad": p - rsz,
        "fv": bytes(inner[p + 4 : p + fsz]),
    }


def parse_offset(v) -> int:
    if isinstance(v, int):
        return v
    s = str(v).strip()
    return int(s, 16 if s.lower().startswith("0x") else 10)


def parse_byte(v) -> int:
    if isinstance(v, int):
        assert 0 <= v <= 0xFF
        return v
    s = str(v).strip().lower().removeprefix("0x")
    assert len(s) == 2, f"expected single byte hex, got {v!r}"
    return int(s, 16)


def apply_unhide_inner(new_fv: bytearray, new_inv, changes):
    """Apply S3B byte change(s) at inner-FV level, same-size only.

    Each change: {file, offset, old, new, proof}. `file` is an FFS GUID
    (full or 8-hex prefix); `offset` is FFS-START-relative (includes the
    24-byte FFS header; verified 57/57 old-byte match for S3B on this
    convention vs 15/57 body-relative). Header bytes (off < 24) are
    rejected. Only single-byte same-size edits; FFS File checksum
    recomputed when ATTRIB_CHECKSUM (0x40) is set.
    Returns list of applied records for provenance.
    """
    applied = []
    for ch in changes:
        file_id = str(ch["file"]).upper()
        off = parse_offset(ch["offset"])
        old, new = parse_byte(ch["old"]), parse_byte(ch["new"])
        cands = [
            f for f in new_inv if f["guid"] == file_id or f["guid"].startswith(file_id)
        ]
        assert len(cands) == 1, f"unhide file {file_id}: {len(cands)} matches"
        f = cands[0]
        body_off, body_len = f["off"] + 24, f["size"] - 24
        assert 24 <= off < f["size"], (
            f"off {off:#x} outside patchable range (24..{f['size']:#x})"
        )
        abs_off = f["off"] + off
        assert new_fv[abs_off] == old, (
            f"{file_id}+{off:#x}: expected old {old:#04x}, found {new_fv[abs_off]:#04x}"
        )
        new_fv[abs_off] = new
        # Recompute FFS File checksum (byte 17) when attribute bit requires it.
        hdr = new_fv[f["off"] : f["off"] + 24]
        if hdr[19] & 0x40:
            body = bytes(new_fv[body_off : body_off + body_len])
            new_fv[f["off"] + 17] = (-sum(body)) & 0xFF
        applied.append(
            {
                "file": f["guid"],
                "offset": hex(off),
                "old": hex(old),
                "new": hex(new),
                "fv_off": hex(abs_off),
                "proof": ch.get("proof", ""),
            }
        )
    # Re-walk to confirm structural validity after patch.
    chk_inv, _ = walk_inner_fv(bytes(new_fv))
    assert len(chk_inv) == len(new_inv)
    return applied


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--s2-base", type=Path, required=True)
    ap.add_argument("--donor", type=Path, required=True)
    ap.add_argument("--s3a-verdict", type=Path, required=True)
    ap.add_argument("--s3b-verdict", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--provenance", type=Path, required=True)
    a = ap.parse_args()

    s3a = json.loads(a.s3a_verdict.read_text())
    s3b = json.loads(a.s3b_verdict.read_text())
    assert s3a.get("replay_go") is True, "S3A replay_go is not true: BLOCKED"
    inputs = s3a.get("inputs", [])
    assert len(inputs) == 6, f"expected exactly 6 arbitrated drivers, got {len(inputs)}"

    base = a.s2_base.read_bytes()
    donor = a.donor.read_bytes()
    assert len(base) == len(donor) == 0x1000000
    base_sha, donor_sha = sha256(base), sha256(donor)
    assert base_sha == EXPECTED_S2_SHA256, f"S2 base hash mismatch: {base_sha}"
    for off, val in S1_ASSERTS:
        assert base[off] == val, f"S2 base S1 byte {off:#x}: {base[off]:#x} != {val:#x}"

    clv = decompress_inner(base)
    fdd = decompress_inner(donor)
    clv_inv, clv_flen = walk_inner_fv(clv["fv"])
    fd_inv, _ = walk_inner_fv(fdd["fv"])
    fd_by_guid = {f["guid"]: f for f in fd_inv}
    clv_guids = {f["guid"] for f in clv_inv}

    blobs = []
    for entry in inputs:
        guid = str(entry["guid"]).upper()
        name = str(entry.get("driver", guid))
        assert guid not in clv_guids, f"{guid} already in S2 FV"
        assert guid in fd_by_guid, f"{guid} not found in donor FV"
        f = fd_by_guid[guid]
        blob = fdd["fv"][f["off"] : f["off"] + f["size"]]
        assert len(blob) == f["size"]
        if entry.get("size"):
            assert f["size"] == parse_offset(entry["size"]), (
                f"{guid} size {f['size']:#x} != verdict {entry['size']}"
            )
        if entry.get("sha256"):
            # S3A sha256 is the full-FFS-blob sha (verified 6/6 pre-build).
            assert sha256(blob) == str(entry["sha256"]).lower(), (
                f"{guid} blob sha mismatch vs S3A verdict"
            )
        blobs.append((guid, name, blob))

    # Append blobs 8-aligned at FV end, grow length to whole 0x1000 blocks.
    new_fv = bytearray(clv["fv"][:clv_flen])
    placements = []
    for guid, name, blob in blobs:
        placements.append((guid, name, len(new_fv), len(blob)))
        new_fv += blob
        while len(new_fv) % 8:
            new_fv += b"\xff"

    new_flen = (len(new_fv) + 0xFFF) & ~0xFFF
    new_fv += b"\xff" * (new_flen - len(new_fv))
    # FV header: length + blockmap + checksum.
    num, blk = struct.unpack_from("<II", new_fv, 0x38)
    assert num * blk == clv_flen, (hex(num), hex(blk), hex(clv_flen))
    assert new_flen % blk == 0
    struct.pack_into("<Q", new_fv, 0x20, new_flen)
    struct.pack_into("<I", new_fv, 0x38, new_flen // blk)
    fv_header_checksum(new_fv, 0x48)
    new_inv, _ = walk_inner_fv(bytes(new_fv))
    assert len(new_inv) == len(clv_inv) + 6, (len(new_inv), len(clv_inv))

    # S3B unhide: inner-FV-level same-size patch BEFORE recompression.
    # Body-only edits keep sizes and the header checksum valid.
    unhide_applied: list = []
    unhide_skipped_note = ""
    if s3b.get("unhide_go") is True:
        changes = s3b.get("changes", [])
        assert len(changes) >= 1, "unhide_go true but no changes listed"
        unhide_applied = apply_unhide_inner(new_fv, new_inv, changes)
    else:
        unhide_skipped_note = (
            "S3B unhide_go false: Setup-unhide deferred, "
            f"reason: {s3b.get('reason', 'see S3B verdict')}"
        )
    for guid, name, blob in blobs:
        f = [x for x in new_inv if x["guid"] == guid]
        if unhide_applied and f[0]["guid"] in {c["file"] for c in unhide_applied}:
            continue  # patched file body intentionally differs from donor
        assert len(f) == 1 and f[0]["sha"] == sha256(blob[24:])

    # Rebuild inner stream + compress + capsule.
    fvim = int.to_bytes(len(new_fv) + 4, 3, "little") + b"\x17" + bytes(new_fv)
    stream = clv["raw"] + b"\x00" * clv["raw_pad"] + fvim
    compressed = lzma.compress(
        bytes(stream), format=lzma.FORMAT_ALONE, filters=LZMA_FILTERS
    )
    guided = bytearray(clv["guided_hdr"])
    new_gsz = len(guided) + len(compressed)
    guided[0:3] = int.to_bytes(new_gsz, 3, "little")
    new_csz = 24 + len(guided) + len(compressed)
    cpos, old_csz = clv["cpos"], clv["csz"]
    outer_end = OUTER_FV + OUTER_LEN
    assert all(b == 0xFF for b in base[cpos + old_csz : outer_end]), (
        "non-FF bytes after capsule"
    )
    assert cpos + new_csz <= outer_end, (hex(cpos + new_csz), hex(outer_end))
    cap_hdr = bytearray(base[cpos : cpos + 24])
    assert cap_hdr[19] & 0x40 == 0, "capsule has file checksum; unsupported"
    cap_hdr[20:23] = int.to_bytes(new_csz, 3, "little")
    ffs_header_checksum(cap_hdr)
    out = bytearray(base)
    out[cpos : cpos + 24] = cap_hdr
    out[cpos + 24 : cpos + new_csz] = bytes(guided) + bytes(compressed)
    out[cpos + new_csz : outer_end] = b"\xff" * (outer_end - cpos - new_csz)
    assert bytes(out[:OUTER_FV]) == base[:OUTER_FV]
    assert bytes(out[outer_end:]) == base[outer_end:]
    out_sha = sha256(bytes(out))

    # Self-validation: full re-parse of output.
    chk = decompress_inner(bytes(out))
    chk_inv, chk_flen = walk_inner_fv(chk["fv"])
    assert chk_flen == new_flen
    assert len(chk_inv) == len(clv_inv) + 6
    for off, val in S1_ASSERTS:
        assert out[off] == val, f"output S1 byte {off:#x} changed"

    def psp_entries(img):
        n = struct.unpack_from("<H", img, 0x8E0000 + 8)[0]
        return bytes(img[0x8E0000 : 0x8E0000 + 16 + 16 * n])

    assert psp_entries(bytes(out)) == psp_entries(base)
    assert bytes(out[0xAB1000 : 0xAB1000 + 0xB9C]) == base[0xAB1000 : 0xAB1000 + 0xB9C]

    diffs = [i for i in range(len(base)) if base[i] != out[i]]
    prov = {
        "profile": "s3-drv",
        "builder": "scripts/build_s3_drivers.py",
        "builder_credit": "FV/FFS/LZMA logic copied from scripts/build_fd_drivers_clv.py (FD->clv 0968a70c); original intact",
        "base_path": str(a.s2_base),
        "base_hash": base_sha,
        "donor_path": str(a.donor),
        "donor_hash": donor_sha,
        "output_path": str(a.output),
        "output_hash": out_sha,
        "s3a_verdict": {
            "file": str(a.s3a_verdict),
            "sha256": sha256(a.s3a_verdict.read_bytes()),
            "replay_go": True,
        },
        "s3b_verdict": {
            "file": str(a.s3b_verdict),
            "sha256": sha256(a.s3b_verdict.read_bytes()),
            "unhide_go": bool(s3b.get("unhide_go")),
        },
        "inner_fv": {
            "old_len": hex(clv_flen),
            "new_len": hex(new_flen),
            "old_files": len(clv_inv),
            "new_files": len(chk_inv),
        },
        "injected": [
            {
                "guid": g,
                "name": n,
                "fv_off": hex(o),
                "size": hex(s),
                "blob_sha256": sha256(b),
                "body_sha256": sha256(b[24:]),
            }
            for (g, n, o, s), (_, _, b) in zip(placements, blobs)
        ],
        "unhide": (
            {"applied": unhide_applied}
            if unhide_applied
            else {"applied": [], "skipped": unhide_skipped_note}
        ),
        "s1_nvram_asserted": [{f"{off:#x}": f"{val:#04x}"} for off, val in S1_ASSERTS],
        "changed_range": {
            "first": hex(diffs[0]),
            "last": hex(diffs[-1]),
            "ndiff": len(diffs),
        },
        "outside_0xAE0000_0xE00000": "byte-identical to S2",
        "compressed": {"old_csz": hex(old_csz), "new_csz": hex(new_csz)},
        "status": "EXPERIMENTAL_REQUEST_ONLY_NOT_FLASH_APPROVED",
        "hardware_written": False,
        "unverified": [
            "dxe dispatch on 5.00-lineage base",
            "depex satisfiability at runtime",
            "menu visibility effect",
            "boot",
            "stability",
        ],
    }
    a.output.write_bytes(bytes(out))
    a.provenance.write_text(json.dumps(prov, indent=2) + "\n")
    print(json.dumps(prov, indent=2))


if __name__ == "__main__":
    main()
