#!/usr/bin/env python3
"""
vcn_s8_rpc_ungate.py — VCN clock ungate via SMU RPC call-anything primitive.

Requires: bc250-smu-unlock (unlock.py + patcher.py with RPC patch applied).
Run as root on the BC-250 board after power cycle.

Sequence:
  1. SMU unlock (Q2 msg 0x23 exploit → secure_access open)
  2. Apply RPC patch (patcher.py with full patches.hex including 0x12000 hook)
  3. PLL_POWER_SET(domain=6, enable=1) — power on VCN PLL
  4. CLK_DOMAIN_UNGATE(0x16, 0x17, 0x18) — ungate VCN clock domains
  5. Optionally reload amdgpu module so driver picks up VCN

Credits: rpc_demo.py by dantisnfs, bc250-smu-unlock by rw-r-r-0644.
"""
import argparse
import os
import subprocess
import sys
import time

# SMU firmware function addresses (Robin_5 / BIOS P3.00, SMU 0.58.7.1)
FN_PLL_POWER_SET    = 0x23b14
FN_CLK_DOMAIN_UNGATE = 0x23744

# VCN clock domains
VCN_DOMAINS = [0x16, 0x17, 0x18]

# Path to bc250-smu-unlock on the board
SMU_UNLOCK_DIR = "/root/vcn_unlock/bc250-smu-unlock"


def run(cmd, **kw):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, **kw)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skip-unlock", action="store_true",
                    help="Skip unlock step (already unlocked this boot)")
    ap.add_argument("--skip-patch", action="store_true",
                    help="Skip RPC patch (already applied this boot)")
    ap.add_argument("--reload-amdgpu", action="store_true",
                    help="rmmod + modprobe amdgpu after ungate")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print plan without executing")
    args = ap.parse_args()

    if os.geteuid() != 0:
        print("ERROR: needs root", file=sys.stderr)
        return 1

    sys.path.insert(0, SMU_UNLOCK_DIR)
    try:
        from bc250_smu import Bc250Smu
        from bc250_smu.errors import SmuError
    except ImportError as e:
        print("ERROR: bc250_smu not found at %s: %s" % (SMU_UNLOCK_DIR, e),
              file=sys.stderr)
        return 1

    sys.stdout.reconfigure(line_buffering=True)

    if args.dry_run:
        print("[DRY] Would: unlock=%s patch=%s ungate=0x16,0x17,0x18 reload=%s"
              % (not args.skip_unlock, not args.skip_patch, args.reload_amdgpu))
        return 0

    smu = Bc250Smu()

    # Step 1: unlock
    if not args.skip_unlock:
        print("[1/4] SMU unlock (Q2 msg 0x23 exploit)...")
        from unlock import unlock
        try:
            unlock(smu)
        except SmuError as e:
            print("ERROR unlock: %s" % e, file=sys.stderr)
            smu.close()
            return 1
    else:
        print("[1/4] unlock: skipped (--skip-unlock)")

    if not smu.alive():
        print("ERROR: SMU not alive after unlock", file=sys.stderr)
        smu.close()
        return 1
    print("  secure_access:", smu.secure_access_enabled())

    # Step 2: RPC patch
    if not args.skip_patch:
        print("[2/4] Applying RPC patch...")
        # Check if already applied
        body = smu.smu_read_bytes(0x12000, 4)
        if any(b != 0 for b in body):
            print("  RPC patch already applied, skipping")
        else:
            from patcher import read_hex
            patches_hex = os.path.join(SMU_UNLOCK_DIR, "patches_full.hex")
            if not os.path.exists(patches_hex):
                patches_hex = os.path.join(SMU_UNLOCK_DIR, "bc250_smu",
                                           "patches.hex")
            patches = read_hex(patches_hex)
            for addr, new in patches:
                cur = smu.smu_read_bytes(addr, len(new))
                if cur != new:
                    smu.smu_write_bytes(addr, new)
                    got = smu.smu_read_bytes(addr, len(new))
                    ok = "OK" if got == new else "FAIL"
                    print("  apply %05X %s" % (addr, ok))
            # Verify hook
            hook = smu.smu_read_bytes(0x1BA6E, 3)
            body = smu.smu_read_bytes(0x12000, 4)
            print("  hook=%s body=%s" % (hook.hex(), body.hex()))
    else:
        print("[2/4] patch: skipped (--skip-patch)")

    if not smu.alive():
        print("ERROR: SMU not alive after patch", file=sys.stderr)
        smu.close()
        return 1

    # Step 3: VCN clock ungate
    print("[3/4] VCN clock ungate...")
    print("  PLL_POWER_SET(6, 1)...")
    r = smu.call(FN_PLL_POWER_SET, 6, 1)
    print("    result: 0x%x alive: %s" % (r, smu.alive()))

    for dom in VCN_DOMAINS:
        print("  CLK_DOMAIN_UNGATE(0x%02x)..." % dom)
        r = smu.call(FN_CLK_DOMAIN_UNGATE, dom)
        print("    result: 0x%x alive: %s" % (r, smu.alive()))

    if not smu.alive():
        print("WARNING: SMU died during ungate", file=sys.stderr)
        smu.close()
        return 1

    smu.close()
    print("  VCN clock ungate complete, SMU alive")

    # Step 4: reload amdgpu
    if args.reload_amdgpu:
        print("[4/4] Reloading amdgpu module...")
        rc, out, err = run("rmmod amdgpu 2>&1")
        if rc != 0:
            print("  rmmod failed: %s %s" % (out, err))
            print("  trying with dependents...")
            run("rmmod drm_client_lib 2>&1")
            run("rmmod drm_kms_helper 2>&1")
            rc, out, err = run("rmmod amdgpu 2>&1")
            if rc != 0:
                print("  ERROR: cannot rmmod amdgpu: %s" % (out or err),
                      file=sys.stderr)
                return 1
        print("  rmmod ok, waiting 2s...")
        time.sleep(2)
        rc, out, err = run("modprobe amdgpu 2>&1")
        print("  modprobe exit=%d" % rc)
        if rc != 0:
            print("  ERROR: modprobe failed: %s" % (out or err),
                  file=sys.stderr)
            return 1
        time.sleep(3)
        # Check VCN ring
        rc, out, _ = run("ls /sys/kernel/debug/dri/0/ 2>/dev/null | grep -iE 'vcn|uvd'")
        if out:
            print("  VCN RINGS FOUND: %s" % out)
        else:
            print("  No VCN rings after reload")
        # dmesg
        rc, out, _ = run("dmesg | tail -30 | grep -iE 'vcn|uvd|video.core|jpeg'")
        if out:
            print("  dmesg VCN: %s" % out)
        else:
            print("  No VCN mentions in recent dmesg")
    else:
        print("[4/4] amdgpu reload: skipped (use --reload-amdgpu)")

    print("\n=== DONE ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())