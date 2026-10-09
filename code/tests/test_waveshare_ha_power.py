"""HA API is replaced by a fake; never touches a live switch."""

import importlib.util
import secrets
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location(
    "ha_power", ROOT / "scripts/waveshare_ha_power.py"
)
power = importlib.util.module_from_spec(spec)
spec.loader.exec_module(power)


class TestHAPower(unittest.TestCase):
    def config(self):
        return {
            "ha_url": "http://127.0.0.1",
            "entity_id": "switch.bc250_power",
            "exclusive_supply_verified": True,
            "ha_token": secrets.token_urlsafe(24),
        }

    def test_dry_run_is_nonmutating(self):
        calls = []

        def api(_config, method, path, payload=None):
            calls.append((method, path, payload))
            return (
                {"POWER": "OFF"}
                if path == "/owned-relay-state"
                else {"entity_id": "switch.bc250_power", "state": "off"}
            )

        result = power.power_on(self.config(), api=api)
        self.assertEqual(result["action"], "dry_run")
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0][0], "GET")

    def test_unknown_and_on_never_actuate(self):
        for state in ["unknown", "unavailable", "on"]:
            calls = []

            def api(_config, method, path, payload=None):
                calls.append(method)
                return (
                    {"POWER": "ON" if state == "on" else "OFF"}
                    if path == "/owned-relay-state"
                    else {"entity_id": "switch.bc250_power", "state": state}
                )

            result = power.power_on(self.config(), True, api)
            self.assertNotEqual(result["action"], "power_on_requested")
            self.assertEqual(calls, ["GET", "GET"])

    def test_explicit_on_has_fixed_service_and_target(self):
        calls = []

        def api(_config, method, path, payload=None):
            calls.append((method, path, payload))
            return (
                {"POWER": "OFF"}
                if path == "/owned-relay-state"
                else {"entity_id": "switch.bc250_power", "state": "off"}
            )

        result = power.power_on(self.config(), True, api)
        self.assertEqual(result["action"], "power_on_requested")
        self.assertEqual(
            calls[-1],
            (
                "POST",
                "/api/services/switch/turn_on",
                {"entity_id": "switch.bc250_power"},
            ),
        )

    def test_missing_physical_supply_reply_blocks(self):
        calls = []

        def api(_config, method, path, payload=None):
            calls.append(method)
            return {"POWER": "UNKNOWN"}

        self.assertEqual(power.power_on(self.config(), True, api)["action"], "blocked")
        self.assertEqual(calls, ["GET"])

    def event(self):
        return {
            "historical": False,
            "boot_id": "0" * 16,
            "ps_event": 1,
            "ps_event_age_ms": 50,
            "received_monotonic": time.monotonic(),
        }

    def test_ps_hold_or_replay_not_fresh(self):
        for event in [
            {"ps_pressed": True},
            dict(self.event(), historical=True),
            dict(self.event(), ps_event_age_ms=2000),
        ]:
            self.assertFalse(power.fresh_ps_event(event))
        self.assertTrue(power.fresh_ps_event(self.event()))

    def test_event_dedup_owner_only(self):
        cache = Path.home() / ".cache/waveshare-power-tests"
        cache.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache) as tmp:
            path = Path(tmp) / "event.json"
            event = self.event()
            self.assertTrue(power.claim_ps_event(event, path))
            self.assertFalse(power.claim_ps_event(event, path))
            event["ps_event"] = 2
            self.assertTrue(power.claim_ps_event(event, path))
            event["boot_id"] = "1" * 16
            event["ps_event"] = 1
            self.assertTrue(power.claim_ps_event(event, path))
            path.chmod(0o644)
            with self.assertRaises(ValueError):
                power.claim_ps_event(dict(event, ps_event=2), path)

    def test_duplicate_event_never_posts(self):
        calls = []

        def api(_config, method, path, payload=None):
            calls.append(method)
            return (
                {"POWER": "OFF"}
                if path == "/owned-relay-state"
                else {"entity_id": "switch.bc250_power", "state": "off"}
            )

        result = power.power_on(
            self.config(), True, api, event=self.event(), claim=lambda event: False
        )
        self.assertEqual(result["action"], "blocked")
        self.assertNotIn("POST", calls)

    def test_watch_survives_transient_mqtt_timeout(self):
        import waveshare_mqtt_status

        with (
            patch.object(sys, "argv", ["power", "--config", "unused", "--watch-ps"]),
            patch.object(power, "private_config", return_value=self.config()),
            patch.object(waveshare_mqtt_status, "status", side_effect=[TimeoutError(), {}]) as reader,
            patch.object(power.time, "sleep", side_effect=[None, KeyboardInterrupt()]),
            patch.object(power, "request_json") as api,
        ):
            with self.assertRaises(KeyboardInterrupt):
                power.main()
            self.assertEqual(reader.call_count, 2)
            api.assert_not_called()

    def test_foreign_or_unconfirmed_target_rejected(self):
        for key, value in [
            ("entity_id", "switch.other_machine"),
            ("ha_url", "https://example.com"),
            ("exclusive_supply_verified", False),
        ]:
            config = self.config()
            config[key] = value
            with self.assertRaises(ValueError):
                power.validate_config(config)


if __name__ == "__main__":
    unittest.main()
