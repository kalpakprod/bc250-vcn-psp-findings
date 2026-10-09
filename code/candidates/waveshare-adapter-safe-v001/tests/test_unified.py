#!/usr/bin/env python3
import os, subprocess, sys, unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.environ.get("WAVESHARE_ADAPTER_BUILD_DIR", os.path.join(REPO, "build"))
UF2 = os.path.join(BUILD, "unified.uf2")
ELF = os.path.join(BUILD, "unified.elf")


class TestUnified(unittest.TestCase):
    def test_uf2_exists(self):
        self.assertTrue(os.path.exists(UF2), f"missing {UF2}")

    def test_size_reasonable(self):
        size = os.path.getsize(UF2)
        self.assertGreater(size, 200_000, f"uf2 too small: {size} bytes")
        self.assertLess(size, 2_000_000, f"uf2 too large: {size} bytes")

    def test_symbols_present(self):
        out = subprocess.check_output(["nm", ELF]).decode()
        self.assertIn("bridge_status_json", out, "bridge status missing")
        self.assertIn("adapter_network_tick", out, "network loop missing")
        self.assertIn("adapter_metrics_json", out, "fresh metrics missing")
        self.assertIn("adapter_spi_capture_tick", out, "passive SPI sampler missing")
        self.assertIn("adapter_spi_capture_start", out, "explicit SPI capture missing")
        self.assertIn("adapter_uart_tick",out,"bounded passive UART observer missing")
        self.assertNotIn("stdio_uart_init",out,"default UART stdout could drive unapproved TX GPIO")
        self.assertIn("bt_usb_identity_ready", out, "identity readiness guard missing")
        for forbidden in ("rig_init", "rig_arm", "rig_selftest", "spi_toctou", "flash_config_write", "mode_switch_and_reboot"):
            self.assertNotIn(forbidden, out, f"unsafe/excluded path linked: {forbidden}")


if __name__ == "__main__":
    unittest.main()
