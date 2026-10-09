# Stage 2 — Exact ABL1 memory-policy function match

## Intent (before own evidence writes)

- Timestamp: 2026-09-20T12:18:00+05:00 (Asia/Almaty)
- Actor: delegated project executor (`gpt-5.6-luna`, xhigh; effective runtime identity not independently exposed by this shell)
- Target: exact decompressed clv ABL1 payload SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`; version-aligned historical `ABL1_decompiled.c` memory routine lead `FUN_000096fc`.
- Scope: bounded ARM/Thumb control/dataflow match around the exact function; establish one memory-speed/training structure path. No signed blob edits, firmware execution, hardware, settings, shared plan/memory, installs, commits, MCP, or children.
- Expected effect: own disassembly/verification/report/action-log only.

## Observed result

Executed ARM/Thumb-aware disassembly on the exact decompressed ABL1 payload and the own byte verifier. Exit `0`; stderr empty; `27/27` checks passed. Exact function `0x95FC` structurally matches historical `FUN_000096FC`: per-channel speed reads at structure `+0x20`, table `+0x278`, minimum reduction to `+0x2BC`, and writeback to `+0x20`. This is a concrete memory-speed policy/training structure match, but no Setup+0x316/INV edge or ratio/unit proof.

Own manifest check exited `0` with all files `OK`.
