# CLV phase-2 complete function boundary: AMD PEI token-0x1204 builders

## Result

Complete containing-function recovery closes the prior tiny-window limitation for the two selected AMD PEI serializers:

- `AmdNbioGfxARIPei`: builder `RVA 0x4E20..0x12FA3`, token `0x1204` at `0xB3F4`.
- `AmdNbioSmuV10Pei`: builder `RVA 0x5770..0x138F3`, token `0x1204` at `0xBD44`.

Each complete builder has two direct calls, both to its size helper before/around the size gate, and **zero direct calls after the token record body** before the `$FFFF` sentinel and successful return. Each wrapper constructs the builder arguments, calls the builder once, then immediately returns; no post-builder init-structure call is present at this concrete boundary.

This is a byte-backed adapter boundary, not proof of no indirect, callback-table, HOB, DMA, later-phase, or hardware consumer.

## Pinned inputs

- ROM: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
- ROM SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- `AmdNbioGfxARIPei`: `AmdNbioGfxARIPei-63413be2ac29.bin`, SHA-256 `63413be2ac290e584bbbeeba5eb573a94b66b9624c4e0ecbea145ded655245b8`
- `AmdNbioSmuV10Pei`: `AmdNbioSmuV10Pei-905b8be68afd.bin`, SHA-256 `905b8be68afd1dce5453acef8273cbf94bdae6d41823c25438ace286348e2c80`

## Byte-backed boundaries

| Module             |  Wrapper |           Builder |               Token site | Direct calls before builder return | Calls after token | Return/sentinel                                    |
| ------------------ | -------: | ----------------: | -----------------------: | ---------------------------------- | ----------------- | -------------------------------------------------- |
| `AmdNbioGfxARIPei` | `0x4DF0` | `0x4E20..0x12FA3` | `0xB3F4: BA 04 12 00 00` | `0x4E26→0x12FB0`, `0x4E35→0x12FB0` | none              | `0x12F93` `$FFFF`; `0x12F9E: B0 01`; `0x12FA3: C3` |
| `AmdNbioSmuV10Pei` | `0x5740` | `0x5770..0x138F3` | `0xBD44: BA 04 12 00 00` | `0x5776→0x13900`, `0x5785→0x13900` | none              | `0x138E3` `$FFFF`; `0x138EE: B0 01`; `0x138F3: C3` |

The two size-helper calls are the required-size probe and the insufficient-size return path. No direct call occurs after the token record construction in either complete function.

Both wrappers share the exact argument-construction bytes at wrapper+4:

```text
8b450c8b4804894dfc8b55fc8b4204508b4dfc8b11528b451050e80d000000
```

Decoded static relation:

```text
[ebp+0x0c] -> descriptor -> [+0x04] -> push size pointer
                                      [+0x00] -> push output buffer
[ebp+0x10] --------------------------> push context/setup
call builder
add esp,0x0c; leave; ret
```

The wrapper's only direct call is the builder (`Gfx 0x4E0E→0x4E20`; `SMU 0x575E→0x5770`). It returns immediately after the call (`8B E5 5D C3`).

## Reproduction

```text
python3 -B evidence/firmware-audit/20260920-clv-sync-stage2-function-boundary/function_boundary_verify.py
```

Exit status: `0`; `30/30` checks passed. Machine result:

`evidence/firmware-audit/20260920-clv-sync-stage2-function-boundary/function-boundary-result.json`

The verifier independently checks ROM/module hashes, complete prologue/ret boundaries, token bytes, both size-helper calls, absence of post-token direct calls, sentinel and success-return bytes, wrapper argument construction, wrapper call sequence and wrapper return.

## Classification and next exact edge

Evidence class: observed bytes + static analysis. The complete function boundary shows that these AMD PEI paths are record-building adapters, not direct clock/divider consumers. The next concrete edge is the wrapper's registration/indirect dispatch (callback table or PEI event descriptor), not another token literal search. No firmware execution, hardware action, shared project change, candidate, voltage or settings write occurred.

## Subsequent investigation (navigation added 2026-09-27)

The next edge proposed above was investigated in [20260920-clv-sync-stage2-wrapper-dispatch.md](20260920-clv-sync-stage2-wrapper-dispatch.md).
Read that continuation before repeating this historical next step.
