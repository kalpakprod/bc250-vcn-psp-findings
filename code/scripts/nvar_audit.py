#!/usr/bin/env python3
"""Read-only, bounded AMI NVAR metadata/selected-field auditor.

The adapter deliberately does not emit raw variable bodies. Security-like names
are redacted and their body hashes/field values are omitted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
from typing import Any

NVAR_SIGNATURE = b"NVAR"
DEFAULT_STORE_OFFSET = 0x1000
DEFAULT_STORE_LENGTH = 0xF000
# Field labels are evidence-derived from the imported BC250 AmdSetup analysis.
KNOWN_FIELDS: dict[str, tuple[int, str]] = {
    "MemoryClockSpeed": (0x316, "u8"),
    "Tcl": (0x317, "u8"),
    "TrefControl": (0x324, "u8"),
    "TrfcPb": (0x327, "u8"),
    "UclkDiv1M0": (0x330, "u8"),
    "DramTimingControl": (0x32F, "u8"),
    "BankGroupSwap": (0x32D, "u8"),
    "PhyPowerSaving": (0x368, "u8"),
    "MemoryPstate": (0x36D, "u8"),
    "FclkDpm": (0x6A3, "u8"),
    "VddcrVddOffsetControl": (0x6E5, "u8"),
    "VddcrVddOffset": (0x6E6, "u32"),
    "VddcrGfxOffsetControl": (0x6EA, "u8"),
    "VddcrGfxOffset": (0x6EB, "u32"),
    "ForceCpuFreq": (0x701, "u16"),
    "DfClockOverrideControl": (0x703, "u8"),
    "DfClockOvrd": (0x704, "u16"),
    "FastPpt": (0x70C, "u32"),
    "SlowPpt": (0x710, "u32"),
    "SlowPptTime": (0x714, "u32"),
    "VrmCurrent": (0x718, "u32"),
    "VrmMaximum": (0x71C, "u32"),
    "TpdControl": (0x343, "u8"),
    "Tpd": (0x344, "u8"),
    "Cmd2T": (0x346, "u8"),
    "GearDown": (0x34C, "u8"),
}
# Match only names that may carry access-bearing security material.
SECRET_NAME_RE = re.compile(
    r"(?:^|[_-])(pk|kek|db|dbx|secureboot|secure|key|keys|cert|certificate|password|token|secret|credential)(?:$|[_-])",
    re.IGNORECASE,
)


def is_secret_like(name: str) -> bool:
    lowered = name.lower()
    return bool(SECRET_NAME_RE.search(lowered) or lowered in {"pk", "kek", "db", "dbx"})


def decode_name(raw: bytes) -> str:
    return raw.decode("ascii", "replace").rstrip("\x00")


def parse_records(data: bytes, absolute_offset: int = 0) -> tuple[list[dict[str, Any]], list[str], int | None]:
    """Parse sequential NVAR records after the first signature in a bounded region."""
    first = data.find(NVAR_SIGNATURE)
    if first < 0:
        return [], ["NVAR signature not found in bounded store"], None
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    cursor = first
    while cursor + 0x0B <= len(data):
        if data[cursor:cursor + 4] != NVAR_SIGNATURE:
            next_sig = data.find(NVAR_SIGNATURE, cursor + 1)
            if next_sig < 0:
                break
            errors.append(f"gap/non-NVAR bytes at relative 0x{cursor:X}; resumed at 0x{next_sig:X}")
            cursor = next_sig
            continue
        size = struct.unpack_from("<H", data, cursor + 4)[0]
        if size < 0x0B:
            errors.append(f"invalid NVAR size 0x{size:X} at relative 0x{cursor:X}")
            break
        end = cursor + size
        if end > len(data):
            errors.append(f"truncated NVAR at relative 0x{cursor:X}: size=0x{size:X}, bounded_length=0x{len(data):X}")
            break
        name_end = data.find(b"\x00", cursor + 0x0B, end)
        if name_end < 0:
            errors.append(f"unterminated NVAR name at relative 0x{cursor:X}")
            cursor = end
            continue
        name = decode_name(data[cursor + 0x0B:name_end])
        body_start = name_end + 1
        body = data[body_start:end]
        secret_like = is_secret_like(name)
        item: dict[str, Any] = {
            "relative_offset": f"0x{cursor:X}",
            "absolute_offset": f"0x{absolute_offset + cursor:X}",
            "size": size,
            "link_or_sequence": f"0x{struct.unpack_from('<H', data, cursor + 6)[0]:04X}",
            "header_byte_8": f"0x{data[cursor + 8]:02X}",
            "attributes_byte_9": f"0x{data[cursor + 9]:02X}",
            "name_length": len(name),
            "body_length": len(body),
            "security_like": secret_like,
            "name": "<redacted-security-variable>" if secret_like else name,
        }
        if not secret_like:
            item["body_sha256"] = hashlib.sha256(body).hexdigest()
        records.append(item)
        cursor = end
    return records, errors, first


def read_typed(body: bytes, offset: int, typ: str) -> int | None:
    widths = {"u8": 1, "u16": 2, "u32": 4}
    width = widths[typ]
    if offset < 0 or offset + width > len(body):
        return None
    return int.from_bytes(body[offset:offset + width], "little")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--store-offset", type=lambda value: int(value, 0), default=DEFAULT_STORE_OFFSET)
    parser.add_argument("--store-length", type=lambda value: int(value, 0), default=DEFAULT_STORE_LENGTH)
    parser.add_argument("--variable", default="AmdSetup")
    args = parser.parse_args()

    raw = args.image.read_bytes()
    start = args.store_offset
    end = min(len(raw), start + args.store_length)
    if start < 0 or start >= len(raw) or end <= start:
        raise SystemExit(f"invalid bounded store: offset=0x{start:X} end=0x{end:X} image_size=0x{len(raw):X}")
    bounded = raw[start:end]
    records, errors, first = parse_records(bounded, start)
    selected = [r for r in records if r.get("name") == args.variable]
    # Re-read selected bodies without emitting them; this keeps sensitive values out.
    selected_fields: list[dict[str, Any]] = []
    for rec in records:
        if rec.get("name") != args.variable or rec.get("security_like"):
            continue
        rel = int(rec["relative_offset"], 16)
        size = int(rec["size"])
        rec_bytes = bounded[rel:rel + size]
        name_end = rec_bytes.find(b"\x00", 0x0B)
        body = rec_bytes[name_end + 1:] if name_end >= 0 else b""
        selected_fields = [
            {"name": name, "offset": f"0x{off:X}", "type": typ, "value": read_typed(body, off, typ)}
            for name, (off, typ) in KNOWN_FIELDS.items()
        ]
        break
    report = {
        "image": str(args.image.resolve()),
        "image_size": len(raw),
        "image_sha256": hashlib.sha256(raw).hexdigest(),
        "bounded_store": {"offset": f"0x{start:X}", "length": end - start, "end": f"0x{end:X}"},
        "first_nvar_relative_offset": f"0x{first:X}" if first is not None else None,
        "record_count": len(records),
        "records": records,
        "selected_variable": args.variable,
        "selected_count": len(selected),
        "selected_fields": selected_fields,
        "errors": errors,
        "redaction": "Security-like variable names are replaced and their body hashes/field values are omitted; raw bodies are never emitted.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output.resolve()), "records": len(records), "selected": len(selected), "errors": len(errors)}))
    return 0 if records and not any("truncated" in e or "invalid NVAR size" in e for e in errors) else 1


if __name__ == "__main__":
    raise SystemExit(main())
