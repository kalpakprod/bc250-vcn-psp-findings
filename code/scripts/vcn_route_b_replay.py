#!/usr/bin/env python3
"""Route-B host-side VCN bring-up replay for BC-250 (goal-session 2026-09-25).

Runs the emu/OVMF-validated 24-step VCN bring-up tail from LINUX RUNTIME (after
full SoC init), NOT inside the BIOS — because the last session proved the in-DXE
driver (v003b/c/e) hangs early init by poking SMN before AGESA is done
(docs/action-logs/2026-09-24-v003b-route-b.md). Host-side after init is the
carrier the log itself recommends.

Source of the write list: evidence/firmware-audit/20260924-plan-consumers/
vcn_replay_writes.json (emu phase-2, 8865 steps, completed). v1 SKIPS: step 1
(0x0220FE00 read-unsafe), step 7 (0x01D80814 0x01D8 read-ban), step 24 (pump,
identity unknown). Transport: SMU mailbox smn_write32 (0x28/0x29 pair) +
smn_read32 (0x2A). ABORT GUARDS: alive() before/after each write; poll timeout
(250 ms) -> abort, never hang; readback-verify each RMW.

WRITE EXPERIMENT — can wedge the SMU (cold-cycle recovery). Requires
--i-am-at-the-power-button. Default prints the plan and exits.

Definition of success: after the replay, a VCN power/status register (via the
SMU SMN read, VCN base from ip_discovery 0x7800/0x7E00/0x02403000) reads
non-0xffffffff and the enable/ready bits set. NOT proof of decode; that is the
next step (amdgpu bc250_vcn_mode=hardware kernel).
"""

import argparse
import json
import sys
import time

sys.path.insert(0, "/root/vcn-t67")

POLL_TIMEOUT_S = 0.25


def _alive_or_die(smu, where, out):
    if not smu.alive():
        out["ABORTED"] = "SMU wedged at %s - cold cycle" % where
        raise SystemExit(_report(out, 2))


def _report(out, code):
    print(json.dumps(out, indent=2))
    return code


def _rmw(smu, addr, fn, out, tag):
    old = smu.smn_read32(addr)
    new = fn(old)
    smu.smn_write32(addr, new)
    back = smu.smn_read32(addr)
    out["writes"].append(
        {
            "step": tag,
            "addr": "0x%08x" % addr,
            "old": "0x%08x" % old,
            "wrote": "0x%08x" % new,
            "readback": "0x%08x" % back,
            "verified": (back == new) or (back & new) == new,
        }
    )
    return back


def _w(smu, addr, val, out, tag):
    smu.smn_write32(addr, val)
    back = smu.smn_read32(addr)
    out["writes"].append(
        {
            "step": tag,
            "addr": "0x%08x" % addr,
            "wrote": "0x%08x" % val,
            "readback": "0x%08x" % back,
        }
    )
    return back


def _poll(smu, addr, mask, out, tag):
    t0 = time.monotonic()
    while time.monotonic() - t0 < POLL_TIMEOUT_S:
        v = smu.smn_read32(addr)
        if v & mask:
            out["writes"].append(
                {
                    "step": tag,
                    "poll": "0x%08x" % addr,
                    "mask": "0x%x" % mask,
                    "value": "0x%08x" % v,
                    "passed": True,
                }
            )
            return True
    out["writes"].append(
        {
            "step": tag,
            "poll": "0x%08x" % addr,
            "mask": "0x%x" % mask,
            "passed": False,
            "ABORT": "poll timeout",
        }
    )
    return False


def run(smu, with_01d8=False) -> dict:
    out = {
        "experiment": "vcn-route-b-host-replay-%s" % ("v2-01d8" if with_01d8 else "v1"),
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "writes": [],
    }
    out["alive_before"] = smu.alive()
    if not out["alive_before"]:
        out["error"] = "SMU not alive - cold cycle"
        return out

    # step 2-6: gate-mode releases (0x0115A3xx family)
    _rmw(smu, 0x0115A320, lambda r: r & ~2, out, "2")
    _alive_or_die(smu, "step2", out)
    _rmw(smu, 0x0115A334, lambda r: r | 0x30, out, "3")
    _alive_or_die(smu, "step3", out)
    _rmw(smu, 0x0115A330, lambda r: (r & ~0xE) | 1, out, "4")
    _alive_or_die(smu, "step4", out)
    time.sleep(0.01)  # step 5 settle delay
    _rmw(smu, 0x0115A32C, lambda r: (r & ~7) | 0x17, out, "6")
    _alive_or_die(smu, "step6", out)
    # step 7: 0x01D80814 = 2 (VCN power-island enable). BLIND write (0x01D8 reads banned).
    # ONLY 0x01D80814 - NEVER 0x01D80218 (the measured SMU-killer). operator-authorized.
    if with_01d8:
        smu.smn_write32(0x01D80814, 2)
        out["writes"].append(
            {
                "step": "7",
                "addr": "0x01d80814",
                "wrote": "0x2",
                "note": "0x01D8 power-island enable, blind write, operator-authorized",
            }
        )
        time.sleep(0.01)
        _alive_or_die(smu, "step7", out)

    # step 8-13: builder TAIL only (preserve boot fields; RMW the enable bit)
    _rmw(smu, 0x0115F808, lambda r: r | 1, out, "8")
    _alive_or_die(smu, "step8", out)
    _w(smu, 0x0115F818, 1, out, "9")
    _alive_or_die(smu, "step9", out)
    if not _poll(smu, 0x0115F964, 0x100, out, "10"):
        out["ABORTED"] = "step10 PLL-ready poll timeout"
        return out
    _w(smu, 0x0115F958, 0x00010000, out, "11")
    _alive_or_die(smu, "step11", out)
    _rmw(smu, 0x0115F95C, lambda r: r | 0x0004C000, out, "12")
    _alive_or_die(smu, "step12", out)
    _w(smu, 0x0115F974, 0, out, "13")
    _alive_or_die(smu, "step13", out)

    # step 14-17: power steps (float-ratio 0 -> min PLL state, emu code 0x3F)
    _w(smu, 0x0115F8FC, 0x3F, out, "14")
    _alive_or_die(smu, "step14", out)
    if not _poll(smu, 0x0115F920, 0x10000, out, "15"):
        out["ABORTED"] = "step15 power-step ack timeout"
        return out
    _w(smu, 0x0115F924, 0x3F, out, "16")
    _alive_or_die(smu, "step16", out)
    if not _poll(smu, 0x0115F948, 0x10000, out, "17"):
        out["ABORTED"] = "step17 power-step ack timeout"
        return out

    # step 18-23: enable block + handshake (0x0100Bxxx) + final
    _w(smu, 0x0100B004, 1, out, "18")
    _alive_or_die(smu, "step18", out)
    _w(smu, 0x0100B008, 1, out, "19")
    _alive_or_die(smu, "step19", out)
    _w(smu, 0x0100B2E0, 0xF, out, "20")
    _alive_or_die(smu, "step20", out)
    _w(smu, 0x0100B00C, 0x75767570, out, "21")
    _alive_or_die(smu, "step21", out)
    _rmw(smu, 0x0100B034, lambda r: r | 1, out, "22")
    _alive_or_die(smu, "step22", out)
    _poll(smu, 0x0100B034, 0x2, out, "22-hs")
    _rmw(smu, 0x0115A338, lambda r: r | 1, out, "23")
    _alive_or_die(smu, "step23", out)
    # step 24 (pump) SKIPPED (v1)

    out["alive_after"] = smu.alive()
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--run",
        action="store_true",
        help="execute the write replay (needs the button flag)",
    )
    ap.add_argument("--i-am-at-the-power-button", action="store_true")
    ap.add_argument(
        "--with-01d8",
        action="store_true",
        help="v2: add step 7 (0x01D80814=2), operator-authorized killer-region write",
    )
    a = ap.parse_args()
    if not a.run:
        print("plan: 21 writes/RMW + 4 polls to 0x0115A3xx/0x0115Fxxx/0x0100Bxxx.")
        print(
            "SKIPS(v1): 0x0220FE00, 0x01D80814, pump. Guards: alive+readback+250ms poll-abort."
        )
        print(
            "Run with: --run --i-am-at-the-power-button (WRITE experiment; can wedge)."
        )
        return 0
    if not a.i_am_at_the_power_button:
        print("REFUSED: writes need --i-am-at-the-power-button", file=sys.stderr)
        return 3
    from bc250_smu import Bc250Smu

    smu = Bc250Smu()
    out = {"experiment": "vcn-route-b-host-replay", "writes": []}
    try:
        out = run(smu, with_01d8=a.with_01d8)
        return _report(out, 0 if out.get("alive_after") else 2)
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001 - clean abort on wedge/timeout
        out["EXCEPTION"] = repr(e)
        try:
            out["alive_after_exc"] = smu.alive()
        except Exception:  # noqa: BLE001
            out["alive_after_exc"] = "unknown (mailbox dead)"
        return _report(out, 2)
    finally:
        try:
            smu.close()
        except Exception:  # noqa: BLE001
            pass


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    raise SystemExit(main())
