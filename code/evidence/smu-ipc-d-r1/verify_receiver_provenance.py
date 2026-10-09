#!/usr/bin/env python3
"""Verify PMFW type-0x12 provenance against dump/2.bin and extracted sources."""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

ROOT = Path("/home/OWNER/orca/projects/bc250")
DUMP = ROOT / "dump/2.bin"
PSP_OFFSET = 0x8E0000
TYPE_NAMES = {0x08: "SMU_OFFCHIP_FW", 0x12: "SMU_OFF_CHIP_FW_2"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def entry(data: bytes, index: int) -> dict[str, object]:
    off = PSP_OFFSET + 0x10 + index * 16
    raw = data[off : off + 16]
    typ, sub, flags = raw[0], raw[1], struct.unpack_from("<H", raw, 2)[0]
    size, location, reserved = struct.unpack_from("<III", raw, 4)
    spi = location & 0x00FFFFFF if location >= 0xFF000000 else location
    signed = data[spi : spi + size]
    # The PSP entry is 0x40200 bytes in the dump: a 0x100-byte $PS1-style
    # prefix, a 0x40000-byte body, and a trailing 0x100-byte signature area.
    body = signed[0x100:0x40100]
    return {
        "index": index,
        "type": f"0x{typ:02X}",
        "name": TYPE_NAMES.get(typ, "unknown"),
        "subprogram": sub,
        "flags": f"0x{flags:04X}",
        "size": size,
        "location_raw": f"0x{location:08X}",
        "spi_offset": f"0x{spi:06X}",
        "reserved": f"0x{reserved:08X}",
        "raw_directory_entry_hex": raw.hex(),
        "signed_sha256": sha(signed),
        "signed_size": len(signed),
        "body_sha256": sha(body),
        "body_size": len(body),
        "entry_tail_sha256": sha(signed[0x40100:]),
        "body_nonzero_count": sum(byte != 0 for byte in body),
        "body_nonzero_offsets": [f"0x{i:05X}" for i, byte in enumerate(body) if byte][:32],
    }


def source(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": str(path),
        "size": len(data),
        "sha256": sha(data),
        "first16": data[:16].hex(),
        "body_sha256_if_ps1": sha(data[0x100:]) if len(data) >= 0x100 else None,
        "body_size_if_ps1": max(0, len(data) - 0x100),
        "nonzero_count": sum(byte != 0 for byte in data),
    }


def main() -> None:
    data = DUMP.read_bytes()
    candidates = [
        ROOT / "import/from-windows/Users/kukuruza/tmp_bc250/recon/robin3_psp_bodies/SMU_OFF_CHIP_FW_2~0x12_0.58.6.0.body",
        ROOT / "import/from-windows/Users/kukuruza/tmp_bc250/recon/robin3_psp_unique/SMU_OFF_CHIP_FW_2~0x12_0.58.6.0",
        ROOT / "import/from-windows/Users/kukuruza/tmp_bc250/recon/robin3_psp_bodies/SMU_OFFCHIP_FW~0x8_0.58.6.0.body",
    ]
    result = {
        "dump": {"path": str(DUMP), "size": len(data), "sha256": sha(data)},
        "psp_directory": {
            "offset": f"0x{PSP_OFFSET:06X}",
            "magic": data[PSP_OFFSET : PSP_OFFSET + 4].decode("ascii", "replace"),
            "count": struct.unpack_from("<I", data, PSP_OFFSET + 8)[0],
            "entries": [entry(data, 2), entry(data, 4)],
        },
        "sources": [source(path) for path in candidates if path.exists()],
        "loader_source": {
            "path": str(ROOT / "import/from-windows/Users/kukuruza/tmp_bc250/recon/extract_psp_bodies.py"),
            "rule": "body = data[0x100:]",
            "loader_sha256": sha((ROOT / "import/from-windows/Users/kukuruza/tmp_bc250/recon/extract_psp_bodies.py").read_bytes()),
        },
    }
    out = Path("evidence/smu-ipc-d-r1/receiver-provenance.json")
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
