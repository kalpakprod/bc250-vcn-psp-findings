#!/usr/bin/env python3
"""probe4l5: read the FULL packed clock plan block 0x0115D000..0x0115D5AC.

We have read only the first two words (A=B=0x0E) and the VCN descriptor
window (0x560+, all zero). The middle (bits 64..0x2B00, bytes 0x08..0x560)
holds the OTHER domains' fields — filled at boot by the SMU (the plan is not
all-zero). Those filled fields are the reference arithmetic (dividers/mux
per domain) from which the VCN donor values (step 0b of the vcn-mailbox
runbook) can be derived consistently.

Whole-block read, 4-byte steps, 0x0115D000..0x0115D5AC inclusive (363 words).
Same proven-safe SMN class as the earlier 0x0115D reads (44 words clean).
alive() every 16 reads; stop on timeout; JSON saved on the board.
"""

import json
import sys
import time

LIB = "/home/OWNER/vcn_unlock/bc250-smu-unlock"
sys.path.insert(0, LIB)

from bc250_smu import Bc250Mailbox, Bc250Smu  # noqa: E402
from unlock import unlock  # noqa: E402

START = 0x0115D000
END = 0x0115D7B8  # inclusive; real plan extent per the ASCII health bit 0x3DB9 (byte 0x7B7)
STEP = 4

OUT = {
    "experiment": "probe4l5-full-clock-plan",
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

        words = {}
        n = 0
        addr = START
        while addr <= END:
            if n % 16 == 0 and not smu.alive():
                OUT["wedge_after"] = "0x%08x" % addr
                OUT["alive_after"] = False
                break
            try:
                st, val = smu.sec_smn_read32(addr)
            except Exception as exc:  # noqa: BLE001
                OUT["wedge_after"] = "0x%08x" % addr
                OUT["alive_after"] = smu.alive()
                OUT["exc"] = repr(exc)[:100]
                break
            if st is None:
                OUT["wedge_after"] = "0x%08x" % addr
                OUT["alive_after"] = smu.alive()
                break
            words["0x%08x" % addr] = val if val is None else "0x%08x" % val
            addr += STEP
            n += 1

        OUT["plan_words"] = words
        OUT["word_count"] = len(words)
        nz = {k: v for k, v in words.items() if v not in (None, "0x00000000")}
        OUT["nonzero_words"] = nz
        OUT["nonzero_count"] = len(nz)
        OUT.setdefault("alive_after", smu.alive())
    finally:
        try:
            smu.close()
        except Exception:  # noqa: BLE001
            pass

    path = "/home/OWNER/vcn_unlock/probe4l5_%s.json" % time.strftime("%H%M%S")
    with open(path, "w") as fh:
        json.dump(OUT, fh, indent=2)
    print(
        json.dumps(
            {
                k: OUT.get(k)
                for k in (
                    "word_count",
                    "nonzero_count",
                    "nonzero_words",
                    "alive_after",
                    "wedge_after",
                )
            },
            indent=2,
        )
    )
    print("saved:", path, flush=True)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    raise SystemExit(main())
