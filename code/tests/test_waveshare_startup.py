"""Compile configuration guards, not a live boot/latency measurement."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TestStartup(unittest.TestCase):
    def test_no_usb_wait_or_blocking_diagnostic_stdout(self):
        cmake = (
            ROOT / "candidates/waveshare-adapter-safe-v001/CMakeLists.txt"
        ).read_text()
        self.assertIn("PICO_STDIO_USB_CONNECT_WAIT_TIMEOUT_MS=0", cmake)
        self.assertIn("PICO_STDIO_USB_STDOUT_TIMEOUT_US=0", cmake)
        self.assertIn("PICO_STDIO_DEADLOCK_TIMEOUT_MS=0", cmake)
        self.assertIn("pico_enable_stdio_uart(unified 0)", cmake)
        self.assertNotIn("CYW43_LWIP=${CYW43_LWIP_VALUE}", cmake)

    def test_usb_first_main_services_cdc_before_subsystems(self):
        main = (ROOT / "candidates/waveshare-adapter-safe-v001/src/main.c").read_text()
        self.assertIn("adapter_startup_set(ADAPTER_STARTUP_USB_READY, 0)", main)
        self.assertIn("cdc_dispatch_tick();", main)
        self.assertIn("adapter_startup_set(ADAPTER_STARTUP_CYW43_INIT, 0)", main)
        self.assertIn("bridge_boot_step()", main)

    def test_usb_only_diagnostic_keeps_command_dispatch(self):
        main = (ROOT / "candidates/waveshare-adapter-safe-v001/src/main.c").read_text()
        diagnostic = main.split("#ifdef USB_ONLY_DIAGNOSTIC", 1)[1].split("#endif", 1)[
            0
        ]
        self.assertIn("tud_task();", diagnostic)
        self.assertIn("cdc_dispatch_tick();", diagnostic)

    def test_status_exposes_startup_stage(self):
        bridge = (
            ROOT / "candidates/waveshare-adapter-safe-v001/src/bridge/bridge_main.cpp"
        ).read_text()
        self.assertIn("startup_stage", bridge)
        self.assertIn("adapter_startup_stage_name()", bridge)


if __name__ == "__main__":
    unittest.main()
