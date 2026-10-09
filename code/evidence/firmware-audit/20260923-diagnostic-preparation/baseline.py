#!/usr/bin/env python3
"""Read-only BC-250 clock/voltage probe. Prints one JSON object on stdout.

Designed to be piped to the board over SSH:

    ssh root@<board> 'python3 -' < scripts/probe_bc250_clocks_readonly.py

Hard constraints (enforced here, not by convention):
  * no import of bc250_smu, no /dev/mem, no PCI config access, no SMU mailbox;
  * no writes of any kind - every access is a read of a kernel-provided file;
  * degrades gracefully on a host without an AMD GPU (returns empty cards).

Evidence class of the result: `hardware-verified` for the kernel-reported
clocks, `observed-bytes` for the raw gpu_metrics blob. It never proves that a
BIOS field was applied; it reports what the running kernel believes.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import sys
from pathlib import Path

DRM_ROOT = Path("/sys/class/drm")
# Only the BC-250 APU (Cyan Skillfish) is in scope. Matching on vendor 0x1002
# alone silently reports whichever AMD GPU the host happens to own, which is a
# wrong-evidence hazard when the script is run locally instead of piped over SSH.
TARGET_PCI_ID = os.environ.get("BC250_PCI_ID", "0x13fe")
TEXT_FILES = (
    "pp_dpm_sclk",
    "pp_dpm_mclk",
    "pp_dpm_fclk",
    "pp_dpm_socclk",
    "pp_dpm_vclk",
    "pp_dpm_dclk",
    "pp_dpm_pcie",
    "pp_features",
    "pp_power_profile_mode",
    "current_link_speed",
    "current_link_width",
    "mem_info_vram_total",
    "mem_info_vram_used",
    "mem_info_gtt_total",
    "gpu_busy_percent",
    "power_dpm_force_performance_level",
)
# Telemetry note (source-specific historical finding from amdgpu/cyan_skillfish_ppt.c):
# In that driver source, pp_dpm_fclk and pp_dpm_mclk both read MemclkFrequency and alias
# each other. This alias is specific to that driver code; it cannot be universally asserted
# about the current running kernel or independent hardware sources unless actually checked.
# Direct queries or counters remain unverified.
BINARY_FILES = ("gpu_metrics", "ip_discovery", "ip_blocks")
MAX_BYTES = 1 << 20

REDACTIONS = (
    (re.compile(r"(?i)(root=UUID=)[0-9a-f-]+"), r"\1<redacted>"),
    (re.compile(r"(?i)(serial(?:number)?[=:])[^\s]+"), r"\1<redacted>"),
)


def sanitize(text: str) -> str:
    for pattern, repl in REDACTIONS:
        text = pattern.sub(repl, text)
    return text


def read_text(path: Path) -> str | None:
    try:
        return sanitize(path.read_bytes()[:MAX_BYTES].decode("utf-8", "replace"))
    except OSError:
        return None


def read_binary(path: Path) -> dict | None:
    try:
        data = path.read_bytes()[:MAX_BYTES]
    except OSError:
        return None
    return {
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "hex": data.hex(),
    }


def main() -> int:
    result: dict = {
        "host": sanitize(platform.node()),
        "uname": sanitize(platform.platform()),
        "kernel": sanitize(platform.release()),
        "cmdline": read_text(Path("/proc/cmdline")),
        "bios_version": read_text(Path("/sys/class/dmi/id/bios_version")),
        "bios_date": read_text(Path("/sys/class/dmi/id/bios_date")),
        "cards": [],
        "forbidden": [
            "bc250_smu",
            "/dev/mem",
            "pci config",
            "SMU mailbox",
            "any write",
        ],
        "hardware_mutation": False,
    }
    for card in sorted(DRM_ROOT.glob("card[0-9]")):
        dev = card / "device"
        try:
            if (dev / "vendor").read_text().strip() != "0x1002":
                continue
            device_id = (dev / "device").read_text().strip()
        except OSError:
            continue
        if device_id != TARGET_PCI_ID:
            result.setdefault("skipped_cards", []).append(
                {
                    "card": card.name,
                    "device": device_id,
                    "reason": f"not the BC-250 APU ({TARGET_PCI_ID})",
                }
            )
            continue
        entry: dict = {
            "card": card.name,
            "files": {},
            "independent_sources_checked": "unknown",
        }
        for name in TEXT_FILES:
            value = read_text(dev / name)
            if value is not None:
                entry["files"][name] = value
        for name in BINARY_FILES:
            blob = read_binary(dev / name)
            if blob is not None:
                entry["files"][name] = blob
        entry["slot"] = read_text(dev / "uevent")
        entry["pci_id"] = read_text(dev / "device")
        result["cards"].append(entry)
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
