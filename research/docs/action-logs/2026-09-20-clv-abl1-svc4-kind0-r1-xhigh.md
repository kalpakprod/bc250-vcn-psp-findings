# CLV ABL1 SVC#4 raw-kind0 R1 construction — intent

- Timestamp: 2026-09-20T14:04:00+05:00 (Asia/Almaty; exact shell result appended)
- Actor: subagent `/root/svc4_register_target`
- Scope: decode only the actual fallback chain `table[0x61E]=0x006CA7C0 -> table[0x6CA]=0x006F47C0` through callback branch conditions, raw kind-0 address construction, context+0x40 bitmask merge, and SVC#4 page/offset split.
- Inputs (read-only): exact ABL1 payload/listing; prior descriptor-join result (`61/61 PASS`) reused by hash; prior callback result reused by hash.
- Expected effect: new verifier/result/report/action log/manifest only. No generic INV census, firmware/hardware/settings/shared edits, installs or commits.
- Rollback: remove only the unique evidence directory, report and action log.

## Execution/result

- Final command: `python3 -B evidence/firmware-audit/20260920-clv-abl1-svc4-kind0-r1-xhigh/verify_kind0_r1.py > evidence/firmware-audit/20260920-clv-abl1-svc4-kind0-r1-xhigh/verifier.stdout 2> evidence/firmware-audit/20260920-clv-abl1-svc4-kind0-r1-xhigh/verifier.stderr`.
- Observed exit `0`, stdout `PASS`, `38/38` checks, stderr empty.
- Corrected prior assumption: raw kind0 path sets R4 from descriptor low12 at `0x9BEA/0x9BF0`; exact fallback value is `R4=0x7C0`, then `R1=R4` at `0x9C28`.
- Context+0x40 replacement mask is exactly `0xFFFF8000`; low15 bits, including low12 target offset, remain preserved while high kind bits may change branch selection.
- Active HEAP/fallback, runtime context+0x40, SVC#4 translation, physical target, and hardware result remain unrun/unresolved.
- Evidence/report/action paths reopened and hashes recorded in `SHA256SUMS.final`; no firmware/hardware/settings/shared edits.
- Rollback: remove only the unique evidence directory, report and action log.
