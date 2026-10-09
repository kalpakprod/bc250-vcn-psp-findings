# CLV phase-2 all-field record-lifetime reconciliation — intent

Timestamp: 2026-09-20T05:55:00+05:00 (+05:00)
Actor: sync_stage2_consumer executor
Target: apply destination/cursor lifetime tracing to remaining Setup fields `+0x316`, `+0x330`, `+0x703`, `+0x704`, `+0x36D`, and `+0x368` in both exact CbsBasePei and AmdNbioSmuV10Pei serializers.

Next executable action: run `evidence/firmware-audit/20260920-clv-sync-stage2-record-lifetime-all-fields/all_fields_verify.py`; discover each field's actual token, same-record value store and cursor advance without trusting historical matrix labels.

Inputs: pinned clv ROM SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`; exact module bodies/instruction metadata; canonical matrix read-only.

Expected effect: own supplemental record-lifetime evidence/report/log only. No firmware, ROM, hardware, shared plan/memory, Ghidra/Cutter/MCP, candidate, installation, voltage or settings changes.

Rollback: remove only this unique evidence directory, report and action log.

## Observed result

Timestamp: 2026-09-20T05:57:00+05:00 (+05:00).

Final command:

```text
python3 -B evidence/firmware-audit/20260920-clv-sync-stage2-record-lifetime-all-fields/all_fields_verify.py
```

Exit status: `0`; `29/29` checks passed. Cbs and SMU analogs agree on all six field→token mappings and cursor lifetimes. The `+0x6A3/+0x1332` contradiction remains explicit from the prior reconciliation.

Corrections retained: non-record Setup loads without nearby token headers were filtered; field-token comparison ignores module-specific RVAs and compares IDs; malformed embedded expected ROM string was unused and did not affect the pinned hash check. No inputs or prior artifacts changed.

## Manifest and final readback

Timestamp: 2026-09-20T05:58:00+05:00 (+05:00).

`sha256sum -c evidence/firmware-audit/20260920-clv-sync-stage2-record-lifetime-all-fields/SHA256SUMS` exited `0`; all three own entries returned `OK`. Final hashes:

```text
568105f8dfd3a364f62e4ffec16d043327a3671a7cfaafc61777e73b7f6e5c69  evidence/firmware-audit/20260920-clv-sync-stage2-record-lifetime-all-fields/all_fields_verify.py
7f865e2a018c9be7f665e01286473593582967808963d8bb29c112514840fbbf  evidence/firmware-audit/20260920-clv-sync-stage2-record-lifetime-all-fields/all-fields-result.json
7ea52e605142d020ecdf32a0889333472adc217d73dd98a3badc452d3b76dac7  docs/research/20260920-clv-sync-stage2-record-lifetime-all-fields.md
```

Final verifier rerun: exit `0`, stderr empty, `29/29` checks passed. All six remaining claims now have same-record token/value/cursor ownership in both serializer modules.
