# CLV ABL1 SVC#4 descriptor-table source — intent

- Timestamp: 2026-09-20T13:03:00+05:00 (Asia/Almaty; shell execution timestamp to be appended)
- Actor: subagent `/root/svc4_register_target`
- Scope: follow only the exact ABL1 source of the descriptor table read by callback index `0x61E`; distinguish in-payload fallback initialization from an existing/runtime HEAP record; do not claim a physical address absent exact slot bytes.
- Target inputs (read-only): exact payload `evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`; exact listing `evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt`; current read-only SVC4 R1 result `evidence/firmware-audit/20260920-clv-abl1-svc4-r1-target-xhigh/svc4-r1-target-result.json`; prior heap reports `docs/research/20260920-clv-abl1-runtime-heap-boundary.md` and `docs/research/20260920-clv-abl1-runtime-heap-followup.md`.
- ISA/base: Thumb-2, exact payload-relative addresses, header `load_address=0`; no physical runtime base assumed.
- Planned check: hash-pinned bounded verifier of function `0xB228` only (HEAP lookup key `0x01240000`, fallback allocation, `0x652`-entry zeroing and static initializer edge), and its use of `context+0x44`; verify no numeric runtime slot value is claimed. Reuse—not rerun—the prior SVC4 mapping/R1 verifier result.
- Expected effect: new verifier, machine report/result, literal stdout/stderr, manifest, and this action log only. No firmware/hardware/settings/shared plan/memory/MCP/Cutter/install/global config writes.
- Rollback: remove only `evidence/firmware-audit/20260920-clv-abl1-svc4-descriptor-source-xhigh/`, its report, and this action log.

## Execution/result addendum

- Final bounded verifier command: `python3 -B evidence/firmware-audit/20260920-clv-abl1-svc4-descriptor-source-xhigh/verify_descriptor_source.py > evidence/firmware-audit/20260920-clv-abl1-svc4-descriptor-source-xhigh/verifier.stdout 2> evidence/firmware-audit/20260920-clv-abl1-svc4-descriptor-source-xhigh/verifier.stderr`.
- Final observed exit `0`, stdout `PASS`, `75/75` checks, stderr empty. Earlier checker-only failures were retained: first execution exit `1` from 5 raw-byte/listing expectation transcription errors; second execution exit `1` from 4 more checker expectations. No pinned input changed; final verifier uses the observed little-endian bytes and correct listing offsets.
- Reused (not rerun) R1 result identity: `05fa26427c0d969a11d3779714089943d01421780beebbe8b62b910661eeecca`.
- Exact raw observations: fallback allocator request key `0x01240000`, size `0x26C0`, type `4`; install pointer at `context+0x44`; zero `0x652` dwords; candidate pointer-relative static stores include literal `0x006D17C0` via `R1+0x1878` and `0x0800027C` via `R1+0x1B44`. This pass does not bind that distant initializer `R1` to the context+0x44 table base.
- Exact context-byte provider: `0x109D8` loads callback pointer `[R4+0x3B0]`, `0x109E0` calls it with an output pointer, `0x109E6` stores the returned byte to `[R4+0x49]`; therefore numeric R4 is dynamic. Conditional candidate descriptor kind-1 formula gives `R4=0x5027C` only for the candidate descriptor plus `context+0x49=0` and does not identify a physical register.
- Exact map-query output: empty for `0x5027C` across `docs/research/`, `docs/action-logs/`, and `memory/`; no map correlation was established.
- Evidence/report/action paths were reopened and hashes recorded in `SHA256SUMS.final`; no firmware/hardware/settings/source-input/shared-plan/memory/global-config/MCP/Cutter/install/commit changes.
- Rollback: remove only the unique evidence directory, this report, and this action log.

## Supplemental static map-correlation intent

- Scope extension (read-only, same bound target): compare the conditional kind-1 `R4` numeric example from the raw ABL1 callback formula with the already retained exact-clv SMU map statement in `docs/research/2026-09-20-oc-df-init-route.md`; retain that the runtime context byte is callback-sourced. The existing project analysis is reused by hash/text anchor, not rerun or promoted to hardware semantics.
- New bounded check: hash the exact map report and ABL1, validate the ABL byte-derived candidate descriptor literals and formula, and record whether `d=0` makes the candidate base coincide with the SMU row+0x20 static address.
- Expected effect: one supplemental verifier/result/stdout/stderr only in the current uniquely named evidence directory. No firmware/hardware/settings/plan/memory changes.

## G7 correction — exact map hit and conditional match

The prior wording in this report/action-log that the exact local query for `0x5027C` was empty/no-hit is withdrawn. Reopening `map-match-query.txt` shows the targeted match at line50 of `docs/research/2026-09-20-oc-df-init-route.md` (SHA-256 `3122a0dce28bc61942a22d567acdc29e318a714097b48877eb0391094a7d0e43`): static function `0x1EF18` writes `row+0x20` at address bases `0x5027C` and `0x5227C`, with slot/mask offsets. The earlier “no match” statement is a search/reporting error; no input bytes changed.

Supplemental bounded command: `python3 -B evidence/firmware-audit/20260920-clv-abl1-svc4-descriptor-source-xhigh/verify_map_candidate.py > evidence/firmware-audit/20260920-clv-abl1-svc4-descriptor-source-xhigh/map-candidate.stdout 2> evidence/firmware-audit/20260920-clv-abl1-svc4-descriptor-source-xhigh/map-candidate.stderr`. Observed exit0, PASS, `18/18` checks, stderr empty. Reused exact raw candidate constants and dynamic `context+0x49` source; no full 58/75-check re-run occurred.

Qualified result: candidate fallback literal `0x0800027C` plus the exact kind-1 formula would produce base `R4=0x5027C` if the relevant `context+0x44` table-base binding is correct and dynamic `context+0x49` equals0. That condition lands on the existing exact map's `row+0x20` address base. The callback byte is runtime sourced from `[context+0x3B0]`; table-body/active-callback identity and SVC#4 translation remain unresolved. No physical register or hardware effect is claimed.
