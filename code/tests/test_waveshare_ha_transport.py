"""Exercise actual urllib request construction against controlled fake responses."""

import importlib.util
import json
import secrets
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location(
    "ha_transport", ROOT / "scripts/waveshare_ha_power.py"
)
power = importlib.util.module_from_spec(spec)
spec.loader.exec_module(power)


class Response:
    def __init__(self, data):
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self, size):
        return self.data[:size]


class Opener:
    def __init__(self, data):
        self.data = data
        self.requests = []

    def open(self, request, timeout):
        self.requests.append((request, timeout))
        return Response(self.data)


class TestHATransport(unittest.TestCase):
    def config(self):
        return {
            "ha_url": "http://ha.lan",
            "entity_id": "switch.bc250_power",
            "exclusive_supply_verified": True,
            "ha_token": secrets.token_urlsafe(24),
        }

    def test_authorization_never_goes_to_relay(self):
        config = self.config()
        opener = Opener(b'{"POWER":"OFF"}')
        with patch.object(power, "build_opener", return_value=opener):
            result = power.request_json(config, "GET", "/owned-relay-state")
        request, timeout = opener.requests[0]
        self.assertEqual(result["POWER"], "OFF")
        self.assertEqual(request.full_url, "http://rozetka.lan/cm?cmnd=Power")
        self.assertIsNone(request.get_header("Authorization"))
        self.assertEqual(timeout, 3)

    def test_fixed_ha_request_and_private_header(self):
        config = self.config()
        opener = Opener(b"[]")
        with patch.object(power, "build_opener", return_value=opener):
            power.request_json(
                config,
                "POST",
                "/api/services/switch/turn_on",
                {"entity_id": "switch.bc250_power"},
            )
        request, _ = opener.requests[0]
        self.assertEqual(request.full_url, "http://ha.lan/api/services/switch/turn_on")
        self.assertEqual(
            request.get_header("Authorization"), "Bearer " + config["ha_token"]
        )
        self.assertEqual(json.loads(request.data), {"entity_id": "switch.bc250_power"})

    def test_redirect_and_oversized_reply_rejected(self):
        with self.assertRaises(ValueError):
            power.NoRedirect().redirect_request(
                None, None, 302, "", {}, "http://other-target"
            )
        with patch.object(power, "build_opener", return_value=Opener(b"X" * 16385)):
            with self.assertRaises(ValueError):
                power.request_json(
                    self.config(), "GET", "/api/states/switch.bc250_power"
                )


if __name__ == "__main__":
    unittest.main()
