#!/usr/bin/env python3
"""Explicit, time-bounded input-only UART capture to an owner-only new file."""

import argparse
import fcntl
import hashlib
import os
import re
import select
import termios
import time
from pathlib import Path

ALLOWED = (
    b"VERSION\n",
    b"UART_LOG\n",
    b"UART_RX_ON VERIFIED_3V3\n",
    b"UART_RX_OFF\n",
    b"MODE diagnostic\n",
    b"MODE controller\n",
    b"SPI_STATS\n",
    b"SPI_TRACE_ON VERIFIED_3V3\n",
    b"SPI_TRACE_READ\n",
    b"SPI_TRACE_OFF\n",
)


def parse_data(text):
    """Recognize only bounded firmware hex payloads; never print unsolicited UART logs."""
    for line in text.splitlines():
        match = re.fullmatch(r"UART_DATA (\d{1,3}) ([0-9A-F]*)", line)
        if match:
            size = int(match[1])
            encoded = match[2]
            if size > 128 or len(encoded) != size * 2:
                raise ValueError("UART payload bounds mismatch")
            return bytes.fromhex(encoded)
    raise ValueError("Recognized UART payload missing")


def exchange(fd, command, timeout=1):
    """Only this module's fixed command set is writable."""
    if command not in ALLOWED:
        raise ValueError("Command outside capture allowlist")
    end = time.monotonic() + timeout
    data = command
    while data:
        remaining = end - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("UART command write timeout")
        if select.select([], [fd], [], remaining)[1]:
            try:
                written = os.write(fd, data)
            except BlockingIOError:
                continue
            if not written:
                raise OSError("UART command write failed")
            data = data[written:]
    reply = b""
    while time.monotonic() < end and len(reply) < 4096:
        if select.select([fd], [], [], max(0, end - time.monotonic()))[0]:
            chunk = os.read(fd, 512)
            if not chunk:
                raise OSError("CDC disconnected")
            reply += chunk
            if b"OK" in reply.splitlines():
                return reply.decode(errors="replace")
    raise TimeoutError("Capture acknowledgement timeout")


def capture(device, output, revision, verified, seconds):
    """No TX to AMD; explicit confirmation/version required before enabling RX."""
    if not re.fullmatch(r"[0-9a-f]{12}", revision):
        raise ValueError("Expected staged source fingerprint required")
    if not verified:
        raise ValueError("Chosen wiring level/ground/connector scheme not confirmed")
    if not 1 <= seconds <= 60:
        raise ValueError("Capture duration must be 1..60 seconds")
    fd = os.open(device, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    old = None
    attempted_enable = False
    attempted_mode = False
    initial_mode = None
    result = None
    dest = None
    sha = hashlib.sha256()
    count = 0
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        old = termios.tcgetattr(fd)
        attrs = termios.tcgetattr(fd)
        attrs[0] = attrs[1] = attrs[3] = 0
        attrs[2] |= termios.CLOCAL | termios.CREAD
        attrs[4] = attrs[5] = termios.B115200
        attrs[6][termios.VMIN] = attrs[6][termios.VTIME] = 0
        termios.tcsetattr(fd, termios.TCSANOW, attrs)
        version = exchange(fd, b"VERSION\n")
        matches = [
            re.fullmatch(
                r"VERSION "
                + revision
                + r" \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z MODE (controller|diagnostic)",
                line,
            )
            for line in version.splitlines()
        ]
        matches = [match for match in matches if match]
        if len(matches) != 1:
            raise ValueError(
                "Installed firmware does not match expected capture protocol"
            )
        dest = os.open(
            output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
        )
        initial_mode = matches[0].group(1)
        if initial_mode == "controller":
            attempted_mode = True
            response = exchange(fd, b"MODE diagnostic\n")
            if "STATE mode=diagnostic" not in response.splitlines():
                raise ValueError("Diagnostic mode not acknowledged")
        attempted_enable = True
        response = exchange(fd, b"UART_RX_ON VERIFIED_3V3\n")
        if "OK uart-rx-enabled" not in response.splitlines():
            raise ValueError("UART RX was not enabled")
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            data = parse_data(exchange(fd, b"UART_LOG\n"))
            if data:
                pending = memoryview(data)
                while pending:
                    written = os.write(dest, pending)
                    if not written:
                        raise OSError("Private capture file write failed")
                    pending = pending[written:]
                sha.update(data)
                count += len(data)
            time.sleep(0.1)
        result = {
            "captured_bytes": count,
            "output": str(output.resolve()),
            "sha256": sha.hexdigest(),
            "content_printed": False,
            "rx_only": True,
            "hardware_acceptance": False,
            "disable_acknowledged": False,
            "diagnostic_isolation": True,
            "original_mode_restored": False,
        }
        return result
    finally:
        if attempted_enable:
            try:
                response = exchange(fd, b"UART_RX_OFF\n")
                if result is not None:
                    result["disable_acknowledged"] = (
                        "OK uart-rx-disabled" in response.splitlines()
                    )
            except (OSError, ValueError, TimeoutError):
                pass
        if attempted_mode:
            try:
                response = exchange(fd, b"MODE controller\n")
                if result is not None:
                    result["original_mode_restored"] = (
                        "STATE mode=controller" in response.splitlines()
                    )
            except (OSError, ValueError, TimeoutError):
                pass
        elif result is not None:
            result["original_mode_restored"] = initial_mode == "diagnostic"
        if dest is not None:
            os.close(dest)
        try:
            if old is not None:
                termios.tcsetattr(fd, termios.TCSANOW, old)
        finally:
            os.close(fd)


def main():
    """Local operator action only; no device capture is run during development."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-version", required=True)
    parser.add_argument("--verified-3v3", action="store_true")
    parser.add_argument("--seconds", type=float, default=10)
    args = parser.parse_args()
    try:
        import json

        print(
            json.dumps(
                capture(
                    args.device,
                    args.output,
                    args.expected_version,
                    args.verified_3v3,
                    args.seconds,
                )
            )
        )
    except (OSError, ValueError, TimeoutError) as error:
        print("Capture failed:", type(error).__name__, "(raw content suppressed)")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
