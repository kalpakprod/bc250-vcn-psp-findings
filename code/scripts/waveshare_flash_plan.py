#!/usr/bin/env python3
"""Prepare a private exact-image plan, never open a device or issue flash commands."""

import argparse
import hashlib
import importlib.util
import json
import os
import stat
import struct
from pathlib import Path

SIZE = 16 * 1024 * 1024


def read_image(path):
    """Freeze a bounded regular image and detect changes during read."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_size != SIZE:
            raise ValueError("Complete 16MiB regular image required")
        data = bytearray()
        while len(data) < SIZE:
            chunk = os.read(fd, min(1024 * 1024, SIZE - len(data)))
            if not chunk:
                raise ValueError("Incomplete image")
            data.extend(chunk)
        after = os.fstat(fd)
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise ValueError("Image changed during read")
        return bytes(data), (before.st_dev, before.st_ino)
    finally:
        os.close(fd)


def preservation_check(original, candidate):
    """Conservative unchanged-byte proof, not signature validation or universal PSP parsing."""
    parser_path = Path(__file__).with_name("firmware_audit.py")
    spec = importlib.util.spec_from_file_location("flash_plan_audit", parser_path)
    parser = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parser)
    root = parser.PSP_OFF
    if original[root : root + 4] != b"$PSP":
        raise ValueError("Known PSP directory anchor required")
    ranges = [(0, parser.BHD_OFF)]
    pending, visited = [root], set()
    while pending:
        offset = pending.pop()
        if offset in visited:
            continue
        if len(visited) >= 64 or offset < 0 or offset + 16 > len(original):
            raise ValueError("Directory graph bounds invalid")
        marker = original[offset : offset + 4]
        if marker not in (b"$PSP", b"$PL2"):
            raise ValueError("Unsupported referenced directory")
        count = struct.unpack_from("<I", original, offset + 8)[0]
        if not 0 < count <= 1024 or offset + 16 + count * 16 > len(original):
            raise ValueError("Directory size invalid")
        # Existing parser's checksum excludes the magic; normalize only for parsing.
        data = (
            original
            if marker == b"$PSP"
            else original[:offset] + b"$PSP" + original[offset + 4 :]
        )
        directory = parser.parse_psp(data, offset)
        if (
            not directory
            or not directory["checksum_match"]
            or len(directory["entries"]) != count
        ):
            raise ValueError("Directory checksum/coverage invalid")
        visited.add(offset)
        ranges.append((offset, offset + 16 + count * 16))
        for entry in directory["entries"]:
            if not entry["in_bounds"]:
                raise ValueError("Unbounded protected reference")
            start, size = entry["spi_offset"], entry["size"]
            ranges.append((start, start + size))
            if original[start : start + 4] in (b"$PSP", b"$PL2"):
                pending.append(start)
    for start, end in ranges:
        if original[start:end] != candidate[start:end]:
            raise ValueError("Protected PSP/boot bytes changed")
    # Unknown PS1 envelopes must never be guessed by marker position alone.
    for data in (original, candidate):
        pos = 0
        while True:
            pos = data.find(b"$PS1", pos)
            if pos < 0:
                break
            if not any(start <= pos and pos + 4 <= end for start, end in ranges):
                raise ValueError("Additional PS1 region mapping required")
            pos += 4
    return {
        "scope": "conservative boot prefix and validated PSP graph referenced bytes unchanged",
        "directory_count": len(visited),
        "signature_validation": "not_performed",
        "unmapped_PS1": False,
        "all_firmware_signed_regions_proven": False,
    }


def prepare(image, backup1, backup2, approved_sha256, target_tag, jedec):
    """Compare complete bytes, not caller-supplied backup hashes; no execution approval."""
    if not target_tag or jedec not in {0xC22018, 0xEF4018}:
        raise ValueError("Supported expected chip and target identity required")
    candidate, _ = read_image(image)
    first, first_id = read_image(backup1)
    second, second_id = read_image(backup2)
    if first_id == second_id or first != second:
        raise ValueError("Distinct matching backup files required")
    digest = hashlib.sha256(candidate).hexdigest()
    if approved_sha256 != digest:
        raise ValueError("Candidate differs from explicitly approved image hash")
    preservation = preservation_check(first, candidate)
    sectors = []
    for offset in range(0, SIZE, 4096):
        old, new = first[offset : offset + 4096], candidate[offset : offset + 4096]
        if old != new:
            sectors.append(
                {
                    "address": offset,
                    "original_sha256": hashlib.sha256(old).hexdigest(),
                    "candidate_sha256": hashlib.sha256(new).hexdigest(),
                }
            )
    return {
        "schema": 1,
        "target_tag": target_tag,
        "expected_jedec": f"{jedec:06x}",
        "size": SIZE,
        "image": str(image.resolve()),
        "image_sha256": digest,
        "backup_sha256": hashlib.sha256(first).hexdigest(),
        "changed_sectors": sectors,
        "backup_file_bytes_match": True,
        "independent_hardware_reads_proven": False,
        "PSP_signed_region_preservation": preservation,
        "recovery_verified": False,
        "physical_execution_authorized": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--backup1", type=Path, required=True)
    parser.add_argument("--backup2", type=Path, required=True)
    parser.add_argument("--approved-sha256", required=True)
    parser.add_argument("--target-tag", required=True)
    parser.add_argument("--jedec", type=lambda value: int(value, 16), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        record = prepare(
            args.image,
            args.backup1,
            args.backup2,
            args.approved_sha256,
            args.target_tag,
            args.jedec,
        )
        fd = os.open(
            args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
        )
        with os.fdopen(fd, "w") as stream:
            json.dump(record, stream, indent=2)
            stream.write("\n")
        print(
            json.dumps(
                {
                    "prepared": True,
                    "changed_sector_count": len(record["changed_sectors"]),
                    "hardware_action": False,
                    "execution_authorized": False,
                }
            )
        )
        return 0
    except (OSError, ValueError) as error:
        print(
            json.dumps(
                {
                    "prepared": False,
                    "error_type": type(error).__name__,
                    "hardware_action": False,
                }
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
