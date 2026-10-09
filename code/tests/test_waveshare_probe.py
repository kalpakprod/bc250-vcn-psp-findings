"""Read-only Waveshare acceptance probe; mocks never imply hardware acceptance."""

import importlib.util
import json
import os
import pty
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "waveshare_probe", ROOT / "scripts/waveshare_probe.py"
)
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


class TestResponse(unittest.TestCase):
    """Validate legacy/modern parsing and bounded serial behavior with fixtures."""

    def test_legacy_status(self):
        self.assertEqual(
            probe.parse_reply("STATUS", "MODE controller\r\nOK\r\n")["mode"],
            "controller",
        )

    def test_modern_status(self):
        self.assertEqual(
            probe.parse_reply("STATUS", "STATE mode=controller\nOK\n")["mode"],
            "controller",
        )

    def test_passive_diagnostic_mode(self):
        self.assertEqual(
            probe.parse_reply("STATUS", "STATE mode=diagnostic\nOK\n")["mode"],
            "diagnostic",
        )

    def test_flash_and_recovery_modes_match_firmware(self):
        for mode in ("flash", "recovery"):
            for command, reply in (
                ("STATUS", f"STATE mode={mode}\nOK\n"),
                ("VERSION", f"VERSION c1e7627 2026-10-08T00:00:00Z MODE {mode}\nOK\n"),
            ):
                result = probe.parse_reply(command, reply)
                self.assertEqual(result["state"], "recognized")
                self.assertEqual(result["mode"], mode)

    def test_bare_ok_is_not_state(self):
        r = probe.parse_reply("STATUS", "OK\n")
        self.assertEqual(r["state"], "acknowledged_unknown")
        self.assertNotIn("mode", r)

    def test_version(self):
        r = probe.parse_reply(
            "VERSION", "VERSION c1e7627 2026-09-28T21:32:39Z MODE controller\nOK\n"
        )
        self.assertEqual(r["revision"], "c1e7627")
        self.assertEqual(r["mode"], "controller")

    def test_unknown_logs_are_not_persisted(self):
        r = probe.parse_reply(
            "STATUS", "wifi-password SECRET\nMODE controller TOKEN SECRET\nOK\n"
        )
        self.assertNotIn("SECRET", json.dumps(r))
        self.assertEqual(r["state"], "acknowledged_unknown")

    def test_version_suffix_rejected(self):
        r = probe.parse_reply(
            "VERSION",
            "VERSION c1e7627 2026-09-28T21:32:39Z MODE controller SECRET\nOK\n",
        )
        self.assertNotIn("revision", r)

    def test_conflicting_state_rejected(self):
        r = probe.parse_reply("STATUS", "MODE controller\nMODE toctou\nOK\n")
        self.assertEqual(r["state"], "conflicting_reply")

    def test_empty_is_unknown(self):
        self.assertEqual(
            probe.parse_reply("STATUS", "")["state"], "no_recognized_reply"
        )

    def test_mutating_command_rejected(self):
        with self.assertRaises(ValueError):
            probe.parse_reply("ARM", "OK")

    def test_fixture_classification(self):
        result = probe.from_fixture(
            {
                "VERSION": "VERSION c1e7627 2026-09-28T21:32:39Z MODE controller\nOK",
                "STATUS": "MODE controller\nOK",
            }
        )
        self.assertEqual(result["evidence_class"], "fixture")
        self.assertFalse(result["hardware_acceptance"])

    def test_missing_device_is_explicit(self):
        result = probe.live_probe("/dev/not-a-waveshare-probe-test", 0.1)
        self.assertEqual(result["serial"]["state"], "access_error")
        self.assertFalse(result["hardware_acceptance"])

    def test_serial_pty_and_restoration(self):
        import termios

        master, slave = pty.openpty()
        device = os.ttyname(slave)
        old = termios.tcgetattr(slave)
        seen = []

        def responder():
            buf = b""
            while len(seen) < 2:
                buf += os.read(master, 256)
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    seen.append(line)
                    response = (
                        b"VERSION c1e7627 2026-09-28T21:32:39Z MODE controller\r\nOK\r\n"
                        if line == b"VERSION"
                        else b"MODE controller\r\nOK\r\n"
                    )
                    os.write(master, response)

        thread = threading.Thread(target=responder, daemon=True)
        thread.start()
        try:
            r = probe.serial_probe(device, 0.5)
            thread.join(1)
            self.assertEqual(seen, [b"VERSION", b"STATUS"])
            self.assertEqual(r["replies"]["STATUS"]["mode"], "controller")
            self.assertEqual(termios.tcgetattr(slave), old)
        finally:
            os.close(master)
            os.close(slave)

    def test_serial_timeout_is_not_success(self):
        master, slave = pty.openpty()
        import termios

        old = termios.tcgetattr(slave)
        try:
            r = probe.serial_probe(os.ttyname(slave), 0.1)
            self.assertEqual(r["replies"]["VERSION"]["state"], "no_recognized_reply")
            self.assertEqual(termios.tcgetattr(slave), old)
        finally:
            os.close(master)
            os.close(slave)

    def test_invalid_timeout(self):
        with self.assertRaises(ValueError):
            probe.serial_probe("/dev/null", 0)

    def test_advisory_busy_port(self):
        import fcntl

        master, slave = pty.openpty()
        guard = os.open(os.ttyname(slave), os.O_RDWR | os.O_NOCTTY)
        try:
            fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaises(BlockingIOError):
                probe.serial_probe(os.ttyname(slave), 0.1)
        finally:
            os.close(guard)
            os.close(master)
            os.close(slave)

    def test_inventory_restricts_gamepad_to_selected_usb(self):
        cache = Path.home() / ".cache/waveshare-probe-tests"
        cache.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache) as tmp:
            sysfs = Path(tmp)
            usb = sysfs / "devices/usb1/1-2.2"
            usb.mkdir(parents=True)
            (usb / "idVendor").write_text("054c")
            (usb / "idProduct").write_text("0ce6")
            serial = "REDACTED"
            serial.mkdir(parents=True)
            tty = sysfs / "class/tty/ttyACM0"
            tty.mkdir(parents=True)
            (tty / "device").symlink_to(serial)
            input_class = sysfs / "class/input"
            for name, parent, bits in [
                ("event1", usb, 1 << 0x130),
                ("event2", sysfs / "devices/other-usb", 1 << 0x130),
                ("event3", usb, 1 << 30),
            ]:
                dev = parent / name
                (dev / "capabilities").mkdir(parents=True)
                (dev / "capabilities/key").write_text(hex(bits)[2:])
                event = input_class / name
                event.mkdir(parents=True)
                (event / "device").symlink_to(dev)
            r = probe.usb_inventory("/dev/ttyACM0", sysfs)
            self.assertEqual(r["vid"], "054c")
            self.assertEqual(r["gamepad_events"], ["/dev/input/event1"])

    def test_cli_fixture(self):
        cache = Path.home() / ".cache/waveshare-probe-tests"
        cache.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache) as tmp:
            path = Path(tmp) / "fixture.json"
            path.write_text(
                json.dumps(
                    {
                        "VERSION": "VERSION c1e7627 2026-09-28T21:32:39Z MODE controller\nOK",
                        "STATUS": "MODE controller\nOK",
                    }
                )
            )
            r = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/waveshare_probe.py"),
                    "--fixture",
                    str(path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(
            json.loads(r.stdout)["replies"]["STATUS"]["mode"], "controller"
        )


if __name__ == "__main__":
    unittest.main()
