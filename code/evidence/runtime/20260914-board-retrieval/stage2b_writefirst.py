#!/usr/bin/env python3
"""S2-A stage 2b (write-first), 2026-09-12.

Donor aperture runtime programming via the SMU secure path, after the 2026-09-12
G7 correction: DF-space/bank-12 SMN READS on a never-programmed cold boot WEDGE
the SMU (Sep-3 x3, 2a readback). WRITES are the proven-safe first touch
(1461-write replay + stage-2a). Therefore: writes only, reads ONLY the single
post-programming bank-12 control readback at the END (26.08-proven pattern),
NO MMIO, no other reads.

Sequence:
  1. unlock (Q2 0x23) if needed
  2. donor aperture: 0x03E810<-6 (grp 0x210), 0x03A2011C<-0x107FF, 0x03A20124<-0x10FFF (grp 0x201)
  3. 56 bank-12 records in donor order (51 x grp 0x201, 5 x grp 0x280; recommit sequence
     identical to smn_vcn_gasket_unclamp.py GASKET_WRITES from the 26.08 run)
  4. smu.alive() after EVERY write (26.08 pattern); abort on first failure
  5. single readback 0x0900C234 (expect commit=1) + alive

Rollback: cold power cycle (all writes volatile, PSP re-applies Robin gasket at boot).
"""
import json
import sys
import time

SMU_LIB = "/home/OWNER/vcn_unlock/bc250-smu-unlock"
sys.path.insert(0, SMU_LIB)

from bc250_smu import Bc250Smu  # noqa: E402
from bc250_smu.errors import SmuTimeout, SmuError  # noqa: E402
import unlock  # noqa: E402

DONOR_APERTURE = [
    ("0x210", 0x03E810,   0x00000006),  # VCN_SEG enable
    ("0x201", 0x03A2011C, 0x000107FF),  # DF window: bank-12 bit added to Robin 0x87FF
    ("0x201", 0x03A20124, 0x00010FFF),  # DF window upper
]

# 56 bank-12 records, byte-identical to smn_vcn_gasket_unclamp.py GASKET_WRITES
# (verified against the 26.08 smn_vcn_gasket_unclamp.out run log)
BANK12 = [
    ("0x201", 0x0900c234, 0x00000000),
    ("0x201", 0x0900c830, 0x00fffffb),
    ("0x201", 0x0900c834, 0x00ffffff),
    ("0x201", 0x0900c838, 0x00ffffff),
    ("0x201", 0x0900c920, 0x000003ff),
    ("0x201", 0x0900c92c, 0x00000000),
    ("0x201", 0x0900c930, 0x00000036),
    ("0x201", 0x0900c944, 0x00000307),
    ("0x201", 0x0900c950, 0x00000000),
    ("0x201", 0x0900c954, 0x00000036),
    ("0x201", 0x0900c934, 0x00021800),
    ("0x201", 0x0900c938, 0x000218ff),
    ("0x201", 0x0900c968, 0x00000307),
    ("0x201", 0x0900c974, 0x00000000),
    ("0x201", 0x0900c978, 0x00000036),
    ("0x201", 0x0900c958, 0x00020300),
    ("0x201", 0x0900c95c, 0x000206ff),
    ("0x201", 0x0900c98c, 0x00000307),
    ("0x201", 0x0900c998, 0x00000000),
    ("0x201", 0x0900c99c, 0x00000036),
    ("0x201", 0x0900c97c, 0x0001f844),
    ("0x201", 0x0900c980, 0x0001f84f),
    ("0x201", 0x0900c9b0, 0x00000307),
    ("0x201", 0x0900c9bc, 0x00000000),
    ("0x201", 0x0900c9c0, 0x00000036),
    ("0x201", 0x0900c9a0, 0x00020180),
    ("0x201", 0x0900c9a4, 0x00020183),
    ("0x201", 0x0900c9d4, 0x00000307),
    ("0x201", 0x0900c9e0, 0x00000000),
    ("0x201", 0x0900c9e4, 0x00000036),
    ("0x201", 0x0900c9c4, 0x00020108),
    ("0x201", 0x0900c9c8, 0x00020117),
    ("0x201", 0x0900c9f8, 0x00000307),
    ("0x201", 0x0900ca04, 0x00000000),
    ("0x201", 0x0900ca08, 0x00000036),
    ("0x201", 0x0900c9e8, 0x00021078),
    ("0x201", 0x0900c9ec, 0x0002107f),
    ("0x201", 0x0900ca1c, 0x00000307),
    ("0x201", 0x0900ca28, 0x00000000),
    ("0x201", 0x0900ca2c, 0x00000036),
    ("0x201", 0x0900ca0c, 0x00020eb0),
    ("0x201", 0x0900ca10, 0x00020eb7),
    ("0x201", 0x0900ca40, 0x00000307),
    ("0x201", 0x0900ca4c, 0x00000000),
    ("0x201", 0x0900ca50, 0x00000036),
    ("0x201", 0x0900ca30, 0x0001f860),
    ("0x201", 0x0900ca34, 0x0001f863),
    ("0x201", 0x0900cb80, 0x000000ff),
    ("0x201", 0x0900c910, 0x00497fff),
    ("0x201", 0x0900c914, 0x00007fff),
    ("0x201", 0x0900c234, 0x00000001),
    ("0x280", 0x0900c234, 0x00000000),
    ("0x280", 0x0900c914, 0x00000000),
    ("0x280", 0x0900c930, 0x00000000),
    ("0x280", 0x0900cb80, 0x00000000),
    ("0x280", 0x0900c234, 0x00000001),
]

OUT = "/home/OWNER/vcn_unlock/stage2b_writefirst_%s.json" % time.strftime("%Y%m%d_%H%M%S")

log = {
    "stage": "s2a-2b-writefirst",
    "started": time.strftime("%Y-%m-%d %H:%M:%S"),
    "smu_alive_before": None,
    "unlock": None,
    "writes": [],
    "write_count": 0,
    "readback_0900c234": None,
    "alive_final": None,
    "verdict": None,
    "finished": None,
}


def save():
    log["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(OUT, "w") as f:
        json.dump(log, f, indent=1, ensure_ascii=False)
    print("JSON-лог: %s" % OUT, flush=True)


def do_write(smu, idx, total, group, address, value):
    print("[++] write[%02d/%02d] %s 0x%08x <= 0x%08x" % (idx, total, group, address, value), flush=True)
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
        sys.exit(2)
    log["writes"].append({"n": idx, "g": group, "a": "0x%08x" % address, "v": "0x%08x" % value})


def main():
    smu = Bc250Smu(timeout=5.0)
    log["smu_alive_before"] = bool(smu.alive())
    print("[*] SMU alive before: %s" % log["smu_alive_before"], flush=True)
    if not log["smu_alive_before"]:
        log["verdict"] = "SMU-NOT-ALIVE-BEFORE (nothing written)"
        save()
        return 3

    if not smu.secure_access_enabled():
        print("[*] gate closed -> VULN-A unlock (Q2 0x23)...", flush=True)
        unlock.smu = smu
        unlock.unlock(smu)
        log["unlock"] = "ran"
    else:
        log["unlock"] = "already-open"
    if not smu.secure_access_enabled():
        log["verdict"] = "UNLOCK-FAILED (nothing written)"
        save()
        return 3
    print("[*] secure access: OPEN (%s)" % log["unlock"], flush=True)

    all_writes = DONOR_APERTURE + BANK12
    total = len(all_writes)
    for idx, (group, address, value) in enumerate(all_writes, 1):
        do_write(smu, idx, total, group, address, value)

    print("[+] all %d writes accepted, SMU alive throughout" % total, flush=True)

    print("[++] single verification readback 0x0900c234 (expect commit=1, 26.08 pattern)", flush=True)
    try:
        back = smu.smn_read32(0x0900C234)
        log["readback_0900c234"] = "0x%08x" % back
        print("[+] readback: 0x%08x %s" % (back, "(commit=1 OK)" if back == 1 else "(UNEXPECTED)"), flush=True)
    except SmuTimeout as e:
        log["readback_0900c234"] = "timeout"
        log["verdict"] = "WRITES-DONE (%d), readback WEDGED: %s — cold power cycle; latch unknown" % (log["write_count"], e)
        print("!! %s" % log["verdict"], flush=True)
        save()
        smu.close()
        return 2

    log["alive_final"] = bool(smu.alive())
    log["verdict"] = "WRITES-DONE+READBACK-OK (%d writes, commit=1, alive=%s)" % (log["write_count"], log["alive_final"])
    print("VERDICT: %s" % log["verdict"], flush=True)
    save()
    smu.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
