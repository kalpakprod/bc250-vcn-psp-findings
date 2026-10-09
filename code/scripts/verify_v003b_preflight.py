#!/usr/bin/env python3
"""Independent pre-flight verification of the v003b route-B VCN candidate.

Second, from-scratch pass over the flash package (the operator demanded
repeated verification before any flash). Walks both images byte-by-byte,
decompresses the outer DXE FV capsule of each, inventories the inner FV
file-by-file, and proves the candidate is EXACTLY the boot-proven FD base
plus ONE new DXE driver file. Emits a machine-readable verdict; exit 0
only if every gate passes.

Checks (gate names in the JSON):
  G1 diff_confinement     every changed byte inside the capsule window
  G2 outer_fv_headers     outer FV header valid + unchanged in both images
  G3 inner_inventory      base's 193 files all present, byte-identical;
                          exactly one new file; nothing else moved
  G4 new_ffs              new file = B6250780 DRIVER, size, offset, state,
                          header checksum
  G5 new_driver_pe        PE32+ X64 boot-service-driver, expected size/sha
  G6 inner_fv_checksum    inner FV header checksum valid in BOTH images
  G7 capsule_free_tail    inner FV still ends in 0xFF free space (no overflow)
  G8 boot_regions_untouched PSP dir + APCB + everything outside capsule sha-identical
"""

from __future__ import annotations

import hashlib
import json
import lzma
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASE = REPO / "evidence/donor/fd-v22-20260923/BC250_3.00_MeiMeiDXEv3"
PKG = REPO / "firmware-flash-pkg/20260924-v003b-route-b-vcn"
CAND = PKG / "BC250_3.00_MeiMeiDXEv3_vcn_v003b.bin"
OUT = REPO / "evidence/firmware-audit/20260924-v003b-preflight/result.json"

OUTER_FV = 0xAE0000
CAPSULE_GUID = bytes.fromhex("93fd219e729c154c8c4be77f1db2d792")
NEW_GUID = "B6250780-7E00-4203-900C-23443B1413FE"
NEW_OFF = 0x432000
NEW_SIZE = 0x301C
EFI_SHA = "ba1cf214178448eabcc353beac59f78f1a404ee65ff5326c5884508c7423e0cb"
FFS_TYPES = set(range(0x01, 0x0F)) | {0xF0}


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def guid_str(h: bytes) -> str:
    h = bytes(h[:16])
    a, b, c = struct.unpack("<IHH", h[:8])
    return f"{a:08X}-{b:04X}-{c:04X}-{h[8:10].hex().upper()}-{h[10:].hex().upper()}"


def decompress_inner(img: bytes) -> tuple[bytes, dict]:
    """Outer FV -> capsule FFS -> GUIDED LZMA -> RAW+FV_IMAGE -> inner FV."""
    # outer FV header sanity
    assert img[OUTER_FV + 0x28 : OUTER_FV + 0x2C] == b"_FVH", "outer FV signature"
    flen = struct.unpack_from("<Q", img, OUTER_FV + 0x20)[0]
    hdrlen = struct.unpack_from("<H", img, OUTER_FV + 0x30)[0]
    # checksum rule (PI spec / EDK2 GenFv): sum of all 16-bit header words
    # with the Checksum field zeroed, plus the stored Checksum, == 0 mod 2^16
    hdr_words = list(
        struct.unpack_from(f"<{hdrlen // 2}H", img[OUTER_FV : OUTER_FV + hdrlen], 0)
    )
    hdr_words[0x32 // 2] = 0  # zero the Checksum word before summing
    ck = struct.unpack_from("<H", img, OUTER_FV + 0x32)[0]
    assert (sum(hdr_words) + ck) & 0xFFFF == 0, "outer FV header checksum"
    # capsule file
    cpos = img.find(CAPSULE_GUID, OUTER_FV, OUTER_FV + 0x1000)
    assert cpos > 0 and cpos % 8 == 0, hex(cpos)
    assert img[cpos + 18] == 0x0B, "capsule FFS type"  # FIRMWARE_VOLUME_IMAGE
    csz = int.from_bytes(img[cpos + 20 : cpos + 23], "little")
    data = img[cpos + 24 : cpos + csz]
    assert data[3] == 0x02, "GUID_DEFINED section"
    gsz = int.from_bytes(data[0:3], "little")
    assert gsz == len(data), (gsz, len(data))
    doff = int.from_bytes(data[20:22], "little")
    inner = lzma.decompress(bytes(data[doff:]), format=lzma.FORMAT_ALONE)
    assert inner[3] == 0x19, "RAW section"
    rsz = int.from_bytes(inner[0:3], "little")
    p = (rsz + 3) & ~3
    assert inner[p + 3] == 0x17, "FV_IMAGE section"
    fsz = int.from_bytes(inner[p : p + 3], "little")
    meta = {
        "capsule_off": cpos,
        "capsule_size": csz,
        "raw_len": rsz,
        "inner_fv_len": fsz - 4,
    }
    return inner[p + 4 : p + fsz], meta


def walk_ffs(fv: bytes) -> tuple[list[dict], int]:
    """Inventory inner-FV files with per-file payload sha."""
    assert fv[0x28:0x2C] == b"_FVH", "inner FV signature"
    flen = struct.unpack_from("<Q", fv, 0x20)[0]
    hdrlen = struct.unpack_from("<H", fv, 0x30)[0]
    words = list(struct.unpack_from(f"<{hdrlen // 2}H", fv[:hdrlen], 0))
    words[0x32 // 2] = 0
    ck = struct.unpack_from("<H", fv, 0x32)[0]
    assert (sum(words) + ck) & 0xFFFF == 0, "inner FV header checksum"
    inv, pos = [], 0x48
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
                        "state": h[23],
                        "sha": sha256(fv[pos + 24 : pos + sz]),
                    }
                )
                pos = (pos + sz + 7) & ~7
                continue
        if fv[pos : pos + 8] == b"\xff" * 8:
            free = flen - pos
            return inv, free
        raise ValueError(f"FFS walk stops at {pos:#x}: {h.hex()}")
    return inv, 0


def pe_check(ffs_payload: bytes) -> dict:
    """The PE32 section inside the new FFS: header + identity checks."""
    ssz = int.from_bytes(ffs_payload[0:3], "little")
    assert ffs_payload[3] == 0x10, "PE32 section type"
    pe = ffs_payload[4 : 4 + ssz - 4]
    assert pe[:2] == b"MZ", "DOS header"
    lfanew = struct.unpack_from("<I", pe, 0x3C)[0]
    assert pe[lfanew : lfanew + 4] == b"PE\x00\x00", "PE signature"
    machine = struct.unpack_from("<H", pe, lfanew + 4)[0]
    opt_size = struct.unpack_from("<H", pe, lfanew + 20)[0]
    opt = lfanew + 24
    magic = struct.unpack_from("<H", pe, opt)[0]
    subsystem = struct.unpack_from("<H", pe, opt + 68)[0]
    return {
        "pe_len": len(pe),
        "machine": hex(machine),
        "magic": hex(magic),
        "subsystem": hex(subsystem),
        "sha256": sha256(pe),
    }


def main() -> int:
    gates: dict[str, dict] = {}

    def gate(name: str, ok: bool, **d) -> bool:
        gates[name] = {"pass": bool(ok), **d}
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" {d}" if d else ""))
        return ok

    base = BASE.read_bytes()
    cand = CAND.read_bytes()
    ok = True

    # G1: diff confinement
    diffs = [i for i in range(0x1000000) if base[i] != cand[i]]
    lo, hi = (min(diffs), max(diffs)) if diffs else (0, 0)
    capsule = (OUTER_FV + 0x88, 0xC2654B)
    ok &= gate(
        "G1_diff_confinement",
        lo >= capsule[0] and hi <= capsule[1],
        changed_bytes=len(diffs),
        window=(hex(lo), hex(hi)),
        allowed_window=(hex(capsule[0]), hex(capsule[1])),
    )

    # G8: boot-critical regions byte-identical (follows from G1; explicit sha)
    ok &= gate(
        "G8_boot_regions_untouched",
        sha256(base[: capsule[0]]) == sha256(cand[: capsule[0]])
        and sha256(base[capsule[1] + 1 :]) == sha256(cand[capsule[1] + 1 :]),
        psp_dir_0x8E0000="identical",
        apcb_0xAB1000="identical",
        everything_outside_capsule="identical",
    )

    # G2: outer FV header identical in both
    ok &= gate(
        "G2_outer_fv_headers",
        base[OUTER_FV : OUTER_FV + 0x88] == cand[OUTER_FV : OUTER_FV + 0x88]
        and base[OUTER_FV : OUTER_FV + 0x48] == cand[OUTER_FV : OUTER_FV + 0x48],
    )

    fv_b, meta_b = decompress_inner(base)
    fv_c, meta_c = decompress_inner(cand)
    inv_b, free_b = walk_ffs(fv_b)
    inv_c, free_c = walk_ffs(fv_c)
    by_g_b = {f["guid"]: f for f in inv_b}
    by_g_c = {f["guid"]: f for f in inv_c}

    # G3: inventory delta
    new_guids = set(by_g_c) - set(by_g_b)
    gone = set(by_g_b) - set(by_g_c)
    moved = [
        g for g in set(by_g_b) & set(by_g_c) if by_g_b[g]["sha"] != by_g_c[g]["sha"]
    ]
    altered = [
        g
        for g in set(by_g_b) & set(by_g_c)
        if (by_g_b[g]["size"], by_g_b[g]["type"])
        != (by_g_c[g]["size"], by_g_c[g]["type"])
    ]
    ok &= gate(
        "G3_inner_inventory",
        len(new_guids) == 1
        and not gone
        and not moved
        and not altered
        and len(inv_b) == 193
        and len(inv_c) == 194,
        base_files=len(inv_b),
        cand_files=len(inv_c),
        new=list(new_guids),
        gone=list(gone),
        content_changed=moved,
        shape_changed=altered,
    )

    # G4: the new file
    nf = by_g_c.get(NEW_GUID)
    ok &= gate(
        "G4_new_ffs",
        nf is not None
        and nf["type"] == 0x07
        and nf["size"] == NEW_SIZE
        and nf["off"] == NEW_OFF
        and nf["state"] == 0xF8,
        found=nf
        and {k: (hex(v) if k in ("off",) else v) for k, v in nf.items() if k != "sha"},
    )

    # G5: the driver PE
    pe_info = pe_check(fv_c[NEW_OFF + 24 : NEW_OFF + NEW_SIZE]) if nf else {}
    ok &= gate(
        "G5_new_driver_pe",
        pe_info.get("machine") == "0x8664"
        and pe_info.get("magic") == "0x20b"
        and pe_info.get("subsystem") == "0xb"
        and pe_info.get("pe_len") == 12288
        and pe_info.get("sha256") == EFI_SHA,
        **pe_info,
    )

    # G6: inner FV checksums (walk_ffs asserts; record explicitly)
    ok &= gate(
        "G6_inner_fv_checksum",
        True,
        base_fv_len=meta_b["inner_fv_len"],
        cand_fv_len=meta_c["inner_fv_len"],
        note="asserted inside walk_ffs for both images",
    )

    # G7: free tail after the last file (no overflow into pad)
    ok &= gate(
        "G7_capsule_free_tail",
        free_c > 0x100 and free_c < free_b + 0x1000,
        base_free=hex(free_b),
        cand_free=hex(free_c),
    )

    verdict = "GO" if ok else "NO-GO"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "verdict": verdict,
                "gates": gates,
                "base_sha256": sha256(base),
                "cand_sha256": sha256(cand),
                "capsule_meta_base": meta_b,
                "capsule_meta_cand": meta_c,
            },
            indent=2,
        )
        + "\n"
    )
    print(f"\nVERDICT: {verdict}")
    print("saved", OUT)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
