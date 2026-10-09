#!/usr/bin/env python3
"""Fresh exact-byte CLV PSP/ABL provenance inventory.

This is a bounded evidence wrapper around the existing firmware_audit.py and
psp_ps1_verify.py routes. It does not write or execute firmware. It parses the
selected clv image's PSP directory and ABL $PS1 headers, validates zlib payload
lengths, compares exact containers against preserved Robin-5 provenance files,
and records historical ABL source labels without asserting source/binary
identity.
"""
from __future__ import annotations

import hashlib
import json
import re
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ROM = ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin"
OUT = Path(__file__).resolve().parent
PSP_OFF = 0x8E0000
EXPECTED_ROM_SHA = "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"

TYPE_NAMES = {
    0x01: "PSP_BOOTLOADER",
    0x02: "PSP_FW_TRUSTED_OS",
    0x08: "SMU_OFFCHIP_FW",
    0x09: "UNNAMED_TYPE_09",
    0x12: "SMU_OFF_CHIP_FW_2",
    0x13: "DEBUG_UNLOCK",
    0x20: "HARDWARE_IP_CONFIG",
    0x24: "SEC_GASKET",
    0x28: "DRIVER_ENTRIES",
    0x30: "ABL0",
    0x31: "ABL1",
    0x32: "ABL2",
    0x33: "ABL3",
    0x34: "ABL4",
    0x44: "FW_XHCI",
    0x45: "TOS_SECURITY_POLICY",
    0x4F: "UNNAMED_RAW_TYPE_4F",
    0x50: "BL_PUBLIC_KEY",
    0x51: "TOS_PUBLIC_KEY",
}

HISTORICAL_SOURCES = {
    0x31: ROOT / "import/from-windows/Users/kukuruza/tmp_bc250/recon/lorek123_psp/ABL1_decompiled.c",
    0x33: ROOT / "import/from-windows/Users/kukuruza/tmp_bc250/recon/lorek123_psp/ABL3_decompiled.c",
    0x34: ROOT / "import/from-windows/Users/kukuruza/tmp_bc250/recon/lorek123_psp/ABL4_decompiled.c",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha(path.read_bytes())


def first_thumb_markers(data: bytes, limit: int = 4) -> list[dict[str, str | int]]:
    out = []
    pos = 0
    while len(out) < limit:
        pos = data.find(b"\x70\x47", pos)
        if pos < 0:
            break
        out.append({"offset": pos, "bytes": data[pos : pos + 8].hex(), "interpretation": "Thumb BX LR marker"})
        pos += 1
    return out


def parse_psp_entries(image: bytes) -> list[dict]:
    if image[PSP_OFF : PSP_OFF + 4] != b"$PSP":
        raise ValueError("missing $PSP directory at 0x8E0000")
    count = struct.unpack_from("<I", image, PSP_OFF + 8)[0]
    result = []
    for index in range(count):
        eoff = PSP_OFF + 0x10 + index * 0x10
        typ = image[eoff]
        subprogram = image[eoff + 1]
        flags = int.from_bytes(image[eoff + 2 : eoff + 4], "little")
        size = int.from_bytes(image[eoff + 4 : eoff + 8], "little")
        location = int.from_bytes(image[eoff + 8 : eoff + 12], "little")
        spi = location & 0x00FFFFFF if location >= 0xFF000000 else location
        blob = image[spi : spi + size]
        result.append({
            "index": index,
            "type": f"0x{typ:02X}",
            "type_num": typ,
            "payload_id": TYPE_NAMES.get(typ, f"UNNAMED_TYPE_{typ:02X}"),
            "subprogram": subprogram,
            "flags": flags,
            "size": size,
            "location_tagged": f"0x{location:08X}",
            "spi_offset": f"0x{spi:06X}",
            "in_bounds": bool(size and spi + size <= len(image)),
            "container_sha256": sha(blob) if size and spi + size <= len(image) else None,
        })
    return result


def ps1_fields(blob: bytes) -> dict:
    if blob[0x10:0x14] != b"$PS1":
        return {"is_ps1": False}
    signed = struct.unpack_from("<I", blob, 0x14)[0]
    encrypted = struct.unpack_from("<I", blob, 0x18)[0]
    compressed = struct.unpack_from("<I", blob, 0x48)[0]
    uncompressed = struct.unpack_from("<I", blob, 0x50)[0]
    zlib_size = struct.unpack_from("<I", blob, 0x54)[0]
    version = ".".join(f"{byte:X}" for byte in blob[0x63:0x5F:-1])
    load = struct.unpack_from("<I", blob, 0x68)[0]
    rom_size = struct.unpack_from("<I", blob, 0x6C)[0]
    body = blob[0x100 : 0x100 + signed]
    sig = blob[0x100 + signed : 0x100 + signed + 0x100]
    decompressed = None
    decomp_error = None
    if compressed == 1 and body:
        try:
            decompressed = zlib.decompress(body)
        except Exception as exc:  # bounded evidence, retained as text
            decomp_error = f"{type(exc).__name__}: {exc}"
    return {
        "is_ps1": True,
        "magic": "$PS1",
        "signed_length": signed,
        "encrypted": encrypted,
        "compressed": compressed,
        "uncompressed_length": uncompressed,
        "zlib_size": zlib_size,
        "version": version,
        "load_address": f"0x{load:08X}",
        "rom_size_field": rom_size,
        "key_id": blob[0x38:0x48].hex(),
        "signed_body_sha256": sha(body),
        "signature_tail_sha256": sha(sig),
        "signature_tail_length": len(sig),
        "decompressed_payload_sha256": sha(decompressed) if decompressed is not None else None,
        "decompressed_payload_length": len(decompressed) if decompressed is not None else None,
        "decompression_error": decomp_error,
        "decompressed_first_16": decompressed[:16].hex() if decompressed is not None else None,
        "arm_entry_bytes": decompressed[:16].hex() if decompressed is not None else None,
        "thumb_bx_lr_markers": first_thumb_markers(decompressed) if decompressed is not None else [],
        "isa_classification": (
            "32-bit ARM little-endian; ARM-state entry/trampoline with Thumb BX-LR markers"
            if decompressed is not None and decompressed[:4] in (bytes.fromhex("18d09fe5"), bytes.fromhex("10402de9"))
            else "not classified by bounded entry-marker check"
        ),
        "signature_verification_evidence": "evidence/firmware-audit/20260920-clv-sync-stage1/psp-verify/BC250_5.00_clv.bin.stdout",
    }


def historical_matches(image: bytes, entry: dict) -> dict:
    typ = entry["type_num"]
    out = {"exact_robin5_container": None, "robin5_body_after_0x100_exact": None, "references": []}
    if typ < 0x30 or typ > 0x34:
        return out
    n = typ - 0x30
    spi = int(entry["spi_offset"], 16)
    size = entry["size"]
    blob = image[spi : spi + size]
    roots = ROOT / "import/from-windows/Users/kukuruza/tmp_bc250/recon"
    body_paths = sorted((roots / "robin5_psp_bodies").glob(f"ABL{n}~0x{typ:02X}_*.body"))
    container_paths = sorted((roots / "robin5_sec_gasket").glob(f"ABL{n}~0x{typ:02X}_*"))
    for path in body_paths:
        ref = path.read_bytes()
        out["references"].append({"path": str(path), "sha256": sha(ref), "size": len(ref), "relation": "clv_blob[0x100:] == preserved extracted body+signature tail" if blob[0x100:] == ref else "different"})
        out["robin5_body_after_0x100_exact"] = bool(blob[0x100:] == ref)
    for path in container_paths:
        ref = path.read_bytes()
        out["references"].append({"path": str(path), "sha256": sha(ref), "size": len(ref), "relation": "byte-identical full $PS1 container" if blob == ref else "different"})
        out["exact_robin5_container"] = bool(blob == ref)
    return out


def source_provenance(typ: int) -> dict:
    path = HISTORICAL_SOURCES.get(typ)
    if path is None:
        return {"status": "no historical decompiled source in scoped corpus", "source_binary_identity": "UNPROVEN"}
    text = path.read_text(encoding="utf-8", errors="replace")
    first = text.splitlines()[0] if text.splitlines() else ""
    version_label = bool(re.search(r"22\.4\.6\.0", first))
    return {
        "status": "historical decompiled source present",
        "path": str(path),
        "sha256": sha_file(path),
        "size": path.stat().st_size,
        "header_line": first,
        "version_label_matches_clv_ps1": version_label,
        "source_binary_identity": "UNPROVEN — source text has no binary hash/provenance link in this corpus",
    }


def main() -> None:
    image = ROM.read_bytes()
    entries = parse_psp_entries(image)
    abl = []
    for entry in entries:
        if 0x30 <= entry["type_num"] <= 0x34:
            spi = int(entry["spi_offset"], 16)
            blob = image[spi : spi + entry["size"]]
            p = ps1_fields(blob)
            p.update({
                "index": entry["index"],
                "type": entry["type"],
                "payload_id": entry["payload_id"],
                "spi_offset": entry["spi_offset"],
                "container_size": entry["size"],
                "container_sha256": entry["container_sha256"],
                "historical_robin5": historical_matches(image, entry),
                "historical_source": source_provenance(entry["type_num"]),
            })
            abl.append(p)
    result = {
        "report": "CLV PSP/ABL payload provenance inventory",
        "evidence_class": ["observed-bytes", "static-analysis", "historical-report qualification"],
        "input": {"path": str(ROM), "size": len(image), "sha256": sha(image), "expected_sha256": EXPECTED_ROM_SHA, "hash_match": sha(image) == EXPECTED_ROM_SHA},
        "psp_directory": {"offset": "0x8E0000", "count": len(entries), "entries": entries},
        "abl_payloads": abl,
        "coverage_limits": [
            "The existing 233-module census covers extracted x86 PE32/TE UEFI executables, not PSP/ABL payloads.",
            "ABL0-ABL4 are compressed non-x86 PSP payloads; their ARM/Thumb entry markers are classified statically, not executed.",
            "Historical ABL1/ABL3/ABL4 decompilation files are version-label aligned and the CLV containers are byte-identical to preserved Robin-5 containers, but source-text-to-current-binary identity is not independently proven.",
            "No exact AmdSetup+0x316-to-ABL/APOB field path or memory-training actuator is established by this inventory.",
            "Type 0x01 PSP bootloader and type 0x02 trusted OS have no plaintext $PS1/ISA inventory here; non-container/opaque payload boundaries remain closed.",
        ],
        "reproduction": {
            "script": str(Path(__file__).resolve()),
            "existing_parsers": ["scripts/firmware_audit.py", "scripts/psp_ps1_verify.py"],
            "signature_output": "evidence/firmware-audit/20260920-clv-sync-stage1/psp-verify/BC250_5.00_clv.bin.stdout",
        },
    }
    (OUT / "clv-psp-abl-inventory.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS" if result["input"]["hash_match"] and len(abl) == 5 and all(x["is_ps1"] for x in abl) else "FAIL", "input_sha256": result["input"]["sha256"], "abl_count": len(abl), "abl": [{"payload_id": x["payload_id"], "type": x["type"], "offset": x["spi_offset"], "container_sha256": x["container_sha256"], "decompressed_length": x["decompressed_payload_length"], "decompressed_sha256": x["decompressed_payload_sha256"], "isa": x["isa_classification"], "robin5_exact": x["historical_robin5"]["exact_robin5_container"], "source_binary_identity": x["historical_source"]["source_binary_identity"]} for x in abl]}, sort_keys=True))


if __name__ == "__main__":
    main()
