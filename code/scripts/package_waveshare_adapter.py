#!/usr/bin/env python3
"""Package only explicit public/staged project artifacts; excludes private profiles and dumps."""

import argparse
import hashlib
import json
import os
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/waveshare-implementation-20260930"


def package(output):
    """Write new verified bundle with manifest and exact file hashes, never a ready-hardware claim."""
    guide = REPORT / "guide"
    manifest = json.loads((guide / "candidate-manifest.json").read_text())
    image = guide / manifest["descriptive_alias"]
    if hashlib.sha256(image.read_bytes()).hexdigest() != manifest["sha256"]:
        raise ValueError("Candidate bytes do not match manifest")
    files = {}
    for name in ["CONNECT.html", "candidate-manifest.json", "hardware-facts.json"]:
        files[name] = guide / name
    files[image.name] = image
    files[image.name + ".txt"] = guide / (image.name + ".txt")
    for name in ["SETUP.md", "READINESS.md", "readiness-matrix.json"]:
        files[name] = REPORT / name
    helpers = [
        "waveshare_probe.py",
        "waveshare_host_metrics.py",
        "waveshare_ha_power.py",
        "waveshare_mqtt_status.py",
        "waveshare_shutdown.py",
        "waveshare_provision_network.py",
        "waveshare_private_profiles.py",
        "waveshare_uart_capture.py",
        "waveshare_spi_capture.py",
        "waveshare_flash_plan.py",
        "waveshare_flash_frames.py",
        "waveshare_bios_audit.py",
        "check_waveshare_uf2.py",
        "firmware_audit.py",
    ]
    for name in helpers:
        files["scripts/" + name] = ROOT / "scripts" / name
    plugin = ROOT / "candidates/waveshare-adapter-safe-v001/tools/decky-plugin"
    for name in [
        "main.py",
        "plugin.json",
        "package.json",
        "package-lock.json",
        "rollup.config.js",
        "tsconfig.json",
        "README.md",
        "src/index.tsx",
        "dist/index.js",
        "licenses/decky-api-LGPL-2.1.txt",
        "licenses/decky-ui-LGPL-2.1.txt",
    ]:
        files["decky-plugin/" + name] = plugin / name
    hashes = {}
    for name, path in files.items():
        if not path.is_file() or path.is_symlink():
            raise ValueError("Package source missing or symlink")
        data = path.read_bytes()
        hashes[name] = {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
    record = {
        "schema": 1,
        "stage": "PRECONNECTION_DRAFT_NOT_FINAL_DO_NOT_FLASH",
        "goal_complete": False,
        "hardware_acceptance": False,
        "upload_authorized": False,
        "private_data_included": False,
        "source_fingerprint": manifest["source_fingerprint"],
        "files": hashes,
    }
    # Exclusive destination avoids destroying any earlier accepted bundle.
    with output.open("xb") as stream:
        with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, path in sorted(files.items()):
                archive.writestr(name, path.read_bytes())
            archive.writestr(
                "PACKAGE-MANIFEST.json",
                json.dumps(record, indent=2, ensure_ascii=False) + "\n",
            )
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise ValueError("Archive CRC failure")
        observed = json.loads(archive.read("PACKAGE-MANIFEST.json"))
        if observed != record:
            raise ValueError("Manifest mismatch")
        if set(archive.namelist()) != set(files) | {"PACKAGE-MANIFEST.json"}:
            raise ValueError("Unexpected package entry")
        for name, entry in hashes.items():
            if hashlib.sha256(archive.read(name)).hexdigest() != entry["sha256"]:
                raise ValueError("Package byte hash mismatch")
    return {
        "path": str(output.resolve()),
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "entries": len(files) + 1,
        "hardware_acceptance": False,
        "upload_authorized": False,
    }


def main():
    """Build explicit package only; no installation/provisioning/board interaction."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(package(args.output), indent=2))
    except (OSError, ValueError) as error:
        print(json.dumps({"packaged": False, "error_type": type(error).__name__}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
