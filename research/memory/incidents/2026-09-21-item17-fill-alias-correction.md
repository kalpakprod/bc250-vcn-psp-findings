# CLV ABL1 item-0x17 gate may be changed by dynamic fill — correction

Date: 2026-09-21
Scope: exact CLV ABL1 `0x95FC` local dataflow; static analysis only.

Earlier item-0x17 notes treated helper `0x6D10` returning `1` and `0x6C20` storing it at `[SP+0x164]` as sufficient to claim the `0x9646 -> 0x9744 -> 0x984E` branch. This is corrected. Before the `0x9644` compare, `0x95FC` calls helper `0x6B78` at `0x963A` with destination `R4+0x278`, fill byte `0xFF`, and length `0x40`. The buffer containing the gate starts at `SP+0x160` and extends through `SP+0x178`; no exact runtime relation establishes that `R4+0x278..R4+0x2B7` is disjoint from that stack range.

Therefore the gate value is initially `1`, but branch `0x9646 -> 0x9744 -> 0x984E`, the ensuing runtime-table U16 read and `context+0x2BC` write at `0x989A`, and any downstream aggregate path are conditional on non-alias/no-clobber. The prior 47-/136-check results validate byte patterns/control-flow decoding only and did not establish the dynamic address relation. Independent review `docs/research/2026-09-21-item17-reachability-review.md` and `evidence/firmware-audit/20260921-item17-reachability-review/item17-reachability-result.json` report `128/128 PASS` and explicitly classify DD4 reachability as conditional/unresolved.

No loader-base proof, runtime execution, clock unit, training effect, hardware behavior, or SVC handler semantics follows. The candidate base `0x57100` remains conditional static coherence only.

Evidence references:

- Independent review report: `docs/research/2026-09-21-item17-reachability-review.md`.
- Independent machine result SHA-256: `5d5599f220425829401bc86fcf1ff0d20eb96907e4d1fa96b8dd010f428cca26`.
- New bounded consumer trace: `docs/research/2026-09-21-abl-item17-reachable-output.md` and `evidence/firmware-audit/20260921-abl-item17-reachable-output/`.
