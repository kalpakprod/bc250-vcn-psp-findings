#!/usr/bin/env python3
"""probe4l2: query the SMU's own clock/voltage answers (public messages only).

Complements probe4_linux.py (secure 0x2A reads): this battery uses only the
driver-facing query messages (q0/q3 classes the amdgpu driver itself uses),
which are the proven-safe envelope on this board. For every answer: record
status+ret; alive() between groups; stop on first timeout.

Goal (R3 falsifier (c), units): compare the SMU's own numbers with the
static decodes - DF pstates 450/450/850/1750/250, MCLK 1800, UCLK 900,
FCLK 1420, and see which selector/pstate maps to which domain.
"""

import json
import sys
import time

LIB = "/home/OWNER/vcn_unlock/bc250-smu-unlock"
sys.path.insert(0, LIB)

from bc250_smu import Bc250Smu  # noqa: E402

OUT = {
    "experiment": "probe4l2-smu-clock-answers",
    "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
}


def grp(smu, out, label, fn):
    """Run one query; record. Rejections (0xFF) are clean answers, continue.

    Return False ONLY on a real death signal: timeout-class exception or a
    failed alive() check.
    """
    try:
        st, ret = None, None
        r = fn()
        if isinstance(r, tuple):
            st, ret = r
        else:
            ret = r
        out[label] = {
            "status": (hex(st) if isinstance(st, int) else st),
            "ret": (hex(ret) if isinstance(ret, int) else ret),
        }
    except Exception as exc:  # noqa: BLE001
        out[label] = {"exc": repr(exc)[:120]}
        if "Rejected" in repr(exc):
            return smu.alive()  # clean refusal: record, keep going
        return False
    return smu.alive()


def main() -> int:
    smu = Bc250Smu(bdf="0000:00:00.0", timeout=5.0)
    try:
        OUT["alive_before"] = smu.alive()
        if not OUT["alive_before"]:
            print(json.dumps({"error": "SMU not alive"}, indent=2))
            return 2

        # P-state clocks (static DF table expectation: 450/450/850/1750/250).
        for p in range(8):
            if not grp(
                smu,
                OUT,
                "pstate_clk_%d" % p,
                lambda p=p: smu.send_message(3, 0x3B, [p]),
            ):
                OUT["died_at"] = "pstate_clk_%d" % p
                break

        # Selector-family clock queries 0x38/0x39/0x3A for selector 0..20.
        if "died_at" not in OUT:
            for sel in range(21):
                ok = True
                for msg, tag in ((0x38, "c38"), (0x39, "c39"), (0x3A, "c3a")):
                    if not grp(
                        smu,
                        OUT,
                        "%s_sel_%02d" % (tag, sel),
                        lambda m=msg, s=sel: smu.send_message(3, m, [s]),
                    ):
                        OUT["died_at"] = "%s_sel_%02d" % (tag, sel)
                        ok = False
                        break
                if not ok:
                    break

        # SoC DPM clocks (q3 0x42) and per-core freq (q3 0x43).
        if "died_at" not in OUT:
            for i in range(8):
                if not grp(
                    smu,
                    OUT,
                    "socdpm_%d" % i,
                    lambda i=i: smu.send_message(3, 0x42, [(i & 0xFFFF) << 16]),
                ):
                    OUT["died_at"] = "socdpm_%d" % i
                    break
        if "died_at" not in OUT:
            for c in range(8):
                if not grp(
                    smu,
                    OUT,
                    "corefreq_%d" % c,
                    lambda c=c: smu.send_message(3, 0x43, [c]),
                ):
                    OUT["died_at"] = "corefreq_%d" % c
                    break

        # Q0 queries: gfx clock (0x0F), SoC clock DPM (0x11), DF pstate (0x13).
        if "died_at" not in OUT:
            grp(smu, OUT, "q0_gfxclk", lambda: smu.send_message(0, 0x0F))
            for i in range(4):
                if not grp(
                    smu,
                    OUT,
                    "q0_socclk_%d" % i,
                    lambda i=i: smu.send_message(0, 0x11, [(i & 0xFFFF) << 16]),
                ):
                    OUT["died_at"] = "q0_socclk_%d" % i
                    break
        if "died_at" not in OUT:
            grp(smu, OUT, "q0_df_pstate", lambda: smu.send_message(0, 0x13))
            grp(smu, OUT, "q0_gfx_freq_37", lambda: smu.send_message(0, 0x37))
            grp(smu, OUT, "q0_gfx_vid_38", lambda: smu.send_message(0, 0x38))

        # Current voltages (q3 0x36/0x37).
        if "died_at" not in OUT:
            grp(smu, OUT, "q3_cpu_volt_36", lambda: smu.send_message(3, 0x36))
            grp(smu, OUT, "q3_gpu_volt_37", lambda: smu.send_message(3, 0x37))

        OUT["alive_after"] = smu.alive()
    finally:
        try:
            smu.close()
        except Exception:  # noqa: BLE001
            pass

    path = "/home/OWNER/vcn_unlock/probe4l2_%s.json" % time.strftime("%H%M%S")
    with open(path, "w") as fh:
        json.dump(OUT, fh, indent=2)
    print(json.dumps(OUT, indent=2))
    print("saved:", path, flush=True)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    raise SystemExit(main())
