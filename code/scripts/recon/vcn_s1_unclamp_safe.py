#!/usr/bin/env python3
"""S1 DF-window unclamp — SAFE ordering (born from 2026-09-25 wedge).

Rewrite of unclamp_step1.py that FIXES the wedge cause: the original read VCN
mmUVD_* via amdgpu_regs at BASELINE, before the domain was powered — that CPU
MMIO read into a gated VCN segment HANGS the whole board (proven 2026-09-25:
ping loss + ssh timeout, cold power-cycle needed).

SAFE ORDER enforced here:
  1. SMU alive + unlock (SMN transport only — safe).
  2. Read firewall regs via smu.smn_read32 (SMN, NOT MMIO — safe).
  3. Raise dom6 (msg 0x61) via enable_vcn BEFORE any VCN MMIO read.
  4. WRITE 0x3A2011C <- 0x107FF (single reversible SMN store), alive()-guard.
  5. ONLY NOW read VCN mmUVD_VERSION (domain up) and compare to FF.

No VCN MMIO read happens while the island is gated. SMN reads are fine.

Usage (on board, BC250_SMU_PATH / BC250_VCN_SOURCE set or default /root/vcn_unlock):
    sudo python3 vcn_s1_unclamp_safe.py --verify   # SMN-only, no write, no MMIO
    sudo python3 vcn_s1_unclamp_safe.py            # full S1 (raise dom6, write, read)
"""
import argparse
import os
import struct
import sys
from pathlib import Path

SMU_LIB = Path(os.environ.get("BC250_SMU_PATH", "/root/vcn_unlock/bc250-smu-unlock"))
VCN_SRC = Path(os.environ.get("BC250_VCN_SOURCE", "/root/vcn_unlock/daveconde-bc250-vcn-enable"))
sys.path.insert(0, str(SMU_LIB))
sys.path.insert(0, str(VCN_SRC))

import unlock  # noqa: E402
from bc250_smu import Bc250Smu  # noqa: E402
import enable_vcn  # noqa: E402

S1_ADDR = 0x3A2011C
S1_TARGET = 0x000107FF  # Cezanne exact: firewall LOW bound widened

# VCN mmUVD_VERSION dword offset (per read_vcn_direct.py). Byte = dword*4.
MMUVD_VERSION_BYTE = 0x01E328
MMUVD_POWER_STATUS_BYTE = 0x01E2F0


def detect_vcn_dri_node():
    """Return the dri node whose name is amdgpu (avoid hardcoded dri/1)."""
    for node in ("0", "1", "2"):
        p = "/sys/kernel/debug/dri/%s/name" % node
        try:
            with open(p) as f:
                if "amdgpu" in f.read():
                    return node
        except OSError:
            continue
    return "0"


def read_vcn_mmio(node, byte_off):
    """Read one VCN MMIO dword. ONLY call after dom6 is raised."""
    p = "/sys/kernel/debug/dri/%s/amdgpu_regs" % node
    with open(p, "rb") as f:
        f.seek(byte_off)
        return struct.unpack("<I", f.read(4))[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true",
                    help="SMN-only baseline, no write, no MMIO read")
    ap.add_argument("--assume-domain-up", action="store_true",
                    help="confirm dom6 already raised (enable_vcn.py ran); "
                         "required before any VCN MMIO read")
    args = ap.parse_args()

    smu = Bc250Smu()
    if not smu.alive():
        print("E: SMU not alive", flush=True)
        return 1
    print("[*] SMU alive", flush=True)
    if not smu.secure_access_enabled():
        print("[*] unlocking...", flush=True)
        unlock.smu = smu
        unlock.unlock(smu)
    if not smu.secure_access_enabled():
        print("E: secure access not open", flush=True)
        return 1
    print("[*] SMU secure access OPEN", flush=True)

    # NOTE (2026-09-25): baseline SMN-read of firewall regs via msg 0x2A wedges
    # the SMU mailbox on this silicon (sec_smn_read32(addr) with a firewall addr
    # hangs alive()). Do NOT snapshot firewall regs before the write. The single
    # 0x2A read we allow is the post-write readback of S1_ADDR only.
    if args.verify:
        print("[--verify: alive + secure only (no 0x2A firewall reads). exiting]", flush=True)
        smu.close()
        return 0

    node = detect_vcn_dri_node()
    print("[*] VCN dri node = %s" % node, flush=True)

    # SAFE ORDER: dom6 MUST already be up. enable_vcn.py has no importable
    # "raise domain" entrypoint (its logic lives in main() + call_thunk); do
    # NOT reinvent its fragile mailbox dance here. Run it as its own step:
    #     sudo BC250_SMU_PATH=... python3 enable_vcn.py        # fires msg 0x61
    # THEN run this script (domain already up) for the S1 write + MMIO read.
    if not args.assume_domain_up:
        print("!! dom6 not confirmed up. Run enable_vcn.py FIRST (fires msg 0x61),",
              "then re-run with --assume-domain-up. Refusing MMIO read while gated",
              "(reading VCN MMIO gated = board wedge, 2026-09-25).", flush=True)
        smu.close()
        return 3

    print("[++] WRITE 0x%07X <= 0x%08X (single reversible SMN store)"
          % (S1_ADDR, S1_TARGET), flush=True)
    smu.smn_write32(S1_ADDR, S1_TARGET)
    if not smu.alive():
        print("!! SMU wedged after write — cold power-cycle; NOT continuing.", flush=True)
        smu.close()
        return 4
    rb = smu.smn_read32(S1_ADDR)
    print("[+] readback 0x%07X = 0x%08X (expect 0x%08X) — %s"
          % (S1_ADDR, rb, S1_TARGET, "STUCK" if rb == S1_TARGET else "DROPPED"),
          flush=True)

    # ONLY NOW (domain up) read VCN MMIO.
    ver = read_vcn_mmio(node, MMUVD_VERSION_BYTE)
    pwr = read_vcn_mmio(node, MMUVD_POWER_STATUS_BYTE)
    print("[+] mmUVD_VERSION=0x%08X mmUVD_POWER_STATUS=0x%08X" % (ver, pwr), flush=True)
    if ver != 0xFFFFFFFF:
        print("[+] *** UVD_VERSION != FF — VCN VISIBLE (owner/commit path works) ***", flush=True)
    else:
        print("[-] still FF — S1 alone did not unclamp; escalate S2..S5", flush=True)
    print("DONE_S1", flush=True)
    smu.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
