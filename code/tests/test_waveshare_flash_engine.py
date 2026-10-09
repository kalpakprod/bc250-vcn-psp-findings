"""Compile the actual conventional flash engine against a fake NOR, never hardware."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "candidates/waveshare-adapter-safe-v001/src"


class TestConventionalFlash(unittest.TestCase):
    def test_actual_engine_with_emulated_transport(self):
        cache = Path.home() / ".cache/waveshare-flash-engine-tests"
        cache.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache) as directory:
            exe = Path(directory) / "engine"
            env = {**os.environ, "TMPDIR": str(cache)}
            command = [
                "cc",
                "-Wall",
                "-Wextra",
                "-Werror",
                "-I",
                str(SRC),
                str(
                    ROOT
                    / "reports/waveshare-implementation-20260930/host-tests/flash_engine_test.c"
                ),
                str(SRC / "adapter_flash_engine.c"),
                str(SRC / "adapter_flash_protocol.c"),
                "-o",
                str(exe),
            ]
            compiled = subprocess.run(
                command, capture_output=True, text=True, timeout=20, env=env
            )
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            result = subprocess.run(
                [str(exe)], capture_output=True, text=True, timeout=5
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("readback mismatch/timeout/ownership: PASS", result.stdout)

    def test_actual_transport_with_mock_sdk(self):
        cache = Path.home() / ".cache/waveshare-flash-engine-tests"
        cache.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache) as directory:
            exe = Path(directory) / "transport"
            base = ROOT / "reports/waveshare-implementation-20260930/host-tests"
            compiled = subprocess.run(
                [
                    "cc",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-I",
                    str(base / "transport_mock"),
                    "-I",
                    str(SRC),
                    str(base / "flash_transport_test.c"),
                    str(SRC / "adapter_flash_transport.c"),
                    str(SRC / "mode/mode.c"),
                    "-o",
                    str(exe),
                ],
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
                env={**os.environ, "TMPDIR": str(cache)},
            )
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            result = subprocess.run(
                [str(exe)], capture_output=True, text=True, timeout=5, check=False
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(
                "default-off/guards/bounds/timeout/mode/lease: PASS", result.stdout
            )

    def test_target_and_image_binding(self):
        cache = Path.home() / ".cache/waveshare-flash-engine-tests"
        cache.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache) as directory:
            exe = Path(directory) / "authority"
            test = (
                ROOT
                / "reports/waveshare-implementation-20260930/host-tests/flash_authority_test.c"
            )
            result = subprocess.run(
                [
                    "cc",
                    "-Wall",
                    "-Wextra",
                    "-Werror",
                    "-I",
                    str(SRC),
                    str(test),
                    str(SRC / "adapter_flash_authority.c"),
                    str(SRC / "adapter_flash_protocol.c"),
                    "-o",
                    str(exe),
                ],
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
                env={**os.environ, "TMPDIR": str(cache)},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run(
                [str(exe)], capture_output=True, text=True, timeout=5, check=False
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(
                "image/backups/sector bytes/default deny: PASS", result.stdout
            )

    def test_actual_service_with_emulated_spi(self):
        cache = Path.home() / ".cache/waveshare-flash-engine-tests"
        cache.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache) as directory:
            exe = Path(directory) / "service"
            base = ROOT / "reports/waveshare-implementation-20260930/host-tests"
            command = [
                "cc",
                "-Wall",
                "-Wextra",
                "-Werror",
                "-I",
                str(base / "service_mock"),
                "-I",
                str(SRC),
                str(base / "flash_service_test.c"),
            ]
            command += [
                str(SRC / name)
                for name in [
                    "adapter_flash_service.c",
                    "adapter_flash_engine.c",
                    "adapter_flash_protocol.c",
                    "adapter_flash_authority.c",
                    "mode/mode.c",
                ]
            ]
            command += ["-o", str(exe)]
            compiled = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
                env={**os.environ, "TMPDIR": str(cache)},
            )
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            result = subprocess.run(
                [str(exe)], capture_output=True, text=True, timeout=5, check=False
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(
                "identity/read bounds/disconnect/mode/expiry: PASS", result.stdout
            )


if __name__ == "__main__":
    unittest.main()
