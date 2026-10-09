#!/usr/bin/env python3
"""Inject the 6 MeiMeiDXEv3 DXE drivers (FD v2.2, 3.00-based) into clv's own DXE FV.

Method: append 6 whole FFS blobs (byte-exact, headers/checksums preserved) to the
end of clv's inner FV, grow FV length by whole 0x1000 blocks, recompute FV header
checksum, rebuild the FV_IMAGE + GUIDED(LZMA) + capsule FFS layers with the proven
d-series LZMA parameters. Everything outside 0xAE0000-0xE00000 stays byte-identical
to clv. Immediate structural self-validation; exits nonzero on any failure.
"""

from __future__ import annotations
import argparse, hashlib, json, lzma, struct, sys
from pathlib import Path

OUTER_FV = 0xAE0000
OUTER_LEN = 0x320000
CAPSULE_GUID = bytes.fromhex("93fd219e729c154c8c4be77f1db2d792")
MEIMEI = [
    ("A3F8B2D5-7C4E-4F0A-B1D2-9E6F3C8A5B71", "MeiMeiDXEv3_SMU_Unlock"),
    ("7A8B9C0D-1E2F-3A4B-5C6D-7E8F9A0B1C2D", "MeiMeiDXEv3_SMU_Core_Unlock"),
    ("0DDDE9E4-4A0C-4679-BEDC-90A37610AB85", "MeiMeiDXEv3_Menu_Driver"),
    ("A9981D14-6329-4698-AD20-173C4363DD30", "MeiMeiDXEv3_ACPI_AutoInject"),
    ("9D4E5E12-3C7A-4F88-A2B7-0D8D6B7F2E41", "MeiMeiDXEv3_SMU_Patch"),
    ("6C98E4F3-9D8B-4E5A-B2E7-31A45B9C5D81", "MeiMeiDXEv3_ColdBoot"),
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--donor", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    a = ap.parse_args()
    base = a.base.read_bytes()
    donor = a.donor.read_bytes()
    assert len(base) == len(donor) == 0x1000000
    base_sha, donor_sha = sha256(base), sha256(donor)

    clv = decompress_inner(base)
    fdd = decompress_inner(donor)
    clv_inv, clv_flen = walk_inner_fv(clv["fv"])
    fd_inv, _ = walk_inner_fv(fdd["fv"])
    fd_by_guid = {f["guid"]: f for f in fd_inv}
    clv_guids = {f["guid"] for f in clv_inv}

    blobs = []
    for guid, name in MEIMEI:
        assert guid not in clv_guids, f"{guid} already in clv"
        f = fd_by_guid[guid]
        blob = fdd["fv"][f["off"] : f["off"] + f["size"]]
        assert len(blob) == f["size"]
        blobs.append((guid, name, blob))

    # append blobs 8-aligned at FV end, grow length to whole 0x1000 blocks
    new_fv = bytearray(clv["fv"][:clv_flen])
    placements = []
    for guid, name, blob in blobs:
        placements.append((guid, name, len(new_fv), len(blob)))
        new_fv += blob
        while len(new_fv) % 8:
            new_fv += b"\xff"
    new_flen = (len(new_fv) + 0xFFF) & ~0xFFF
    new_fv += b"\xff" * (new_flen - len(new_fv))
    # FV header: length + blockmap + checksum
    num, blk = struct.unpack_from("<II", new_fv, 0x38)
    assert num * blk == clv_flen, (hex(num), hex(blk), hex(clv_flen))
    assert new_flen % blk == 0
    struct.pack_into("<Q", new_fv, 0x20, new_flen)
    struct.pack_into("<I", new_fv, 0x38, new_flen // blk)
    fv_header_checksum(new_fv, 0x48)
    # verify new FV checksum + walk (194 files: 187 + 6 + pad... count check below)
    new_inv, _ = walk_inner_fv(bytes(new_fv))
    assert len(new_inv) == len(clv_inv) + 6, (len(new_inv), len(clv_inv))
    for guid, name, blob in blobs:
        f = [x for x in new_inv if x["guid"] == guid]
        assert len(f) == 1 and f[0]["sha"] == sha256(blob[24:])

    # rebuild inner stream + compress + capsule (FV_IMAGE: size(3) + type(1) + fv)
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
    # capsule header: same GUID/attrs, new size, recomputed header checksum
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

    # self-validation: full re-parse of output
    chk = decompress_inner(bytes(out))
    chk_inv, chk_flen = walk_inner_fv(chk["fv"])
    assert chk_flen == new_flen
    assert len(chk_inv) == len(clv_inv) + 6

    # PSP/APCB identity (entry table compare)
    def psp_entries(img):
        n = struct.unpack_from("<H", img, 0x8E0000 + 8)[0]
        return bytes(img[0x8E0000 : 0x8E0000 + 16 + 16 * n])

    assert psp_entries(bytes(out)) == psp_entries(base)
    assert bytes(out[0xAB1000 : 0xAB1000 + 0xB9C]) == base[0xAB1000 : 0xAB1000 + 0xB9C]

    diffs = [i for i in range(len(base)) if base[i] != out[i]]
    manifest = {
        "candidate": str(a.output),
        "base": {"path": str(a.base), "sha256": base_sha},
        "donor": {"path": str(a.donor), "sha256": donor_sha},
        "output_sha256": out_sha,
        "inner_fv": {
            "old_len": hex(clv_flen),
            "new_len": hex(new_flen),
            "old_files": len(clv_inv),
            "new_files": len(chk_inv),
        },
        "injected": [
            {"guid": g, "name": n, "fv_off": hex(o), "size": hex(s)}
            for g, n, o, s in placements
        ],
        "changed_range": {
            "first": hex(diffs[0]),
            "last": hex(diffs[-1]),
            "ndiff": len(diffs),
        },
        "outside_0xAE0000_0xE00000": "byte-identical",
        "compressed": {"old_csz": hex(old_csz), "new_csz": hex(new_csz)},
    }
    a.output.write_bytes(bytes(out))
    a.manifest.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
