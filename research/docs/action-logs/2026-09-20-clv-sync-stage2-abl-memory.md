# Stage 2 — Exact ABL1 memory-policy source/binary applicability

## Intent (before own evidence writes)

- Timestamp: 2026-09-20T11:42:00+05:00 (Asia/Almaty)
- Actor: delegated project executor (`gpt-5.6-luna`, xhigh; effective runtime identity not independently exposed by this shell)
- Target: exact clv ABL1 PSP type `0x31` at SPI `0x99FD00`, version `22.4.6.0`; historical version-aligned `ABL1_decompiled.c`/strings retained as provenance only.
- Scope: bounded falsification of direct source-to-current-binary applicability using exact decompression, hashes, and memory-training string/address anchors. No signed blob edit, firmware execution, hardware, settings, shared plan/memory, install, commit, MCP, or child-agent changes.
- Expected effect: own decompressed payload/anchor verifier/report/action-log only.
- Rollback: delete only this evidence/report/action-log set.

## Observed result

Executed the exact ABL1 decompression/anchor verifier. Exit `0`; stderr empty; `21/21` checks passed. The payload hash/provenance is exact, but all five version-aligned historical memory-policy string addresses mismatch the exact decompressed clv payload locations. Direct source-to-current-binary applicability is therefore UNPROVEN/blocked pending ARM function/dataflow matching; no historical source semantics were applied.

Own manifest check exited `0` with all files `OK`.
