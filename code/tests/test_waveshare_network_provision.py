"""No device I/O: validate the private configuration wire format."""

import importlib.util
import os
import pty
import secrets
import struct
import tempfile
import threading
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "provision", ROOT / "scripts/waveshare_provision_network.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TestProvision(unittest.TestCase):
    def fixture(self):
        return {
            "ssid": "fixture-only",
            "psk": "fixture-pass",
            "broker": "127.0.0.1",
            "web_token": secrets.token_hex(16),
        }

    def test_frame_size_and_crc(self):
        frame = module.frame(self.fixture())
        self.assertEqual(len(frame), 289)
        self.assertEqual(zlib.crc32(frame[:-4]), struct.unpack("<I", frame[-4:])[0])

    def test_wrong_device_version_receives_no_credentials(self):
        master, slave = pty.openpty()
        seen = []

        def device():
            data = b""
            while b"\n" not in data:
                data += os.read(master, 256)
            seen.append(data)
            os.write(
                master,
                b"VERSION aaaaaaaaaaaa 2026-09-30T00:00:00Z MODE controller\r\nOK\r\n",
            )

        thread = threading.Thread(target=device)
        thread.start()
        try:
            with self.assertRaises(ValueError):
                module.send_config(
                    os.ttyname(slave),
                    module.frame(self.fixture()),
                    False,
                    "bbbbbbbbbbbb",
                )
            thread.join(2)
            self.assertEqual(seen, [b"VERSION\n"])
        finally:
            os.close(master)
            os.close(slave)

    def test_bad_values_rejected(self):
        for key, value in [
            ("ssid", ""),
            ("ssid", "A" * 33),
            ("psk", "short"),
            ("broker", "8.8.8.8"),
            ("broker", "127.0.0.1"),
            ("web_token", "short"),
            ("port", 0),
        ]:
            config = self.fixture()
            config[key] = value
            with self.assertRaises(ValueError):
                module.frame(config)

    def test_public_config_rejected(self):
        cache = Path.home() / ".cache/waveshare-network-tests"
        cache.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache) as tmp:
            path = Path(tmp) / "config.json"
            path.write_text("{}")
            path.chmod(0o644)
            with self.assertRaises(ValueError):
                module.private_config(path)
            path.chmod(0o600)
            self.assertEqual(module.private_config(path), {})


if __name__ == "__main__":
    unittest.main()
