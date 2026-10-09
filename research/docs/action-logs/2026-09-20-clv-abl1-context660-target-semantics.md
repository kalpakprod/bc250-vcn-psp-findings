# CLV ABL1 0x9AD8 target semantics — intent and result

## Intent

Timestamp: 2026-09-20T11:10:00+05:00
Actor: bounded static-analysis executor.
Target: exact CLV ABL1 candidate entry `0x9AD8` under conditional base `0x57100`, its dispatcher argument mapping at `0x10958`, and its direct helper bodies `0x6DA4` / `0x6E70`.
Hypothesis: with dispatcher-normalized arguments `R1=1`, `R2=0x61E`, and `R3=selected value`, the candidate is a generic descriptor-indexed register field read/modify/write helper rather than an incompatible initializer callback. This semantic classification must remain separate from proof that the active Fclk context reaches this slot.
Pinned inputs:

- Exact ABL1 `evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`, SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Exact Thumb listing `evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt`, SHA-256 `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`.
- Prior callback pointer result `evidence/firmware-audit/20260920-clv-abl1-context660-callback-xhigh/abl1-context660-callback-result.json`, reused only for the conditional pointer map.
  Next executable action: create and run one byte/listing verifier that checks the dispatcher argument shuffle, token-index and descriptor-field extraction, selected-value insertion, exact `0x6DA4` mapped 32-bit read, exact `0x6E70` mapped 32-bit write, and the explicit active-binding boundary. Capture literal stdout/stderr/exit status.
  Expected effect: one unique evidence directory, one report, and this action log. No ROM, firmware, hardware, source input, memory, or project-plan changes.
  Rollback: remove only `evidence/firmware-audit/20260920-clv-abl1-context660-target-semantics/`, this report, and this action log.

## Correction after pointer-entry assertion

Timestamp: 2026-09-20T11:12:00+05:00
Observed command: `python3 -B evidence/firmware-audit/20260920-clv-abl1-context660-target-semantics/abl1_context660_semantics_verify.py`. Exit status `1`; the verifier incorrectly applied Thumb-bit clearing to the absolute literal (`0x60BD9 & ~1`) instead of to the mapped offset (`0x60BD9 - 0x57100 = 0x9AD9`, entry `0x9AD8`). No pinned input was changed.

Correction intent: change only the pointer-entry assertion to validate `(POINTER - BASE) & ~1 == 0x9AD8`, then rerun the same exact-input verifier. Preserve the failed stderr capture.

## Correction after raw-byte endianness assertion

Timestamp: 2026-09-20T11:13:00+05:00
Observed rerun exit status `1`; the verifier stored LLVM listing halfwords as file-byte order. Exact ABL bytes at `0x9AD8` are `2d e9 ff 4f`, while the listing prints `e92d 4fff`. The listing and raw-byte evidence are consistent after per-halfword little-endian normalization.

Correction intent: normalize all verifier raw expectations from listing halfword notation to direct file-byte order inside the verifier, and retain the failed stderr capture before rerunning. No input bytes change.

## Correction after descriptor-field byte assertion

Timestamp: 2026-09-20T11:14:00+05:00
Observed rerun exit status `1`; the verifier assigned the field-start encoding to the field-end extraction at `0x9B32`. The exact listing is `UBFX R8,R6,#0x6,#0x6` (`f3c6 1885`), while `0x9B36` is the field-start extraction (`f3c6 0705`).

Correction intent: correct only the `0x9B32` expected halfwords and rerun on the same pinned inputs. No input bytes change.

## Correction after second descriptor-field byte assertion

Timestamp: 2026-09-20T11:15:00+05:00
Observed rerun exit status `1`; the verifier similarly mistyped the field-start encoding. Exact listing `0x9B36` is `UBFX R7,R6,#0x0,#0x6` (`f3c6 0705`), not `f3c6 0005`.

Correction intent: correct only the `0x9B36` expected halfwords and rerun on the same pinned inputs. No input bytes change.

## Correction after mapped-word-store address assertion

Timestamp: 2026-09-20T11:16:00+05:00
Observed rerun exit status `1`; the verifier placed the type-3 store at `0x6EEA`, but the exact helper listing performs `LDR R0,[R4]` at `0x6EE6` and `STR R0,[R5,R6]` at `0x6EE8`; `0x6EEA` is the loop branch.

Correction intent: move only the expected type-3 store assertion to `0x6EE8` and rerun on the same pinned inputs. No input bytes change.

## Final target-semantics result

Timestamp: 2026-09-20T11:17:00+05:00
Command: `python3 -B evidence/firmware-audit/20260920-clv-abl1-context660-target-semantics/abl1_context660_semantics_verify.py`
Observed exit status: `0`.
Observed stdout: JSON result `{"status":"PASS","checks":79,...}` in `evidence/firmware-audit/20260920-clv-abl1-context660-target-semantics/verifier.stdout`.
Observed stderr: empty in `evidence/firmware-audit/20260920-clv-abl1-context660-target-semantics/verifier.stderr`.

Verified semantic result: under the conditional `0x57100` map, dispatcher `0x10958` passes `R1=1`, token `R2=0x61E`, and selected value `R3`; `0x9AD8` saves the context in `R5`, indexes `[R5+0x44]` by the token low 12 bits, decodes descriptor fields, and copies `R3` to `R11`. The exact `0x6DA4` callee maps descriptor `>>12` through `SVC #4`, masks the low 12-bit offset, and for type `3` performs a word read into the supplied output pointer. The `0x9D20..0x9D28` sequence merges selected `R3` bits into that local word. The exact `0x6E70` callee performs the complementary type-3 mapped word store from the output pointer; `0x6C1C`/`0x6C1E` are `BX LR` stubs.

Classification: possible generic descriptor-indexed register field read/modify/write helper. This is possible target semantics only; no live context table/descriptor bytes were recovered, and no dataflow proves the active Fclk dispatcher `R4` object is the initializer `R5` object. No hardware, MMIO effect, clock equality, or active callback binding is claimed.

Input readback: ABL SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`; Thumb listing SHA-256 `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`; prior callback-result SHA-256 recorded in machine result.

## Intent: direct dispatcher argument readback

Timestamp: 2026-09-20T11:19:00+05:00
The first semantic verifier established the target/helper operations but did not independently assert the caller-side `0x107E8` token load and `0x10820` dispatcher shuffle. Add only those raw/listing assertions plus the exact `0x10958` register shuffle, then rerun the same bounded verifier. This is a directness improvement, not a new semantic route; no pinned input or hardware action is involved.

## Final direct dispatcher readback

Timestamp: 2026-09-20T11:20:00+05:00
The strengthened verifier added direct checks for `0x107E8` (`R1=0x61E`), `0x1081E/0x10820` (`R0=context`, dispatcher call), and `0x10958..0x10968` (`R0+0x660` load, `R2->R3`, `R1->R2`, `R1=1`, `BX R12`).

Command: `python3 -B evidence/firmware-audit/20260920-clv-abl1-context660-target-semantics/abl1_context660_semantics_verify.py`. Exit status `0`; stdout now reports `{"status":"PASS","checks":96,...}`; stderr remains empty. Machine result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-context660-target-semantics/abl1-context660-semantics-result.json`.
