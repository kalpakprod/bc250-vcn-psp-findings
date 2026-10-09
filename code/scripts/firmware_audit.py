#!/usr/bin/env python3
"""Read-only AMD BC-250 firmware inventory and UEFI FV/FFS extractor.

This adapter is intentionally path-parameterized and standard-library-only. It
reuses the project-observed PSP/BHD/APCB and UEFI layout rules without touching
an input image. Executable sections are copied to a separate output tree with
hashes and structural provenance; no key or signature material is printed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import lzma
import re
import struct
from pathlib import Path
from typing import Any, Iterable

PSP_OFF = 0x8E0000
BHD_OFF = 0xAB0000
APCB_OFF = 0xAB1000
LZMA_GUID = bytes.fromhex("98584eee143959429d6edc7bd79403cf")
SECURITY_CORE_GUID = bytes.fromhex("2e06a01b79c782458566336ae8f78f09")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def u24(data: bytes, off: int) -> int:
    return int.from_bytes(data[off : off + 3], "little")


def fletcher32(data: bytes) -> int:
    if len(data) % 2:
        data += b"\0"
    s1 = s2 = 0
    for off in range(0, len(data), 2):
        word = data[off] | (data[off + 1] << 8)
        s1 = (s1 + word) % 65535
        s2 = (s2 + s1) % 65535
    return (s2 << 16) | s1


def apcb_checksum(data: bytes, off: int, size: int) -> int:
    total = sum(data[off : off + size]) - data[off + 0x10]
    return (-total) & 0xFF


def safe_name(text: str, fallback: str) -> str:
    text = re.sub(r"[^A-Za-z0-9_.@#-]+", "_", text).strip("._")
    return (text or fallback)[:100]


def guid_string(raw: bytes) -> str:
    if len(raw) != 16:
        return ""
    d1, d2, d3 = struct.unpack_from("<IHH", raw, 0)
    return f"{d1:08X}-{d2:04X}-{d3:04X}-{raw[8:10].hex().upper()}-{raw[10:16].hex().upper()}"


def find_fv_headers(data: bytes) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    pos = 0
    while True:
        sig = data.find(b"_FVH", pos)
        if sig < 0:
            break
        base = sig - 0x28
        if base >= 0 and base + 0x38 <= len(data) and data[base + 0x28 : base + 0x2C] == b"_FVH":
            fv_len = int.from_bytes(data[base + 0x20 : base + 0x28], "little")
            header_len = int.from_bytes(data[base + 0x30 : base + 0x32], "little")
            if 0x1000 <= fv_len <= len(data) - base and 0x30 <= header_len <= fv_len:
                result.append({
                    "base": base,
                    "length": fv_len,
                    "header_length": header_len,
                    "attributes": int.from_bytes(data[base + 0x2C : base + 0x30], "little"),
                    "filesystem_guid": guid_string(data[base + 0x10 : base + 0x20]),
                })
        pos = sig + 1
    unique: dict[tuple[int, int], dict[str, Any]] = {}
    for item in result:
        unique[(item["base"], item["length"])] = item
    return [unique[key] for key in sorted(unique)]


def parse_psp(data: bytes, off: int = PSP_OFF) -> dict[str, Any] | None:
    if off + 0x10 > len(data) or data[off : off + 4] != b"$PSP":
        return None
    checksum, count, info = struct.unpack_from("<III", data, off + 4)
    end = off + 0x10 + 16 * count
    calc = fletcher32(data[off + 8 : end]) if end <= len(data) else None
    entries: list[dict[str, Any]] = []
    for index in range(count):
        eoff = off + 0x10 + index * 16
        if eoff + 16 > len(data):
            break
        typ = data[eoff]
        subprogram = data[eoff + 1]
        flags = int.from_bytes(data[eoff + 2 : eoff + 4], "little")
        size = int.from_bytes(data[eoff + 4 : eoff + 8], "little")
        location = int.from_bytes(data[eoff + 8 : eoff + 12], "little")
        reserved = int.from_bytes(data[eoff + 12 : eoff + 16], "little")
        spi = location & 0x00FFFFFF if location >= 0xFF000000 else location
        in_bounds = bool(size and spi + size <= len(data))
        entries.append({
            "index": index,
            "type": typ,
            "subprogram": subprogram,
            "flags": flags,
            "size": size,
            "location": location,
            "spi_offset": spi,
            "reserved": reserved,
            "in_bounds": in_bounds,
            "body_sha256": sha256_bytes(data[spi : spi + size]) if in_bounds else None,
        })
    return {
        "offset": off,
        "stored_fletcher32": f"0x{checksum:08X}",
        "calculated_fletcher32": f"0x{calc:08X}" if calc is not None else None,
        "checksum_match": calc == checksum,
        "count": count,
        "info": f"0x{info:08X}",
        "entries": entries,
    }


def parse_bhd(data: bytes, off: int = BHD_OFF) -> dict[str, Any] | None:
    if off + 0x10 > len(data) or data[off : off + 4] != b"$BHD":
        return None
    checksum, count, info = struct.unpack_from("<III", data, off + 4)
    end = off + 0x10 + 24 * count
    calc = fletcher32(data[off + 8 : end]) if end <= len(data) else None
    entries: list[dict[str, Any]] = []
    for index in range(count):
        eoff = off + 0x10 + index * 24
        if eoff + 24 > len(data):
            break
        typ, region_type, flags = data[eoff], data[eoff + 1], int.from_bytes(data[eoff + 2 : eoff + 4], "little")
        size = int.from_bytes(data[eoff + 4 : eoff + 8], "little")
        location = int.from_bytes(data[eoff + 8 : eoff + 12], "little")
        reserved = int.from_bytes(data[eoff + 12 : eoff + 16], "little")
        destination = int.from_bytes(data[eoff + 16 : eoff + 24], "little")
        spi = location & 0x00FFFFFF if location >= 0xFF000000 else location
        in_bounds = bool(size and spi + size <= len(data))
        entries.append({
            "index": index,
            "type": typ,
            "region_type": region_type,
            "flags": flags,
            "size": size,
            "location": location,
            "spi_offset": spi,
            "reserved": reserved,
            "destination": destination,
            "in_bounds": in_bounds,
            "body_sha256": sha256_bytes(data[spi : spi + size]) if in_bounds else None,
        })
    return {
        "offset": off,
        "stored_fletcher32": f"0x{checksum:08X}",
        "calculated_fletcher32": f"0x{calc:08X}" if calc is not None else None,
        "checksum_match": calc == checksum,
        "count": count,
        "info": f"0x{info:08X}",
        "entries": entries,
    }


def parse_apcb(data: bytes, off: int = APCB_OFF) -> dict[str, Any] | None:
    if off + 0x20 > len(data) or data[off : off + 4] != b"APCB":
        return None
    size = int.from_bytes(data[off + 8 : off + 12], "little")
    end = off + size
    stored = data[off + 0x10] if off + 0x10 < len(data) else None
    calc = apcb_checksum(data, off, size) if 0x20 <= size <= len(data) - off else None
    groups: list[dict[str, Any]] = []
    p = off + 0x20
    while p + 0x10 <= end and p + 0x10 <= len(data):
        signature = data[p : p + 4].decode("latin1", "replace")
        gid, flags, instance, group_size = struct.unpack_from("<HHII", data, p + 4)
        if group_size < 0x10 or p + group_size > end:
            groups.append({"offset": p, "signature": signature, "gid": gid, "flags": flags, "instance": instance, "size": group_size, "valid": False})
            break
        groups.append({"offset": p, "signature": signature, "gid": gid, "flags": flags, "instance": instance, "size": group_size, "valid": True})
        p += group_size
    words: dict[str, Any] = {}
    for rel in (0x130, 0x16C):
        if rel + 4 <= size:
            words[f"0x{rel:X}"] = f"0x{int.from_bytes(data[off + rel : off + rel + 4], 'little'):08X}"
    return {
        "offset": off,
        "size": size,
        "stored_checksum_byte": f"0x{stored:02X}" if stored is not None else None,
        "calculated_checksum_byte": f"0x{calc:02X}" if calc is not None else None,
        "checksum_match": stored == calc,
        "group_count": len(groups),
        "groups": groups,
        "dfg_words": words,
    }


def parse_sections(blob: bytes) -> Iterable[tuple[int, int, bytes]]:
    off = 0
    while off + 4 <= len(blob):
        size = u24(blob, off)
        section_type = blob[off + 3]
        header_size = 4
        if size == 0xFFFFFF:
            if off + 8 > len(blob):
                break
            size = int.from_bytes(blob[off + 4 : off + 8], "little")
            header_size = 8
        if size < header_size or off + size > len(blob):
            break
        yield off, section_type, blob[off + header_size : off + size]
        off = (off + size + 3) & ~3


def decode_ui(body: bytes) -> str:
    try:
        # Preserve the final UTF-16 code unit before the two-byte terminator.
        return body.decode("utf-16-le", "ignore").split("\x00", 1)[0]
    except Exception:
        return ""


def lzma_attempts(raw: bytes) -> Iterable[bytes]:
    # EDK2 compression sections carry a LZMA-alone header; GUIDed sections
    # usually carry the same stream after a data-offset field.
    try:
        yield lzma.decompress(raw, format=lzma.FORMAT_ALONE)
    except (lzma.LZMAError, EOFError, ValueError):
        pass
    if len(raw) >= 5:
        props = raw[0]
        lc = props % 9
        lp = (props // 9) % 5
        pb = props // 45
        dict_size = int.from_bytes(raw[1:5], "little")
        for candidate in (dict_size, 1 << 27, 1 << 24, 1 << 20):
            try:
                yield lzma.decompress(raw[5:], format=lzma.FORMAT_RAW, filters=[{"id": lzma.FILTER_LZMA1, "dict_size": candidate, "lc": lc, "lp": lp, "pb": pb}])
            except (lzma.LZMAError, EOFError, ValueError):
                continue


class Extractor:
    def __init__(self, image: bytes, output: Path, label: str):
        self.image = image
        self.output = output
        self.label = safe_name(label, "image")
        self.records: list[dict[str, Any]] = []
        self.saved: dict[str, str] = {}
        self.seen_fvs: set[tuple[str, int, int]] = set()
        self.max_depth = 10

    def save_executable(self, body: bytes, image_type: str, context: dict[str, Any]) -> None:
        if image_type not in ("PE32", "TE") or not body:
            return
        digest = sha256_bytes(body)
        if digest not in self.saved:
            index = len(self.saved)
            stem = safe_name(context.get("ui") or context.get("ffs_guid", "module"), "module")
            path = self.output / "modules" / f"{index:04d}_{stem}_{image_type.lower()}.bin"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
            self.saved[digest] = str(path.relative_to(self.output))
        self.records.append({
            "local_path": self.saved[digest],
            "sha256": digest,
            "size": len(body),
            "image_type": image_type,
            "ui": context.get("ui", ""),
            "ffs_guid": context.get("ffs_guid", ""),
            "ffs_type": context.get("ffs_type"),
            "fv_base": context.get("fv_base"),
            "ffs_offset": context.get("ffs_offset"),
            "section_offset": context.get("section_offset"),
            "origin": context.get("origin", ""),
        })

    def walk_sections(self, blob: bytes, context: dict[str, Any], depth: int) -> None:
        if depth > self.max_depth:
            return
        sections = list(parse_sections(blob))
        ui = next((decode_ui(body) for _, typ, body in sections if typ == 0x15), "")
        local = dict(context)
        if ui:
            local["ui"] = ui
        for section_offset, section_type, body in sections:
            if section_type == 0x10 and body[:2] == b"MZ":
                self.save_executable(body, "PE32", {**local, "section_offset": section_offset})
            elif section_type == 0x12 and body[:2] == b"VZ":
                self.save_executable(body, "TE", {**local, "section_offset": section_offset})
            elif section_type == 0x01 and len(body) >= 5 and body[4] == 1:
                decoded = next(iter(lzma_attempts(body[5:])), None)
                if decoded:
                    self.walk_nested(decoded, {**local, "origin": f"{local.get('origin', '')}/compression@0x{section_offset:X}"}, depth + 1)
            elif section_type == 0x02 and body[:16] == LZMA_GUID:
                candidates: list[bytes] = []
                if len(body) >= 0x14:
                    data_offset = int.from_bytes(body[0x10:0x12], "little")
                    if data_offset >= 4 and data_offset - 4 < len(body):
                        candidates.append(body[data_offset - 4 :])
                    candidates.append(body[0x14:])
                candidates.append(body)
                decoded = None
                for raw in candidates:
                    decoded = next(iter(lzma_attempts(raw)), None)
                    if decoded:
                        break
                if decoded:
                    self.walk_nested(decoded, {**local, "origin": f"{local.get('origin', '')}/guided@0x{section_offset:X}"}, depth + 1)
            elif section_type == 0x18 and len(body) >= 16:
                # EFI_SECTION_FREEFORM_SUBTYPE_GUID contains a subtype GUID
                # followed by a payload that may itself be a PE32/TE section.
                subtype_guid = guid_string(body[:16])
                nested = body[16:]
                nested_context = {**local, "origin": f"{local.get('origin', '')}/freeform-{subtype_guid}@0x{section_offset:X}"}
                if nested[:2] == b"MZ":
                    self.save_executable(nested, "PE32", {**nested_context, "section_offset": section_offset})
                elif nested[:2] == b"VZ":
                    self.save_executable(nested, "TE", {**nested_context, "section_offset": section_offset})
                else:
                    self.walk_nested(nested, nested_context, depth + 1)
            elif section_type == 0x17:
                self.walk_nested(body, {**local, "origin": f"{local.get('origin', '')}/fv-image@0x{section_offset:X}"}, depth + 1)

    def walk_nested(self, blob: bytes, context: dict[str, Any], depth: int) -> None:
        fvs = find_fv_headers(blob)
        if fvs:
            for fv in fvs:
                self.walk_fv(blob, fv["base"], {**context, "nested_base": fv["base"]}, depth)
        else:
            self.walk_sections(blob, context, depth)

    def walk_fv(self, blob: bytes, base: int, context: dict[str, Any], depth: int) -> None:
        if depth > self.max_depth or base < 0 or base + 0x38 > len(blob):
            return
        if blob[base + 0x28 : base + 0x2C] != b"_FVH":
            return
        fv_len = int.from_bytes(blob[base + 0x20 : base + 0x28], "little")
        header_len = int.from_bytes(blob[base + 0x30 : base + 0x32], "little")
        if not (0x1000 <= fv_len <= len(blob) - base and 0x30 <= header_len <= fv_len):
            return
        key = (context.get("origin", "outer"), base, fv_len)
        if key in self.seen_fvs:
            return
        self.seen_fvs.add(key)
        end = base + fv_len
        # PI FV headers may place a 20-byte extended header (FV name)
        # between the block map and the first FFS. Respect its offset/size
        # instead of treating the extended-header bytes as an FFS header.
        off = base + header_len
        if base + 0x38 <= end:
            ext_offset = int.from_bytes(blob[base + 0x34 : base + 0x36], "little")
            if ext_offset and base + ext_offset + 20 <= end:
                ext_size = int.from_bytes(blob[base + ext_offset + 16 : base + ext_offset + 20], "little")
                if 20 <= ext_size <= end - (base + ext_offset):
                    off = max(off, base + ext_offset + ext_size)
        off = (off + 7) & ~7
        ffs_count = 0
        while off + 0x18 <= end:
            if blob[off : min(off + 8, end)] == b"\xff" * min(8, end - off):
                # Firmware volumes commonly align the first FFS at +0x50
                # while the FV header length is +0x48; skip free-space padding.
                off += 8
                continue
            ffs_size = u24(blob, off + 0x14)
            if ffs_size < 0x18 or off + ffs_size > end:
                break
            ffs_guid = guid_string(blob[off : off + 16])
            ffs_type = blob[off + 0x12]
            sections = blob[off + 0x18 : off + ffs_size]
            context2 = {**context, "fv_base": base, "ffs_offset": off, "ffs_guid": ffs_guid, "ffs_type": ffs_type, "origin": context.get("origin", "outer")}
            self.walk_sections(sections, context2, depth + 1)
            ffs_count += 1
            off = (off + ffs_size + 7) & ~7
            if ffs_count > 4096:
                break

    def extract(self, fv_only: bool = False) -> list[dict[str, Any]]:
        for fv in find_fv_headers(self.image):
            # The BC250 x86 UEFI region is the useful target; retain other FVs
            # in metadata but avoid treating descriptor-only blobs as modules.
            if fv["base"] < 0xA00000 and fv["base"] != 0:
                continue
            self.walk_fv(self.image, fv["base"], {"origin": "outer", "fv_base": fv["base"]}, 0)

        # AMD images may carry SECURITY_CORE as a Volume Top File immediately
        # after the BIOS FV rather than inside an FV. Parse the known GUID as an
        # FFS header so its TE body is included without scanning arbitrary data.
        top = self.image.find(SECURITY_CORE_GUID)
        if top >= 0 and top + 0x18 <= len(self.image) and self.image[top + 0x12] == 0x03:
            ffs_size = u24(self.image, top + 0x14)
            if 0x18 <= ffs_size <= len(self.image) - top:
                self.walk_sections(self.image[top + 0x18 : top + ffs_size], {
                    "origin": "security-core-top-file",
                    "ffs_guid": guid_string(self.image[top : top + 16]),
                    "ffs_type": 0x03,
                    "ffs_offset": top,
                    "fv_base": None,
                }, 0)
        return self.records


def analyze_image(path: Path, extract_output: Path | None = None) -> dict[str, Any]:
    data = path.read_bytes()
    result: dict[str, Any] = {
        "path": str(path),
        "size": len(data),
        "sha256": sha256_bytes(data),
        "psp": parse_psp(data),
        "bhd": parse_bhd(data),
        "apcb": parse_apcb(data),
        "firmware_volumes": find_fv_headers(data),
    }
    if extract_output is not None:
        extractor = Extractor(data, extract_output, path.stem)
        records = extractor.extract()
        result["extraction"] = {"output": str(extract_output), "module_count": len(records), "unique_module_files": len(extractor.saved), "modules": records}
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True, help="JSON report path")
    parser.add_argument("--extract-image", type=Path, help="Extract PE32/TE sections from this exact input")
    parser.add_argument("--extract-dir", type=Path, help="Output directory for extracted executable sections")
    args = parser.parse_args()
    extract_resolved = args.extract_image.resolve() if args.extract_image else None
    reports = []
    for image in args.images:
        image = image.resolve()
        extraction = None
        if extract_resolved is not None and image == extract_resolved:
            if args.extract_dir is None:
                parser.error("--extract-dir is required with --extract-image")
            extraction = args.extract_dir.resolve()
        reports.append(analyze_image(image, extraction))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "tool": "scripts/firmware_audit.py",
        "tool_version": "1.0-readonly",
        "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "scope": "read-only inventory and UEFI FV/FFS executable extraction; no input writes",
        "images": reports,
    }
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "images": len(reports), "extracted": sum(r.get("extraction", {}).get("unique_module_files", 0) for r in reports)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
