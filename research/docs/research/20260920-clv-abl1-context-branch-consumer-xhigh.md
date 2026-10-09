# Exact CLV ABL1 context+0x78 consequent branches and callback boundary

## Current

The completed 59-check reader-output result was reused by hash only. This fresh bounded trace starts at exact ABL1 `0x107E4` and follows all three consequent paths through the first closest callee, `0x10958`. No prior verifier was rerun as the progress operation.

## Conclusion

The field is consumed as policy/timing-selection data and dispatched indirectly; direct hardware programming is not proven.

1. `0x107E4` loads the halfword at `[R4+0x78]`.
2. If it equals raw immediate `0x3E8`, control reaches `0x107FA`; R5/R6/R7 comparisons select `R2=0x264` (`0x107FE`) or `R2=0x464` (`0x10808`), then converge at `0x1081E` and call the dispatcher at `0x10820`.
3. If it equals raw immediate `0x4B0`, control reaches `0x1080E`; R5/R7/R6 comparisons select `R2=0x260` (`0x10816`), then converge at `0x1081E` and call the dispatcher at `0x10820`.
4. Otherwise `0x107F8 -> 0x1081C` selects `R2=0` and converges at `0x1081E`.
5. The convergent path first calls `0x10958` at `0x10820` with `R0=context`, incoming `R1=0x61E`, and branch-selected incoming `R2` in `{0,0x260,0x264,0x464}`. Dispatcher `0x10958` presents `R1=1`, `R2=0x61E`, and `R3=branch-selected value` to an indirect `BX R12` callback.
6. The subsequent direct stores are through a pointer in the context: `0x10854` forms `R4=context+0x2C4`; `0x1085A` loads `R1=[R4]`; `STRH R0,[R1+0x06/+0x44/+0x46/+0x4C]` occurs at `0x1085C/0x10864/0x1086E/0x10878`; `0x1087E` restores `R4`. This is an in-memory child object with unknown semantics/address mapping, not evidence of MMIO.
7. Exact closest callee `0x10958` loads a callback pointer from `[R0+0x660]`, moves incoming arguments (`R1 -> R2`, `R2 -> R3`), sets `R1=1`, and branches through `BX R12`. There is no direct MMIO/register store in this callee; its callback target/effect remains unresolved.

Therefore the observed path is configuration/timing-selection dataflow into an indirect callback and an indirect child data object. It does not prove hardware-register programming, a clock value's units, or a physical clock effect.

## Reproduction

```text
python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-context-branch-consumer-xhigh/abl1_context_branch_consumer_verify.py
```

Observed stdout:

```json
{
  "status": "PASS",
  "checks": 89,
  "branch": {
    "field_load": "0x107E4 LDRH R0,[R4,#0x78]",
    "compare_0x3e8": "taken path 0x107FA -> 0x107FE -> 0x10802 -> 0x1081E; selects R2=0x264 or R2=0x464 after R5 comparisons",
    "compare_0x4b0": "taken path 0x1080E -> 0x10816 -> 0x1081E; selects R2=0x260 when R5 matches R7 or R6",
    "default": "0x107F8 -> 0x1081C -> 0x1081E; selects R2=0",
    "first_dispatch_arguments": "R0=context; prior R1=0x61E; branch-selected prior R2 in {0,0x260,0x264,0x464}; dispatcher 0x10958 presents R1=1, R2=0x61E, R3=branch-selected prior R2 to BX R12 target",
    "convergent_calls": [
      "0x10820",
      "0x1082C",
      "0x10838",
      "0x10844",
      "0x10850",
      "0x10890",
      "0x108A0",
      "0x108B8",
      "0x108CA",
      "0x108FC",
      "0x10946"
    ],
    "context_data_writes": {
      "pointer_source": "R4 = context + 0x2C4 at 0x10854; R1 = [R4] at 0x1085A",
      "stores": [
        "STRH R0,[R1+0x06] at 0x1085C",
        "STRH R0,[R1+0x44] at 0x10864",
        "STRH R0,[R1+0x46] at 0x1086E",
        "STRH R0,[R1+0x4C] at 0x10878"
      ],
      "classification": "stores through the pointer stored at context+0x2C4 into an in-memory child object; exact semantics/address mapping unknown; not direct MMIO evidence",
      "context_base_restored": "R4 -= 0x2C4 at 0x1087E"
    },
    "indirect_dispatcher": "0x10958 loads callback [R0+0x660], maps incoming R1 -> R2 and R2 -> R3, sets R1=1, and BX R12; no direct MMIO/register write is present in this callee",
    "classification": "configuration/timing-selection values are passed through an indirect callback and written to a child data object; no direct hardware-register programming is present in this bounded path. Callback target/effect remains unresolved because the context object's [R0+0x660] value is not bound to this call site."
  }
}
```

Observed stderr: empty. Exit status: `0`. Fresh checks: `89/89 PASS`.

## Inputs and hashes

- Exact ABL1: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin` — SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Exact Thumb listing: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt` — SHA-256 `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`.
- Prior reader-output result reused by hash only: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-output-context-xhigh/abl1-reader-output-context-result.json` — SHA-256 `6abae87817c9aa5baf8565524b071f5fae6d19ad5e478d140e22fdea0da42c21`.

## Owned artifacts

- Verifier: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-context-branch-consumer-xhigh/abl1_context_branch_consumer_verify.py`.
- Machine result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-context-branch-consumer-xhigh/abl1-context-branch-consumer-result.json`.
- Literal stdout/stderr: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-context-branch-consumer-xhigh/verifier.stdout` and `verifier.stderr`.
- Procoder check log: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-context-branch-consumer-xhigh/procoder-check.log`.
- Action log: `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-20-clv-abl1-context-branch-consumer-xhigh.md`.

## Limits and checks

- PASS: exact ABL1/listing/prior-result hashes.
- PASS: 89 raw-byte and listing/dataflow assertions, including the child-pointer load/store path and dispatcher argument mapping.
- PASS: all three consequent branch paths, child-pointer stores, and closest indirect dispatcher bounded.
- PASS: path-scoped Procoder check exit `0`, with `0 unformatted`, `0 unchecked`, `0 out of scope`, and `0 blocking`; broad repository hygiene notices remain non-blocking. Python tests were not collected (`0 passed, 0 failed`), so tests are unrun, not passed.
- UNRUN: callback target execution, loader/base mapping, firmware runtime, hardware behavior, physical clocks, training, or frequency-unit interpretation.

No firmware, hardware, settings, memory, shared plan, MCP/Cutter, install, global configuration, candidate, source or commit changed. Rollback is removal of this uniquely named evidence/report/action-log set.
