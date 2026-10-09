#!/usr/bin/env python3
"""BC250 diagnostic preparation: default is a no-inspection plan.

Explicit metadata/telemetry modes read allowlisted kernel files only. Telemetry
reads can invoke driver callbacks; no claim of zero hardware side effects.
No PCI config, SMN, mailbox, /dev/mem, settings writes, or subprocesses.
Results are kernel reports, never independent proof of physical clocks or SoC.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import sys
from pathlib import Path

DRM_ROOT = Path("/sys/class/drm")
# Only the BC-250 APU (Cyan Skillfish) is in scope. Matching on vendor 0x1002
# alone silently reports whichever AMD GPU the host happens to own, which is a
# wrong-evidence hazard when the script is run locally instead of piped over SSH.
TARGET_PCI_ID = "0x13fe"
SYSFS_ROOT = Path("/sys")
TEXT_FILES = ("pp_dpm_mclk", "pp_dpm_fclk", "pp_dpm_socclk", "pp_dpm_sclk")
# Telemetry note (source-specific historical finding from amdgpu/cyan_skillfish_ppt.c):
# In that driver source, pp_dpm_fclk and pp_dpm_mclk both read MemclkFrequency and alias
# each other. This alias is specific to that driver code; it cannot be universally asserted
# about the current running kernel or independent hardware sources unless actually checked.
# Direct queries or counters remain unverified.
BINARY_FILES = ("gpu_metrics",)
MAX_BYTES = 1 << 20

REDACTIONS = (
    (re.compile(r"(?i)(root=UUID=)[0-9a-f-]+"), r"\1<redacted>"),
    (re.compile(r"(?i)(serial(?:number)?[=:])[^\s]+"), r"\1<redacted>"),
)


def sanitize(text: str) -> str:
    for pattern, repl in REDACTIONS:
        text = pattern.sub(repl, text)
    return text


def bounded_read(path: Path) -> bytes:
    # Keep fixture symlinks or unexpected sysfs links inside the chosen root.
    if not path.resolve().is_relative_to(SYSFS_ROOT.resolve()):
        raise OSError("source escapes sysfs root")
    with path.open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise OSError("source exceeds read limit")
    return data


def read_text(path: Path) -> str | None:
    try:
        return sanitize(bounded_read(path).decode("utf-8", "replace"))
    except OSError:
        return None


def read_binary(path: Path) -> dict | None:
    try:
        data = bounded_read(path)
    except OSError:
        return None
    return {
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "hex": data.hex(),
    }


def main(argv=None) -> int:
    global SYSFS_ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode", choices=("plan", "metadata", "telemetry"), default="plan"
    )
    parser.add_argument(
        "--sysfs-root",
        type=Path,
        default=Path("/sys"),
        help="fixture root or /sys on separately authorized board",
    )
    args = parser.parse_args(argv)
    result = {
        "mode": args.mode,
        "expected_pci_id": "1002:13fe",
        "status": "PLAN_ONLY",
        "cards": [],
        "forbidden": [
            "PCI config",
            "SMN",
            "SMU mailbox",
            "/dev/mem",
            "settings writes",
            "hostname",
            "cmdline",
        ],
        "independent_clock_proof": False,
        "soc_voltage_verified": False,
    }
    if args.mode == "plan":
        result["planned_telemetry"] = list(TEXT_FILES + BINARY_FILES)
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    SYSFS_ROOT = args.sysfs_root.resolve()
    drm = SYSFS_ROOT / "class/drm"
    for card in sorted(drm.glob("card*")):
        if re.fullmatch(r"card[0-9]+", card.name) is None:
            continue
        dev = card / "device"
        vendor = read_text(dev / "vendor")
        device = read_text(dev / "device")
        if vendor is None or device is None:
            continue
        if (vendor.strip(), device.strip()) != ("0x1002", TARGET_PCI_ID):
            continue
        entry = {
            "card": card.name,
            "pci_id": "1002:13fe",
            "files": {},
            "unavailable": [],
        }
        result["cards"].append(entry)
    if len(result["cards"]) > 1:
        result["status"] = "AMBIGUOUS_TARGET"
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 5
    if result["cards"]:
        entry = result["cards"][0]
        dev = drm / entry["card"] / "device"
        if args.mode == "telemetry":
            for name in TEXT_FILES:
                value = read_text(dev / name)
                if value is None:
                    entry["unavailable"].append(name)
                else:
                    entry["files"][name] = value
            for name in BINARY_FILES:
                value = read_binary(dev / name)
                if value is None:
                    entry["unavailable"].append(name)
                else:
                    entry["files"][name] = value
    code = 0
    if not result["cards"]:
        result["status"] = "NO_TARGET"
        code = 3
    else:
        result["kernel"] = platform.release()
        result["bios_version"] = read_text(SYSFS_ROOT / "class/dmi/id/bios_version")
        result["bios_date"] = read_text(SYSFS_ROOT / "class/dmi/id/bios_date")
        result["status"] = (
            "METADATA_ONLY" if args.mode == "metadata" else "KERNEL_TELEMETRY_ONLY"
        )
        if args.mode == "telemetry" and any(c["unavailable"] for c in result["cards"]):
            result["status"] = "PARTIAL_TELEMETRY"
            code = 4
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
