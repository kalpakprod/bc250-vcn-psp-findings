# G7 correction: serializer record ownership for FCLK_DPM

## Result

The canonical nearest-RVA pairing was wrong. Full destination-pointer dataflow in contiguous `CbsBasePei` and `AmdNbioSmuV10Pei` blocks establishes:

- `Setup+0x6A2 -> record/token 0x1330`;
- `Setup+0x6A3 (FCLK_DPM) -> record/token 0x1331`;
- `Setup+0x6A4 -> record/token 0x1332`.

Corrected table:

| Module             |         Header token | Source load | Source field | Same-destination value store | Pointer increment |
| ------------------ | -------------------: | ----------: | -----------: | ---------------------------: | ----------------: |
| `CbsBasePei`       | `0x1330` at `0xD9AE` |    `0xD9CE` |     `+0x6A2` |                     `0xD9D4` |          `0xD9DA` |
| `CbsBasePei`       | `0x1331` at `0xD9E0` |    `0xDA00` |     `+0x6A3` |                     `0xDA06` |          `0xDA0C` |
| `CbsBasePei`       | `0x1332` at `0xDA12` |    `0xDA32` |     `+0x6A4` |                     `0xDA38` |          `0xDA3E` |
| `AmdNbioSmuV10Pei` | `0x1330` at `0xFA2E` |    `0xFA4E` |     `+0x6A2` |                     `0xFA54` |          `0xFA5A` |
| `AmdNbioSmuV10Pei` | `0x1331` at `0xFA60` |    `0xFA80` |     `+0x6A3` |                     `0xFA86` |          `0xFA8C` |
| `AmdNbioSmuV10Pei` | `0x1332` at `0xFA92` |    `0xFAB2` |     `+0x6A4` |                     `0xFAB8` |          `0xFABE` |

Therefore **FCLK_DPM `+0x6A3` owns record/token `0x1331`**, not `0x1332`. The previous `+0x6A3 -> 0x1332` correction was itself based on pairing each source with the preceding header and is superseded. The adjacent `+0x6A2 -> 0x1330` and `+0x6A4 -> 0x1332` relationships follow the same destination-pointer trace.

## Ownership rule

Each block uses the same destination pointer `[ebp-0x8]` for:

1. token header store `WORD PTR [eax], dx` at `dest+0`;
2. flags update at `dest+2`;
3. source load and `BYTE PTR [ecx+0x3], al` at `dest+3`;
4. `add ecx, 4` after the value store.

The source load immediately before the value store belongs to the header already written at the current destination, not to the next header encountered by address order.

## Reproduction

```text
python3 -B evidence/firmware-audit/20260920-clv-sync-record-ownership-correction/record_ownership_verify.py
```

Observed exit status: `0`; `12/12` checks passed. Machine result SHA-256: `cab9dd7e18defabe1459537fe870a520c24602f1641bd44af5e78ad3e2b2aaf3`.

This is a static serializer ownership correction only. Downstream consumers, units, training, physical clocks, synchronization, and hardware acceptance remain unknown.
