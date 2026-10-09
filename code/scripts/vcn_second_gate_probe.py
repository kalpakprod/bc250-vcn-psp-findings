#!/usr/bin/env python3
"""VCN second-gate probe/actuator for BC-250 (goal-session 2026-09-25).

STATUS: DRAFT. Diagnostic-read path is intended to be safe; the --powerup write
path is a GATED hardware experiment (can wedge the SMU → cold power cycle). Do
NOT run --powerup without an operator at the power button and explicit approval.

Corrected model (verified this session, see
.procoder/plans/2026-09-25-second-gate-passthrough.md):
- FUN_00023b14 is a DOMAIN STATUS/LEVEL APPLIER (reads a status word, stores a
  3-bit field and a 7-bit "level" per domain across a 27-entry table). It is NOT
  a VCN power-island enable. The community "0x23b14(6,1) powered VCN domain 6"
  therefore set a domain level/PLL, not the video block's power.
- The real Navi10 PowerUpVcn (SMU 0x233f0) does a PGFSM tile-0xc request plus
  a [<smu_win>+0x210] low-2-bits = 2 write. The BC-250 SMU lacks this logic, so
  it must be issued manually over SMN.

UNVERIFIED ADDRESS ASSUMPTIONS (must be closed by --read before any --powerup):
- A1  PGFSM request register SMN address. Navi10 uses SMU-window 0x100C784;
      the assumed BC-250 mapping (window 0x1000000 -> SMN 0x09000000) gives
      0x0900C784. Same 0x0900Cxxx family as rxl's proven cold-reset 0x0900C004.
- A2  the [0x111F600+0x210] "power-status low2=2" register on BC-250.
- A3  0x7fec (vcn2-bringup diff §2): unresolved. Left as a read target only.
Live ip_discovery VCN bases (this board): 0x7800 / 0x7E00 / 0x02403000.

Transport: /root/vcn-t67/bc250_smu (Bc250Smu). Requires patcher.py run at boot
for call(); smn_* need the secure gate open (unlock).
"""

import argparse
import json
import sys
import time

LIB_CANDIDATES = ["/root/vcn-t67", "/home/OWNER/vcn_unlock/bc250-smu-unlock"]

# --- read-only diagnostic targets (close A1/A2/A3 before any write) ---
# name, addr, note. All SMN. Read via smn_read32 (Q3 0x2A). alive() between.
READS = [
    # --- tier 0: proven-safe families first (sanity + the clock-hypothesis test) ---
    ("sanity_5a870", 0x0005A870, "known-good SMU SRAM sanity"),
    ("domain_bitmap_ccb8", 0x0000CCB8, "domain bitmap (safe family)"),
    (
        "dclk_prog_6d100",
        0x0116D100,
        "2nd-gate descr idx22: is this a real DCLK MHz value or not?",
    ),
    ("dclk_poll_6d114", 0x0116D114, "descr idx22 ack"),
    (
        "vclk_prog_6d128",
        0x0116D128,
        "2nd-gate descr idx23: VCLK window (metrics say VCLK=0)",
    ),
    ("vclk_poll_6d13c", 0x0116D13C, "descr idx23 ack"),
    ("sel_prog_6d150", 0x0116D150, "2nd-gate descr idx24: selector"),
    ("vcn_ctrl_5f800", 0x0115F800, "VCN clock-controller block base (probe4l6 family)"),
    ("vcn_ctrl_5f808", 0x0115F808, "VCN ctrl +0x08 enable"),
    ("vcn_ctrl_5f964", 0x0115F964, "VCN ctrl poll/ready bit"),
    # --- tier 1: RISKY, unverified addresses last (one at a time, alive() between) ---
    ("rsmu_coldreset_0900C004", 0x0900C004, "context: rxl proven-safe cold-reset reg"),
    ("pgfsm_req_0900C784", 0x0900C784, "A1: PGFSM request reg (ASSUMED mapping)"),
    ("pwrstatus_111F810", 0x0111F810, "A2 candidate: [win+0x210] region"),
    ("low_7fec", 0x00007FEC, "A3: unresolved 0x7fec (read only)"),
]

# corrected PowerUpVcn write sequence (GATED — not executed without approval)
FN_STATUS_LEVEL_APPLIER = 0x23B14  # NOT power; kept for A/B comparison only
FN_CLK_DOMAIN_UNGATE = 0x23744  # slots 0x16/0x17/0x18
PGFSM_REQ_SMN = 0x0900C784  # A1 (unverified)


def _load_smu():
    for p in LIB_CANDIDATES:
        sys.path.insert(0, p)
    from bc250_smu import Bc250Smu  # noqa: E402

    return Bc250Smu


def do_read(smu) -> dict:
    out = {"mode": "read", "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "reads": {}}
    out["alive_before"] = smu.alive()
    if not out["alive_before"]:
        out["error"] = "SMU not alive - cold power cycle"
        return out
    for name, addr, note in READS:
        try:
            v = smu.smn_read32(addr)
            out["reads"][name] = {
                "addr": "0x%08x" % addr,
                "value": "0x%08x" % v,
                "note": note,
            }
        except Exception as e:  # noqa: BLE001
            out["reads"][name] = {
                "addr": "0x%08x" % addr,
                "error": repr(e),
                "note": note,
            }
        if not smu.alive():
            out["reads"][name]["wedged_after"] = True
            out["stopped"] = "SMU wedged after %s - STOP" % name
            break
    out.setdefault("alive_after", smu.alive())
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    g = ap.add_mutually_exclusive_group()
    g.add_argument(
        "--read",
        action="store_true",
        help="diagnostic SMN reads only (close A1/A2/A3). alive() between, stop on wedge.",
    )
    g.add_argument(
        "--powerup",
        action="store_true",
        help="GATED write experiment - refuses without --i-am-at-the-power-button",
    )
    ap.add_argument(
        "--i-am-at-the-power-button",
        action="store_true",
        help="operator confirmation required for --powerup",
    )
    a = ap.parse_args()

    if not (a.read or a.powerup):
        print("plan:")
        print(
            "  --read    -> smn_read32 of:",
            ", ".join("%s(0x%08x)" % (n, x) for n, x, _ in READS),
        )
        print(
            "  --powerup -> corrected PowerUpVcn (PGFSM pulse @ A1) - GATED, needs approval + operator"
        )
        print(
            "NOTE: 0x23b14 is a level applier, NOT power (see docstring). Reads first, always."
        )
        return 0

    Bc250Smu = _load_smu()
    smu = Bc250Smu()
    try:
        if a.read:
            out = do_read(smu)
            print(json.dumps(out, indent=2))
            return 0 if out.get("alive_after") else 2
        # --powerup
        if not a.i_am_at_the_power_button:
            print(
                "REFUSED: --powerup needs --i-am-at-the-power-button and prior --read verifying A1.",
                file=sys.stderr,
            )
            return 3
        print(
            "REFUSED-BY-DEFAULT: write sequence intentionally not wired in this DRAFT.",
            file=sys.stderr,
        )
        print(
            "Wire it only after --read confirms A1/A2 return non-0xffffffff and the operator approves.",
            file=sys.stderr,
        )
        return 3
    finally:
        try:
            smu.close()
        except Exception:  # noqa: BLE001
            pass


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    raise SystemExit(main())
