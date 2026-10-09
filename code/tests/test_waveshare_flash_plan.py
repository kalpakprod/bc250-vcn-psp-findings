"""Synthetic image planning, never a hardware recovery or signature proof."""

import hashlib
import importlib.util
import struct
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "flash_plan", ROOT / "scripts/waveshare_flash_plan.py"
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class TestFlashPlan(unittest.TestCase):
    def fixture_images(self, root):
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "audit", ROOT / "scripts/firmware_audit.py"
        )
        audit = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(audit)
        data = bytearray(module.SIZE)
        body = audit.PSP_OFF + 4096
        entries = struct.pack("<IIII", 1, 256, body, 0)
        tail = struct.pack("<II", 1, 0) + entries
        data[audit.PSP_OFF : audit.PSP_OFF + 32] = (
            b"$PSP" + struct.pack("<I", audit.fletcher32(tail)) + tail
        )
        data[body : body + 256] = b"A" * 256
        paths = [root / n for n in ["a.bin", "b.bin", "image.bin"]]
        for p in paths:
            p.write_bytes(data)
        return paths, body, audit.BHD_OFF

    def test_changed_psp_payload_rejected(self):
        cache = Path.home() / ".cache/waveshare-flash-plan-tests"
        cache.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache) as directory:
            (a, b, image), body, _ = self.fixture_images(Path(directory))
            with image.open("r+b") as f:
                f.seek(body)
                f.write(b"B")
            digest = hashlib.sha256(image.read_bytes()).hexdigest()
            with self.assertRaises(ValueError):
                module.prepare(image, a, b, digest, "fixture target", 0xC22018)

    def test_malformed_or_unmapped_signed_layout_rejected(self):
        cache = Path.home() / ".cache/waveshare-flash-plan-tests"
        cache.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache) as directory:
            (a, _, _), _, allowed = self.fixture_images(Path(directory))
            original = a.read_bytes()
            malformed = bytearray(original)
            malformed[0x8E0008:0x8E000C] = (1025).to_bytes(4, "little")
            with self.assertRaises(ValueError):
                module.preservation_check(bytes(malformed), bytes(malformed))
            marker = bytearray(original)
            marker[allowed + 4096 : allowed + 4100] = b"$PS1"
            with self.assertRaises(ValueError):
                module.preservation_check(bytes(marker), bytes(marker))
            added = bytearray(original)
            added[allowed + 4096 : allowed + 4100] = b"$PS1"
            with self.assertRaises(ValueError):
                module.preservation_check(original, bytes(added))

    def test_exact_image_and_backup_content(self):
        cache = Path.home() / ".cache/waveshare-flash-plan-tests"
        cache.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache) as directory:
            root = Path(directory)
            (a, b, image), _, allowed = self.fixture_images(root)
            with image.open("r+b") as stream:
                stream.seek(allowed + 4096)
                stream.write(b"modified fixture")
            digest = hashlib.sha256(image.read_bytes()).hexdigest()
            plan = module.prepare(image, a, b, digest, "fixture target", 0xC22018)
            self.assertEqual(len(plan["changed_sectors"]), 1)
            self.assertFalse(plan["physical_execution_authorized"])
            self.assertFalse(plan["independent_hardware_reads_proven"])
            with self.assertRaises(ValueError):
                module.prepare(image, a, a, digest, "fixture target", 0xC22018)
            with self.assertRaises(ValueError):
                module.prepare(image, a, b, "wrong digest", "fixture target", 0xC22018)
            with b.open("r+b") as stream:
                stream.write(b"drift")
            with self.assertRaises(ValueError):
                module.prepare(image, a, b, digest, "fixture target", 0xC22018)


if __name__ == "__main__":
    unittest.main()
