#!/usr/bin/env python3
"""probe4l: read the BC-250 SMU clock plan from Linux via the proven mailbox chain.

Route (all primitives hardware-proven on this board, see
docs/action-logs/2026-09-23-probe3-auto-usb-payload.md Run 1/2):
  1. alive() + secure_access_enabled()  (non-wedging checks, assess_S1 class)
  2. if closed: unlock(smu) from ~/vcn_unlock/bc250-smu-unlock/unlock.py
     (the community ring-overflow debug unlock; raises SmuError on failure)
  3. sec_smn_read32(addr) = SMU Q3 0x2A secure read, one address at a time,
     risk-ordered, alive() between reads, STOP on first timeout/dead SMU.

No raw host SMN reads of DF/SMU space (the run-1 wedge class). The only
hardware touched is the Q3 mailbox via the bc250_smu library.

Output: JSON on stdout + ~/vcn_unlock/probe4l_<ts>.json. Needs root.
"""

import json
import sys
import time

LIB = "/home/OWNER/vcn_unlock/bc250-smu-unlock"
sys.path.insert(0, LIB)

from bc250_smu import Bc250Mailbox, Bc250Smu  # noqa: E402
from unlock import unlock  # noqa: E402

# Risk-ordered read list (v2, after probe4l run 1 measured the wedge):
# SMU-local SRAM first, the clock-plan prize next, the descriptor window,
# then STOP — 0x01D80218 is a MEASURED SMU-killer (power island), and the
# 0x0115Fxxx controller window is suspect-until-proven (same SMN-external
# class). Do not re-add them without a separate decision.
READS = [
    ("probe_5a870", 0x0005A870),
    ("domain_bitmap_ccb8", 0x0000CCB8),
    ("clock_plan_a", 0x0115D000),
    ("clock_plan_b", 0x0115D004),
]
# VCN descriptor window: both shadows, 0x0115D560..0x0115D588.
for i in range(20):
    READS.append(("desc_%03x" % (0x560 + i * 4), 0x0115D560 + i * 4))

OUT = {
    "experiment": "probe4l-clock-plan-linux-mailbox",
    "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    "lib": LIB,
}


def main() -> int:
    smu = Bc250Smu(bdf="0000:00:00.0", timeout=5.0)
    try:
        OUT["alive_before"] = smu.alive()
        if not OUT["alive_before"]:
            print(json.dumps({"error": "SMU not alive - cold power cycle"}, indent=2))
            return 2

        secure = smu.secure_access_enabled()
        OUT["secure_before"] = bool(secure)
        if not secure:
            print("gate: closed, running the proven unlock...", flush=True)
            OUT["unlock"] = bool(unlock(smu))
            OUT["secure_after"] = bool(smu.secure_access_enabled())
            if not OUT["secure_after"]:
                print(json.dumps({"error": "unlock did not open the gate"}, indent=2))
                return 3
        else:
            print("gate: already open", flush=True)

        values = {}
        for name, addr in READS:
            if not smu.alive():
                OUT["wedge_after"] = name
                OUT["alive_after"] = False
                break
            try:
                st, val = smu.sec_smn_read32(addr)
            except Exception as exc:  # noqa: BLE001
                values[name] = {"addr": "0x%08x" % addr, "exc": repr(exc)[:100]}
                OUT["wedge_after"] = name
                OUT["alive_after"] = smu.alive()
                break
            if st is None or st in (Bc250Mailbox.SMU_RETURN_REJECTED_PREREQ,):
                values[name] = {
                    "addr": "0x%08x" % addr,
                    "status": st if st is None else hex(st),
                    "refused_or_timeout": True,
                }
                if st is None:
                    OUT["wedge_after"] = name
                    OUT["alive_after"] = smu.alive()
                    break
                continue
            values[name] = {
                "addr": "0x%08x" % addr,
                "status": hex(st),
                "value": "0x%08x" % val if val is not None else None,
            }
        OUT["reads"] = values
        OUT.setdefault("alive_after", smu.alive())

        # Verdict lines (probe3 semantics).
        da = values.get("clock_plan_a", {}).get("value")
        db = values.get("clock_plan_b", {}).get("value")
        if da is not None and db is not None:
            OUT["clock_plan_words"] = {"A": da, "B": db}
        desc_zero = True
        for i in range(20):
            v = values.get("desc_%03x" % (0x560 + i * 4), {}).get("value")
            if v is not None and int(v, 16) != 0:
                desc_zero = False
        if any("desc_" in k for k in values):
            OUT["vcn_descriptor"] = (
                "EMPTY (donor fill required)" if desc_zero else "populated"
            )
        bm = values.get("domain_bitmap_ccb8", {}).get("value")
        if bm is not None:
            OUT["vcn_domain_bit6"] = bool(int(bm, 16) & 0x40)
        ps = values.get("power_status_1d80218", {}).get("value")
        if ps is not None:
            OUT["power_status_0c00_mask"] = bool(int(ps, 16) & 0x0C00)
    finally:
        try:
            smu.close()
        except Exception:  # noqa: BLE001
            pass

    path = "/home/OWNER/vcn_unlock/probe4l_%s.json" % time.strftime("%H%M%S")
    with open(path, "w") as fh:
        json.dump(OUT, fh, indent=2)
    print(json.dumps(OUT, indent=2))
    print("saved:", path, flush=True)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    raise SystemExit(main())
