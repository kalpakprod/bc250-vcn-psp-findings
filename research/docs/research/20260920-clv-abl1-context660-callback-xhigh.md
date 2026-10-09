# Exact CLV ABL1 +0x660 callback candidate and ownership boundary

## Current

Fresh exact-byte verification followed one conditional callback candidate installed at an ABL1 `+0x660` slot and the closest callback body. It does **not** prove this is the callback pointer loaded by the Fclk consumer's active context: the observed installer base and the active call's current `R4` base are not statically joined.

## Findings

1. **Exact initializer store:** function `0x7378` sets `R5=arg0`; it later calls `0xAF90` with `R0=R5` at `0x74E0`. At `0xAF90`, `R4=R0` (`0xAF94`); `0xB0C2` loads pointer literal at `0xB168`, and `0xB0C4` stores it to `[R4+0x660]`. Thus the observed write is to the `R5`/parent object passed to the initializer.
2. **Conditional target map:** literal `0x00060BD9` minus candidate base `0x57100` yields Thumb pointer `0x9AD9`, with code entry `0x9AD8`. Exact target bytes at `0x9AD8` are the `push.w` prologue `2d e9 ff 4f`. Adjacent literals in the same initializer map to additional local code anchors (`0xB16C -> 0x10C54`, `0xB170 -> 0x9A30`, `0xB174 -> 0x9A8C`); the previously validated four independent anchors also match. This supports `0x57100` as a **conditional static mapping**, not a loader/base execution proof.
3. **Active dispatcher ownership is unresolved:** the consumer at `0x10820` passes the current `R4` to dispatcher `0x10958`; that helper loads `[R0+0x660]` and branches through it. In the surrounding function, `R4` is loaded from `[R6+0x3C4]` at `0x73AE` and stored at `[R5+0x08]` at `0x73B2`, while the initializer call uses `R5`. There are explicit R4 adjustments at `0x7F4C` and `0x7FC2`, and an unresolved indirect `BLX R1` at `0x74EA`. The exact `R4` value at the later `0x8426/0x10820` call and its identity with the `R5+0x660` initializer object are not proved. A second `+0x660` store appears at `0xCABE` through `R1`, loading literal `0x006EC140` from `0xCE78`; its base owner is unknown. Under the candidate `0x57100` base this literal maps to `0x697040`, not a local ABL1 file offset, but that alone does **not** establish an external address or target.
4. **Candidate callback data effect:** if `0x9AD8` is the mapped callback, dispatcher arguments make its `R3` the selected value and `R2=0x61E` the token/index. Callback entry copies `R3 -> R11` (`0x9AE2`), indexes context table `[R5+0x44]` from low 12 bits of `R2` (`0x9AE8`), updates local stack scratch `[SP+0x14]` through bitfield operations (`0x9BFA`, `0x9D20..0x9D28`), then returns that local value from `0x9E6A`. Its direct stores in this bounded body are stack-local only. One path calls `0x6C1E`, whose exact instruction is `BX LR`; another calls `0x6DA4` with output pointer `SP+0x14`. `0x6DA4` invokes opaque `SVC #4` and copies byte/halfword/word data to the supplied output pointer. No direct MMIO/PLL write is present in this candidate callback body, but its relation to the active context remains unproved.

## G7 correction to prior checkpoint

The previous 89-check report's claim that the same `R4` base necessarily flowed unchanged from `0x7E74` to `0x8428` is withdrawn. Its no-write verifier parser misread tab-separated LLVM operands. The exact raw listing records `ADD.W R4,R4,#0x2C0` at `0x7F4C` and `SUB.W R4,R4,#0x2C0` at `0x7FC2`; the current verifier records these adjustments and does not claim same-object identity. The prior machine result remains preserved; this supplemental result is authoritative for the callback/ownership question.

## Reproduction

```text
python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-context660-callback-xhigh/abl1_context660_callback_verify.py
```

Observed stdout:

```json
{
  "status": "PASS",
  "checks": 97,
  "pointer_map": {
    "literal_site": "0xB168",
    "pointer_literal": "0x00060BD9",
    "candidate_base": "0x57100 (conditional static mapping, not loader proof)",
    "thumb_target": "0x9AD9",
    "local_code_entry": "0x9AD8",
    "independent_prior_anchor_count": 4,
    "same_initializer_adjacent_anchors": [
      "0xB16C->0x10C54",
      "0xB170->0x9A30",
      "0xB174->0x9A8C"
    ]
  },
  "ownership": {
    "initializer_call": "0x74DE R0=R5; 0x74E0 BL 0xAF90; 0xAF94 R4=R0; 0xB0C4 stores [initializer R4+0x660], so the slot base is parent R5",
    "active_dispatch": "0x73AE loads a child pointer candidate from [R6+0x3C4] into R4; 0x73B2 stores that pointer at [R5+8]. At 0x8426 the current R4 is passed to 0x10200, and 0x10958 later loads [current R0+0x660]. The exact current value at 0x8426 is not reconstructed here.",
    "intervening_register_fact": "raw instructions 0x7F4C and 0x7FC2 explicitly add/subtract 0x2C0 from R4 in the parent span; this verifier does not prove these adjustments restore the same child pointer on the path to 0x8426",
    "prior_context_alias_claim": "the prior 89-check result claimed the same R4 base at 0x7E74 and 0x8428 using a no-write scan; that scanner was malformed and the claim is withdrawn",
    "identity": "not proven: installer base is parent R5; active dispatcher receives the current R4 at 0x8426. R4 is set from an R6+0x3C4 child-pointer load at 0x73AE and has later explicit adjustments; no direct dataflow links that slot to the B0C4-installed +0x660, and BLX R1 at 0x74EA is unresolved."
  },
  "callback_effect": {
    "input_mapping": "branch-selected incoming R2 at 0x10958 becomes callback R3; callback 0x9AD8 copies R3 into R11 at 0x9AE2",
    "token_mapping": "incoming dispatcher R1=0x61E becomes callback R2; 0x9AE8 extracts low 12 bits and indexes [R5+0x44]",
    "local_state": "R11 can be stored in [SP+0x14] at 0x9BFA and transformed by bitfield sequence 0x9D20..0x9D28; return path reloads [SP+0x14] into R0 at 0x9E6A",
    "helper_effect": "0x9D38 calls 0x6C1E, whose exact instruction is BX LR. Another path calls 0x6DA4 with R2=SP+0x14; the helper uses SVC #4 then copies byte/halfword/word into the supplied output pointer. SVC #4 mapping semantics remain opaque.",
    "direct_write_class": "candidate callback direct stores are to its stack frame; no direct MMIO or PLL write is present in this bounded callback body"
  },
  "claim_boundary": "A candidate initializer literal maps to exact local callback code under the conditional 0x57100 base and has validating anchors. Exact identity between the installed parent-object slot and the active child-object [R4+0x660] dispatch slot is not proven. Therefore the callback candidate is not asserted to be the callback actually invoked for Fclk; neither callback hardware effect nor MCLK=UCLK=FCLK is established."
}
```

Observed stderr: empty. Exit status: `0`. Fresh raw-byte/listing assertions: `97/97 PASS`.

## Exact inputs and hashes

- ROM: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` — SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Exact ABL1: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin` — SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Exact Thumb listing: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt` — SHA-256 `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`.
- Prior accepted branch-consumer result (hash reused): `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-context-branch-consumer-xhigh/abl1-context-branch-consumer-result.json` — SHA-256 `269049d9fb13f32dbf8c037f85ebfe695fd5099e37fe354e8b2a939d1c4cf671`.
- Prior conditional-base evidence: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-producer-trace-result.json` — SHA-256 `d9b40965d4901df0544e460da7e16ac30b4ccd4cd97b07d2de2ec8b1afddf5f8`.

## Owned artifacts

- Verifier: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-context660-callback-xhigh/abl1_context660_callback_verify.py`.
- Machine result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-context660-callback-xhigh/abl1-context660-callback-result.json`.
- Literal stdout/stderr: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-context660-callback-xhigh/verifier.stdout` and `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-context660-callback-xhigh/verifier.stderr`.
- Final path-scoped Procoder log: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-context660-callback-xhigh/procoder-check-final.log`.
- Action log: `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-20-clv-abl1-context660-callback-xhigh.md`.

## Checks and limits

- PASS: exact source hashes and prior-result identities.
- PASS: pointer literal/install bytes, conditional base arithmetic, prior and adjacent target-code anchors.
- PASS: active dispatcher register mapping and candidate callback R3/token-to-local-output path.
- PASS: final path-scoped Procoder check (`procoder-check-final.log`, exit `0`; 0 unformatted, 0 unchecked, 0 out of scope, 0 blocking; broad repository hygiene findings non-blocking). Python tests were unrun (`0 passed, 0 failed`; no tests ran).
- UNRUN/UNPROVEN: exact `R4+0x660` initializer ownership, actual callback invocation/effect, loader/base mapping, firmware runtime, hardware behavior, physical clocks, training, or `MCLK=UCLK=FCLK`.

No firmware, hardware, settings, memory, shared plan, MCP/Cutter, install, global configuration, candidate, source input or commit changed. Rollback is removal of this unique evidence directory, report, and action log.
