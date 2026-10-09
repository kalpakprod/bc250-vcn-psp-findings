# CLV phase-2 token record-lifetime reconciliation

> Audit 2026-09-27: the current canonical matrix matches the chronology below. The claimed remaining semantic-row contradiction refers to an older matrix revision and is resolved by 2026-09-20-clv-sync-record-ownership-correction.md. Do not reopen the resolved field pairing.

## Conclusion

Complete chronological instruction tracking resolves the record identity and destination stores for adjacent IDs `0x1331` and `0x1332` in both exact clv serializer bodies:

```text
cursor = [ebp-0x8]
write token WORD at [cursor+0]
load Setup byte
write value BYTE at [cursor+3]
advance cursor by +4
```

Observed mapping in both modules:

- `0x1331` → `Setup+0x6A3`;
- `0x1332` → `Setup+0x6A4`.

The canonical matrix labels `+0x6A3 FclkDpm -> 0x1332`, so its semantic field row conflicts with exact serializer bytes. The contradiction is now proven at same-record destination level, not inferred from RVA adjacency. No semantic field rename is made.

## CbsBasePei chronology

|    Token | Token header                          | Source load                                 | Value store                     | Cursor advance                         |
| -------: | ------------------------------------- | ------------------------------------------- | ------------------------------- | -------------------------------------- |
| `0x1331` | `0xD9E8: 66 89 10` (`[ebp-8]` cursor) | `0xDA00: 8A 82 A3 06 00 00` (`Setup+0x6A3`) | `0xDA06: 88 41 03` (`cursor+3`) | `0xDA0C: 83 C1 04`, `0xDA0F: 89 4D F8` |
| `0x1332` | `0xDA1A: 66 89 10` (`[ebp-8]` cursor) | `0xDA32: 8A 82 A4 06 00 00` (`Setup+0x6A4`) | `0xDA38: 88 41 03` (`cursor+3`) | `0xDA3E: 83 C1 04`, `0xDA41: 89 4D F8` |

Token header writes precede source loads; source loads precede value stores; the cursor advances only after the value store. Both records are four bytes with flag low bits zero.

## AmdNbioSmuV10Pei analog

The same complete chronology is duplicated:

- `0x1331` at `0xFA60`, source `0xFA80` (`Setup+0x6A3`), value store `0xFA86`, cursor advance `0xFA8C/0xFA8F`.
- `0x1332` at `0xFA92`, source `0xFAB2` (`Setup+0x6A4`), value store `0xFAB8`, cursor advance `0xFABE/0xFAC1`.

This independent module analog rules out a one-module extraction artifact for the source split.

## Ownership/requester boundary

Both records enter the previously verified Cbs callback/`$INV` construction path. The checked direct reader owners still request neither ID:

- Fabric `0x1EBD -> 0x10FF`, `0x1F94 -> 0x1104`;
- CCX `0x5CA5 -> 0x1000`, `0x5CF1 -> 0x1001`.

The remaining unknown is the actual requester/consumer after generic INV ownership, plus resolution of the matrix semantic field mismatch.

## Reproduction

```text
python3 -B evidence/firmware-audit/20260920-clv-sync-stage2-record-lifetime/record_lifetime_verify.py
```

Exit status: `0`; `58/58` checks passed.

Machine result: `evidence/firmware-audit/20260920-clv-sync-stage2-record-lifetime/record-lifetime-result.json`.
Runner: `evidence/firmware-audit/20260920-clv-sync-stage2-record-lifetime/record_lifetime_verify.py`.

Evidence class: observed bytes + static analysis. No firmware execution, hardware operation, candidate, voltage, source, shared plan/memory, Ghidra/Cutter/MCP or installation change occurred.
