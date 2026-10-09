#!/usr/bin/env python3
"""Opt-in BC250 power-on via existing HA; never power-off, reset or arbitrary service calls."""

import argparse
import fcntl
import json
import os
import re
import stat
import time
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from waveshare_provision_network import private_config


class NoRedirect(HTTPRedirectHandler):
    """Never forward an Authorization header to a redirect target."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Redirect refused")


def validate_config(config):
    """Bind only the already documented owned HA and BC250 switch."""
    url = config.get("ha_url", "")
    parsed = urlsplit(url)
    if (
        parsed.scheme not in ("http", "https")
        or parsed.hostname not in ("ha.lan", "homeassistant.local", "127.0.0.1")
        or parsed.username
        or parsed.password
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("HA target differs from documented BC250 HA")
    if config.get("entity_id") != "switch.bc250_power":
        raise ValueError("Only the documented BC250 power switch is allowed")
    if config.get("exclusive_supply_verified") is not True:
        raise ValueError("Exclusive supply of this BC250 is not confirmed")
    token = config.get("ha_token")
    if not isinstance(token, str) or not token or "\n" in token or "\r" in token:
        raise ValueError("Private HA authorization is not configured")
    return url.rstrip("/")


def request_json(config, method, path, payload=None):
    """Small fixed-API request, without credential/query logging or redirects."""
    base = validate_config(config)
    relay = path == "/owned-relay-state"
    if relay:
        if method != "GET" or payload is not None:
            raise ValueError("Relay is read-only")
        url = "http://rozetka.lan/cm?cmnd=Power"
    else:
        url = base + path
    data = None if payload is None else json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    if not relay:
        headers["Authorization"] = "Bearer " + config["ha_token"]
    req = Request(url, data=data, method=method, headers=headers)
    opener = build_opener(ProxyHandler({}), NoRedirect())
    with opener.open(req, timeout=3) as response:
        body = response.read(16385)
        if len(body) > 16384:
            raise ValueError("Oversized HA reply")
        return json.loads(body)


def fresh_ps_event(observed):
    """Only a recent rising edge, never held-state or replayed historical telemetry."""
    if not isinstance(observed, dict) or observed.get("historical") is not False:
        return False
    if (
        type(observed.get("ps_event")) is not int
        or not 0 < observed["ps_event"] <= 0xFFFFFFFF
    ):
        return False
    if not isinstance(observed.get("boot_id"), str) or not re.fullmatch(
        r"[0-9a-f]{16}", observed["boot_id"]
    ):
        return False
    age = observed.get("ps_event_age_ms")
    received = observed.get("received_monotonic")
    if (
        type(age) is not int
        or type(received) not in (int, float)
        or not 0 <= age <= 1500
    ):
        return False
    elapsed = time.monotonic() - received
    return 0 <= elapsed and age + elapsed * 1000 <= 1500


def claim_ps_event(observed, path=None):
    """Owner-only locked local deduplication; an attempt is recorded before actuation."""
    if not fresh_ps_event(observed):
        return False
    if path is None:
        parent = Path.home() / ".cache/waveshare-power"
        parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        info = os.stat(parent, follow_symlinks=False)
        if (
            not stat.S_ISDIR(info.st_mode)
            or info.st_uid != os.getuid()
            or info.st_mode & 0o077
        ):
            raise ValueError("Private event directory required")
        path = parent / "last-ps-event.json"
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(fd)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.getuid()
            or info.st_mode & 0o077
        ):
            raise ValueError("Private event file required")
        fcntl.flock(fd, fcntl.LOCK_EX)
        raw = os.read(fd, 4097)
        if len(raw) > 4096:
            raise ValueError("Event file oversized")
        old = json.loads(raw) if raw else None
        if old is not None and not isinstance(old, dict):
            raise ValueError("Invalid event file")
        if (
            old
            and old.get("boot_id") == observed["boot_id"]
            and type(old.get("ps_event")) is int
            and old["ps_event"] >= observed["ps_event"]
        ):
            return False
        data = json.dumps(
            {"boot_id": observed["boot_id"], "ps_event": observed["ps_event"]}
        ).encode()
        os.lseek(fd, 0, os.SEEK_SET)
        os.ftruncate(fd, 0)
        while data:
            written = os.write(fd, data)
            if not written:
                raise OSError("Event file write failed")
            data = data[written:]
        os.fsync(fd)
        return True
    finally:
        os.close(fd)


def power_on(config, execute=False, api=request_json, event=None, claim=claim_ps_event):
    """No off inference from network loss; a real fresh off reply is required."""
    validate_config(config)
    start = time.monotonic()
    relay = api(config, "GET", "/owned-relay-state")
    if (
        time.monotonic() - start > 3
        or not isinstance(relay, dict)
        or relay.get("POWER") not in ("ON", "OFF")
    ):
        return {"action": "blocked", "reason": "physical_supply_unknown"}
    start = time.monotonic()
    state = api(config, "GET", "/api/states/switch.bc250_power")
    if time.monotonic() - start > 3:
        return {"action": "blocked", "reason": "stale_reply"}
    if not isinstance(state, dict) or state.get("entity_id") != "switch.bc250_power":
        return {"action": "blocked", "reason": "wrong_target"}
    if (state.get("state") == "on" and relay["POWER"] != "ON") or (
        state.get("state") == "off" and relay["POWER"] != "OFF"
    ):
        return {"action": "blocked", "reason": "supply_state_conflict"}
    if state.get("state") == "on":
        return {
            "action": "none",
            "reason": "supply_already_on",
            "board_running": "unverified",
        }
    if state.get("state") != "off":
        return {"action": "blocked", "reason": "supply_state_unknown"}
    if not execute:
        return {
            "action": "dry_run",
            "would_call": "switch.turn_on",
            "requires_explicit_execution": True,
        }
    if event is not None and (not fresh_ps_event(event) or not claim(event)):
        return {"action": "blocked", "reason": "ps_event_stale_or_duplicate"}
    api(
        config,
        "POST",
        "/api/services/switch/turn_on",
        {"entity_id": "switch.bc250_power"},
    )
    return {"action": "power_on_requested", "boot_verified": False}


def main():
    """Default is dry-run. Explicit flag affects only the documented power-on target."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="explicitly power ON only; no off/reset operations",
    )
    parser.add_argument(
        "--on-ps",
        action="store_true",
        help="one fresh nonretained MQTT PS observation, no background installation",
    )
    parser.add_argument(
        "--watch-ps",
        action="store_true",
        help="explicit foreground PS watcher; no service install or power-off",
    )
    args = parser.parse_args()
    try:
        config = private_config(args.config)
        if args.on_ps or args.watch_ps:
            from waveshare_mqtt_status import status

            if args.execute and (
                not config.get("mqtt_user")
                or not config.get("mqtt_password")
                or config.get("mqtt_owner_topic_acl_verified") is not True
            ):
                raise ValueError(
                    "Authenticated owned-topic MQTT ACL confirmation required for PS actuation"
                )
            while True:
                try:
                    observed = status(
                        config.get("broker", "127.0.0.1"),
                        config.get("mqtt_port", 1883),
                        config.get("mqtt_user", ""),
                        config.get("mqtt_password", ""),
                    )
                except (OSError, TimeoutError):
                    if not args.watch_ps:
                        raise
                    time.sleep(0.25)
                    continue
                if not fresh_ps_event(observed):
                    result = {"action": "none", "reason": "no_fresh_ps_event"}
                else:
                    result = power_on(config, args.execute, event=observed)
                if not args.watch_ps:
                    break
                if result["action"] not in ("none", "blocked"):
                    print(json.dumps(result))
                time.sleep(0.25)
        else:
            result = power_on(config, args.execute)
    except Exception as error:
        print(
            json.dumps(
                {
                    "action": "blocked",
                    "error_type": type(error).__name__,
                    "credentials_suppressed": True,
                }
            )
        )
        return 1
    print(json.dumps(result))
    return 0 if result["action"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
