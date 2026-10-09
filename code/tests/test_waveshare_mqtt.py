"""Owned-topic MQTT framing fixtures only; no network connections."""

import importlib.util
import json
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "mqtt_reader", ROOT / "scripts/waveshare_mqtt_status.py"
)
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)


class TestMQTT(unittest.TestCase):
    def payload(self, topic=reader.TOPIC):
        return (
            struct.pack("!H", len(topic))
            + topic
            + json.dumps(
                {
                    "power": "unknown",
                    "uptime_ms": 500,
                    "ps_pressed": True,
                    "age_ms": 0,
                    "historical": False,
                    "ps_event": 1,
                    "ps_event_age_ms": 100,
                    "boot_id": "0" * 16,
                    "wifi_secret": "not_returned",
                }
            ).encode()
        )

    def test_owned_fresh_nonretained(self):
        result, _ = reader.parse_publish(0x30, self.payload())
        self.assertTrue(result["ps_pressed"])
        self.assertEqual(result["ps_event"], 1)
        self.assertEqual(result["ps_event_age_ms"], 100)
        self.assertNotIn("secret", json.dumps(result))

    def test_retained_and_foreign_not_accepted(self):
        self.assertIsNone(reader.parse_publish(0x31, self.payload()))
        self.assertIsNone(reader.parse_publish(0x30, self.payload(b"other/topic")))

    def test_missing_or_historical_age_rejected(self):
        missing = (
            reader.mqtt_string(reader.TOPIC)
            + json.dumps(
                {"power": "unknown", "uptime_ms": 500, "ps_pressed": True}
            ).encode()
        )
        self.assertIsNone(reader.parse_publish(0x30, missing))
        for age, historical in [(2000, False), (0, True), (-1, False)]:
            payload = (
                reader.mqtt_string(reader.TOPIC)
                + json.dumps(
                    {
                        "power": "unknown",
                        "uptime_ms": 500,
                        "age_ms": age,
                        "historical": historical,
                        "ps_pressed": True,
                    }
                ).encode()
            )
            self.assertIsNone(reader.parse_publish(0x30, payload))

    def test_size_limit(self):
        self.assertEqual(reader.remaining_length(128), b"\x80\x01")
        with self.assertRaises(ValueError):
            reader.remaining_length(20000)


if __name__ == "__main__":
    unittest.main()
