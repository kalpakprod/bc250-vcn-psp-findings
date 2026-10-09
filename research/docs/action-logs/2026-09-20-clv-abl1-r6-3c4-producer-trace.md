# CLV ABL1 active-context pointer producer trace — intent and result

## Intent

Timestamp: 2026-09-20T19:08:52+05:00 (Asia/Almaty)
Actor: bounded read-only analysis subtask.
Target: exact CLV ABL1 function at payload offset `0x7378`; read of `[R6+0x3C4]` at `0x73AE`; callback initializer call at `0x74E0`.

Hypothesis: the pointer loaded from `[R6+0x3C4]` may be initialized by an in-image field writer and may or may not be the same object as the `R5` parent initialized through `0xAF90`. Acceptance is only the exact static object/dataflow relationship, not firmware runtime or clock behavior.

Pinned inputs:

- ROM `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, 16,777,216 bytes, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- ABL1 `evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`, 94,624 bytes, SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Existing exact Thumb listing `evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt`, 2,586,986 bytes, SHA-256 `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`.

Reused route: use the existing pinned Thumb listing and prior context-ownership reports; do not re-decode, rescan tokens, or rerun their verifiers. The bounded check records the function entry argument mapping, the `[R6+0x3C4]` read and parent-object store, the exact callback-initializer call argument, all direct `+0x3C4` store rows in this listing, and direct `BL` references to `0x7378`. It stops if the candidate producer has a runtime-dependent base/value and object identity cannot be joined.

Expected effect: one unique result directory and this report/log only. No ROM, firmware, settings, hardware, memory, candidate, source input, or shared MCP state changes.

Rollback: remove only `evidence/firmware-audit/20260920-clv-abl1-r6-3c4-producer-trace/`, this research report, and this action log.

## Correction before artifact creation

Timestamp: 2026-09-20T19:10:14+05:00 (Asia/Almaty). The first shell invocation used an unquoted heredoc for Markdown containing backticks. Bash command-substituted the inline code spans, emitted `command not found` and `Permission denied` messages for the referenced words/paths, but the outer command still exited `0`. The resulting log was incomplete. No source or evidence input was changed. This file is being replaced with a literal-safe Python write before continuing; the shell errors and exit status are retained here. This supersedes the malformed first version only.

Observed first-command errors include `/usr/bin/bash: line 5: 0x7378: command not found`, `[R6+0x3C4]: command not found`, `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin: Permission denied`, and analogous Markdown backtick spans. The shell reported exit `0`; this was not evidence that the initial action-log content was correct.

## Planned bounded execution

Read-only command will select the named rows from the existing Thumb listing, report its and the ABL1 body's size/hash, list exact instruction rows around `0x7378`, `0x73AE`, `0x73B2`, `0x74E0`, each direct `+0x3C4` writer, and any direct BL target to `0x7378`. It will not invoke a disassembler or alter the inputs. The exact producer/runtime-object identity boundary will be reported as partial if the caller-supplied bases remain unjoined.

## G7 memory-correction intent

Timestamp: 2026-09-20T19:13:10+05:00 (Asia/Almaty). Before any further static trace or result-artifact write, create the new, narrowly scoped incident note `memory/incidents/2026-09-20-bash-markdown-heredoc-expansion.md` recording the unquoted-heredoc command expansion error, observed misleading shell exit `0`, and literal-safe correction. This new file is the correction record; no existing memory file is edited, so no memory writer is displaced. Expected additional path is only this incident note. Rollback: remove only that note if its content is wrong.

## Correction after first bounded execution

Timestamp: 2026-09-20 (Asia/Almaty). The bounded verifier exited `1` before producing stdout because the existing linear listing has a BL row at `0x74E0` targeting `0xAF90`, but does not contain a decoded instruction row at function entry `0xAF90`. This was an over-strict required-row assertion, not a source mismatch. The listing does contain the needed downstream store at `0xB0C4`. The corrected run will require the BL row, `0xB0C4`, and all producer/consumer rows; it will not invent an absent `0xAF90` body row or rerun a broader scan.

Observed failed command: `PYTHONDONTWRITEBYTECODE=1 python3 -B - <<'PY' ...`; exit status `1`. Literal stderr is retained at `evidence/firmware-audit/20260920-clv-abl1-r6-3c4-producer-trace/trace.stderr`; assertion: `missing required listing row(s): ['0xaf90']`.

## Observed bounded result

Timestamp: 2026-09-20 (Asia/Almaty). Corrected bounded command exited `0`; literal stderr was empty. It reopened and matched all pinned identities: ROM 16,777,216 bytes / `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`; ABL1 94,624 bytes (`0x171A0`) / `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`; existing listing 2,586,986 bytes / `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`.

The fresh result is `PARTIAL_UNRESOLVED_RUNTIME_OBJECT_IDENTITY`. The exact `0x7378` function maps `arg1` to `R6`, reads `[R6+0x3C4]` at `0x73AE`, stores that pointer to `[R5+0x8]` at `0x73B2`, and passes `R5` to `BL 0xAF90` at `0x74E0`. The only direct `+0x3C4` stores in the listing are `0xB93C` through `R1` with a PC-relative-literal value and `0x10B2E` through `R4` with `[SP+0x10]`; neither base joins to `R6` in this bounded trace. No direct `BL 0x7378` row occurs. The listing has no decoded `0xAF90` entry row; its downstream `0xB0C4` slot store is present.

Acceptance is therefore a specific unresolved boundary, not pointer identity: runtime/indirect object values prevent a static join between the field producer, initializer parent, and active dispatcher object. The trace stops here. No ROM, firmware, settings, hardware, candidate, or source input changed. No physical clock, SVC#4 target, or `MCLK=UCLK=FCLK` claim follows.

Artifacts reopened after writing: report `docs/research/20260920-clv-abl1-r6-3c4-producer-trace.md`; result `evidence/firmware-audit/20260920-clv-abl1-r6-3c4-producer-trace/producer-trace-result.json`; corrected stdout/stderr/exit in the same directory.

Final observed artifact hashes:

- report: `655e99c5456453e59643ae9bce287f8414ab0387025e157c687dd862a0f267ab`
- result: `02e75d02c3660eef2cc85fde47f54a8add0f6027250982b701a39da2128166e0`
- corrected stdout: `4253e5bf1861889663912023aeb9742cc3d0f07b8ef628c926e89a87eee31c66`
- corrected stderr: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- corrected exit: `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`
- this action log after append: computed at final readback below.
