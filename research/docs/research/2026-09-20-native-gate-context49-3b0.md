# Exact CLV ABL1 context+0x49 source and +0x3B0 callback target boundary

> BASE/OBJECT CORRECTION: 20260920-native-gate-context49-3b0-review.md binds the C058 store to fallback table base R1, not helper context base R4. Therefore 0x006E5082 is not established as the helper callback target; the external-callback-image request below is based on a superseded binding. The u8 width finding remains separate.

Supplemental exact-byte review: this report is scoped only to the byte value read by the conditional ABL1 callback at payload `0x9AD8` through context `+0x49`, and the helper `0x109BC`'s indirect callback slot `+0x3B0`. It does not revisit context `+0x44` table ownership.

Current: exact CLV ABL1 / `+0x49` width proven as `u8`; initial proposal is `0`, final stored value unresolved because optional callback target at `0x006E5082` is not mapped to the exact ABL1 payload / next = obtain an authorized, version-matched target image or trace that anchors `0x006E5082` and the live callback-gate byte.

## Result

**The exact byte width is known; the final byte value is not statically fixed.** ABL1 helper `0x109BC` takes a caller-proposed byte in `R1`, checks it against the context's count byte `+0x4B`, optionally calls a function pointer loaded from context `+0x3B0` with `(context, &output_byte)`, then copies the output byte from `[SP+4]` to context `+0x49` using `STRB`. The `BLX` return register is not consumed. The candidate callback at `0x9AD8` reads `+0x49` using byte loads and uses its bits in address construction.

The initialization call at `0x7500` explicitly proposes `0x00` (`MOVS R0,#0; MOV R1,R0; MOV R0,R5; BL 0x109BC`). That is only the incoming value. It does not prove the stored value remains zero: if the global byte addressed by literal `0x006E0130` is zero, the helper invokes `[context+0x3B0]`, which can change the pointed-to output byte before the `STRB` to `+0x49`; if the global byte is nonzero, the helper skips that callback and stores the caller's input. The runtime global byte and callback output are not in the extracted ABL1 payload.

The unique local candidate initializer writes the 32-bit literal `0x006E5082` into a `+0x3B0` slot at payload `0xC058`, using pool word at `0xC3D4`. The helper loads the same offset at `0x109D8` and uses `BLX R2` at `0x109E0`. However, object identity between the initializer's destination base `R1` and the helper's runtime context base `R4` is not statically established here. Even if they are the same object, `0x006E5082 - conditional local base 0x57100 = 0x68DF82`, outside the exact ABL1 payload length `0x171A0`; therefore this pointer cannot be mapped to a local function using that conditional base. No other target base is assumed.

## Exact dataflow

|                                                                 Payload offset | Observed byte-backed operation                                                                     | Consequence                                                                                                |
| -----------------------------------------------------------------------------: | -------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
|                                                                       `0x7500` | `R0=R5`, `R1=0` then `BL 0x109BC`                                                                  | Initial caller proposal is zero.                                                                           |
|                                                                      `0x109C0` | `LDRB R0,[R0,#0x4B]`; `0x109C4` reads saved `R1`; compare and bounds branch                        | `+0x4B` supplies an 8-bit count; request must be less than count on the checked path.                      |
|                                                             `0x109D2..0x109D6` | Load byte at global pointer literal `0x006E0130`; branch when nonzero                              | Callback-invocation gate depends on runtime memory not in ABL1 payload.                                    |
|                                                                      `0x109D8` | `LDR.W R2,[R4,#0x3B0]`; `0x109DC` forms `SP+4`; `0x109DE` passes context in `R0`; `0x109E0 BLX R2` | Optional callback receives context plus writable output-byte pointer.                                      |
|                                                                      `0x109E2` | `LDRB R0,[SP,#4]`                                                                                  | The value used next is the callback output byte or untouched caller byte—not the callback's returned `R0`. |
|                                                                      `0x109E6` | `STRB.W R0,[R4,#0x49]`                                                                             | `context+0x49` is exactly one byte wide.                                                                   |
| `0x9C44`, `0x9C52`, `0x9C8C`, `0x9CBC`, `0x9CD4`, `0x9D9C`, `0x9DD2`, `0x9E04` | `LDRB` from `[R5,#0x49]`                                                                           | Callback uses the byte in type-specific address composition/read/write paths.                              |
|                                                    `0xC058` / literal `0xC3D4` | `STR.W R0,[R1,#0x3B0]`; `R0` loaded from pool                                                      | Sole direct local `+0x3B0` writer initializes candidate pointer `0x006E5082`.                              |

There is no post-callback bounds check or normalization before the `STRB` at `0x109E6`; an external callback may write any byte value unless its own implementation constrains it. The target implementation is not mapped in this exact ABL1 payload evidence.

## Conditional-base discipline

Only the previously anchored callback literal `0x00060BD9` at `0xB168` is mapped conditionally under base `0x57100`: `0x60BD9 - 0x57100 = 0x9AD9`, Thumb entry `0x9AD8`. This is consistent with prior independent local anchors. The distinct `+0x3B0` literal `0x006E5082` is **not** mapped with that base; arithmetic yields `0x68DF82`, well outside the decompressed payload. The base is not extended or reinterpreted to force a target match.

## Reproduction

```text
PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260920-native-gate-context49-3b0/verify_context49_3b0.py
```

Observed: exit `0`, `45/45` checks passed, stderr empty. Machine result: `evidence/firmware-audit/20260920-native-gate-context49-3b0/context49-3b0-result.json`.

Exact input hashes:

- ABL1 payload `evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`: size `94,624`, SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Thumb listing `evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt`: SHA-256 `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`.

## Evidence boundary and next discriminator

- **Observed bytes/static analysis:** `+0x49` is a `u8` field; initializer call proposes zero; helper may bypass or invoke an output-parameter callback; helper stores the post-call byte; `+0x3B0` is a 32-bit indirect-call field with a candidate literal `0x006E5082`; the exact payload does not locally map that target under anchored base `0x57100`.
- **Unresolved:** active initializer object identity, runtime global gate `0x006E0130`, actual callback target body/source, callback output value, runtime `+0x4B` count, whether the target pointer belongs to a different executable mapping, and physical/hardware effect.
- **Next decisive check:** recover the exact version-matched PSP/ABL executable mapping for `0x006E5082` or capture a bounded authorized execution trace of helper `0x109BC` with `(context, input byte, gate, callback output)` recorded. Until then do not assign a decoded selector value or imply nonzero/zero final state for an OC candidate.
- No ROM, firmware, hardware, settings, shared plan, MCP, install, or commit changed. Rollback is deletion of this unique report/log/evidence directory only.
