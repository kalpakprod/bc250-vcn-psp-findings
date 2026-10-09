#!/usr/bin/env python3
"""Bounded, read-only CDC/USB evidence collection. Never switches firmware modes."""

import argparse
import array
import errno
import datetime
import fcntl
import json
import os
import re
import select
import termios
import time
from pathlib import Path

COMMANDS = ("VERSION", "STATUS")
MAX_REPLY = 16384
MODES = r"(controller|diagnostic|toctou|monitor|flash|recovery|overclock|vcn_unblock)"
VERSION = re.compile(
    r"VERSION ([0-9a-fA-F]{7,64}|unknown|nogit) (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z|unknown) MODE "
    + MODES
)
STATE = re.compile(r"(?:MODE |STATE mode=)" + MODES)


def parse_reply(command, text):
    """Keep only fully recognized protocol data, never unsolicited logs."""
    if command not in COMMANDS:
        raise ValueError("Only VERSION and STATUS are allowed")
    matches = []
    acknowledged = False
    for line in text.splitlines():
        if line == "OK":
            acknowledged = True
        match = (VERSION if command == "VERSION" else STATE).fullmatch(line)
        if match:
            if command == "VERSION":
                revision, built, mode = match.groups()
                if built != "unknown":
                    try:
                        datetime.datetime.strptime(built, "%Y-%m-%dT%H:%M:%SZ").replace(
                            tzinfo=datetime.timezone.utc
                        )
                    except ValueError:
                        continue
                matches.append({"revision": revision, "build_utc": built, "mode": mode})
            else:
                matches.append({"mode": match.group(1)})
    unique = {json.dumps(item, sort_keys=True) for item in matches}
    if len(unique) > 1:
        return {"state": "conflicting_reply", "acknowledged": acknowledged}
    if matches:
        return {"state": "recognized", "acknowledged": acknowledged, **matches[0]}
    return {
        "state": "acknowledged_unknown" if acknowledged else "no_recognized_reply",
        "acknowledged": acknowledged,
    }


def from_fixture(data):
    """Parse bounded offline responses without implying hardware acceptance."""
    if not isinstance(data, dict) or any(
        not isinstance(data.get(cmd), str) for cmd in COMMANDS
    ):
        raise ValueError("Fixture requires string VERSION and STATUS replies")
    if any(len(data[cmd].encode()) > MAX_REPLY for cmd in COMMANDS):
        raise ValueError("Fixture reply too large")
    return {
        "evidence_class": "fixture",
        "hardware_acceptance": False,
        "replies": {cmd: parse_reply(cmd, data[cmd]) for cmd in COMMANDS},
    }


def serial_probe(device, timeout):
    """Query only two read-only commands. Restore terminal settings on all paths."""
    if not 0.1 <= timeout <= 10:
        raise ValueError("timeout must be between 0.1 and 10 seconds")
    fd = os.open(device, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    old = None
    modem = None
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        old = termios.tcgetattr(fd)
        attrs = termios.tcgetattr(fd)
        attrs[0] = attrs[1] = attrs[3] = 0
        attrs[2] |= termios.CLOCAL | termios.CREAD
        attrs[4] = attrs[5] = termios.B115200
        attrs[6][termios.VMIN] = attrs[6][termios.VTIME] = 0
        termios.tcsetattr(fd, termios.TCSANOW, attrs)
        modem = array.array("i", [0])
        try:
            fcntl.ioctl(fd, termios.TIOCMGET, modem, True)
        except OSError as error:
            modem = None
            if error.errno != errno.ENOTTY:
                raise
        if modem is not None:
            asserted = array.array("i", [modem[0] | termios.TIOCM_DTR])
            fcntl.ioctl(fd, termios.TIOCMSET, asserted)
        replies = {}
        for command in COMMANDS:
            pending = (command + "\r\n").encode("ascii")
            deadline = time.monotonic() + timeout
            while pending:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("CDC write timeout")
                if select.select([], [fd], [], remaining)[1]:
                    try:
                        sent = os.write(fd, pending)
                    except BlockingIOError:
                        continue
                    if not sent:
                        raise OSError("CDC write made no progress")
                    pending = pending[sent:]
            received = bytearray()
            while time.monotonic() < deadline:
                if select.select([fd], [], [], max(0, deadline - time.monotonic()))[0]:
                    try:
                        chunk = os.read(fd, min(4096, MAX_REPLY + 1 - len(received)))
                    except BlockingIOError:
                        continue
                    if not chunk:
                        raise OSError("CDC disconnected")
                    received.extend(chunk)
                    if len(received) > MAX_REPLY:
                        raise OSError("CDC reply limit exceeded")
            replies[command] = parse_reply(
                command, received.decode("utf-8", errors="replace")
            )
        return {"state": "queried", "replies": replies}
    finally:
        try:
            try:
                if modem is not None:
                    fcntl.ioctl(fd, termios.TIOCMSET, modem)
            finally:
                if old is not None:
                    termios.tcsetattr(fd, termios.TCSANOW, old)
        finally:
            os.close(fd)


def usb_inventory(device, sysfs=Path("/sys")):
    """Only inventory inputs descending from this CDC's USB ancestor."""
    tty = sysfs / "class/tty" / Path(device).name / "device"
    if not tty.exists():
        return {"state": "no_usb_ancestor", "gamepad_events": []}
    target = tty.resolve()
    usb = next(
        (
            parent
            for parent in [target, *target.parents]
            if (parent / "idVendor").exists() and (parent / "idProduct").exists()
        ),
        None,
    )
    if usb is None:
        return {"state": "no_usb_ancestor", "gamepad_events": []}

    def hex_id(name):
        value = (usb / name).read_text().strip()
        return value if re.fullmatch(r"[0-9a-fA-F]{4}", value) else None

    classes = []
    for interface in usb.glob(usb.name + ":*"):
        path = interface / "bInterfaceClass"
        if path.exists():
            value = path.read_text().strip()
            if re.fullmatch(r"[0-9a-fA-F]{2}", value):
                classes.append(value.lower())
    events = []
    for event in sorted((sysfs / "class/input").glob("event*")):
        input_device = (event / "device").resolve()
        if not input_device.is_relative_to(usb):
            continue
        try:
            # BTN_SOUTH is the first Linux gamepad button; do not capture keyboards.
            bits = int(
                (input_device / "capabilities/key")
                .read_text()
                .replace(" ", "")
                .strip(),
                16,
            )
            if bits & (1 << 0x130):
                events.append("/dev/input/" + event.name)
        except (OSError, ValueError):
            continue
    return {
        "state": "usb_ancestor_found",
        "vid": hex_id("idVendor"),
        "pid": hex_id("idProduct"),
        "interface_classes": sorted(classes),
        "gamepad_events": events,
        "identity_note": "USB IDs do not prove board identity; input nodes do not prove button delivery",
    }


def live_probe(device, timeout):
    """Collect selected USB metadata and read-only CDC replies."""
    result = {"evidence_class": "actual_device_query", "hardware_acceptance": False}
    try:
        result["usb"] = usb_inventory(device)
    except OSError:
        result["usb"] = {"state": "inventory_error", "gamepad_events": []}
    try:
        result["serial"] = serial_probe(device, timeout)
        result["replies"] = result["serial"]["replies"]
    except (OSError, termios.error) as error:
        result["serial"] = {
            "state": "access_error",
            "error_type": type(error).__name__,
            "errno": getattr(error, "errno", None),
        }
    return result


def main():
    """Print JSON evidence; fail when firmware mode replies are not consistent."""
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--device", help="CDC node; only VERSION and STATUS are sent")
    source.add_argument(
        "--fixture", type=Path, help="offline sanitized response fixture"
    )
    parser.add_argument("--timeout", type=float, default=1.5)
    args = parser.parse_args()
    if not 0.1 <= args.timeout <= 10:
        parser.error("timeout must be between 0.1 and 10 seconds")
    try:
        result = (
            from_fixture(json.loads(args.fixture.read_text()))
            if args.fixture
            else live_probe(args.device, args.timeout)
        )
    except (OSError, ValueError) as error:
        print(
            json.dumps(
                {
                    "state": "input_error",
                    "error_type": type(error).__name__,
                    "hardware_acceptance": False,
                }
            )
        )
        return 1
    replies = result.get("replies", {})
    version = replies.get("VERSION", {})
    status = replies.get("STATUS", {})
    recognized = version.get("state") == status.get("state") == "recognized"
    consistent = recognized and version.get("mode") == status.get("mode")
    result["consistent_mode_reply"] = bool(consistent)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if consistent else 1


if __name__ == "__main__":
    raise SystemExit(main())
