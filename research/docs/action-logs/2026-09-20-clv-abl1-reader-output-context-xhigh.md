# Exact CLV ABL1 typed-reader output/context trace — intent and result

## Intent

Timestamp: 2026-09-20, Asia/Almaty (exact wall-clock timestamp printed by the executor before this write).
Actor: bounded executor luna-xhigh.
Target: exact decompressed BIOS 5.00 clv ABL1 payload at reader `0x1FB4`, the UclkDiv1/Fclk branches, their direct caller/output slots, and one statically linked downstream Fclk context read.

Hypothesis: the generic reader's output destination is caller-selected; UclkDiv1 outputs may remain temporary stack values, while the Fclk output may be committed to a context field and loaded later. The discriminating evidence is raw little-endian instructions and direct call/dataflow in the exact pinned ABL1, not a frequency-unit interpretation.

Inputs and expected SHA-256:

- ROM `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Exact ABL1 `evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`: `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Existing exact Thumb listing `evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt`: `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`.
- Prior reader result `evidence/firmware-audit/20260920-clv-abl1-apcb-reader-boundary-resume/abl1-apcb-reader-boundary-result.json`: `537f987266057865bd7f278939304f2f40dcc5db4e57c6048ca0905ce2dac128`.
- Prior exact branch result `evidence/firmware-audit/20260920-clv-abl1-fclk-uclk-branch-xhigh/abl1-fclk-uclk-branch-result.json`: `d6d053b5e4a74a5b4fe0526e4d4659d22a500601074baad751977ab21e2ecdfa`.

Reused route: the existing exact Thumb listing and byte-backed reader/branch verifiers already establish payload `0x1FB4`, descriptors `[0x20,0x21..0x24]` and `[0x015F,0x0160]`, and the typed stores. They do not trace the output pointer through the actual Fclk caller to a later context-field load. This executor will check only that missing consumer edge and stack/context destinations; helper `0x4800`, previously mapped minimum `0x95FC`, and aggregate classifier `0x751C` are outside this deliverable.

Next executable action: create `evidence/firmware-audit/20260920-clv-abl1-reader-output-context-xhigh/abl1_reader_output_context_verify.py` and run it with `python3 -B`; capture literal stdout, stderr and exit status. It checks the immutable exact bytes/listing and direct call chain `0x7E74 -> 0x5E68 -> (0x5FAE -> 0x463C)`, then `0x8428 -> 0x10200 -> 0x107E4`.

Expected effect: one uniquely named verifier, machine result, stdout/stderr captures, one research report, and this action log only. No source/input, firmware, hardware, settings, memory, shared plan, installation, MCP/Cutter, candidate or Git history changes.

Rollback: remove only this uniquely named evidence directory, research report and action log; preserve every pinned source and prior result.

## Observed result

Pending execution.

## Correction after verifier execution 1

Timestamp: 2026-09-20T08:33:19+05:00

Observed command: `python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-output-context-xhigh/abl1_reader_output_context_verify.py`.
Observed exit status: `1`. Captured stdout was empty. Captured stderr ended with `KeyError: 'fclk_branch'` at the verifier's prior branch-result schema lookup. Direct JSON readback showed the historical result key is `exact_fclk_branch` (top-level schema), not `fclk_branch`.

Correction intent: change only the verifier's JSON key to `exact_fclk_branch`, record the prior failure unchanged in `verifier.stderr`, then rerun the same verifier on the same pinned inputs. Expected effect: resume the intended raw-byte/dataflow checks; no input or prior evidence mutation. Rollback remains removal of only this uniquely named evidence directory, report, and action log.

## Correction after verifier execution 2

Timestamp: 2026-09-20T08:34:24+05:00
Observed command: .
Observed exit status: . Captured stderr: . The existing LLVM listing formats payload offsets without a forced five-digit leading zero (), while the new verifier requested .

Correction intent: change only address formatting from zero-padded width five to lowercase unpadded hexadecimal, preserving raw-byte checks, hash pins, and listing content; retain this failed stdout/stderr under and rerun the verifier on the same pinned inputs. No source input or previous evidence changes.

## G7 correction: verifier-run 2 log section and shell heredoc interpolation

The preceding `Correction after verifier execution 2` section is incomplete and superseded here. Its Markdown backticks were placed in an unquoted shell heredoc; Bash attempted command substitutions, leaving blank fields and emitting `command not found` errors. The command substitution also launched one unredirected repeat of the verifier before the address-format edit; it produced the same `listing offset 0x2d0c: expected one line, found 0` assertion as the captured `verifier-attempt-2.stderr`. This extra failed attempt was observed in the execution event but not separately captured. The shell command then changed the listing regex to unpadded hex and the intended rerun passed; its literal stdout is preserved in `verifier.stdout`, stderr is empty, and the machine result exists.

Timestamp: see next correction record; this note repairs the evidence ledger, not the firmware or input.

## Observed verifier result before formatter gate

Command: `python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-output-context-xhigh/abl1_reader_output_context_verify.py`.
Exit status: `0`; checks: `59/59`; captured stderr empty. Literal stdout and JSON result are retained in this evidence directory. It established the exact dataflow from Fclk reader output `SP+0x08`, through caller local `SP+0x04`, to `[context+0x78]` at `0x5FBA`; first direct downstream load in the exact listing is `LDRH R0,[R4,#0x78]` at `0x107E4` on a direct `0x10200` path. This is static analysis only.

## Procoder check result and formatting intent

Command: `procoder check /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-output-context-xhigh/abl1_reader_output_context_verify.py`.
Observed exit status: `1`. It reported the owned verifier as `unformatted` and also returned broad repository hygiene/test/infra notices (`154 hygiene findings`, `0 blocking`); those imported-tree and unrelated findings are out of scope. The checker explicitly recommended `procoder format <path>` to stdout, never formatting over the source directly.

Next action: run `procoder format` into a uniquely named temporary file, inspect its diff, and if only formatting changes are present, replace the verifier from that reviewed formatted copy; then rerun both the verifier and path-scoped `procoder check`. Pinned inputs and prior results remain read-only. Rollback remains removal of only this evidence directory/report/action-log set.
timestamp=2026-09-20T08:37:39+05:00

## Correction and final verifier rerun after Procoder formatting

The formatter diff contained only Ruff formatting (line wrapping, spacing, and a blank line); no instruction offsets, expected hashes, checks, or result strings changed. The formatted file replaced the verifier, the temporary formatter output was removed, and `python3 -m py_compile` passed.

Final verifier command: `python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-output-context-xhigh/abl1_reader_output_context_verify.py`.
Observed exit status: `0`; checks `59/59 PASS`; captured stderr empty. Literal stdout is in `verifier.stdout`; machine result is `abl1-reader-output-context-result.json`.

Final path-scoped Procoder command: `procoder check /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-reader-output-context-xhigh/abl1_reader_output_context_verify.py`.
Observed exit status: `0`; owned verifier `unformatted` finding cleared (`1 clean`, `0 unformatted`, `0 unchecked`, `0 out of scope`). It retained non-blocking documentation-obligation notices for public helper docstrings and the action-log mention, and broad repository test status `python tests: FAILED (0 passed, 0 failed)` because no test files were discovered in that check; these are recorded as unrun/non-blocking and do not alter the static verifier result.

Final evidence interpretation: UclkDiv1 M0..M3 outputs are temporary byte slots followed by logger reads. Fclk's typed halfword result is copied through the caller local and committed to `[context+0x78]` at `0x5FBA`; the same direct outer context reaches `0x10200`, and the first identified downstream load is `[R4+0x78]` at `0x107E4`, with observed comparisons to `0x3E8` and `0x4B0`. This does not establish units, runtime invocation, loader/base mapping, divider/PLL writes, training, physical clocks, or MCLK=UCLK=FCLK.
timestamp=2026-09-20T08:41:52+05:00

## Final role reopen and hash ledger

All owned report/evidence roles were reopened successfully after the final verifier run. Temporary Python `__pycache__` outputs were removed; no source/input or prior evidence was touched.

Final owned hashes:

- verifier `abl1_reader_output_context_verify.py`: `d20f722afed37fd5421beb7f0ee392626177cdc0a31c27dc85dce91ba3d1d061`
- machine result `abl1-reader-output-context-result.json`: `6abae87817c9aa5baf8565524b071f5fae6d19ad5e478d140e22fdea0da42c21`
- stdout `verifier.stdout`: `65f66c16b03889df07fb329a1f1c694c1a87c278327e2cea71b54c26a0d77449`
- stderr `verifier.stderr` (empty): `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- report: `docs/research/20260920-clv-abl1-reader-output-context-xhigh.md`, SHA-256 `1a9af1468749ee6725535cc9c1b6f50af1483f3428f9b5fa52f49fe3d17f5ea9`
- this action log is the append-only execution record; its final hash is recorded by the parent integration readback.

Pinned-input readback remained unchanged: ROM `ea578104...`, ABL1 `af8cf562...`, exact Thumb listing `b5b10b95...`, prior reader result `537f9872...`, prior branch result `d6d053b5...`.
