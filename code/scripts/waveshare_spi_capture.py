#!/usr/bin/env python3
"""Bounded private input-only SPI waveform capture, never a full BIOS dump."""

import argparse
import fcntl
import hashlib
import json
import os
import re
import struct
import termios
import time
from pathlib import Path

from waveshare_uart_capture import exchange


def parse_data(text):
    """Accept exactly one bounded word frame; preserve PIO little-endian packing."""
    frames = [
        re.fullmatch(r"SPI_DATA (\d{1,2}) ([0-9A-F]*)", line)
        for line in text.splitlines()
        if line.startswith("SPI_DATA ")
    ]
    if len(frames) != 1 or frames[0] is None:
        raise ValueError("Expected one SPI frame")
    count, data = frames[0].groups()
    count = int(count)
    if count > 32 or len(data) != count * 8:
        raise ValueError("SPI frame bounds mismatch")
    return b"".join(
        struct.pack("<I", int(data[i : i + 8], 16)) for i in range(0, len(data), 8)
    )


def parse_state(text):
    """Reject contradictory, malformed or unbounded capture metadata."""
    lines = [line[10:] for line in text.splitlines() if line.startswith("SPI_STATE ")]
    if len(lines) != 1:
        raise ValueError("Expected one SPI state")
    data = json.loads(lines[0])
    if not isinstance(data, dict):
        raise ValueError("Invalid capture state object")
    if (
        data.get("state") not in {"idle", "running", "complete", "timeout", "overrun"}
        or data.get("full_rom") is not False
        or data.get("quad") is not False
        or data.get("gpio_base") != 10
    ):
        raise ValueError("Unexpected capture scope")
    for field, limit in [
        ("sample_hz", 200_000_000),
        ("samples", 16384),
        ("remaining_words", 2048),
    ]:
        if type(data.get(field)) is not int or not 0 <= data[field] <= limit:
            raise ValueError("Invalid capture metadata")
    if data["state"] == "complete" and (
        data["samples"] != 16384 or data["sample_hz"] == 0
    ):
        raise ValueError("Incomplete waveform")
    return data


def capture(device, output, revision, verified):
    """Capture one finite waveform, disarm and restore mode, never print bytes."""
    if not verified or not re.fullmatch(r"[0-9a-f]{12}", revision):
        raise ValueError("Expected source ID and selected wiring confirmation required")
    # Reserve output before sending any mode or capture command.
    dest = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    fd = None
    old = None
    attempted_mode = attempted_capture = False
    result = None
    initial = None
    try:
        fd = os.open(device, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        old = termios.tcgetattr(fd)
        attrs = termios.tcgetattr(fd)
        attrs[0] = attrs[1] = attrs[3] = 0
        attrs[2] |= termios.CLOCAL | termios.CREAD
        attrs[4] = attrs[5] = termios.B115200
        attrs[6][termios.VMIN] = attrs[6][termios.VTIME] = 0
        termios.tcsetattr(fd, termios.TCSANOW, attrs)
        versions = [
            re.fullmatch(
                r"VERSION "
                + revision
                + r" \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z MODE (controller|diagnostic)",
                line,
            )
            for line in exchange(fd, b"VERSION\n").splitlines()
        ]
        versions = [v for v in versions if v]
        if len(versions) != 1:
            raise ValueError("Unexpected installed version")
        initial = versions[0].group(1)
        if initial == "controller":
            attempted_mode = True
            if (
                "STATE mode=diagnostic"
                not in exchange(fd, b"MODE diagnostic\n").splitlines()
            ):
                raise ValueError("Diagnostic mode not acknowledged")
        attempted_capture = True
        if (
            "OK spi-trace-started"
            not in exchange(fd, b"SPI_TRACE_ON VERIFIED_3V3\n").splitlines()
        ):
            raise ValueError("Capture start not acknowledged")
        end = time.monotonic() + 3
        while True:
            state = parse_state(exchange(fd, b"SPI_STATS\n"))
            if state["state"] == "complete":
                break
            if state["state"] != "running" or time.monotonic() >= end:
                raise TimeoutError("No complete finite waveform")
            time.sleep(0.02)
        if state["remaining_words"] != 2048:
            raise ValueError("Waveform was already consumed")
        payload = bytearray()
        for _ in range(64):
            data = parse_data(exchange(fd, b"SPI_TRACE_READ\n"))
            if len(data) != 128:
                raise ValueError("Incomplete capture chunk")
            payload.extend(data)
        if len(payload) != 8192:
            raise ValueError("Incomplete bounded waveform")
        header = (
            json.dumps(
                {
                    "schema": 1,
                    "format": "pio_4bit_le32",
                    "pins": ["CLK", "MOSI", "MISO", "CS"],
                    "source_id": revision,
                    "sample_hz": state["sample_hz"],
                    "samples": 16384,
                    "full_rom": False,
                    "quad": False,
                    "payload_sha256": hashlib.sha256(payload).hexdigest(),
                }
            ).encode()
            + b"\n"
        )
        data = memoryview(header + payload)
        while data:
            n = os.write(dest, data)
            if not n:
                raise OSError("Private waveform write failed")
            data = data[n:]
        result = {
            "output": str(output.resolve()),
            "payload_bytes": len(payload),
            "payload_sha256": hashlib.sha256(payload).hexdigest(),
            "sample_hz": state["sample_hz"],
            "full_rom": False,
            "hardware_acceptance": False,
            "content_printed": False,
            "disarm_acknowledged": False,
            "original_mode_restored": False,
        }
        return result
    finally:
        try:
            if fd is not None:
                if attempted_capture:
                    try:
                        ack = (
                            "OK spi-trace-stopped"
                            in exchange(fd, b"SPI_TRACE_OFF\n").splitlines()
                        )
                        if result is not None:
                            result["disarm_acknowledged"] = ack
                    except (OSError, ValueError, TimeoutError):
                        pass
                if attempted_mode:
                    try:
                        ack = (
                            "STATE mode=controller"
                            in exchange(fd, b"MODE controller\n").splitlines()
                        )
                        if result is not None:
                            result["original_mode_restored"] = ack
                    except (OSError, ValueError, TimeoutError):
                        pass
                elif result is not None:
                    result["original_mode_restored"] = initial == "diagnostic"
                try:
                    if old is not None:
                        termios.tcsetattr(fd, termios.TCSANOW, old)
                finally:
                    os.close(fd)
        finally:
            os.close(dest)


def main():
    """Explicit operator-only action; no capture on import."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-version", required=True)
    parser.add_argument("--verified-3v3", action="store_true")
    args = parser.parse_args()
    try:
        print(
            json.dumps(
                capture(
                    args.device, args.output, args.expected_version, args.verified_3v3
                )
            )
        )
    except (OSError, ValueError, TimeoutError) as error:
        print(
            json.dumps(
                {
                    "captured": False,
                    "error_type": type(error).__name__,
                    "content_printed": False,
                }
            )
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
