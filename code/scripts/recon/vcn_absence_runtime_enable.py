#!/usr/bin/env python3
"""Runtime VCN enable for BC250 with gasket-absent firmware.

Requires: BC250_P3.00_NO_GASKET_v001.bin flashed (no SEC_GASKET, no TOS_POLICY).
Without gasket, DF window and bank-12 registers are in default (unlocked) state.
This script writes the donor values that the gasket would have written on a
working platform, then powers up VCN.

Transport: PCI config B8/BC window (Bc250PciTransport.write_smu_reg).
Proven safe for DF/IOHC/bank-12 addresses. Does NOT use mailbox msgs 0x2A/0x2B
(those wedge on VCN-related addresses when gasket is applied).

Safety: all writes are volatile (lost on cold power cycle). No flash touched.
Rollback: cold power cycle restores PSP-applied defaults.
"""
from __future__ import annotations

import argparse
import os
import struct
import sys
import time

# ---------------------------------------------------------------------------
# Transport: direct PCI config B8/BC SMN window (proven on this board)
# ---------------------------------------------------------------------------

_FD = None

def _open_config():
    global _FD
    if _FD is None:
        path = "/sys/bus/pci/devices/0000:00:00.0/config"
        _FD = os.open(path, os.O_RDWR | os.O_CLOEXEC)

def smn_read(addr: int) -> int:
    _open_config()
    os.pwrite(_FD, struct.pack("<I", addr), 0xB8)
    return struct.unpack("<I", os.pread(_FD, 4, 0xBC))[0]

def smn_write(addr: int, value: int) -> None:
    _open_config()
    os.pwrite(_FD, struct.pack("<I", addr), 0xB8)
    os.pwrite(_FD, struct.pack("<I", value), 0xBC)

# ---------------------------------------------------------------------------
# SMU alive check (Q3 msg 0x01 via the same B8/BC window)
# ---------------------------------------------------------------------------

Q3_CMD = 0x03B10A20
Q3_RSP = 0x03B10A80
Q3_ARG = 0x03B10A88

def smu_alive() -> bool:
    try:
        smn_write(Q3_RSP, 0)
        smn_write(Q3_ARG, 0x42)
        smn_write(Q3_CMD, 0x01)  # MSG_ALIVE
        for _ in range(500):
            rsp = smn_read(Q3_RSP)
            if rsp == 0x01:
                arg = smn_read(Q3_ARG)
                return arg == 0x43  # alive returns arg+1
            time.sleep(0.002)
        return False
    except Exception:
        return False

# ---------------------------------------------------------------------------
# Write sequence
# ---------------------------------------------------------------------------

# Donor gasket values (Cezanne, from gasket-script-decode.md).
# ORDER MATTERS: DF windows first → VCN_SEG → bank-12 → IOHC/mirrors.
GASKET_WRITES = [
    # 1. Open DF windows (bit 12 enables bank-12 visibility)
    (0x03A2011C, 0x000107FF, "DF window LOW (bit12=bank-12)"),
    (0x03A20124, 0x00010FFF, "DF window 2"),
    (0x03A20128, 0xFFFF0000, "DF window 3 (donor)"),
    # 2. VCN_SEG enable
    (0x03E810,   0x00000006, "VCN_SEG enable"),
    # 3. VCN cold-reset release (what t28 does on working cards via svc 0x7C)
    (0x0900C004, 0x00000001, "VCN cold-reset release"),
    # 4. Bank-12 firewall aperture (donor Cezanne group 0x201 subset)
    (0x0900C910, 0x00497FFF, "bank-12 mask 0"),
    (0x0900C914, 0x00007FFF, "bank-12 mask 1"),
    (0x0900C930, 0x00497FFF, "bank-12 mask 2"),
    (0x0900C830, 0x00FFFFFB, "bank-12 window 0"),
    (0x0900C834, 0x00000004, "bank-12 window 1"),
    (0x0900C838, 0x00000000, "bank-12 window 2"),
    (0x0900C234, 0x00000001, "bank-12 COMMIT"),
    # 5. DF mirror bank
    (0x03D2011C, 0x000107FF, "DF mirror LOW"),
    (0x03D20124, 0x00010FFF, "DF mirror 2"),
    # 6. IOHC windows (from stage5_full_dataplane 2026-09-12)
    (0x0322011C, 0x000107FF, "IOHC window LOW"),
    (0x03220124, 0x00010FFF, "IOHC window 2"),
    (0x0322012C, 0x000107FF, "IOHC window 3"),
]


def do_write(addr: int, value: int, label: str) -> bool:
    try:
        smn_write(addr, value)
        rb = smn_read(addr)
        ok = rb == value
        tag = "OK" if ok else f"MISMATCH(rb={rb:#010x})"
        print(f"  [{tag}] {label}: {addr:#010x} <- {value:#010x}", flush=True)
        return ok
    except Exception as e:
        print(f"  [FAIL] {label}: {addr:#010x} <- {value:#010x}: {e}", flush=True)
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true",
                    help="Print the write sequence without executing")
    ap.add_argument("--read-only", action="store_true",
                    help="Only read current register values, no writes")
    args = ap.parse_args()

    if args.dry_run:
        print("=== DRY RUN ===")
        for addr, val, label in GASKET_WRITES:
            print(f"  {addr:#010x} <- {val:#010x}  # {label}")
        return 0

    print("=== BC250 VCN RUNTIME ENABLE (gasket-absent firmware) ===", flush=True)
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    # Pre-check: SMU alive
    alive = smu_alive()
    print(f"SMU alive: {alive}", flush=True)
    if not alive:
        print("ABORT: SMU not responding. Cold power cycle needed.", flush=True)
        return 1

    # Baseline reads — the KEY diagnostic
    print("\n[BASELINE] Current register values:", flush=True)
    diag_addrs = [
        (0x03A2011C, "DF window LOW"),
        (0x03A20124, "DF window 2"),
        (0x03E810,   "VCN_SEG"),
        (0x0900C234, "bank-12 commit"),
    ]
    for addr, label in diag_addrs:
        val = smn_read(addr)
        extra = ""
        if addr == 0x03A2011C:
            bit12 = (val >> 12) & 1
            extra = f" bit12={'OPEN' if bit12 else 'CLOSED'}"
        print(f"  {label}: {addr:#010x} = {val:#010x}{extra}", flush=True)

    if not smu_alive():
        print("ABORT: SMU wedged on baseline reads. Cold cycle needed.", flush=True)
        return 1

    if args.read_only:
        print("\n(read-only mode, no writes)", flush=True)
        return 0

    # Write sequence
    print("\n[WRITES] Applying donor gasket values...", flush=True)
    failed = 0
    for addr, val, label in GASKET_WRITES:
        if not do_write(addr, val, label):
            failed += 1
        if not smu_alive():
            print(f"ABORT: SMU wedged after {label}. Cold cycle needed.", flush=True)
            return 1

    # Post-write diagnostic
    print(f"\n[RESULT] {len(GASKET_WRITES) - failed}/{len(GASKET_WRITES)} writes OK", flush=True)

    # Read VCN MMIO via B8/BC (mmUVD_VERSION at SMN 0x1F832A8)
    # VCN0 SMN base from IP discovery = 0x7800 dwords = byte 0x1E000
    # UVD_VERSION offset = 0x78CA dwords = byte 0x1E328
    # Full SMN addr = VCN0_base + offset. VCN0_base from discovery = varies.
    # Safe approach: read via enable_vcn.py after power-up.
    print("\n[NEXT] Run on the board:", flush=True)
    print("  cd ~/vcn_unlock", flush=True)
    print("  python3 daveconde-bc250-vcn-enable/enable_vcn.py --manual-powerup", flush=True)
    print("  python3 daveconde-bc250-vcn-enable/enable_vcn.py --verify", flush=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
