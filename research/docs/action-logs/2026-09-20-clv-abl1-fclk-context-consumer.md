# CLV ABL1 FCLK context consumer — intent

Timestamp: 2026-09-20T09:45:00+05:00 (+05:00)
Actor: luna-xhigh bounded executor
Target: exact CLV ABL1 FCLK reader result path, from caller `0x5FAE` through reader output storage at `0x5FBA` and downstream context handling at `0x107E4`.

Bounded question: verify raw dataflow `FCLK reader stack+0x08 -> caller +0x04 -> [context+0x78]`, then follow the exact branch comparing that halfword against `0x3E8` and `0x4B0`; compare only raw APCB/IFR enum values and do not infer units.

Pinned inputs:

- ROM SHA-256 ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8.
- Exact ABL1 SHA-256 af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a.
- Exact ABL1 disassembly SHA-256 b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65.
- Existing completed FCLK branch result SHA-256 d6d053b5e4a74a5b4fe0526e4d4659d22a500601074baad751977ab21e2ecdfa.

Next executable action: run unique verifier evidence/firmware-audit/20260920-clv-abl1-fclk-context-consumer/abl1_fclk_context_consumer_verify.py.

Expected effect: new evidence/report/action-log artifacts only. No firmware, hardware, settings, shared plan/memory, global config, MCP/Cutter, candidates, source, commits, or subagents.

Rollback: remove only this unique evidence directory, report, and action log.

## Correction after verifier execution

Timestamp: 2026-09-20T09:50:00+05:00 (+05:00)
Observed execution error: FCLK stack reload halfword was transcribed in disassembly order; exact raw bytes at `0x5FB2` are `01 9B`.

Correction: update raw byte expectation only; no input changed.

## Correction after second verifier execution

Timestamp: 2026-09-20T09:51:00+05:00 (+05:00)
Observed execution error: context-base movement window used display order; exact raw bytes at `0x5FB4..0x5FB9` are `00 21 42 A2 30 46`.

Correction: update only raw expectation.

## Correction after third verifier execution

Timestamp: 2026-09-20T09:52:00+05:00 (+05:00)
Observed execution error: post-store call check expected six bytes for a four-byte selected span; exact raw call bytes are `fb f7 a5 f9`.

Correction: align expected length to selected bytes.

## Correction after fourth verifier execution

Timestamp: 2026-09-20T09:53:00+05:00 (+05:00)
Observed execution error: 0x107E4 dispatch comparisons used disassembly halfword display order. Correct raw Thumb bytes are applied for all selector compares/branches (`b5 42`, `bd 42`, `01 d0`, `b5 42`, `02 d1`).

Correction: update only raw encodings.

## Correction after fifth verifier execution

Timestamp: 2026-09-20T09:54:00+05:00 (+05:00)
Observed execution error: default selector/call window used display-order `mov r0,r4` bytes. Exact raw bytes are `00 22 20 46 00 f0 9a f8`.

Correction: update raw expectation only.

## Correction after sixth verifier execution

Timestamp: 2026-09-20T09:55:00+05:00 (+05:00)
Observed execution error: separate caller edge to `0x10200` used display-order bytes; exact raw window is `10 b1 20 46 07 f0 ea fe`.

Correction: update only raw bytes.

## Correction after seventh verifier execution

Timestamp: 2026-09-20T09:56:00+05:00 (+05:00)
Observed execution error: `0x10200` prologue window used display-order bytes; exact raw bytes are `2d e9 f0 43 d9 b0 fa 49 04 46`.

Correction: update raw prologue bytes only.

## Correction after eighth verifier execution

Timestamp: 2026-09-20T09:57:00+05:00 (+05:00)
Observed execution error: `0x10200` dispatch-loop window used display-order bytes; exact raw bytes are `56 f8 35 00 48 45 a0 f2 0b 21`.

Correction: update only raw window.

## Correction after ninth verifier execution

Timestamp: 2026-09-20T09:58:00+05:00 (+05:00)
Observed execution error: all substantive checks passed, but the verifier's final assertion expected `59` while the implemented ledger contained `54`; this is a check-ledger completeness issue, not an artifact mismatch.

Correction: add five explicit ledger checks for shared field offset, threshold set, emitted selector set, default/threshold identity, and raw APCB comparison scope. No input changed.
