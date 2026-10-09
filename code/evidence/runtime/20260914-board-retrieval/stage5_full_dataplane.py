#!/usr/bin/env python3
"""S2-A stage 5: complete donor dataplane state (2026-09-12). Operator-approved goal:
VCN unlock. Runs AFTER the domain bring-up + 59-write gasket (stage2b) in the same
session. Adds the donor records that have never been written at runtime:

  NBIF routes (donor/b2a, from smn_lock_probe SURVEY + chain report):
    0x01C760 <- 0xff400000   0x01C764 <- 0xff400000
    0x01C780 <- 0x00000000   0x01C784 <- 0x00000000
    0x01C788 <- 0x000000ff   0x01C78c <- 0x00000107
  NBIO VCN route:
    0x01F820 <- 0x00185103   0x01F8a4 <- 0x0000000b, then <- 0x00000000
  DF windows b2b (IOHC 0x322):
    0x0322011c <- 0x00010000 0x03220124 <- 0x00010707 0x0322012c <- 0x000101ff
  DF mirror 0x3d2:
    0x03d2011c <- 0x000107ff 0x03d20124 <- 0x00010fff
  VCN_SEG binding (donor):
    0x03e814 <- 0x2544c382   (DTR FIFO binding; previously left untouched)

Then: single readback 0x0900c234 (commit), alive check, and NBIF config capture
(0x6a1xx class) + arbiter pointers for the separate arbiter step.
Stop rule: any SmuTimeout -> cold power cycle. All writes volatile (cold cycle = rollback).
"""
import json
import sys
import time

SMU_LIB = "/home/OWNER/vcn_unlock/bc250-smu-unlock"
sys.path.insert(0, SMU_LIB)

from bc250_smu import Bc250Smu  # noqa: E402
from bc250_smu.errors import SmuTimeout, SmuError  # noqa: E402
import unlock  # noqa: E402

WRITES = [
    # NBIF routes (b2a)
    ("0x201", 0x01C760, 0xFF400000),
    ("0x201", 0x01C764, 0xFF400000),
    ("0x201", 0x01C780, 0x00000000),
    ("0x201", 0x01C784, 0x00000000),
    ("0x201", 0x01C788, 0x000000FF),
    ("0x201", 0x01C78C, 0x00000107),
    # NBIO VCN route (b2a; 0x1f8a4 written twice per donor)
    ("0x201", 0x01F820, 0x00185103),
    ("0x201", 0x01F8A4, 0x0000000B),
    ("0x201", 0x01F8A4, 0x00000000),
    # IOHC 0x322 windows (b2b)
    ("0x201", 0x0322011C, 0x00010000),
    ("0x201", 0x03220124, 0x00010707),
    ("0x201", 0x0322012C, 0x000101FF),
    # DF mirror 0x3d2 (b2a)
    ("0x201", 0x03D2011C, 0x000107FF),
    ("0x201", 0x03D20124, 0x00010FFF),
    # VCN_SEG binding (donor)
    ("0x210", 0x03E814, 0x2544C382),
]

CAPTURE = [
    ("config_reg_0x6a140", 0x6A140),
    ("config_reg_0x6a144", 0x6A144),
    ("config_reg_0x6a148_rmw", 0x6A148),
    ("config_reg_0x6a14c_rmw", 0x6A14C),
    ("config_reg_0x6a150_rmw", 0x6A150),
    ("config_reg_0x6a154_rmw", 0x6A154),
    ("config_reg_0x6a15c", 0x6A15C),
    ("config_reg_0x6a17c", 0x6A17C),
    ("config_reg_0x6a1b4", 0x6A1B4),
    ("config_reg_0x33e0_rmw", 0x33E0),
]

OUT = "/home/OWNER/vcn_unlock/stage5_full_dataplane_%s.json" % time.strftime("%Y%m%d_%H%M%S")

log = {
    "stage": "s2a-5-full-dataplane",
    "started": time.strftime("%Y-%m-%d %H:%M:%S"),
    "smu_alive_before": None,
    "unlock": None,
    "writes": [],
    "write_count": 0,
    "readback_0900c234": None,
    "capture": [],
    "verdict": None,
    "finished": None,
}


def save():
    log["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(OUT, "w") as f:
        json.dump(log, f, indent=1, ensure_ascii=False)
    print("JSON-лог: %s" % OUT, flush=True)


def main():
    smu = Bc250Smu(timeout=5.0)
    log["smu_alive_before"] = bool(smu.alive())
    print("[*] SMU alive before: %s" % log["smu_alive_before"], flush=True)
    if not log["smu_alive_before"]:
        log["verdict"] = "SMU-NOT-ALIVE-BEFORE"
        save()
        return 3

    if not smu.secure_access_enabled():
        print("[*] gate closed -> VULN-A unlock...", flush=True)
        unlock.smu = smu
        unlock.unlock(smu)
        log["unlock"] = "ran"
    else:
        log["unlock"] = "already-open"
    if not smu.secure_access_enabled():
        log["verdict"] = "UNLOCK-FAILED"
        save()
        return 3
    print("[*] secure access: OPEN (%s)" % log["unlock"], flush=True)

    total = len(WRITES)
    for idx, (group, address, value) in enumerate(WRITES, 1):
        print("[++] write[%02d/%02d] 0x%08x <= 0x%08x" % (idx, total, address, value), flush=True)
        try:
            smu.smn_write32(address, value)
        except SmuTimeout as e:
            log["verdict"] = "WEDGED at write[%02d] 0x%08x: %s — cold power cycle" % (idx, address, e)
            print("!! %s" % log["verdict"], flush=True)
            save()
            smu.close()
            sys.exit(2)
        except SmuError as e:
            log["verdict"] = "REJECTED at write[%02d] 0x%08x: %s" % (idx, address, e)
            print("?? %s" % log["verdict"], flush=True)
            save()
            smu.close()
            sys.exit(3)
        log["write_count"] += 1
        if not smu.alive():
            log["verdict"] = "SMU-DEAD after write[%02d] 0x%08x — cold power cycle" % (idx, address)
            print("!! %s" % log["verdict"], flush=True)
            save()
            smu.close()
            return 2
        log["writes"].append({"n": idx, "a": "0x%08x" % address, "v": "0x%08x" % value})

    print("[+] all %d writes accepted, SMU alive" % total, flush=True)

    print("[++] readback 0x0900c234 (commit)", flush=True)
    try:
        back = smu.smn_read32(0x0900C234)
        log["readback_0900c234"] = "0x%08x" % back
        print("[+] commit readback: 0x%08x" % back, flush=True)
    except SmuTimeout as e:
        log["verdict"] = "WRITES-DONE, readback WEDGED — cold power cycle"
        print("!! %s" % log["verdict"], flush=True)
        save()
        smu.close()
        return 2

    print("[++] NBIF config capture (0x6a1xx class, single-reg reads)", flush=True)
    for label, addr in CAPTURE:
        print("[r] %-24s 0x%06x ... " % (label, addr), end="", flush=True)
        try:
            v = smu.smn_read32(addr)
        except SmuTimeout as e:
            print("TIMEOUT/SMU-WEDGED (%s)" % e, flush=True)
            log["verdict"] = "WRITES-DONE+COMMIT-OK; WEDGED at capture %s — cold cycle" % label
            print("!! %s" % log["verdict"], flush=True)
            save()
            smu.close()
            return 2
        except SmuError as e:
            print("REJECTED (%s)" % e, flush=True)
            log["capture"].append({"label": label, "addr": "0x%06x" % addr, "error": str(e)})
            continue
        print("0x%08x" % v, flush=True)
        log["capture"].append({"label": label, "addr": "0x%06x" % addr, "value": "0x%08x" % v})

    log["verdict"] = "FULL-DATAPLANE-APPLIED (%d writes, commit=%s); next: stage4_arbiter" % (
        log["write_count"], log["readback_0900c234"])
    print("VERDICT: %s" % log["verdict"], flush=True)
    save()
    smu.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
