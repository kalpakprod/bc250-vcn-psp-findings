#!/usr/bin/env python3
"""Explicit graceful local BC250 shutdown only; never relay-off, reset, reboot or arbitrary commands."""

import argparse
import json
import subprocess

from waveshare_host_metrics import verified_bc250


def system_shutdown(command):
    """One fixed command. Authorization is handled by the local system; no sudo bypass."""
    if command != ["systemctl", "poweroff"]:
        raise ValueError("Command outside shutdown allowlist")
    result = subprocess.run(
        command, capture_output=True, text=True, check=False, timeout=5
    )
    return result.returncode


def shutdown(execute=False, identity=verified_bc250, executor=system_shutdown):
    """Default dry-run; board identity and explicit intent are both required."""
    if not identity():
        return {"action": "blocked", "reason": "local_DMI_not_BC250"}
    if not execute:
        return {
            "action": "dry_run",
            "would_request": "graceful_local_shutdown",
            "power_removed_verified": False,
        }
    code = executor(["systemctl", "poweroff"])
    return {
        "action": "shutdown_requested" if code == 0 else "failed",
        "exit_status": code,
        "power_removed_verified": False,
        "relay_off_requested": False,
    }


def main():
    """No action is performed without the caller's explicit --execute."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    try:
        result = shutdown(args.execute)
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(
            json.dumps(
                {
                    "action": "failed",
                    "error_type": type(error).__name__,
                    "relay_off_requested": False,
                }
            )
        )
        return 1
    print(json.dumps(result))
    return 0 if result["action"] not in ("blocked", "failed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
