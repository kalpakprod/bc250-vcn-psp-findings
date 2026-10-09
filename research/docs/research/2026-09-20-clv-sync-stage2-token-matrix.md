# Final preventive audit — requested clock-field serializer matrix

## Canonical matrix

Independent raw-byte checks in both exact clv serializer bodies produce:

| AmdSetup field                  | Width | clv body bytes/value | CbsBasePei source load / record ID                                                  | AmdNbioSmuV10Pei source load / record ID                                            |
| ------------------------------- | ----- | -------------------- | ----------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `+0x316 MemoryClockSpeed`       | u8    | `24` / 36            | RVA `0x9857` `8a8216030000` / `0x11ED` at `0x9837`                                  | RVA `0xB8D7` `8a8216030000` / `0x11ED` at `0xB8B7`                                  |
| `+0x330 UclkDiv1M0`             | u8    | `01` / 1             | RVA `0x9CE4` `8a8230030000` / `0x1204` at `0x9CC4`                                  | RVA `0xBD64` `8a8230030000` / `0x1204` at `0xBD44`                                  |
| `+0x6A3 FclkDpm`                | u8    | `0F` / 15            | RVA `0xDA00` `8a82a3060000` then store `0xDA06`; record header `0x1331` at `0xD9E0` | RVA `0xFA80` `8a82a3060000` then store `0xFA86`; record header `0x1331` at `0xFA60` |
| `+0x703 DfClockOverrideControl` | u8    | `01` / 1             | RVA `0xE726` `8a8203070000` / `0x1373` at `0xE706`                                  | RVA `0x107A6` `8a8203070000` / `0x1373` at `0x10786`                                |
| `+0x704 DfClockOvrd`            | u16   | `8c05` LE / 1420     | RVA `0xE75B` `668b8204070000` / `0x1374` at `0xE738`                                | RVA `0x107DB` `668b8204070000` / `0x1374` at `0x107B8`                              |

Contiguous cursor/dataflow matters: record `0x1331` is opened at `0xD9E0`/`0xFA60`, then the `+0x6A3` load/store fills that record before the cursor advances; record `0x1332` opens at `0xDA12`/`0xFA92` and receives the following `+0x6A4` load/store. The preceding `+0x6A2` value belongs to record `0x1330`.

## Correction

This corrects the worker's previous off-by-one correction: contiguous value-store order proves `+0x6A3 -> 0x1331`, agreeing with the earlier `memory/oc-recheck.md` mapping. The worker's intermediate claim `+0x6A3 -> 0x1332` is superseded. Shared memory remains unedited; reviewer/root should retain only the contiguous-dataflow result.

## Boundary

The matrix establishes serializer field/token identity only. Record IDs are handoff identifiers; downstream consumers, units, training, physical clocks, synchronization, and hardware acceptance remain unknown. `+0x703` is the u8 control byte; `+0x704` is the u16 DF override value. No patch or hardware/settings action was performed.

## Reproduction

```text
python3 evidence/firmware-audit/20260920-clv-sync-stage2-token-matrix/token_matrix_verify.py
```

Observed exit `0`, stderr empty, `37/37` checks passed. Own evidence manifest check: exit `0`, all listed files `OK`.
