"""Exercise actual MQTT byte transport via controlled sockets, not any live broker."""

import importlib.util
import json
import socket
import struct
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "mqtt_transport", ROOT / "scripts/waveshare_mqtt_status.py"
)
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)


def payload(age=0, historical=False):
    data = {
        "power": "unknown",
        "uptime_ms": 1234,
        "age_ms": age,
        "historical": historical,
        "boot_id": "0" * 16,
        "ps_event": 1,
        "ps_event_age_ms": 100,
        "ps_pressed": True,
    }
    return reader.mqtt_string(reader.TOPIC) + json.dumps(data).encode()


def send_publish(sock, first, data):
    sock.sendall(bytes([first]) + reader.remaining_length(len(data)) + data)


class TestMQTTTransport(unittest.TestCase):
    def test_auth_subscribe_skip_stale_receive_fresh_disconnect(self):
        client, server = socket.socketpair()
        seen = []
        errors = []

        def broker():
            try:
                first, data = reader.receive(server)
                seen.append((first, data))
                server.sendall(b"\x20\x02\0\0")
                first, data = reader.receive(server)
                seen.append((first, data))
                server.sendall(b"\x90\x03\0\x01\0")
                send_publish(server, 0x31, payload())
                send_publish(server, 0x30, payload(5000, True))
                send_publish(server, 0x30, payload())
                seen.append(reader.receive(server))
            except Exception as error:
                errors.append(type(error).__name__)
            finally:
                server.close()

        thread = threading.Thread(target=broker)
        thread.start()
        try:
            with patch.object(reader.socket, "create_connection", return_value=client):
                result = reader.status(
                    "127.0.0.1", 1883, "fixture-user", "fixture-only-pass"
                )
            thread.join(3)
            self.assertFalse(thread.is_alive())
            self.assertEqual(errors, [])
            self.assertEqual(result["ps_event"], 1)
            self.assertFalse(result["historical"])
            self.assertEqual(seen[0][0], 0x10)
            self.assertEqual(seen[0][1][7], 0xC2)
            self.assertIn(reader.mqtt_string(b"fixture-user"), seen[0][1])
            self.assertEqual(seen[1][0], 0x82)
            self.assertIn(reader.TOPIC, seen[1][1])
            self.assertEqual(seen[-1], (0xE0, b""))
        finally:
            client.close()

    def test_rejected_auth_never_subscribes(self):
        client, server = socket.socketpair()
        seen = []

        def broker():
            seen.append(reader.receive(server)[0])
            server.sendall(b"\x20\x02\0\x05")
            server.close()

        thread = threading.Thread(target=broker)
        thread.start()
        try:
            with patch.object(reader.socket, "create_connection", return_value=client):
                with self.assertRaises(ValueError):
                    reader.status("127.0.0.1")
            thread.join(2)
            self.assertEqual(seen, [0x10])
        finally:
            client.close()

    def test_fragmented_receive_and_deadline(self):
        client, server = socket.socketpair()
        try:
            server.sendall(b"\x30\x04test")
            first, data = reader.receive(client)
            self.assertEqual((first, data), (0x30, b"test"))
            with self.assertRaises(TimeoutError):
                reader.receive(client, deadline=reader.time.monotonic() + 0.02)
        finally:
            client.close()
            server.close()


if __name__ == "__main__":
    unittest.main()
