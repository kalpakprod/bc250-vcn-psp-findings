# Exact CLV ABL1 context+0x660 callback boundary — intent and result

## Intent

Timestamp: 2026-09-20T10:10:59.150576+05:00
Actor: bounded executor luna-xhigh.
Target: exact CLV ABL1 pointer install at `0xB0C4` / literal `0xB168`, conditional base `0x57100`, and dispatcher `0x10958` from the accepted `0x107E4` branch checkpoint.

Hypothesis: the initializer literal `0x60BD9`, under the existing candidate base, targets ABL1 code at `0x9AD8`; that callback may consume the branch-selected value. However, the exact runtime object identity must be checked separately: the init store base and active dispatcher base may be different. The only acceptance claim is exact static bytes/dataflow, not loader/runtime or hardware execution.

Pinned inputs:

- ROM `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Exact ABL1 `evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`, SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Exact Thumb listing `evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt`, SHA-256 `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`.
- Prior accepted 89-check branch result `evidence/firmware-audit/20260920-clv-abl1-context-branch-consumer-xhigh/abl1-context-branch-consumer-result.json`, SHA-256 `269049d9fb13f32dbf8c037f85ebfe695fd5099e37fe354e8b2a939d1c4cf671`.
- Prior conditional-base anchor result `evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-producer-trace-result.json`, SHA-256 `d9b40965d4901df0544e460da7e16ac30b4ccd4cd97b07d2de2ec8b1afddf5f8`.

Reused route: the prior producer trace already validates a conditional `0x57100` map for four different literals, but it does not cover the `0xB168` literal, the `+0x660` installation, or identity between the initializer object and the branch dispatcher object. This verifier checks only those pointer/identity facts plus the single mapped callback body `0x9AD8` and its first state/helper effect. No broader ABL1 hunt, no 751C/95FC rerun, and no hardware/firmware action.

Next executable action: create and run `evidence/firmware-audit/20260920-clv-abl1-context660-callback-xhigh/abl1_context660_callback_verify.py` with `python3 -B`, capturing literal stdout/stderr/exit. It will validate raw bytes for constructor argument flow `0x74E0 -> 0xAF90 -> 0xB0C4`, dispatcher context flow at `0x10820`, both `+0x660` writer sites, conditional target anchor(s), the mapped candidate callback's selected-value-to-local-output flow, and the explicit unresolved object-identity boundary.

Expected effect: only this unique evidence directory, one report, and this action log. No firmware, hardware, settings, memory, shared plan, MCP/Cutter, install, global configuration, candidate, source, or commit changes.

Rollback: remove only this uniquely named evidence directory, report and action log.

## Correction after callback-store scan execution 1

Timestamp: 2026-09-20T10:20:32.567677+05:00
Command: `python3 -B evidence/firmware-audit/20260920-clv-abl1-context660-callback-xhigh/abl1_context660_callback_verify.py`. Exit status `1`; captured stderr reported `candidate callback non-stack direct stores` and listed the callback body stack locations (`0x9AE6`, `0x9AF0`, `0x9B30`, `0x9B68`, `0x9B70`, `0x9BB4`, `0x9BFA`, `0x9D28`, `0x9E3E`). Inspection of exact listing lines confirms each destination is `[SP+offset]`; the new verifier parser joined tab-separated mnemonic and operands incorrectly and classified them as non-stack.

Correction intent: only fix assembly-field parsing to combine the mnemonic and operand tab columns as space-separated text; preserve this failed capture, then rerun. No input or source bytes change.

## Correction after callback-local-store scan execution

Timestamp: 2026-09-20T10:25:23.754388+05:00
Observed verifier command: `python3 -B evidence/firmware-audit/20260920-clv-abl1-context660-callback-xhigh/abl1_context660_callback_verify.py`. Exit status `1`; captured stderr showed the callback-store scanner misclassified `STRD` stack slots because it split operands at commas inside `[SP,#offset]`. All listed stores were visibly stack-relative in the exact listing. The prior R4 no-write scanner was removed because it found real writes and was not needed for the ownership conclusion; the report will explicitly retract the earlier alias claim.

Correction intent: change only the store-destination parser to extract the bracketed memory operand, retain this failure capture, and rerun the same exact input test. No pinned input changes.

## Correction after output-slot instruction assertion

Timestamp: 2026-09-20T10:26:38.885846+05:00
Observed verifier exit status `1`; stderr: `AssertionError: candidate helper 6DA4 output is SP+0x14: got False`. The exact listing uses `ADD R2,SP,#0x14` at `0x9C26`, not the verifier phrase `SP+0x14`.

Correction intent: replace only the listing substring assertion with the exact `ADD R2,SP,#0x14` instruction and add its raw bytes `05 aa`; rerun on the same hashes.

## G7 intent: withdraw prior unchanged-R4 inference

Timestamp: 2026-09-20T10:32:43.758600+05:00
Fresh inspection of the exact listing found explicit R4 writes at `0x7F4C` (`ADD.W R4,R4,#0x2C0`) and `0x7FC2` (`SUB.W R4,R4,#0x2C0`) in the span that the earlier verifier scanned as unchanged. The earlier scanner had a tab parsing bug. The callback ownership conclusion must therefore use only the exact bases at the install and call sites; it must not state that the 0x73AE pointer necessarily remains unchanged through 0x8428.

Correction intent: add raw checks for these R4 write instructions and qualify the machine result/report as unresolved current-base identity; rerun the targeted callback verifier only. No broad traversal or input changes.

## Intent: reconcile final verifier count and misplaced result section

Timestamp: 2026-09-20T11:00:00+05:00
Actor: root-integrated bounded executor.
Target: this report/action-log pair and the unique callback evidence directory only.
Procedure: update the research report from the stale `93/93 PASS` text to the observed `97/97 PASS`, record the raw `0x7F4C`/`0x7FC2` R4-adjustment correction and final Procoder log path, and merge the final supplemental result from the malformed undated action-log duplicate into this dated log. Do not rerun broad analysis or alter pinned inputs.
Expected effect: documentation becomes consistent with the already captured verifier stdout/result and final Procoder log; no firmware, hardware, source input, or candidate changes.
Rollback: restore the pre-edit report and dated action log from the command-scoped backups or remove only the newly appended reconciliation sections; retain the malformed duplicate pending root review.

## Final supplemental callback660 result and code-check readback

Timestamp: 2026-09-20T10:49:28.554653+05:00
Fresh callback verifier command exited `0`: `97/97 PASS`; `verifier.stderr` is empty. The accepted result is `evidence/firmware-audit/20260920-clv-abl1-context660-callback-xhigh/abl1-context660-callback-result.json`. It verifies the candidate pointer map and exact callback body while retaining the explicit unresolved ownership boundary.

The final scoped Procoder check exited `0`: 0 unformatted, 0 unchecked, 0 out-of-scope, 0 blocking; broad repository hygiene findings are non-blocking. The literal log is `evidence/firmware-audit/20260920-clv-abl1-context660-callback-xhigh/procoder-check-final.log`. Python tests were not collected (`0 passed, 0 failed`) and remain unrun.

Current verified result: B0C4 installs pointer `0x60BD9` at the initializer base `R5`; under conditional base `0x57100` it maps to local candidate callback `0x9AD8`. The active dispatcher loads current `R4+0x660`; `R4` is derived from `[R6+0x3C4]` and has explicit adjustments at `0x7F4C`/`0x7FC2`. No dataflow proves that current slot equals the initializer slot. Candidate `0x9AD8` performs local bitfield/state assembly and stack-local writes only; helper `SVC #4` remains opaque. No direct MMIO/PLL/hardware effect or `MCLK=UCLK=FCLK` proof follows.
