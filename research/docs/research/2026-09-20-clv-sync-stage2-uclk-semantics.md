# Stage 2 — Bounded UclkDiv1M0/Memory-P-state semantics

## Result

The new discriminating check does not find a ratio calculation or FCLK-relative conversion on the exact native paths. It finds typed-byte serializers:

- `AmdSetup+0x330` (`UclkDiv1M0`) is copied into `$INV` record `0x1204`.
- `AmdSetup+0x36D` (`Memory P-state`) is copied into `$INV` record `0x123C` (the contiguous record-cursor audit corrected an earlier mistaken `0x123D` association).
- `CbsBasePei` and `AmdFabricAriPei` both contain serializer windows for these records; the checked value loads/stores contain no ratio arithmetic.
- The bounded confirmed direct-reader calls in `AmdFabricAriPei` use `0x10FF` and `0x1104`, not `0x1204`/`0x123C`; the final consumer after the INV handoff remains unresolved.

Therefore, **`UclkDiv1M0=Enabled` cannot be promoted to “selects a ratio relative to FCLK” from this evidence**. The exact native help string says “relative to FCLK,” but the byte-backed code path only preserves an enable/value byte and does not assign a ratio or frequency.

## Exact byte-backed edges

`CbsBasePei`:

```text
0x9CC4: ba04120000       record header 0x1204
0x9CE4: 8a8230030000     load Setup+0x330
0x9CEA: 884103           store value into current record

0xA7C1: ba3c120000       record header 0x123C
0xA7E1: 8a826d030000     load Setup+0x36D
0xA7E7: 884103           store value into current record
```

`AmdFabricAriPei` repeats typed serializer windows:

```text
0xD224: ba04120000       record header 0x1204
0xD244: 8a8230030000     load Setup+0x330
0xD24A: 884103           store value

0xDD21: ba3c120000       record header 0x123C
0xDD41: 8a826d030000     load Setup+0x36D
0xDD47: 884103           store value
```

The record cursor advances between header/value groups; record `0x123C`, not `0x123D`, receives `+0x36D`.

## Generic training-source comparison (not exact-clv consumer proof)

The retained historical ABL1 source contains a concrete generic memory-training routine (`FUN_000096FC`) that logs “Synchronize Mem Speed for each channel,” computes/propagates per-channel memory-speed structures, and writes synchronized memory speed back through `param_1[3]+0x20`. Its strings also include “Memory P-state Enabled/Disabled,” `NumOfMemPstates`, and “Current Memory P-state.”

This source is a generic/historical PSP ABL artifact, not the pinned clv callback consumer. It demonstrates that memory-speed synchronization and Memory-P-state state exist as training concepts, but provides no byte-backed edge from clv records `0x1204`/`0x123C` to that routine.

## Reproduction

```text
python3 evidence/firmware-audit/20260920-clv-sync-stage2-uclk-semantics/uclk_semantics_verify.py
```

Observed exit status `0`; stderr empty; `31/31` checks passed. Own manifest check exited `0`; all listed files `OK`.

## Boundary

- **PASS:** typed serializer edges and absence of ratio arithmetic in the bounded immediate paths.
- **INCONCLUSIVE:** final INV consumer, UCLK/FCLK ratio semantics, training gate, units, and synchronous crossing.
- **UNRUN:** browser/save/reset, firmware execution, memory training, hardware, clocks, voltage, and latency.

No firmware, settings, hardware, shared plan/memory, installation, or MCP state was changed.
