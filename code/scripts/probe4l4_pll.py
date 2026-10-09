#!/usr/bin/env python3
"""probe4l4: read the LIVE PLL program/poll windows for the FCLK/UCLK domains.

Rationale: probe4l3 measured that the static 'in-image SRAM' offsets
(0x0F568/0x1729C/0x0CF0C...) read as zeros through 0x2A — the running firmware
is not mapped 1:1 at those SMN offsets. But the R3 §1 domain table gives the
SMN program/poll window of every clock domain, and the program window holds
the LAST PROGRAMMED CODE (the live PLL state):

  domain 0x0E FCLK        program 0x0115C0FC  poll 0x0115C120
  domain 0x0F UCLK        program 0x0115C8FC  poll 0x0115C920
  domain 0x10 UCLK deriv  program 0x0115C924  poll 0x0115C948
  domain 0x11 UCLK mirror program 0x0116C0FC  poll 0x0116C120
  domain 0x12 deriv mirr  program 0x0116C124  poll 0x0116C148
  domain 0x18 selector    program 0x0116D150  poll 0x0116D174

These are 0x0115C/0x0116C blocks — the same SMN family as the proven-safe
0x0115D plan block (44 words read cleanly). The PLL domains are powered
(clocks run), unlike the 0x01D8 power island that killed the SMU.

Order: FCLK first (the prize), then UCLK pair, derived, mirror, selector.
alive() between reads; stop on first timeout; JSON saved on the board.
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
    ("fclk_prog_c0fc", 0x0115C0FC),
    ("fclk_poll_c120", 0x0115C120),
    ("uclk_prog_c8fc", 0x0115C8FC),
    ("uclk_poll_c920", 0x0115C920),
    ("uclkdiv_prog_c924", 0x0115C924),
    ("uclkdiv_poll_c948", 0x0115C948),
    ("uclkm_prog_6c0fc", 0x0116C0FC),
    ("uclkm_poll_6c120", 0x0116C120),
    ("uclkmdiv_prog_6c124", 0x0116C124),
    ("uclkmdiv_poll_6c148", 0x0116C148),
    ("sel11_prog_6d150", 0x0116D150),
    ("sel11_poll_6d174", 0x0116D174),
]

OUT = {
    "experiment": "probe4l4-pll-windows",
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

    path = "/home/OWNER/vcn_unlock/probe4l4_%s.json" % time.strftime("%H%M%S")
    with open(path, "w") as fh:
        json.dump(OUT, fh, indent=2)
    print(json.dumps(OUT, indent=2))
    print("saved:", path, flush=True)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    raise SystemExit(main())
