# Stage 2 supplemental — Memory P-state versus Phy Power Saving and FCLK_DPM

## Intent (before own evidence writes)

- Timestamp: 2026-09-20T08:35:00+05:00 (Asia/Almaty)
- Actor: delegated project executor (`gpt-5.6-luna`, xhigh; effective runtime identity not independently exposed by this shell)
- Target: exact clv donor `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`; historical ULTIMATE comparison is read-only stage-1 artifact.
- Scope: distinguish native `Memory P-state +0x36D`, `Phy Power Saving +0x368`, and `FCLK_DPM +0x6A3` by exact labels/enums/bytes and serializer record IDs. Reuse the existing exact-clv menu text and 233-module CbsBasePei instruction records; no broad parser sweep.
- Expected effect: own supplemental evidence/result/report/action-log only; no firmware, candidate, hardware, settings, voltage, shared plan/memory, installation, commit, or child-agent changes.
- Rollback: delete only this evidence/report/action-log set.

## Observed result

Executed:

```text
python3 evidence/firmware-audit/20260920-clv-sync-stage2-memory-pstate-discrimination/discrimination_verify.py > evidence/firmware-audit/20260920-clv-sync-stage2-memory-pstate-discrimination/verifier.stdout 2> evidence/firmware-audit/20260920-clv-sync-stage2-memory-pstate-discrimination/verifier.stderr
```

Observed exit status: `0`; stderr empty; `19/19` checks passed.

The exact clv, historical ULTIMATE, menu text, and CbsBasePei hashes were rechecked. The three controls are distinct: `+0x368 -> 0x1238`, `+0x36D -> 0x123D`, and `+0x6A3 -> 0x1332`. ULTIMATE sets all three to zero, so its filename cannot identify the correct DF-help field. Hardware/training semantics remain unknown.

Own evidence manifest check exited `0` with all listed files `OK`.
