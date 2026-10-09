# CLV phase-2 wrapper registration and indirect-dispatch boundary

## Result

The two AMD PEI `$INV` adapters have an exact callback descriptor and provider-table pointer in the pinned clv module bodies:

- `AmdNbioGfxARIPei+0x4DF0`: descriptor body offset `0x14EE8` / module RVA `0x15080`; provider-table pointer body offset `0x14F58` / RVA `0x150F0` points to `imagebase+0x15080`.
- `AmdNbioSmuV10Pei+0x5740`: descriptor body offset `0x158E0` / module RVA `0x15A70`; provider-table pointer body offset `0x15950` / RVA `0x15AE0` points to `imagebase+0x15A70`.

Both descriptors decode byte-for-byte as:

```text
CPU selector = 0xFFFFFFFF (wildcard)
reserved     = 0
callback     = imagebase + wrapper RVA
event        = 0xFFFFFFFE
```

This resolves the registration-table edge `provider pointer -> callback descriptor -> wrapper`. The module-local indirect-call inventory contains 28 calls (Gfx) and 36 calls (SMU), but no callsite was promoted as the consumer of these descriptor pointers because the checked instruction operands do not join to the descriptor/table addresses. Therefore the actual dispatch caller remains unresolved; no final token-0x1204 consumer is claimed.

## Pinned inputs

- ROM: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
- ROM SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- `AmdNbioGfxARIPei`: SHA-256 `63413be2ac290e584bbbeeba5eb573a94b66b9624c4e0ecbea145ded655245b8`
- `AmdNbioSmuV10Pei`: SHA-256 `905b8be68afd1dce5453acef8273cbf94bdae6d41823c25438ace286348e2c80`

## Exact registration evidence

| Module  |  Wrapper VA | Descriptor body off/RVA | Descriptor bytes                            | Provider pointer body off/RVA | Pointer value       |
| ------- | ----------: | ----------------------- | ------------------------------------------- | ----------------------------- | ------------------- |
| Gfx PEI | `0x9E41A24` | `0x14EE8` / `0x15080`   | `FF FF FF FF 00... 24 1A E4 09 FE FF FF FF` | `0x14F58` / `0x150F0`         | `imagebase+0x15080` |
| SMU PEI | `0x9E8E71C` | `0x158E0` / `0x15A70`   | `FF FF FF FF 00... 1C E7 E8 09 FE FF FF FF` | `0x15950` / `0x15AE0`         | `imagebase+0x15A70` |

The descriptor is asserted as `<QQII> = (0xFFFFFFFF, 0, imagebase+wrapper, 0xFFFFFFFE)`. Event `0xFFFFFFFE` appears adjacent to each callback pointer. The wrapper pointer is in a non-code/data section mapping, not an instruction immediate in the checked registration record.

## Dispatch boundary

The verifier retained all decoded indirect `call` instructions from each exact module (`28` Gfx, `36` SMU) and a sample of their byte-backed operands. No selected operand directly materializes the descriptor RVA, provider-table RVA, or wrapper VA. This is a join failure at the checked dataflow boundary, not a negative claim about arbitrary computed pointers, cross-module dispatch, runtime-built tables, or DMA.

The exact edge now established is:

```text
provider-table pointer (data) -> callback descriptor (wildcard CPU/event FFFFFFFE) -> wrapper 0x4DF0/0x5740 -> complete record builder -> $INV token 0x1204
```

The next narrow edge, if continued, is the PEI registration/dispatch function that consumes the descriptor pointer, using the descriptor's containing table and the module's specific indirect callsite; do not repeat token searches.

## Reproduction

```text
python3 -B evidence/firmware-audit/20260920-clv-sync-stage2-wrapper-dispatch/wrapper_dispatch_verify.py
```

Exit status: `0`; `20/20` checks passed. Machine result:

`evidence/firmware-audit/20260920-clv-sync-stage2-wrapper-dispatch/wrapper-dispatch-result.json`

Runner:

`evidence/firmware-audit/20260920-clv-sync-stage2-wrapper-dispatch/wrapper_dispatch_verify.py`

Evidence class: observed bytes + static analysis. No firmware execution, hardware operation, candidate, voltage, source, shared plan/memory, Ghidra/Cutter/MCP or installation change occurred.

## Subsequent investigation (navigation added 2026-09-27)

The next edge proposed above was investigated in [20260920-clv-sync-stage2-provider-dispatch.md](20260920-clv-sync-stage2-provider-dispatch.md).
Read that continuation before repeating this historical next step.
