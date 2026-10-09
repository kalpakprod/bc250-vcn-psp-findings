#!/usr/bin/env python3
"""probe4l8: SMU ring-forgery delivery tool (ZD-1 append route), version-gated.

Plan source: evidence/firmware-audit/20260923-smu-forged-record-plan/
plan-result.json — offline arithmetic verified against the robin-5 body
(smu_fw_robin_5, sha cae8617c…, SMU version 0x00580701 = 58.7.1, the
5.00-clv type-0x08 payload).

Sequence (ring 0, slot 0; entry i lands at RING_BASE + i*0x10):
  indices 0..87   : no-op fillers (mask 0 -> record applies old value)
  index  88       : the forged record at Q0_TABLE[0] (0x18E20 in robin-5)
                    DRYRUN: mask 0 (no-op). PROBE: mask 0xffffffff, value 0
                    -> full clear of the word at 0x02000000+0x60.
  indices 89..118 : no-op fillers (Q0 table rows 1..30)
  index  119      : entry[3]=1 lands on the Q0 record count (0x1901C)
                    -> the applier sees exactly 1 staged record.
Trigger: a later Q2/Q3 command whose handler chain reaches FUN_0002D4E0
(per the plan: callers 0x2D308/0x2D35C; VCN/clock paths 0x1F814/0x1FAF0,
reached by the Q3 0x1B bring-up family).

SAFETY GATE: the baked geometry is ONLY valid for SMU version 0x00580701.
The live board reported 0x00580600 (a 3.00-lineage robin) on 2026-09-24:
different SRAM layout, the sequence would land at UNVERIFIED addresses.
The tool REFUSES to append unless the live version matches, unless
--force-version is given (operator-only, with a re-derived plan).

Modes:
  --version        read+report the SMU version (read-only, default)
  --read-geometry  read the predicted counter/table words via Q3 0x2A
                   (read-only; on 58.7.1 they must look like ring data)
  --dryrun         stage the DRYRUN_NOOP sequence (all no-op records) + trigger
  --probe          stage the Q0_WINDOW_PROBE_0x02000060 record + trigger

One-shot per boot: ring counters persist in SRAM until power cycle.
NEVER target fuse/OTP space. Appends beyond #119 trash the counter block.
"""

import argparse
import json
import sys
import time

LIB = "/home/OWNER/vcn_unlock/bc250-smu-unlock"
sys.path.insert(0, LIB)

from bc250_smu import Bc250Smu  # noqa: E402

# ---- baked robin-5 (58.7.1) geometry, from plan-result.json --------------
PLAN_VERSION = 0x00580701
RING_BASE = 0x188A0
ENTRY_SZ = 16
FORGED_INDEX = 88  # Q0_TABLE[0] @ 0x18E20
COUNT_FLIP_INDEX = 119  # entry[3] -> Q0 count @ 0x1901C
APPENDS = 120
Q0_TABLE = 0x18E20
Q0_COUNT = 0x1901C
# record words for the two plan variants (addr tag as stored, value, mask, 1)
REC_DRYRUN = (0x02000060, 0x0, 0x0, 1)  # mask 0 -> no-op
REC_PROBE = (0x02000060, 0x0, 0xFFFFFFFF, 1)  # full clear of 0x02000060
FILLER = (0x0, 0x0, 0x0, 1)  # mask 0 -> no-op
ARG3_RING0_SLOT0 = 0x01000001  # (1<<24)|ring(0)<<20|slot+1(1)

# read-only geometry words (Q3 0x2A reads; valid only under the baked plan)
GEOMETRY_READS = [
    ("ring_slot0_ctr_19020", 0x19020),
    ("q0_count_1901c", 0x1901C),
    ("q0_table0_18e20", 0x18E20),
    ("q0_table0_word4", 0x18E24),
]


def ring_args(rec):
    """Q2 0x23 args (arg0, arg1=mask, arg2=value, arg3=ring/slot selector).

    The handler stores entry = {arg0+tag, arg2, arg1, 1}; the applier's
    record fields are {addr, value, mask}: entry[1]=arg2=value,
    entry[2]=arg1=mask. new = value & mask | old & ~mask.
    """
    addr_tag, value, mask, _ = rec
    # the stored entry[0] = arg0 + 0x16C00000; the plan's stored word for
    # target 0x02000060 is 0x02000060, so arg0 cancels the tag in the
    # applier: arg0 = 0x02000060 - 0x16C00000 = -0x14BFFF94 (mod 2^32)
    arg0 = (addr_tag - 0x16C00000) & 0xFFFFFFFF
    return [arg0, mask, value, ARG3_RING0_SLOT0]


def send_ring(smu, rec):
    st, ret = smu.send_message(2, 0x23, ring_args(rec))
    return st, ret


def stage_sequence(smu, forged_rec):
    log = []
    for i in range(APPENDS):
        if i == FORGED_INDEX:
            rec = forged_rec
        else:
            rec = FILLER
        st, ret = send_ring(smu, rec)
        log.append({"i": i, "st": st, "ret": ret})
        if st != 0x01:
            print(f"APPEND REJECTED at i={i}: st=0x{st:02x} — ABORT, nothing more sent")
            return log, False
        if i % 20 == 0:
            print(f"  append {i}/119 ok")
    return log, True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--mode",
        choices=("version", "read-geometry", "dryrun", "probe"),
        default="version",
    )
    ap.add_argument(
        "--force-version",
        action="store_true",
        help="override the version gate (operator only)",
    )
    ap.add_argument("--out", default="/tmp/probe4l8-ring-forgery.json")
    a = ap.parse_args()

    smu = Bc250Smu()
    result = {
        "tool": "probe4l8_ring_forgery",
        "mode": a.mode,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    try:
        if not smu.alive():
            print("SMU not alive — abort")
            return 1
        st, ver = smu.send_message(0, 0x02)
        result["smu_version"] = "0x%08x" % ver
        print("SMU version: 0x%08x (plan baked for 0x%08x)" % (ver, PLAN_VERSION))
        if a.mode in ("dryrun", "probe"):
            if ver != PLAN_VERSION and not a.force_version:
                print(
                    "VERSION GATE: live SMU is not the plan's robin — REFUSING to append."
                )
                print(
                    "Re-derive the plan for this body, or flash the 5.00-clv base first."
                )
                result["gate"] = "REFUSED_VERSION_MISMATCH"
                return 2
            rec = REC_DRYRUN if a.mode == "dryrun" else REC_PROBE
            result["record"] = ["0x%08x" % w for w in rec]
            log, ok = stage_sequence(smu, rec)
            result["appends"] = log
            result["appends_ok"] = ok
            if ok:
                # trigger: Q3 0x1B (the bring-up family reaching the applier)
                st, ret = smu.send_message(3, 0x1B, [0])
                result["trigger_q3_0x1b"] = {"st": st, "ret": ret}
                print("trigger Q3 0x1B: st=0x%02x ret=0x%x" % (st, ret))
        elif a.mode == "read-geometry":
            reads = {}
            for name, addr in GEOMETRY_READS:
                try:
                    st, val = smu.send_message(3, 0x2A, [addr])
                    reads[name] = {
                        "addr": "0x%08x" % addr,
                        "st": st,
                        "val": "0x%08x" % val,
                    }
                    print(f"{name} @0x{addr:06x}: st=0x{st:02x} val=0x{val:08x}")
                except Exception as ex:
                    reads[name] = {"addr": "0x%08x" % addr, "error": repr(ex)}
            result["reads"] = reads
        else:
            result["alive"] = True
    finally:
        smu.close()
        with open(a.out, "w") as f:
            json.dump(result, f, indent=2)
        print("saved", a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
