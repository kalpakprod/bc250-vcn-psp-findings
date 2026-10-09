# CLV phase-2 provider-table to dispatcher boundary

## Result

The provider-table fields and callback descriptors are byte-backed in both exact clv AMD PEI bodies, but no module-local executable operand directly materializes or joins the descriptor/provider/wrapper address set. The checked indirect/service-slot call candidates therefore cannot be promoted to the actual dispatcher.

Established static edge:

```text
provider field -> callback descriptor (wildcard CPU, event FFFFFFFE) -> wrapper 0x4DF0/0x5740
```

Installed/invoked registration remains unresolved. This is a precise falsification of a direct module-local code/data join, not a census-wide or runtime negative.

## Exact pointer/descriptor data

| Module             | Provider field RVA | Value               | Descriptor RVA | Descriptor `<QQII>`                          |
| ------------------ | -----------------: | ------------------- | -------------: | -------------------------------------------- |
| `AmdNbioGfxARIPei` |          `0x150F0` | `imagebase+0x15080` |      `0x15080` | `(0xFFFFFFFF,0,imagebase+0x4DF0,0xFFFFFFFE)` |
| `AmdNbioSmuV10Pei` |          `0x15AE0` | `imagebase+0x15A70` |      `0x15A70` | `(0xFFFFFFFF,0,imagebase+0x5740,0xFFFFFFFE)` |

Body offsets for the provider fields are `0x14F58` (Gfx) and `0x15950` (SMU). Descriptor body offsets are `0x14EE8` and `0x158E0`. The wrapper pointers occur at descriptor+`0x10`; event `0xFFFFFFFE` occurs at descriptor+`0x14`.

## Bounded executable join

The verifier scanned the exact decoded instruction metadata for each module for operands containing the descriptor RVA, provider RVA, descriptor VA, provider VA or wrapper VA:

- Gfx: `28` indirect calls retained; `5` PEI/service-slot-shaped candidates retained; executable operand joins to the pointer set: `0`.
- SMU: `36` indirect calls retained; `13` PEI/service-slot-shaped candidates retained; executable operand joins to the pointer set: `0`.

Examples are retained in the machine result; they are generic indirect calls such as `call DWORD PTR [eax+0x20]`, not proven consumers of these descriptors. No installed/invoked state is inferred from static pointer presence.

## Reproduction

```text
python3 -B evidence/firmware-audit/20260920-clv-sync-stage2-provider-dispatch/provider_dispatch_verify.py
```

Exit status: `0`; `18/18` checks passed.

Machine result: `evidence/firmware-audit/20260920-clv-sync-stage2-provider-dispatch/provider-dispatch-result.json`.
Runner: `evidence/firmware-audit/20260920-clv-sync-stage2-provider-dispatch/provider_dispatch_verify.py`.

Evidence class: observed bytes + static analysis. No firmware execution, hardware write, candidate, voltage, source, shared plan/memory, Ghidra/Cutter/MCP or installation change occurred.

Next exact edge, if continued: resolve the PEI registration function that consumes the descriptor pointer using this table's containing structure and one of the module's indirect callsites. Do not repeat serializer or pointer-presence scans.

## Subsequent investigation (navigation added 2026-09-27)

The next edge proposed above was investigated in [20260920-clv-sync-stage2-pei-lifecycle.md](20260920-clv-sync-stage2-pei-lifecycle.md).
Read that continuation before repeating this historical next step.
