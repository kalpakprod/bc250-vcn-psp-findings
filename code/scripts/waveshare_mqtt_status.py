#!/usr/bin/env python3
"""Read one fresh owned-topic MQTT snapshot, no third-party client or power actions."""

import argparse
import ipaddress
import json
import re
import socket
import struct
import time

TOPIC = b"bc250/wv/status"


def remaining_length(size):
    """MQTT variable-length encoding, bounded for local status messages."""
    if not 0 <= size <= 16384:
        raise ValueError("MQTT packet too large")
    out = bytearray()
    while True:
        byte = size % 128
        size //= 128
        out.append(byte | (0x80 if size else 0))
        if not size:
            return bytes(out)


def mqtt_string(value):
    """Length-prefix one small protocol string."""
    if len(value) > 1024:
        raise ValueError("MQTT string too large")
    return struct.pack("!H", len(value)) + value


def receive(sock, deadline=None):
    """Read one bounded MQTT packet, not arbitrary topic data."""

    if deadline is None:
        deadline = time.monotonic() + 3

    def exact(size):
        data = b""
        while len(data) < size:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("MQTT packet deadline exceeded")
            sock.settimeout(remaining)
            part = sock.recv(size - len(data))
            if not part:
                raise OSError("MQTT disconnected")
            data += part
        return data

    first = exact(1)[0]
    length = 0
    multiplier = 1
    for _ in range(4):
        byte = exact(1)[0]
        length += (byte & 127) * multiplier
        if length > 16384:
            raise ValueError("MQTT packet exceeds limit")
        if not byte & 128:
            return first, exact(length)
        multiplier *= 128
    raise ValueError("Invalid remaining length")


def parse_publish(first, payload):
    """Accept only QoS0/1 nonretained data on the exact owner adapter topic."""
    if first >> 4 != 3 or first & 1:
        return None
    if len(payload) < 2:
        raise ValueError("Short PUBLISH")
    size = struct.unpack("!H", payload[:2])[0]
    if payload[2 : 2 + size] != TOPIC:
        return None
    pos = 2 + size
    qos = (first >> 1) & 3
    if qos > 1:
        raise ValueError("Unsupported MQTT QoS")
    packet_id = None
    if qos:
        if len(payload) < pos + 2:
            raise ValueError("Short QoS packet")
        packet_id = payload[pos : pos + 2]
        pos += 2
    data = json.loads(payload[pos:])
    if (
        not isinstance(data, dict)
        or data.get("power") not in ("on", "unknown")
        or type(data.get("uptime_ms")) is not int
        or not 0 <= data["uptime_ms"] <= 0xFFFFFFFF
        or type(data.get("age_ms")) is not int
        or not 0 <= data["age_ms"] <= 1000
        or data.get("historical") is not False
    ):
        return None
    result = {
        "power": data["power"],
        "uptime_ms": data["uptime_ms"],
        "age_ms": data["age_ms"],
        "historical": False,
        "received_monotonic": time.monotonic(),
        "source": "owned_waveshare_mqtt",
        "hardware_acceptance": False,
    }
    for name in ["bt_connected", "identity_ready", "ps_pressed", "mqtt_connected"]:
        if type(data.get(name)) is bool:
            result[name] = data[name]
    event = data.get("ps_event")
    event_age = data.get("ps_event_age_ms")
    boot = data.get("boot_id")
    if (
        type(event) is int
        and 0 < event <= 0xFFFFFFFF
        and type(event_age) is int
        and 0 <= event_age <= 0xFFFFFFFF
        and isinstance(boot, str)
        and re.fullmatch(r"[0-9a-f]{16}", boot)
    ):
        result.update(
            ps_event=event, ps_event_age_ms=event_age + data["age_ms"], boot_id=boot
        )
    return result, packet_id


def status(broker, port=1883, username="", password=""):
    """One bounded LAN subscription; optional private credentials never enter CLI/logs."""
    address = ipaddress.IPv4Address(broker)
    if (
        not address.is_private
        or address.is_loopback
        or address.is_multicast
        or address.is_unspecified
    ):
        raise ValueError("Private LAN broker required")
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("Invalid broker port")
    if (
        not isinstance(username, str)
        or not isinstance(password, str)
        or any("\0" in value for value in (username, password))
    ):
        raise ValueError("Invalid MQTT credential type")
    user = username.encode()
    secret = password.encode()
    if len(user) > 128 or len(secret) > 128 or (secret and not user):
        raise ValueError("Invalid MQTT credential size")
    import secrets

    client = mqtt_string(("bc250-wv-read-" + secrets.token_hex(4)).encode())
    flags = 0x02
    if user:
        flags |= 0x80
        client += mqtt_string(user)
    if secret:
        flags |= 0x40
        client += mqtt_string(secret)
    variable = b"\x00\x04MQTT\x04" + bytes([flags]) + b"\x00\x0a"
    with socket.create_connection((broker, port), timeout=3) as sock:
        sock.sendall(
            b"\x10" + remaining_length(len(variable) + len(client)) + variable + client
        )
        kind, data = receive(sock)
        if kind != 0x20 or data != b"\0\0":
            raise ValueError("Broker connection not accepted; no auth bypass")
        subscription = b"\0\x01" + mqtt_string(TOPIC) + b"\0"
        sock.sendall(b"\x82" + remaining_length(len(subscription)) + subscription)
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            sock.settimeout(max(0.1, deadline - time.monotonic()))
            first, payload = receive(sock, deadline)
            parsed = parse_publish(first, payload)
            if parsed:
                result, packet_id = parsed
                if packet_id:
                    sock.sendall(b"\x40\x02" + packet_id)
                sock.sendall(b"\xe0\0")
                return result
    raise TimeoutError("No fresh nonretained owned status")


def main():
    """Read-only explicit LAN observation; never prints arbitrary broker payloads."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--broker", required=True)
    parser.add_argument("--port", type=int, default=1883)
    args = parser.parse_args()
    try:
        print(json.dumps(status(args.broker, args.port)))
    except (OSError, ValueError, TimeoutError) as error:
        print(
            json.dumps(
                {
                    "state": "unavailable",
                    "error_type": type(error).__name__,
                    "power": "unknown",
                }
            )
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
