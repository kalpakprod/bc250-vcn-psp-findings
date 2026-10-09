"""Fixture-only tests of non-invasive Linux telemetry."""

import importlib.util
import json
import os
import pty
import select
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "host_metrics", ROOT / "scripts/waveshare_host_metrics.py"
)
metrics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(metrics)


class TestHostMetrics(unittest.TestCase):
    def fixture(self):
        cache = Path.home() / ".cache/waveshare-metrics-tests"
        cache.mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(dir=cache)

    def test_dmi_identity_required_for_heartbeat(self):
        with self.fixture() as tmp:
            root = Path(tmp)
            self.assertFalse(metrics.verified_bc250(root))
            d = root / "class/dmi/id"
            d.mkdir(parents=True)
            (d / "board_name").write_text("ASRock BC-250")
            self.assertTrue(metrics.verified_bc250(root))
            (d / "board_name").write_text("another-laptop")
            self.assertFalse(metrics.verified_bc250(root))

    def test_missing_sensor_is_not_zero(self):
        with self.fixture() as tmp:
            result = metrics.snapshot(Path(tmp))
        self.assertEqual(result["metrics"], [])
        self.assertEqual(result["power_state"], "unknown")

    def test_only_allowlisted_hwmon_and_actual_units(self):
        with self.fixture() as tmp:
            root = Path(tmp)
            d = root / "class/hwmon/hwmon0"
            d.mkdir(parents=True)
            (d / "name").write_text("k10temp\n")
            (d / "temp1_label").write_text("Tctl\n")
            (d / "temp1_input").write_text("45125\n")
            (d / "temp2_input").write_text("bad\n")
            (d / "fan1_input").write_text("1200\n")
            unknown = root / "class/hwmon/hwmon1"
            unknown.mkdir()
            (unknown / "name").write_text("unknown_secret_driver")
            (unknown / "temp1_input").write_text("99999")
            result = metrics.snapshot(root)
        temps = [x for x in result["metrics"] if x["unit"] == "°C"]
        self.assertEqual(len(temps), 1)
        self.assertEqual(temps[0]["value"], 45.125)
        self.assertTrue(temps[0]["valid"])
        self.assertNotIn("secret", json.dumps(result))

    def test_actual_bc250_superio_hwmon_name(self):
        with self.fixture() as tmp:
            root = Path(tmp)
            d = root / "class/hwmon/hwmon0"
            d.mkdir(parents=True)
            (d / "name").write_text("nct6686\n")
            (d / "fan2_input").write_text("1372\n")
            (d / "temp14_input").write_text("57125\n")
            result = metrics.snapshot(root)
        self.assertEqual({item["unit"] for item in result["metrics"]}, {"RPM", "°C"})
        self.assertTrue(all(item["source"] == "nct6686" for item in result["metrics"]))

    def test_real_serial_fan_forwarding_keeps_sensor_indices(self):
        master, slave = pty.openpty()
        received = []
        errors = []

        def device():
            try:
                pending = b""
                while len(received) < 3:
                    if not select.select([master], [], [], 3)[0]:
                        raise TimeoutError("fixture missing command")
                    pending += os.read(master, 1024)
                    while b"\n" in pending:
                        line, pending = pending.split(b"\n", 1)
                        received.append(line.decode())
                        os.write(master, b"OK\n")
            except Exception as error:
                errors.append(error)

        worker = threading.Thread(target=device)
        worker.start()
        try:
            sample = {
                "metrics": [
                    {
                        "id": "nct6686:hwmon7:fan1",
                        "source": "nct6686",
                        "unit": "RPM",
                        "value": 1372,
                        "valid": True,
                    },
                    {
                        "id": "nct6686:hwmon7:fan2",
                        "source": "nct6686",
                        "unit": "RPM",
                        "value": 982,
                        "valid": True,
                    },
                ]
            }
            with patch.object(metrics, "verified_bc250", return_value=True):
                metrics.send_sample(os.ttyname(slave), sample)
            worker.join(4)
            self.assertFalse(worker.is_alive())
            self.assertEqual(errors, [])
            self.assertEqual(
                received, ["HOST_ALIVE", "METRIC fan1_rpm 1372", "METRIC fan2_rpm 982"]
            )
        finally:
            os.close(master)
            os.close(slave)
            worker.join(4)

    def test_nan_and_stale_file_not_substituted(self):
        with self.fixture() as tmp:
            d = Path(tmp) / "class/hwmon/hwmon0"
            d.mkdir(parents=True)
            (d / "name").write_text("amdgpu")
            (d / "temp1_input").write_text("nan")
            result = metrics.snapshot(Path(tmp))
        self.assertEqual(result["metrics"], [])
        self.assertTrue(result["errors"])


if __name__ == "__main__":
    unittest.main()
