"""Diagnostic fixtures do not touch a device or make firmware security claims."""

import importlib.util
import os
import pty
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


uart = load("uart_capture", ROOT / "scripts/waveshare_uart_capture.py")
bios = load("bios_audit", ROOT / "scripts/waveshare_bios_audit.py")


class TestDiagnostics(unittest.TestCase):
    def test_uart_fixed_frame(self):
        self.assertEqual(
            uart.parse_data("irrelevant private log\nUART_DATA 3 414243\nOK\n"), b"ABC"
        )
        for text in [
            "UART_DATA 2 41",
            "UART_DATA 129 " + ("41" * 129),
            "UART_DATA 1 ZZ",
        ]:
            with self.assertRaises(ValueError):
                uart.parse_data(text)

    def test_capture_requires_confirmation_before_open(self):
        with self.assertRaises(ValueError):
            uart.capture("/dev/no-device", Path("/no-file"), "0123456789ab", False, 1)
        with self.assertRaises(ValueError):
            uart.capture("/dev/no-device", Path("/no-file"), "bad", True, 1)

    def test_capture_selects_diagnostic_and_restores_controller(self):
        master, slave = pty.openpty()
        try:
            cache = Path.home() / ".cache/waveshare-diagnostic-tests"
            cache.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(dir=cache) as tmp:
                replies = [
                    "VERSION 0123456789ab 2026-09-30T00:00:00Z MODE controller\nOK\n",
                    "STATE mode=diagnostic\nOK\n",
                    "OK uart-rx-enabled\n",
                    "OK uart-rx-disabled\n",
                    "STATE mode=controller\nOK\n",
                ]
                with (
                    patch.object(uart, "exchange", side_effect=replies) as exchange,
                    patch.object(uart.time, "monotonic", side_effect=[0, 2]),
                ):
                    result = uart.capture(
                        os.ttyname(slave),
                        Path(tmp) / "capture.bin",
                        "0123456789ab",
                        True,
                        1,
                    )
                self.assertEqual(
                    [call.args[1] for call in exchange.call_args_list],
                    [
                        b"VERSION\n",
                        b"MODE diagnostic\n",
                        b"UART_RX_ON VERIFIED_3V3\n",
                        b"UART_RX_OFF\n",
                        b"MODE controller\n",
                    ],
                )
                self.assertTrue(result["diagnostic_isolation"])
                self.assertTrue(result["disable_acknowledged"])
                self.assertTrue(result["original_mode_restored"])
                self.assertEqual(result["captured_bytes"], 0)
        finally:
            os.close(master)
            os.close(slave)

    def test_project_directory_bound_check(self):
        cache = Path.home() / ".cache/waveshare-diagnostic-tests"
        cache.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache) as tmp:
            path = Path(tmp) / "fixture16.bin"
            with path.open("wb") as stream:
                stream.truncate(16 * 1024 * 1024)
            with path.open("r+b") as stream:
                stream.seek(0x8E0000)
                stream.write(b"$PSP" + struct.pack("<III", 0, 1025, 0))
            result = bios.structure_summary(path)
            self.assertEqual(result["PSP"]["state"], "invalid_directory_bounds")
            self.assertEqual(result["signature_acceptance"], "not_verified")
            self.assertNotIn("offset", str(result))
            self.assertNotIn("key", str(result))

    def test_bios_size_and_identity_not_fabricated(self):
        cache = Path.home() / ".cache/waveshare-diagnostic-tests"
        cache.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache) as tmp:
            path = Path(tmp) / "fixture.bin"
            with path.open("wb") as stream:
                stream.truncate(8 * 1024 * 1024)
            with path.open("r+b") as stream:
                stream.write(b"$PSP")
            result = bios.audit(path, path)
            self.assertTrue(result["identical_to_baseline"])
            self.assertFalse(result["hardware_acceptance"])
            self.assertEqual(result["source"]["marker_counts"]["$PSP"], 1)
            self.assertEqual(
                result["source"]["signed_region_preservation"], "not_verified"
            )
            bad = Path(tmp) / "short.bin"
            bad.write_bytes(b"not-a-rom")
            with self.assertRaises(ValueError):
                bios.inspect(bad)


if __name__ == "__main__":
    unittest.main()
