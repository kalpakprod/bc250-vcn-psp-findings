#!/usr/bin/env python3
"""Check voltage serializer windows against pinned CLV ROM bytes, not labels."""

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "evidence/donor/retroweb-20260916/BC250_5.00_clv.bin"
SHA256 = "ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8"


def main():
    blob = ROM.read_bytes()
    assert hashlib.sha256(blob).hexdigest() == SHA256
    result = []
    # Adjacent serialized fields have a one-byte control and four-byte payload.
    for token, offset, width in [
        (0x1363, 0x6E5, 1),
        (0x1364, 0x6E6, 4),
        (0x1365, 0x6EA, 1),
        (0x1366, 0x6EB, 4),
    ]:
        start = b"\xba" + token.to_bytes(4, "little")
        load = (b"\x8a\x82" if width == 1 else b"\x8b\x82") + offset.to_bytes(
            4, "little"
        )
        payload_store = b"\x88\x41\x03" if width == 1 else b"\x89\x41\x03"
        sites = []
        pos = 0
        while (pos := blob.find(start, pos)) != -1:
            size = 0x32 if width == 1 else 0x35
            window = blob[pos : pos + size]
            assert window[8:11] == bytes.fromhex("668910"), hex(pos)
            assert load + payload_store in window, hex(pos)
            with tempfile.NamedTemporaryFile() as f:
                f.write(window)
                f.flush()
                cmd = [
                    "objdump",
                    "-D",
                    "-b",
                    "binary",
                    "-m",
                    "i386",
                    "-M",
                    "intel",
                    f.name,
                ]
                run = subprocess.run(cmd, capture_output=True, text=True, check=True)
            sites.append(
                {
                    "rom_offset": hex(pos),
                    "bytes": window.hex(),
                    "decode_stdout": run.stdout,
                    "decode_stderr": run.stderr,
                    "decode_exit": run.returncode,
                }
            )
            pos += len(start)
        assert len(sites) == 7, (hex(token), len(sites))
        result.append(
            {
                "token": hex(token),
                "amdsetup_offset": hex(offset),
                "width": width,
                "sites": sites,
            }
        )
    print(
        json.dumps(
            {
                "status": "PASS",
                "source": str(ROM),
                "sha256": SHA256,
                "scope": "four voltage producer fields only, NOT actuator verification",
                "fields": result,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
