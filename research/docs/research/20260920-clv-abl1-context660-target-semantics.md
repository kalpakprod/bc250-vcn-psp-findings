# Possible CLV ABL1 `0x9AD8` target semantics

## Current

Fresh exact-byte/listing verification independently classifies the candidate mapped from initializer literal `0x00060BD9` under conditional base `0x57100` to entry `0x9AD8`. With the dispatcher argument shape `(R1=1, R2=0x61E, R3=selected value)`, the body is compatible with a generic descriptor-indexed register field read/modify/write helper. This is **possible target semantics only**; active Fclk-context binding remains unproven.

## Findings

1. **Argument positions are compatible.** The exact caller loads `R1=0x61E` at `0x107E8`, preserves `R0=context` at `0x1081E`, and calls `0x10958` at `0x10820` after setting `R2` to the branch-selected value. Dispatcher `0x10958` loads `[R0+0x660]`, copies caller `R2 -> R3`, caller `R1 -> R2`, sets `R1=1`, and branches through the callback pointer. Therefore the candidate receives `R1=1`, `R2=0x61E`, `R3=selected value`.
2. **The candidate indexes a descriptor table.** At `0x9ADE`, `R5=R0`. At `0x9AE8`, the low 12 bits of incoming `R2` are extracted and saved at `[SP+0x3C]`; `0x9B18` loads `[R5+0x44]`; `0x9B1C` loads `table[token_index]`. Descriptor bits are decoded at `0x9B2C` (nested index bits 12..23), `0x9B32` (field end bits 6..11), `0x9B36` (field start bits 0..5), and `0x9B40` (wide flag bit 30), followed by a nested table load at `0x9B54`.
3. **The selected value is a field input.** `0x9AE2` copies incoming `R3` to `R11`. For a normal-width field, `0x9D20..0x9D28` masks and shifts `R11`, merges it with the locally read value, and stores the result at `[SP+0x14]`. For a wide-field branch, `0x9BFA` can seed `[SP+0x14]` directly from `R11`.
4. **One exact callee operation is a mapped word read.** In helper `0x6DA4`, `0x6DCC` computes `descriptor >> 12`, `0x6DCE` extracts `descriptor & 0xFFF`, `0x6DD2` shifts the selector back by 12, and `0x6DD4` executes `SVC #4`. For the candidate's type argument `R0=3`, `0x6E1A` performs `LDR R3,[mapped,R4]` and `0x6E1E` stores that word through the supplied output pointer. The candidate reaches this helper at `0x9C2A` with `R0=3`, `R2=SP+0x14`, and `R1=R4` on the normal-field path.
5. **The complementary exact callee operation is a mapped word store.** Helper `0x6E70` repeats the `descriptor >> 12` / low-12-bit offset / `SVC #4` mapping at `0x6EA6..0x6EAE`; for type `3`, `0x6EE6` loads the word from the supplied value pointer and `0x6EE8` stores it to the mapped address. The candidate calls it at `0x9D96` with `R0=3`, `R2=SP+0x14`, and `R1=R4` on the high-index path.
6. **Stub callee.** Exact bytes at both `0x6C1C` and `0x6C1E` are `70 47` (`BX LR`), so those calls have no observed body-side memory operation.

## Classification boundary

The exact static body is compatible with a descriptor-indexed register field read/modify/write helper, not merely an initializer-context callback. However, the live `[R5+0x44]` table and descriptor entries were not recovered in this bounded check; the helper's `SVC #4` mapping semantics are opaque; and the prior ownership result does not prove that the active Fclk dispatcher current `R4` equals the initializer's `R5`. Therefore this report does not assert the candidate is active, does not name a physical register, and does not claim an MMIO/PLL/hardware effect or `MCLK=UCLK=FCLK`.

## Reproduction

```text
python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-context660-target-semantics/abl1_context660_semantics_verify.py
```

Observed stdout is stored at:

```text
/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-context660-target-semantics/verifier.stdout
```

Observed stderr is empty at:

```text
/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-context660-target-semantics/verifier.stderr
```

The machine-readable result is:

```text
/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-context660-target-semantics/abl1-context660-semantics-result.json
```

## Exact inputs and hashes

- ABL1: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin` — SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Thumb listing: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt` — SHA-256 `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`.
- Prior callback pointer result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-context660-callback-xhigh/abl1-context660-callback-result.json` — SHA-256 is recorded in the new machine result.

## Checks and limits

- PASS: 96 exact raw-byte/listing assertions, dispatcher-argument checks, and pointer checks.
- PASS: exact mapped word-read operation in `0x6DA4`.
- PASS: exact mapped word-write operation in `0x6E70`.
- PASS: exact `BX LR` stub bytes at `0x6C1C`/`0x6C1E`.
- UNPROVEN: live context table/descriptor values, active Fclk callback binding, `SVC #4` physical mapping, physical MMIO/PLL effect, firmware runtime, hardware behavior, and `MCLK=UCLK=FCLK`.

No firmware, hardware, ROM, settings, source input, memory, MCP/Cutter, candidate, or project plan changed. Rollback is removal of this unique evidence directory, report, and action log.
