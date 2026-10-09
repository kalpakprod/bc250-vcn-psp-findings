#!/usr/bin/env python3
"""Offline ROM integrity inventory, no flashing, patching, execution or security-material output."""

import argparse
import hashlib
import importlib.util
import json
import os
import stat
import struct
from pathlib import Path

MARKERS = (b"$PSP", b"$BHD")


def inspect(path):
    """Read an existing regular image; signatures are weak markers, not validation."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size not in (
            8 * 1024 * 1024,
            16 * 1024 * 1024,
            32 * 1024 * 1024,
        ):
            raise ValueError("Expected complete 8/16/32 MiB regular image")
        digest = hashlib.sha256()
        counts = {m.decode(): 0 for m in MARKERS}
        tail = b""
        read = 0
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            read += len(chunk)
            combined = tail + chunk
            for marker in MARKERS:
                counts[marker.decode()] += combined.count(marker)
            tail = combined[-3:]
        after = os.fstat(fd)
        if (after.st_size, after.st_mtime_ns, after.st_ctime_ns) != (
            info.st_size,
            info.st_mtime_ns,
            info.st_ctime_ns,
        ):
            raise ValueError("Image changed during read")
        if read != info.st_size:
            raise ValueError("Image changed or incomplete read")
        return {
            "size": read,
            "sha256": digest.hexdigest(),
            "marker_counts": counts,
            "board_identity": "not_established_from_bytes",
            "signed_region_preservation": "not_verified",
            "raw_bytes_or_offsets_printed": False,
            "writes_performed": False,
        }
    finally:
        os.close(fd)


def structure_summary(path):
    """Reuse the project PSP/BHD parser; emit no offsets, body/key hashes or raw data."""
    parser_path = Path(__file__).with_name("firmware_audit.py")
    spec = importlib.util.spec_from_file_location("project_firmware_audit", parser_path)
    if spec is None or spec.loader is None:
        raise ValueError("Project firmware parser unavailable")
    parser = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parser)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_size not in (
            8 * 1024 * 1024,
            16 * 1024 * 1024,
            32 * 1024 * 1024,
        ):
            raise ValueError("Complete regular ROM required")
        data = bytearray()
        while len(data) < before.st_size:
            part = os.read(fd, min(1024 * 1024, before.st_size - len(data)))
            if not part:
                raise ValueError("ROM short read")
            data.extend(part)
        after = os.fstat(fd)
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise ValueError("ROM changed during structural read")
    finally:
        os.close(fd)
    summary = {
        "parser_sha256": hashlib.sha256(parser_path.read_bytes()).hexdigest(),
        "evidence_class": "static_directory_structure_only",
        "signature_acceptance": "not_verified",
        "private_material_emitted": False,
    }
    for kind, offset, width, parse in [
        ("PSP", parser.PSP_OFF, 16, parser.parse_psp),
        ("BHD", parser.BHD_OFF, 24, parser.parse_bhd),
    ]:
        marker = ("$" + kind).encode()
        if offset + 16 > len(data) or data[offset : offset + 4] != marker:
            summary[kind] = {"state": "not_present_at_project_anchor"}
            continue
        count = struct.unpack_from("<I", data, offset + 8)[0]
        if count > 1024 or offset + 16 + width * count > len(data):
            summary[kind] = {"state": "invalid_directory_bounds"}
            continue
        result = parse(bytes(data), offset)
        entries = result["entries"]
        summary[kind] = {
            "state": "parsed",
            "entry_count": len(entries),
            "checksum_match": result["checksum_match"],
            "entries_with_valid_image_bounds": sum(
                item["in_bounds"] for item in entries
            ),
            "entries_with_invalid_image_bounds": sum(
                not item["in_bounds"] for item in entries
            ),
        }
    return summary


def audit(source, baseline=None, structure=False):
    """Compare identities only; no payload, offset map or candidate transform."""
    result = {
        "evidence_class": "offline_file_integrity",
        "source": inspect(source),
        "hardware_acceptance": False,
    }
    if baseline is not None:
        result["baseline"] = inspect(baseline)
        result["identical_to_baseline"] = (
            result["source"]["sha256"] == result["baseline"]["sha256"]
        )
    if structure:
        result["structure"] = structure_summary(source)
    return result


def main():
    """Paths are inputs, never interpreted as scripts or authority to flash."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument(
        "--structure",
        action="store_true",
        help="project PSP/BHD parser, counts/checksum only, no extraction",
    )
    args = parser.parse_args()
    try:
        print(json.dumps(audit(args.source, args.baseline, args.structure), indent=2))
    except (OSError, ValueError) as error:
        print(
            json.dumps(
                {
                    "verified": False,
                    "error_type": type(error).__name__,
                    "raw_content_suppressed": True,
                }
            )
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
