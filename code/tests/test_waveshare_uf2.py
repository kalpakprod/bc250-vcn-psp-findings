"""Strict format checks against generated, non-flashable one-page fixtures."""

import importlib.util
import struct
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "uf2_check", ROOT / "scripts/check_waveshare_uf2.py"
)
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


def block(
    address=0x10000000, family=0xE48BFF59, flags=0x2000, total=1, payload=b"\0" * 256
):
    return (
        struct.pack(
            "<8I", 0x0A324655, 0x9E5D5157, flags, address, 256, 0, total, family
        )
        + payload
        + b"\0" * (476 - len(payload))
        + struct.pack("<I", 0x0AB16F30)
    )


class TestUF2(unittest.TestCase):
    def validate(self, data):
        cache = Path.home() / ".cache/waveshare-uf2-tests"
        cache.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache) as tmp:
            path = Path(tmp) / "fixture.uf2"
            path.write_bytes(data)
            return check.validate(path)

    def test_real_program_range(self):
        result = self.validate(block())
        self.assertTrue(result["program_pages_exclude_private_sectors"])
        self.assertFalse(result["hardware_boot_verified"])

    def test_only_exact_documented_marker(self):
        marker = bytearray(block(0x10FFFF00, 0xE48BFF57, 0xA000, 2, b"\xef" * 256))
        marker[288:292] = struct.pack("<I", 0x9957E304)
        self.assertEqual(len(self.validate(bytes(marker) + block())["metadata"]), 1)
        marker[32] = 0
        with self.assertRaises(ValueError):
            self.validate(bytes(marker) + block())

    def test_protected_sector_program_rejected(self):
        with self.assertRaises(ValueError):
            self.validate(block(0x10FFC000))

    def test_missing_program_block_rejected(self):
        with self.assertRaises(ValueError):
            self.validate(block(total=2))

    def test_bad_family_rejected(self):
        with self.assertRaises(ValueError):
            self.validate(block(family=123))


if __name__ == "__main__":
    unittest.main()
