#!/usr/bin/env python3
"""probe4l6: read the LIVE VCN clock-controller block + second-gate PLL windows.

Rationale (2026-09-24 plan-consumers session): FUN_00024594 writes the VCN
clock controller at SMN 0x0115F600 (+0x200..+0x374) from plan bits 0x2B00+,
and polls ready bit 0x100 at 0x0115F964. The second-gate descriptors idx
22/23/24 carry program windows 0x0116D100/0x0116D128/0x0116D150 (DCLK/VCLK/
selector) — and the board's own metrics report DCLK alive at ~1111 MHz,
VCLK at 0. If the DCLK window 0x0116D100 holds a real 16.16 fixed-point
MHz value, it is a LIVE WORKING EXAMPLE of a sane PLL programming in the
exact family the derivation needs.

All addresses are in the proven-safe 0x0115F/0x0116D/0x01159 families read
through the Q3 0x2A mailbox service (the same transport as probe4l3/4l4/4l5).
The 0x01D8 power island is NOT touched (SMU-killer, R3 ban).

Order: sanity -> second-gate PLLs (the live donor) -> VCN controller block
-> init-defaults block -> power-step windows. alive() between reads; stop on
first timeout; JSON saved on the board.
"""

import json
import sys
import time

LIB = "/home/OWNER/vcn_unlock/bc250-smu-unlock"
sys.path.insert(0, LIB)

from bc250_smu import Bc250Mailbox, Bc250Smu  # noqa: E402
from unlock import unlock  # noqa: E402

READS = [
    ("sanity_5a870", 0x0005A870),
    # second-gate PLL windows (descriptor idx 22/23/24)
    ("dclk_prog_6d100", 0x0116D100),
    ("dclk_ack_6d114", 0x0116D114),
    ("dclk_ack_6d124", 0x0116D124),
    ("vclk_prog_6d128", 0x0116D128),
    ("vclk_ack_6d13c", 0x0116D13C),
    ("vclk_ack_6d14c", 0x0116D14C),
    ("sel_prog_6d150", 0x0116D150),
    ("sel_ack_6d164", 0x0116D164),
    ("sel_poll_6d174", 0x0116D174),
    # VCN clock controller block (base 0x0115F600, offsets FUN_00024594 writes)
    ("vcn_200", 0x0115F800),
    ("vcn_208_en", 0x0115F808),
    ("vcn_210", 0x0115F810),
    ("vcn_214", 0x0115F814),
    ("vcn_218", 0x0115F818),
    ("vcn_250_t0", 0x0115F850),
    ("vcn_254_c0", 0x0115F854),
    ("vcn_258_t1", 0x0115F858),
    ("vcn_25c_c1", 0x0115F85C),
    ("vcn_260_t2", 0x0115F860),
    ("vcn_264_c2", 0x0115F864),
    ("vcn_268_t3", 0x0115F868),
    ("vcn_26c_c3", 0x0115F86C),
    ("vcn_2b4_nib", 0x0115F8B4),
    ("vcn_35c", 0x0115F95C),
    ("vcn_358", 0x0115F958),
    ("vcn_364_poll", 0x0115F964),
    ("vcn_374", 0x0115F974),
    # power-step windows (descriptor idx 25/26 raws inside the same block)
    ("pstep19_5f8fc", 0x0115F8FC),
    ("pstep19_ack14", 0x0115F910),
    ("pstep19_ack24", 0x0115F920),
    ("pstep1a_5f924", 0x0115F924),
    ("pstep1a_ack14", 0x0115F938),
    ("pstep1a_ack24", 0x0115F948),
    # init-defaults block (FUN_0001b024 fallback writes)
    ("idef_224", 0x01159C24),
    ("idef_244", 0x01159C44),
    ("idef_324", 0x01159D24),
    ("idef_344", 0x01159D44),
]

OUT = {
    "experiment": "probe4l6-vcn-ctl-live",
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
            if st is None:
                values[name] = {"addr": "0x%08x" % addr, "timeout": True}
                OUT["wedge_after"] = name
                OUT["alive_after"] = smu.alive()
                break
            values[name] = {
                "addr": "0x%08x" % addr,
                "status": hex(st),
                "value": "0x%08x" % val if val is not None else None,
                **(
                    {"refused": True}
                    if st == Bc250Mailbox.SMU_RETURN_REJECTED_PREREQ
                    else {}
                ),
            }
        OUT["reads"] = values
        OUT.setdefault("alive_after", smu.alive())
    finally:
        try:
            smu.close()
        except Exception:  # noqa: BLE001
            pass

    path = "/home/OWNER/vcn_unlock/probe4l6_%s.json" % time.strftime("%H%M%S")
    with open(path, "w") as fh:
        json.dump(OUT, fh, indent=2)
    print(json.dumps(OUT, indent=2))
    print("saved:", path, flush=True)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    raise SystemExit(main())
