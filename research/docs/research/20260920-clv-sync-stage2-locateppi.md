# CLV phase-2 LocatePpi argument/interface audit

## Result

All six `AmdNbioSmuV10Pei` LocatePpi-slot candidates were reconstructed with bounded argument and immediate-use slices. The CBS GUID was not requested by any of the six checked paths, while a real non-CBS PPI handoff was byte-backed:

- Five direct calls (`0x372`, `0x410`, `0x51C`, `0xB26`, `0xC22`) push the same GUID pointer `imagebase+0x15A10`, resolving to `5af9cd51-36ee-4bab-b414-aaa0541c5b38`.
- The returned interface is immediately used. On the `0x372` path, after `LocatePpi` returns, `0x396: FF 50 04` calls the returned interface method at `[eax+0x4]`.
- The sixth call (`0x1583`) is inside helper `0x156F`; its three direct helper callers at `0x33F`, `0x1597`, and `0x1552A` provide GUID pointers `RVA 0x15A00`, `0x15A30`, and `0x15A20` respectively. None resolves to the CBS GUID.

CBS GUID `04126c85-5c4e-458f-abc1-29f1f7da365e` is present in the module as static data and byte-identical to `CbsBasePei`, but no direct CBS-GUID LocatePpi join was observed across all six candidate paths and the helper callers.

## Exact call/argument evidence

| LocatePpi call | GUID argument evidence                                                                                      | Immediate interface use                                   |
| -------------: | ----------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
|        `0x372` | `push imagebase+0x15A10` → `5af9cd51-36ee-4bab-b414-aaa0541c5b38`                                           | `0x396: FF 50 04`                                         |
|        `0x410` | same `imagebase+0x15A10`                                                                                    | returned `EAX` copied to `ESI`; subsequent interface path |
|        `0x51C` | same `imagebase+0x15A10`                                                                                    | returned `EAX` copied to `ESI`; subsequent interface path |
|        `0xB26` | same `imagebase+0x15A10`                                                                                    | returned `EAX` copied to `ESI`; subsequent interface path |
|        `0xC22` | same `imagebase+0x15A10`                                                                                    | returned `EAX` copied to `ESI`; subsequent interface path |
|       `0x1583` | helper `0x156F`; callers push pointers at `0x33F/0x1597/0x1552A` → RVAs `0x15A00/0x15A30/0x15A20`; none CBS | helper returns; caller-specific use remains bounded       |

All six call bytes were checked (`0x372: FF 50 20`; remaining five: `FF 51 20`). The CBS GUID pointer's direct materialization was checked and absent in these slices.

## Reproduction

```text
python3 -B evidence/firmware-audit/20260920-clv-sync-stage2-locateppi/locateppi_verify.py
```

Exit status: `0`; `12/12` checks passed.

Machine result: `evidence/firmware-audit/20260920-clv-sync-stage2-locateppi/locateppi-result.json`.
Runner: `evidence/firmware-audit/20260920-clv-sync-stage2-locateppi/locateppi_verify.py`.

Evidence class: observed bytes + static analysis. No firmware execution, hardware operation, candidate, voltage, source, shared plan/memory, Ghidra/Cutter/MCP or installation change occurred.

## Boundary

This resolves an actual non-CBS PPI interface handoff and a full six-call no-join for the CBS GUID. It does not prove callback descriptor installation/invocation or `$INV` token `0x1204` reaching a clock/divider actuator. The next edge would be the non-CBS PPI's method implementation or the three helper caller structures, not another token search.
