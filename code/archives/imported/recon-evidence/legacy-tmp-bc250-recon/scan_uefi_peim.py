#!/usr/bin/env python3
"""Disassemble and scan UEFI PEI TE images using pypcode x86:LE:32 / 64."""
from __future__ import annotations

import re
import struct
import sys
from pathlib import Path

import pypcode


def parse_te(data: bytes) -> tuple[int, int, bytes]:
    """Parse UEFI EFI_TE_IMAGE_HEADER (VZ header)."""
    if len(data) < 0x28 or data[:2] != b"VZ":
        return 0, 0, data
    # struct EFI_TE_IMAGE_HEADER {
    #   UINT16 Signature; // 'VZ' = 0x5A56
    #   UINT16 Machine;   // 0x014c (i386) or 0x8664 (x64)
    #   UINT8  NumberOfSections;
    #   UINT8  Subsystem;
    #   UINT16 StrippedSize;
    #   UINT32 AddressOfEntryPoint;
    #   UINT32 BaseOfCode;
    #   UINT64 ImageBase;
    # };
    machine = struct.unpack_from("<H", data, 2)[0]
    stripped = struct.unpack_from("<H", data, 6)[0]
    entry = struct.unpack_from("<I", data, 8)[0]
    image_base = struct.unpack_from("<Q", data, 16)[0] if len(data) >= 24 else 0
    # adjust for stripped offset: entry in file = entry - stripped + 0x28 (if adjusted)
    arch = "x86:LE:64:default" if machine == 0x8664 else "x86:LE:32:default"
    print(f"TE machine=0x{machine:04x} ({arch}) stripped=0x{stripped:04x} entry=0x{entry:08x} base=0x{image_base:08x}")
    return machine, stripped, data


def main() -> None:
    path = Path(sys.argv[1])
    data = path.read_bytes()
    machine, stripped, raw = parse_te(data)
    arch = "x86:LE:64:default" if machine == 0x8664 else "x86:LE:32:default"
    context = pypcode.Context(arch)

    # Search for SMN / MMIO addresses:
    # 0x02403000 (VCN), 0x02400000, 0x13FE (BC-250 DID), 0x03B1 (SMU), 0x1002 (AMD VID)
    patterns = {
        "VCN_FABRIC": bytes.fromhex("00 30 40 02"),
        "GC_FABRIC": bytes.fromhex("00 2c 40 02"),
        "FABRIC_BASE": bytes.fromhex("00 00 40 02"),
        "DID_13FE": bytes.fromhex("fe 13"),
        "NBIF_SMN": bytes.fromhex("00 00 01 01"),
        "NBIO_GASKET": bytes.fromhex("14 30 40 02"),
    }
    print(f"\nScanning {path.name} ({len(data)} bytes)...")
    for name, pat in patterns.items():
        hits = [hex(i) for i in range(len(data) - len(pat) + 1) if data.startswith(pat, i)]
        if hits:
            print(f"  {name}: {hits}")

    # Extract printable ASCII strings
    strings = []
    for m in re.finditer(rb"[A-Za-z0-9_\-\.]{4,}", data):
        strings.append((hex(m.start()), m.group().decode("ascii", "replace")))
    print(f"\nStrings found ({len(strings)}):")
    for off, s in strings[:40]:
        print(f"  {off}: {s}")


if __name__ == "__main__":
    main()
