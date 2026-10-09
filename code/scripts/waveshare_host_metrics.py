#!/usr/bin/env python3
"""Read existing Linux hwmon files only; no I2C/SMN, power, installation or shell commands."""

import argparse
import datetime
import fcntl
import json
import math
import os
import re
import select
import termios
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

DRIVERS = {"k10temp", "amdgpu", "nct6683", "nct6687", "nct6686", "nvme"}
FIELDS = {
    "temp": ("°C", 1000),
    "fan": ("RPM", 1),
    "power": ("W", 1000000),
    "in": ("V", 1000),
    "curr": ("A", 1000),
}


def read_small(path):
    """Read one bounded sysfs value, without disclosing arbitrary source content."""
    with path.open() as stream:
        value = stream.read(257)
    if len(value) > 256:
        raise ValueError("oversized sysfs value")
    return value.strip()


def snapshot(sysfs=Path("/sys")):
    """Read allowlisted hwmon drivers; unavailable data never becomes zero."""
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result = {
        "schema": 1,
        "source": "linux_hwmon",
        "observed_at": timestamp,
        "power_state": "unknown",
        "board_identity": "bc250" if verified_bc250(sysfs) else "unverified",
        "hardware_acceptance": False,
        "metrics": [],
        "errors": [],
    }
    for hw in sorted((sysfs / "class/hwmon").glob("hwmon*")):
        try:
            driver = read_small(hw / "name")
        except (OSError, ValueError):
            continue
        if driver not in DRIVERS:
            continue
        for path in sorted(hw.glob("*_input")):
            match = re.fullmatch(r"(temp|fan|power|in|curr)(\d+)_input", path.name)
            if not match:
                continue
            kind, index = match.groups()
            unit, scale = FIELDS[kind]
            try:
                raw = read_small(path)
                if not re.fullmatch(r"-?\d+", raw):
                    raise ValueError("noninteger sysfs value")
                value = int(raw) / scale
                if not math.isfinite(value):
                    raise ValueError("nonfinite value")
                label_path = path.with_name(kind + index + "_label")
                label = read_small(label_path) if label_path.exists() else kind + index
                # Labels are for display, never executable or firmware data.
                label = re.sub(r"[^\w .:+/-]", "", label)[:48]
                result["metrics"].append(
                    {
                        "id": f"{driver}:{hw.name}:{kind}{index}",
                        "label": label,
                        "value": value,
                        "unit": unit,
                        "source": driver,
                        "valid": True,
                        "age_ms": 0,
                        "observed_at": timestamp,
                    }
                )
            except (OSError, ValueError, OverflowError):
                result["errors"].append(
                    {"source": driver, "sensor": kind + index, "state": "unavailable"}
                )
    return result


def verified_bc250(sysfs=Path("/sys")):
    """Require this Linux machine's board identity, not merely remote reachability."""
    for field in ("board_name", "product_name"):
        try:
            value = read_small(sysfs / "class/dmi/id" / field)
        except (OSError, ValueError):
            continue
        if re.search(r"\bBC[-_ ]?250\b", value, re.IGNORECASE):
            return True
    return False


def send_sample(device, sample):
    """Send only allowlisted measured values and an on-host heartbeat; never power commands."""
    if not verified_bc250():
        raise ValueError("This host is not identified as BC250; no metrics transmitted")
    values = {}
    for item in sample["metrics"]:
        if not item["valid"]:
            continue
        if (
            item["source"] == "k10temp"
            and item["unit"] == "°C"
            and "cpu_temp" not in values
        ):
            values["cpu_temp"] = round(item["value"] * 1000)
        elif (
            item["source"] == "amdgpu"
            and item["unit"] == "°C"
            and item["label"].lower() in ("edge", "temp1")
            and "gpu_temp" not in values
        ):
            values["gpu_temp"] = round(item["value"] * 1000)
        elif (
            item["source"] == "amdgpu"
            and item["unit"] == "W"
            and "gpu_power" not in values
        ):
            values["gpu_power"] = round(item["value"] * 1000)
        elif (
            item["source"] in {"nct6683", "nct6687", "nct6686"}
            and item["unit"] == "RPM"
            and item["id"].rsplit(":", 1)[-1] in {"fan1", "fan2"}
        ):
            key = item["id"].rsplit(":", 1)[-1] + "_rpm"
            if key not in values:
                values[key] = round(item["value"])
    commands = ["HOST_ALIVE"] + [
        f"METRIC {key} {value}" for key, value in values.items()
    ]
    fd = os.open(device, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    old = None
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        old = termios.tcgetattr(fd)
        attrs = termios.tcgetattr(fd)
        attrs[0] = attrs[1] = attrs[3] = 0
        attrs[2] |= termios.CLOCAL | termios.CREAD
        attrs[4] = attrs[5] = termios.B115200
        attrs[6][termios.VMIN] = attrs[6][termios.VTIME] = 0
        termios.tcsetattr(fd, termios.TCSANOW, attrs)
        for command in commands:
            data = (command + "\n").encode()
            end = time.monotonic() + 1
            while data:
                remaining = end - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("CDC write timeout")
                if select.select([], [fd], [], remaining)[1]:
                    try:
                        written = os.write(fd, data)
                    except BlockingIOError:
                        continue
                    if not written:
                        raise OSError("CDC write failed")
                    data = data[written:]
            # Consume only bounded acknowledgement; never retain unsolicited logs.
            reply = b""
            end = time.monotonic() + 1
            while time.monotonic() < end and len(reply) < 4096:
                if select.select([fd], [], [], 0.1)[0]:
                    chunk = os.read(fd, 512)
                    if not chunk:
                        raise OSError("CDC disconnected")
                    reply += chunk
                    if b"OK" in reply.splitlines():
                        break
            else:
                raise TimeoutError("No acknowledgement")
    finally:
        try:
            if old is not None:
                termios.tcsetattr(fd, termios.TCSANOW, old)
        finally:
            os.close(fd)


class ReadOnlyHandler(BaseHTTPRequestHandler):
    """Loopback-only JSON endpoint. No POST and no control operations."""

    def do_GET(self):
        if self.path not in ("/status", "/status.json"):
            self.send_error(404)
            return
        data = json.dumps(snapshot(), ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, _format, *_args):
        """Do not persist arbitrary URL/query content."""


def main():
    """Print a snapshot or explicitly serve a local read-only endpoint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--serve",
        action="store_true",
        help="read-only localhost HTTP, not a service install",
    )
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument(
        "--device",
        help="explicitly forward real local BC250 measurements to this verified Waveshare CDC",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="foreground 2-second loop, no service installation",
    )
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("port must be 1024..65535")
    if args.device:
        if args.serve:
            parser.error("choose serve or serial forwarding")
        if not verified_bc250():
            parser.error(
                "local DMI does not identify BC250; refusing metrics forwarding"
            )
        while True:
            send_sample(args.device, snapshot())
            if not args.watch:
                break
            time.sleep(2)
    elif args.watch:
        parser.error("--watch requires --device")
    elif args.serve:
        if not verified_bc250():
            parser.error(
                "local DMI does not identify BC250; refusing named AMD telemetry endpoint"
            )
        with HTTPServer(("127.0.0.1", args.port), ReadOnlyHandler) as server:
            server.serve_forever()
    else:
        print(json.dumps(snapshot(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
