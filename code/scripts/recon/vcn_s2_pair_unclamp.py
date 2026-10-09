#!/usr/bin/env python3
"""S2 pair unclamp — Data-Fabric firewall LOW+HIGH bounds.

Session 3 established: S1 alone (0x3A2011C 0x87FF->0x107FF) landed but VCN
still 0xFFFFFFFF. Per docs/research/imported/unclamp_decode.md the LOW bound
without the HIGH bound leaves the secured window incomplete.

This runner:
  1. Verifies SMU alive (assumes domain already up via enable_vcn.py full run).
  2. WRITE-FIRST S1 0x3A2011C 0x87FF -> 0x107FF (Q3 0x98 smn_write32).
  3. WRITE-FIRST S2 0x3A20124 0x0    -> 0x10FFF (Q3 0x98 smn_write32).
  4. MMIO readback of mmUVD_VERSION (0x05C9) via VcnDirect (amdgpu_regs).

Rules from vcn-unclamp-live SKILL.md and MISTAKES.md:
  - NEVER read firewall SMN via q2 0x2A on 0x3A2011C or 0x3A20124 (wedges SMU).
  - Verification is x86 MMIO of UVD_VERSION, not SMU readback.
  - Reversible: power-cycle restores stock gasket.
"""
import argparse
import os
import struct
import sys
import time

# path to bc250-smu-unlock (on board layout)
sys.path.insert(0, "/root/vcn_unlock/bc250-smu-unlock")
sys.path.insert(0, "/root/vcn_unlock/daveconde-bc250-vcn-enable")

from bc250_smu import Bc250Smu  # type: ignore

# UVD reg addressing (BASE_IDX 1 -- from enable_vcn.py)
VCN_SEG1_DW = 0x07E00
UVD_VERSION_OFF = 0x05C9
UVD_POWER_STATUS_OFF = 0x0004


def _uvd_bytes(off):
    return (VCN_SEG1_DW + off) * 4


def find_regs():
    """amdgpu_regs debugfs path (dri/0 or dri/1)."""
    for n in (0, 1, 2, 3):
        p = f"/sys/kernel/debug/dri/{n}/amdgpu_regs"
        if os.path.exists(p):
            # prefer BC-250 card
            vend = f"/sys/kernel/debug/dri/{n}/name"
            try:
                nm = open(vend).read()
                if "1002:13FE" in nm.upper() or "cyan" in nm.lower() or "bc250" in nm.lower():
                    return p
            except Exception:
                pass
    for n in (0, 1, 2, 3):
        p = f"/sys/kernel/debug/dri/{n}/amdgpu_regs"
        if os.path.exists(p):
            return p
    raise SystemExit("amdgpu_regs not found under /sys/kernel/debug/dri")


def mmio_read(rf, byte_off):
    os.lseek(rf.fileno(), byte_off, os.SEEK_SET)
    return struct.unpack('<I', rf.read(4))[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="Print plan, do not write. SMN reads still skipped (0x2A wedge risk).")
    ap.add_argument("--s1-only", action="store_true",
                    help="Only apply S1 (0x3A2011C). For session 3 replay.")
    ap.add_argument("--skip-s1", action="store_true",
                    help="Skip S1 (already landed from prior run).")
    ap.add_argument("--s3", action="store_true",
                    help="Apply S3: NBIF routing-firewall pair 0x1C780/0x1C784.")
    ap.add_argument("--s4", action="store_true",
                    help="Apply S4: 0x3A20128 high window + 0x3E810/14 SEG binding.")
    args = ap.parse_args()

    s = Bc250Smu()
    if not s.alive():
        print("[!] SMU wedged — cold cycle required. Exit.")
        return 2
    print("[*] SMU alive")

    # NOTE: do NOT baseline-read 0x3A2011C / 0x3A20124 via smn_read32.
    # SMU internal path for those addresses wedges the mailbox (proven session 2/3).
    # We trust SEC_GASKET-derived current values and go WRITE-FIRST.

    if not args.skip_s1:
        print("[S1] WRITE 0x3A2011C  0x87FF -> 0x0000107F   (LOW bound, Q3 0x98)")
        if not args.dry_run:
            s.smn_write32(0x3A2011C, 0x0000107F)
            time.sleep(0.05)
            print("[S1] alive after write =", s.alive())

    if not args.s1_only:
        print("[S2] WRITE 0x3A20124  0x0000 -> 0x00010FFF   (HIGH bound, Q3 0x98)")
        if not args.dry_run:
            s.smn_write32(0x3A20124, 0x00010FFF)
            time.sleep(0.05)
            print("[S2] alive after write =", s.alive())

    if args.s3:
        # NBIF routing-firewall pair (Cezanne exact); primary values only,
        # no 2nd-write 0x0 tie-down until #2 proves needed.
        print("[S3a] WRITE 0x0001C780  -> 0x0002DF4D   (NBIF routing low, Q3 0x98)")
        if not args.dry_run:
            s.smn_write32(0x1C780, 0x0002DF4D)
            time.sleep(0.05)
            print("[S3a] alive =", s.alive())
        print("[S3b] WRITE 0x0001C784  -> 0xFF100000   (NBIF routing high, Q3 0x98)")
        if not args.dry_run:
            s.smn_write32(0x1C784, 0xFF100000)
            time.sleep(0.05)
            print("[S3b] alive =", s.alive())

    if args.s4:
        print("[S4a] WRITE 0x03A20128  -> 0xFFFF0000   (secondary fabric high, Q3 0x98)")
        if not args.dry_run:
            s.smn_write32(0x3A20128, 0xFFFF0000)
            time.sleep(0.05)
            print("[S4a] alive =", s.alive())
        print("[S4b] WRITE 0x0003E810  -> 0x00000006   (VCN_SEG binding, Q3 0x98)")
        if not args.dry_run:
            s.smn_write32(0x3E810, 0x00000006)
            time.sleep(0.05)
            print("[S4b] alive =", s.alive())
        print("[S4c] WRITE 0x0003E814  -> 0x2544C382   (VCN_SEG binding upper, Q3 0x98)")
        if not args.dry_run:
            s.smn_write32(0x3E814, 0x2544C382)
            time.sleep(0.05)
            print("[S4c] alive =", s.alive())

    # MMIO verification (x86-side, arbiter)
    print("[V] MMIO read mmUVD_VERSION and mmUVD_POWER_STATUS")
    regs_path = find_regs()
    print("[V] amdgpu_regs =", regs_path)
    with open(regs_path, 'r+b', buffering=0) as rf:
        v_ver = mmio_read(rf, _uvd_bytes(UVD_VERSION_OFF))
        v_pwr = mmio_read(rf, _uvd_bytes(UVD_POWER_STATUS_OFF))
    print(f"[V] mmUVD_VERSION      = 0x{v_ver:08X}  (0xFFFFFFFF = still clamped)")
    print(f"[V] mmUVD_POWER_STATUS = 0x{v_pwr:08X}  (0xFFFFFFFF = still clamped)")

    if v_ver != 0xFFFFFFFF or v_pwr != 0xFFFFFFFF:
        print("[+] BREAKTHROUGH — VCN register block visible.")
        return 0
    print("[-] Still 0xFFFFFFFF — need S3 (0x1C780/0x1C784 pair) next.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
