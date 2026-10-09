# CLV phase-2 token record-lifetime reconciliation — intent

Timestamp: 2026-09-20T05:47:00+05:00 (+05:00)
Actor: sync_stage2_consumer executor
Target: resolve the canonical-matrix contradiction by tracking the record cursor and exact token/value destination stores for records `0x1331` and `0x1332` across complete Cbs and SMU serializer windows.

Next executable action: run `evidence/firmware-audit/20260920-clv-sync-stage2-record-lifetime/record_lifetime_verify.py`; produce chronological instruction rows showing token header write, Setup source load, value store, and cursor advance for both modules.

Inputs: pinned clv ROM SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`; canonical matrix read-only; exact CbsBasePei and AmdNbioSmuV10Pei bodies/instruction metadata.

Expected effect: own record-lifetime evidence/report/log only. No firmware, ROM, hardware, shared plan/memory, Ghidra/Cutter/MCP, candidate, installation, voltage or settings changes.

Rollback: remove only this unique evidence directory, report and action log.

## Observed result

Timestamp: 2026-09-20T05:51:00+05:00 (+05:00).

Final command:

```text
python3 -B evidence/firmware-audit/20260920-clv-sync-stage2-record-lifetime/record_lifetime_verify.py
```

Exit status: `0`; `58/58` checks passed. Complete token/value/cursor chronology was captured for both IDs in CbsBasePei and AmdNbioSmuV10Pei. Exact same-record destinations prove the source split; canonical matrix semantic mapping remains contradictory.

Correction retained: token-store byte assertion was shortened to the exact `66 89 10` instruction length. No source, ROM or prior artifact changed.

## Manifest and final readback

Timestamp: 2026-09-20T05:52:00+05:00 (+05:00).

`sha256sum -c evidence/firmware-audit/20260920-clv-sync-stage2-record-lifetime/SHA256SUMS` exited `0`; all three own entries returned `OK`. Final hashes:

```text
612a39639e1242bf2d40008a481522e903994f1a91fab29b52ff932ae4863adc  evidence/firmware-audit/20260920-clv-sync-stage2-record-lifetime/record_lifetime_verify.py
2faaca7f458a0c04fa69b3f1f1d4c9048df7d5ae851a088338812c1aee2879b2  evidence/firmware-audit/20260920-clv-sync-stage2-record-lifetime/record-lifetime-result.json
d1706f3ad76610175f247c12202fd71fb186234ea61f6d7e603bd39c371e3f24  docs/research/20260920-clv-sync-stage2-record-lifetime.md
```

Final verifier rerun: exit `0`, stderr empty, `58/58` checks passed. Complete record lifetimes match across Cbs and SMU; canonical matrix/source contradiction remains explicit.
