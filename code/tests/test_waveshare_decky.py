"""Decky backend freshness tests, no Decky installation or HTTP calls."""

import datetime
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "decky_backend",
    ROOT / "candidates/waveshare-adapter-safe-v001/tools/decky-plugin/main.py",
)
backend = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend)


class TestDecky(unittest.TestCase):
    def data(self, age=0):
        return {
            "schema": 1,
            "source": "linux_hwmon",
            "board_identity": "bc250",
            "observed_at": (
                datetime.datetime.now(datetime.timezone.utc)
                - datetime.timedelta(seconds=age)
            ).isoformat(),
            "metrics": [
                {
                    "label": "Tctl",
                    "value": 45.1,
                    "unit": "°C",
                    "source": "k10temp",
                    "valid": True,
                }
            ],
        }

    def test_fresh_metrics_source(self):
        r = backend.sanitized_status(self.data())
        self.assertTrue(r["available"])
        self.assertEqual(r["metrics"][0]["source"], "k10temp")

    def test_actual_superio_name_preserved(self):
        data = self.data()
        data["metrics"][0].update(
            source="nct6686", unit="RPM", value=1372, label="fan2"
        )
        self.assertEqual(
            backend.sanitized_status(data)["metrics"][0]["source"], "nct6686"
        )

    def test_stale_and_wrong_source(self):
        self.assertFalse(backend.sanitized_status(self.data(10))["available"])
        d = self.data()
        d["source"] = "fabricated"
        with self.assertRaises(ValueError):
            backend.sanitized_status(d)

    def test_wrong_board_is_not_amd_data(self):
        data = self.data()
        data["board_identity"] = "unverified"
        with self.assertRaises(ValueError):
            backend.sanitized_status(data)

    def test_nonfinite_or_invalid_not_zero(self):
        d = self.data()
        d["metrics"][0]["value"] = float("nan")
        self.assertEqual(backend.sanitized_status(d)["metrics"], [])
        d = self.data()
        d["metrics"][0]["valid"] = False
        self.assertEqual(backend.sanitized_status(d)["metrics"], [])


if __name__ == "__main__":
    unittest.main()
