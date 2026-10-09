#!/usr/bin/env python3
"""probe4l3: read the live SMU SRAM slots (PLL coefficients, table pointers,
DF pstate rows, per-domain current codes) via the proven Linux 0x2A route.

Purpose (R3 §5 remaining gap + the FCLK-override question):
  - [0x1729c]/[0x1792c]/[0x17930] = the PLL coefficient slots; with the
    per-domain current-code caches (descriptor+0x82 for domains 0x0E FCLK /
    0x0F+0x11 UCLK) they give the LIVE FCLK/UCLK in absolute terms.
  - [0x1745c] = the domain-descriptor table pointer (two-phase: follow it
    only if it points into the SRAM range, else record and skip).
  - 0x0CEFC pointer array + 0x0CF0C rows (0x28 stride): the DF pstate rows
    at runtime — +0x10 (/2 derived), +0x14 (k-derived), +0x18 (freq float).
    Static image says 450/450/850/1750/250; the c38 answers said
    250/250/750/1200 — this read decides which is live.

Safety: every address is in the proven SMU-local SRAM class (0x0000xxxx).
No 0x01D8xxxx (measured SMU-killer), no 0x0115Fxxx (suspect). alive() between
reads; stop on timeout/death; JSON saved on the board.

Needs root. Output: JSON on stdout + ~/vcn_unlock/probe4l3_<ts>.json.
"""

import json
import sys
import time

LIB = "/home/OWNER/vcn_unlock/bc250-smu-unlock"
sys.path.insert(0, LIB)

from bc250_smu import Bc250Mailbox, Bc250Smu  # noqa: E402
from unlock import unlock  # noqa: E402

# Phase 1: fixed SRAM reads.
FIXED = [
    ("probe_5a870", 0x0005A870),
    ("domain_bitmap_ccb8", 0x0000CCB8),
    ("coef_1729c", 0x0001729C),
    ("coef_1792c", 0x0001792C),
    ("coef_17930", 0x00017930),
    ("ptr_1745c", 0x0001745C),
    ("bounds_17488", 0x00017488),
    ("mult_17450", 0x00017450),
    ("ppt_17180", 0x00017180),
]
# DF pointer array at 0x0CEFC (5 words).
for i in range(5):
    FIXED.append(("dfptr_%02x" % (0xFC + i * 4), 0x0000CEFC + i * 4))
# DF rows at 0x0CF0C, 0x28 stride, p=0..4: words +0x00, +0x04, +0x10, +0x14, +0x18.
for p in range(5):
    base = 0x0000CF0C + p * 0x28
    for off in (0x00, 0x04, 0x10, 0x14, 0x18):
        FIXED.append(("dfrow%d_%02x" % (p, off), base + off))
# Clock-slot struct base (context words).
for off in (0x00, 0x04, 0x08):
    FIXED.append(("slot_f568_%02x" % off, 0x0000F568 + off))

# Phase 2 (conditional on ptr_1745c pointing into SRAM): per-domain reads.
PHASE2_DOMAINS = [0x03, 0x04, 0x0E, 0x0F, 0x10, 0x11, 0x12]
PHASE2_FIELDS = [0x80, 0x98, 0x254]  # +0x80 word covers flags 0x80/0x83 + code 0x82

OUT = {
    "experiment": "probe4l3-smu-sram-slots",
    "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    "lib": LIB,
}


def rd(smu, values, name, addr):
    """One 0x2A read. Returns 'ok', 'refused', or 'dead'."""
    try:
        st, val = smu.sec_smn_read32(addr)
    except Exception as exc:  # noqa: BLE001
        values[name] = {"addr": "0x%08x" % addr, "exc": repr(exc)[:100]}
        return "dead"
    if st is None:
        values[name] = {"addr": "0x%08x" % addr, "timeout": True}
        return "dead"
    values[name] = {
        "addr": "0x%08x" % addr,
        "status": hex(st),
        "value": "0x%08x" % val if val is not None else None,
    }
    if st == Bc250Mailbox.SMU_RETURN_REJECTED_PREREQ:
        values[name]["refused"] = True
    return "ok"


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
        for name, addr in FIXED:
            if not smu.alive():
                OUT["wedge_after"] = name
                OUT["alive_after"] = False
                break
            if rd(smu, values, name, addr) == "dead":
                OUT["wedge_after"] = name
                OUT["alive_after"] = smu.alive()
                break

        # Phase 2: follow the descriptor table pointer if it is SRAM-class.
        ptr = values.get("ptr_1745c", {}).get("value")
        if ptr is not None and OUT.get("wedge_after") is None:
            v = int(ptr, 16)
            OUT["descriptor_ptr"] = "0x%08x" % v
            if 0x1000 <= v <= 0xFFFFF:
                for dom in PHASE2_DOMAINS:
                    entry = v + dom * 0x1C
                    for off in PHASE2_FIELDS:
                        name = "dom%02x_%03x" % (dom, off)
                        if not smu.alive():
                            OUT["wedge_after"] = name
                            OUT["alive_after"] = False
                            break
                        if rd(smu, values, name, entry + off) == "dead":
                            OUT["wedge_after"] = name
                            OUT["alive_after"] = smu.alive()
                            break
                    if OUT.get("wedge_after"):
                        break
            else:
                OUT["phase2"] = "skipped: pointer outside SRAM range"

        OUT["reads"] = values
        OUT.setdefault("alive_after", smu.alive())
    finally:
        try:
            smu.close()
        except Exception:  # noqa: BLE001
            pass

    path = "/home/OWNER/vcn_unlock/probe4l3_%s.json" % time.strftime("%H%M%S")
    with open(path, "w") as fh:
        json.dump(OUT, fh, indent=2)
    print(json.dumps(OUT, indent=2))
    print("saved:", path, flush=True)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    raise SystemExit(main())
