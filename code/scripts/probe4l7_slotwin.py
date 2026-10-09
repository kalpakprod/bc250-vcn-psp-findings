#!/usr/bin/env python3
"""probe4l7: read the LIVE program/ack windows of all 8 clock slots + the
VCN domain power-gate windows.

Rationale (2026-09-24 plan-consumers, route B): the slot program window
(page + 0x34/0x38/0x44/0x4C per slot) holds the 16.16 fixed-point MHz the
recalc decodes (FUN_0002360c: (reg & 0x1FF) + (reg >> 16)/65536). Reading
the RUNNING slots (0-5) shows the live format of a working PLL program
word; the VCN slot 7 windows (0x0115F834 prog / 0x0115F838 + 0x0115F83C
power gate / 0x0115F870 ack) give the inputs the power-step code
derivation needs (slot7 freq, gate state).

All reads via the proven Q3 0x2A mailbox service. No 0x01D8/0x0320
addresses. alive() between reads; stop on first timeout.
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
    # slot program windows (page + offset from the slot table)
    ("s0_prog_5b04c", 0x0115B04C),
    ("s1_prog_5b844", 0x0115B844),
    ("s2_prog_5c034", 0x0115C034),
    ("s3_prog_5c834", 0x0115C834),
    ("s4_prog_6c034", 0x0116C034),
    ("s5_prog_6c838", 0x0116C838),
    ("s6_prog_6d038", 0x0116D038),
    ("s7_prog_5f834", 0x0115F834),
    # slot ack/raw2 windows
    ("s0_ack_5b088", 0x0115B088),
    ("s1_ack_5b880", 0x0115B880),
    ("s2_ack_5c070", 0x0115C070),
    ("s3_ack_5c870", 0x0115C870),
    ("s4_ack_6c070", 0x0116C070),
    ("s5_ack_6c874", 0x0116C874),
    ("s6_ack_6d074", 0x0116D074),
    ("s7_ack_5f870", 0x0115F870),
    # VCN domain power-gate windows (FUN_00023d78 slot-7 on/off path)
    ("s7_gate_5f838", 0x0115F838),
    ("s7_gate_5f83c", 0x0115F83C),
    # descriptor DPM-level windows for idx 25/26 (FUN_00024084 path,
    # desc word +0x8C from the 0xF568 base: idx25 -> 0xF568+0x2BC+0x8C)
    # raw values are in-image; read the two SMN targets live instead:
    ("vcn_358_again", 0x0115F958),
    ("vcn_374_again", 0x0115F974),
]

OUT = {
    "experiment": "probe4l7-slot-windows",
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

    path = "/home/OWNER/vcn_unlock/probe4l7_%s.json" % time.strftime("%H%M%S")
    with open(path, "w") as fh:
        json.dump(OUT, fh, indent=2)
    print(json.dumps(OUT, indent=2))
    print("saved:", path, flush=True)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    raise SystemExit(main())
