# CLV phase-2 all-field record-lifetime reconciliation

> Audit 2026-09-27: the final paragraph about a remaining +0x6A3 matrix contradiction is historical. The current matrix and ownership correction match +0x6A3 ->0x1331 and +0x6A4 ->0x1332. This does not resolve downstream consumers or physical clocks.

## Corrected map

Destination/cursor tracking independently recovers the same field→token mapping in `CbsBasePei` and `AmdNbioSmuV10Pei`:

| Setup field |    Token | Width | Cbs source/value/advance   | SMU source/value/advance     |
| ----------: | -------: | ----: | -------------------------- | ---------------------------- |
|    `+0x316` | `0x11ED` |    u8 | `0x9857` → `0x985D` → `+4` | `0xB8D7` → `0xB8DD` → `+4`   |
|    `+0x330` | `0x1204` |    u8 | `0x9CE4` → `0x9CEA` → `+4` | `0xBD64` → `0xBD6A` → `+4`   |
|    `+0x703` | `0x1373` |    u8 | `0xE726` → `0xE72C` → `+4` | `0x107A6` → `0x107AC` → `+4` |
|    `+0x704` | `0x1374` |   u16 | `0xE75B` → `0xE762` → `+5` | `0x107DB` → `0x107E2` → `+5` |
|    `+0x36D` | `0x123C` |    u8 | `0xA7E1` → `0xA7E7` → `+4` | `0xC861` → `0xC867` → `+4`   |
|    `+0x368` | `0x1237` |    u8 | `0xA6E7` → `0xA6ED` → `+4` | `0xC767` → `0xC76D` → `+4`   |

Each row is proven as:

```text
mov eax,[ebp-8]       ; current record cursor
mov [eax],dx          ; token header at record+0
mov ecx,[ebp-8]
mov al/ax,[edx+field]  ; Setup source
mov [ecx+3],al/ax     ; value at same record+3
add ecx,4/5
mov [ebp-8],ecx       ; next record
```

The prior `+0x6A3` contradiction remains explicit: adjacent tracking proves `0x1331 -> +0x6A3` and `0x1332 -> +0x6A4` in both modules, despite the canonical matrix's semantic row.

## Reproduction

```text
python3 -B evidence/firmware-audit/20260920-clv-sync-stage2-record-lifetime-all-fields/all_fields_verify.py
```

Exit status: `0`; `29/29` checks passed.

Machine result: `evidence/firmware-audit/20260920-clv-sync-stage2-record-lifetime-all-fields/all-fields-result.json`.
Runner: `evidence/firmware-audit/20260920-clv-sync-stage2-record-lifetime-all-fields/all_fields_verify.py`.

Evidence class: observed bytes + static analysis. No firmware execution, hardware operation, candidate, voltage, source, shared plan/memory, Ghidra/Cutter/MCP or installation change occurred.

## Boundary

This corrects/validates serializer field→token identity and same-record ownership for all six remaining claims. It does not establish a downstream requester, unit conversion, training semantics, clock synchronization or hardware behavior. Unrelated source loads without a nearby token-builder header were not promoted as record rows.
