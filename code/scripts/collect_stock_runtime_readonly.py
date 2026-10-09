#!/usr/bin/env python3
"""Collect BC-250 stock runtime telemetry using an explicit read-only allowlist.

This collector intentionally does not import bc250_smu, open PCI config, access
/dev/mem, write sysfs, or issue SMU/mailbox messages. It is for a stock boot
only, after any SPI programmer/clip has been removed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ALLOWLIST = (
    "firmware_info", "ip_discovery", "ip_blocks", "gpu_metrics",
    "pp_dpm_sclk", "pp_dpm_mclk", "pp_dpm_fclk", "pp_dpm_socclk",
    "pp_dpm_vclk", "pp_dpm_dclk", "pp_features", "pp_power_profile_mode",
    "current_link_speed", "current_link_width", "mem_info_vram_total",
    "mem_info_vram_used", "mem_info_gtt_total",
)
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_COMMAND_BYTES = 2 * 1024 * 1024

# Keep identifiers and access-bearing values out of derived telemetry logs.
REDACTIONS = (
    (re.compile(r"(?i)(root=UUID=)[0-9a-f-]+"), r"\1<redacted>"),
    (re.compile(r"(?i)(serial(?:number)?[=:])[^\s]+"), r"\1<redacted>"),
    (re.compile(r"(?i)(id_serial(?:_short)?[=:])[^\s]+"), r"\1<redacted>"),
    (re.compile(r"(?i)(password|passwd|token|secret|private[_ -]?key)[=:][^\s]+"), r"\1=<redacted>"),
)


def sanitize(text: str) -> str:
    for pattern, replacement in REDACTIONS:
        text = pattern.sub(replacement, text)
    return text


def run_read_command(argv: list[str], timeout: float = 20.0) -> dict[str, Any]:
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
        output = (proc.stdout or "") + (proc.stderr or "")
        output = sanitize(output)[:MAX_COMMAND_BYTES]
        return {"argv": argv, "returncode": proc.returncode, "output": output}
    except FileNotFoundError:
        return {"argv": argv, "returncode": None, "output": "command-not-found"}
    except subprocess.TimeoutExpired as exc:
        output = sanitize((exc.stdout or "") + (exc.stderr or ""))[:MAX_COMMAND_BYTES]
        return {"argv": argv, "returncode": None, "output": output, "timeout": True}


def save_text(out_dir: Path, name: str, text: str) -> dict[str, Any]:
    path = out_dir / f"{name}.txt"
    data = sanitize(text).encode("utf-8", "replace")
    path.write_bytes(data)
    return {"path": str(path), "size": len(data), "sha256": hashlib.sha256(data).hexdigest(), "kind": "sanitized-text"}


def save_bytes(out_dir: Path, name: str, data: bytes) -> dict[str, Any]:
    path = out_dir / f"{name}.bin"
    path.write_bytes(data)
    return {"path": str(path), "size": len(data), "sha256": hashlib.sha256(data).hexdigest(), "kind": "raw-sysfs-bytes"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--sysfs-drm", type=Path, default=Path("/sys/class/drm"))
    parser.add_argument("--proc-cmdline", type=Path, default=Path("/proc/cmdline"))
    parser.add_argument("--skip-journal", action="store_true")
    args = parser.parse_args()

    out_dir = args.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[dict[str, Any]] = []
    commands: list[dict[str, Any]] = []

    for argv in (["uname", "-a"], ["lspci", "-nnk"], ["modinfo", "amdgpu"], ["modinfo", "amd_psp"]):
        result = run_read_command(list(argv))
        commands.append({"argv": result["argv"], "returncode": result["returncode"], "timeout": result.get("timeout", False)})
        outputs.append({"source": "command:" + argv[0], **save_text(out_dir, "command_" + argv[0] + ("_" + argv[1] if len(argv) > 1 else ""), result["output"])})

    if args.proc_cmdline.is_file():
        outputs.append({"source": str(args.proc_cmdline), **save_text(out_dir, "proc_cmdline", args.proc_cmdline.read_text(errors="replace"))})
    else:
        outputs.append({"source": str(args.proc_cmdline), "status": "missing"})

    if not args.skip_journal:
        result = run_read_command(["journalctl", "-k", "-b", "--no-pager"], timeout=30.0)
        commands.append({"argv": result["argv"], "returncode": result["returncode"], "timeout": result.get("timeout", False)})
        outputs.append({"source": "command:journalctl", **save_text(out_dir, "kernel_journal", result["output"])})

    cards = []
    for card in sorted(args.sysfs_drm.glob("card[0-9]")):
        vendor_path = card / "device" / "vendor"
        try:
            vendor = vendor_path.read_text(errors="replace").strip()
        except OSError:
            continue
        if vendor != "0x1002":
            continue
        card_entry: dict[str, Any] = {"card": str(card), "vendor": vendor, "files": []}
        for name in ALLOWLIST:
            source = card / "device" / name
            if not source.is_file():
                continue
            try:
                data = source.read_bytes()[:MAX_FILE_BYTES]
            except OSError as exc:
                card_entry["files"].append({"source": str(source), "status": "read-error", "error": type(exc).__name__})
                continue
            # Binary-ish discovery/metrics data is preserved with a hash; textual values are sanitized.
            if b"\x00" in data or name in {"gpu_metrics", "ip_discovery", "ip_blocks"}:
                saved = save_bytes(out_dir, "sysfs_" + card.name + "_" + name, data)
            else:
                saved = save_text(out_dir, "sysfs_" + card.name + "_" + name, data.decode("utf-8", "replace"))
            card_entry["files"].append({"source": str(source), **saved})
            outputs.append({"source": str(source), **saved})
        cards.append(card_entry)

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "host": {"uid": os.getuid(), "hostname": sanitize(os.uname().nodename)},
        "scope": "stock BC-250 runtime telemetry; explicit read-only kernel/sysfs/journal/lspci/modinfo collection",
        "sysfs_drm_root": str(args.sysfs_drm),
        "cards": cards,
        "commands": commands,
        "outputs": outputs,
        "hardware_mutation": False,
        "forbidden_paths": ["bc250_smu", "/dev/mem", "/sys/bus/pci/devices/*/config write", "pp_od_clk_voltage", "SMU mailbox setters"],
        "limitations": [
            "Run only after programmer/clip removal and stock power restoration.",
            "A successful collection proves only that host telemetry was read; it does not prove candidate behavior.",
            "Some sysfs files may be absent or unavailable depending on the kernel/driver.",
        ],
    }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"manifest": str(manifest_path), "cards": len(cards), "outputs": len(outputs), "hardware_mutation": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
