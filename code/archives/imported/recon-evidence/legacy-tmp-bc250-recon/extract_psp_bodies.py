#!/usr/bin/env python3
"""Strip PSP $PS1 headers from PSPTool -u extracts and record metadata."""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path


def main() -> None:
    source = Path(sys.argv[1])
    destination = Path(sys.argv[2])
    destination.mkdir(parents=True, exist_ok=True)
    metadata = []
    for path in sorted(source.iterdir()):
        if not path.is_file() or path.stat().st_size < 0x100:
            continue
        data = path.read_bytes()
        if data[0x10:0x14] != b"$PS1":
            continue
        size_signed = struct.unpack_from("<I", data, 0x14)[0]
        encrypted = struct.unpack_from("<I", data, 0x18)[0]
        compressed = struct.unpack_from("<I", data, 0x48)[0]
        size_uncompressed = struct.unpack_from("<I", data, 0x50)[0]
        zlib_size = struct.unpack_from("<I", data, 0x54)[0]
        version = ".".join(f"{byte:X}" for byte in data[0x63:0x5F:-1])
        load_address = struct.unpack_from("<I", data, 0x68)[0]
        rom_size = struct.unpack_from("<I", data, 0x6C)[0]
        body = data[0x100:]
        output = destination / (path.name + ".body")
        output.write_bytes(body)
        metadata.append({
            "file": path.name,
            "body_file": output.name,
            "body_size": len(body),
            "size_signed": size_signed,
            "size_uncompressed": size_uncompressed,
            "zlib_size": zlib_size,
            "encrypted": encrypted,
            "compressed": compressed,
            "version": version,
            "load_address": f"0x{load_address:08x}",
            "rom_size": rom_size,
        })
    meta_path = destination / "metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"extracted={len(metadata)} metadata={meta_path}")
    for entry in metadata:
        print(
            f"{entry['file']}: body={entry['body_size']} load={entry['load_address']} "
            f"compressed={entry['compressed']} encrypted={entry['encrypted']}"
        )


if __name__ == "__main__":
    main()
