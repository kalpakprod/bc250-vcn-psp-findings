# CLV ABL1 SVC#4 HEAP/fallback and context+0x40 branch — intent

- Timestamp: 2026-09-20T13:42:00+05:00 (Asia/Almaty; shell result timestamp appended)
- Actor: subagent `/root/svc4_register_target`
- Scope: one bounded exact-byte edge: resolve B228 HEAP-vs-fallback branch semantics and identify the nearest exact producer of callback context+0x40 before 0x9B82. No repeat of prior 61-check descriptor join arithmetic.
- Inputs (read-only): exact ABL1 payload/listing; prior descriptor-join result; prior exact callback report.
- Method: raw bytes/listing checks for helper 0x6374 return values, B23A/B23E branch polarity, B264/B266/B26A/B274 stores, and initializer 0x7378->0x73B8 context+0x40 source. Preserve runtime/provider boundary.
- Expected effect: create only this evidence directory, verifier/result/stdout/stderr, report, manifest, and action log. No firmware/hardware/settings/shared plan/memory/MCP/Cutter/install/global config writes.
- Rollback: remove only this evidence directory, report, and action log.

## Execution/result

- Final command: `python3 -B evidence/firmware-audit/20260920-clv-abl1-svc4-heap-context40-xhigh/verify_heap_context40.py > evidence/firmware-audit/20260920-clv-abl1-svc4-heap-context40-xhigh/verifier.stdout 2> evidence/firmware-audit/20260920-clv-abl1-svc4-heap-context40-xhigh/verifier.stderr`.
- Observed exit `0`, stdout `PASS`, `37/37` checks, stderr empty.
- Branch result: 0x6374 match returns R0=0 and takes B264/B266; no-match returns R0=2 and takes fallback B240/B252 then B26A/B274.
- Context result: function 0x7378 sets parent R5=arg0; child R4=[arg1+0x3C4]; stores [child+0x4] into [parent+0x40] at 0x73B6/0x73B8. Callback consumes [R5+0x40] at 0x9B82.
- Active dispatcher object identity remains unresolved; no physical register or hardware claim follows.
- Evidence/report/action paths reopened and hashes recorded in SHA256SUMS.final; no firmware/hardware/settings/source/shared-plan/memory/global-config/MCP/Cutter/install/commit changes.
- Rollback: remove only the unique evidence directory, report and action log.
