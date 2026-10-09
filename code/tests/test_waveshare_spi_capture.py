"""Source/PIO capture contract; these checks are not physical capture evidence."""

import importlib.util
import json
import os
import pty
import re
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "candidates/waveshare-adapter-safe-v001/src"

SPEC = importlib.util.spec_from_file_location(
    "spi_capture", ROOT / "scripts/waveshare_spi_capture.py"
)
with patch.object(sys, "path", [str(ROOT / "scripts")] + sys.path):
    host = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(host)


class TestHostCapture(unittest.TestCase):
    def test_bounded_word_parser(self):
        self.assertEqual(
            host.parse_data("SPI_DATA 1 12345678\nOK\n"), struct.pack("<I", 0x12345678)
        )
        for bad in [
            "SPI_DATA 33 " + "0" * 264,
            "SPI_DATA 1 1234",
            "SPI_DATA 1 AAAAAAAA\nSPI_DATA 1 AAAAAAAA",
            "SPI_DATA 1 ZZZZZZZZ",
        ]:
            with self.assertRaises(ValueError):
                host.parse_data(bad)

    def test_invalid_state_object_rejected(self):
        for data in [[], None, "private arbitrary text", {"state": "complete"}]:
            with self.assertRaises(ValueError):
                host.parse_state("SPI_STATE " + json.dumps(data) + "\nOK\n")

    def test_private_capture_and_cleanup(self):
        cache = Path.home() / ".cache/waveshare-spi-host-tests"
        cache.mkdir(parents=True, exist_ok=True)
        master, slave = pty.openpty()
        try:
            with tempfile.TemporaryDirectory(dir=cache) as tmp:
                output = Path(tmp) / "trace.bin"
                state = {
                    "state": "complete",
                    "sample_hz": 150000000,
                    "samples": 16384,
                    "remaining_words": 2048,
                    "gpio_base": 10,
                    "full_rom": False,
                    "quad": False,
                }
                replies = [
                    "VERSION 0123456789ab 2026-09-30T00:00:00Z MODE controller\nOK\n",
                    "STATE mode=diagnostic\nOK\n",
                    "OK spi-trace-started\n",
                    "SPI_STATE " + json.dumps(state) + "\nOK\n",
                ]
                replies += ["SPI_DATA 32 " + "12345678" * 32 + "\nOK\n"] * 64
                replies += ["OK spi-trace-stopped\n", "STATE mode=controller\nOK\n"]
                with patch.object(host, "exchange", side_effect=replies) as exchange:
                    result = host.capture(
                        os.ttyname(slave), output, "0123456789ab", True
                    )
                self.assertEqual(output.stat().st_mode & 0o777, 0o600)
                header, payload = output.read_bytes().split(b"\n", 1)
                self.assertEqual(len(payload), 8192)
                self.assertEqual(json.loads(header)["samples"], 16384)
                self.assertFalse(json.loads(header)["full_rom"])
                self.assertTrue(result["disarm_acknowledged"])
                self.assertTrue(result["original_mode_restored"])
                self.assertEqual(
                    exchange.call_args_list[-2].args[1], b"SPI_TRACE_OFF\n"
                )
                self.assertEqual(
                    exchange.call_args_list[-1].args[1], b"MODE controller\n"
                )
                with patch.object(host, "exchange") as exchange:
                    with self.assertRaises(FileExistsError):
                        host.capture(os.ttyname(slave), output, "0123456789ab", True)
                    exchange.assert_not_called()
        finally:
            os.close(master)
            os.close(slave)

    def test_timeout_disarms_and_restores(self):
        cache = Path.home() / ".cache/waveshare-spi-host-tests"
        cache.mkdir(parents=True, exist_ok=True)
        master, slave = pty.openpty()
        try:
            with tempfile.TemporaryDirectory(dir=cache) as tmp:
                state = {
                    "state": "timeout",
                    "sample_hz": 0,
                    "samples": 0,
                    "remaining_words": 0,
                    "gpio_base": 10,
                    "full_rom": False,
                    "quad": False,
                }
                replies = [
                    "VERSION 0123456789ab 2026-09-30T00:00:00Z MODE controller\nOK\n",
                    "STATE mode=diagnostic\nOK\n",
                    "OK spi-trace-started\n",
                    "SPI_STATE " + json.dumps(state) + "\nOK\n",
                    "OK spi-trace-stopped\n",
                    "STATE mode=controller\nOK\n",
                ]
                with patch.object(host, "exchange", side_effect=replies) as exchange:
                    with self.assertRaises(TimeoutError):
                        host.capture(
                            os.ttyname(slave),
                            Path(tmp) / "trace.bin",
                            "0123456789ab",
                            True,
                        )
                self.assertEqual(
                    exchange.call_args_list[-2].args[1], b"SPI_TRACE_OFF\n"
                )
                self.assertEqual(
                    exchange.call_args_list[-1].args[1], b"MODE controller\n"
                )
        finally:
            os.close(master)
            os.close(slave)


class TestPassiveCapture(unittest.TestCase):
    def test_input_only_pio_program(self):
        lines = (SRC / "adapter_spi_capture.pio").read_text().splitlines()
        instructions = [line.split(";")[0].strip() for line in lines]
        instructions = [
            line for line in instructions if line and not line.startswith(".")
        ]
        self.assertEqual(
            instructions,
            [
                "pull block",
                "mov x, osr",
                "wait 0 pin 3",
                "sample:",
                "in pins, 4",
                "jmp x-- sample",
                "hold:",
                "jmp hold",
            ],
        )

    def test_confirmation_and_observer_modes_before_any_resources(self):
        text = (SRC / "adapter_spi_capture.c").read_text()
        # Both observer modes are permitted by the integrated adapter plan;
        # verification, scratch ownership, and flash exclusion still gate PIO.
        gate = re.search(
            r"if\s*\(\s*!verified\s*\|\|\s*scratch_leased\s*\|\|\s*"
            r"\(\s*mode_load\(\)\s*!=\s*MODE_DIAGNOSTIC\s*&&\s*"
            r"mode_load\(\)\s*!=\s*MODE_MONITOR\s*\)\s*\)\s*return false;",
            text,
        )
        self.assertIsNotNone(gate, "observer confirmation/mode/scratch gate missing")
        claim = text.index("if(!pio_claim_free_sm")
        flash_gate = text.index("if(adapter_flash_transport_ready())return false;")
        self.assertLess(gate.start(), flash_gate)
        self.assertLess(flash_gate, claim)
        self.assertIn("gpio_set_dir(pin,GPIO_IN)", text)
        self.assertIn("pio_sm_set_consecutive_pindirs(owned_pio,sm,BASE,4,false)", text)
        for forbidden in [
            "gpio_put",
            "GPIO_OUT",
            "spi_write",
            "watchdog_reboot",
            "flash_range",
        ]:
            self.assertNotIn(forbidden, text)

    def test_bounded_private_waveform_not_rom_or_quad(self):
        text = (SRC / "adapter_spi_capture.c").read_text()
        self.assertIn("#define WORDS 2048u", text)
        self.assertIn("if(capacity>32)capacity=32;", text)
        self.assertIn("WORDS-read_pos", text)
        self.assertIn("clock_get_hz(clk_sys)/2", text)
        self.assertIn("owned_pio->fdebug & (1u<<sm)", text)
        self.assertIn("pio_sm_put_blocking(owned_pio,sm,WORDS*8-1)", text)
        self.assertNotIn("set_sys_clock", text)
        self.assertIn(r"\"full_rom\":false", text)
        self.assertIn(r"\"quad\":false", text)
        self.assertIn("-started)>1000", text)

    def test_mode_change_disarms_both_observers(self):
        cdc = (SRC / "cdc_dispatch.c").read_text()
        self.assertIn("adapter_uart_disable(); adapter_spi_capture_stop();", cdc)
        self.assertIn('"SPI_TRACE_ON VERIFIED_3V3"', cdc)
        network = (SRC / "adapter_network.c").read_text()
        self.assertNotIn("SPI_TRACE_READ", network)
        self.assertNotIn("SPI_TRACE_ON", network)


if __name__ == "__main__":
    unittest.main()
