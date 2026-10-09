# APOB/ABL1 handoff scope correction — action log

## Intent (recorded before owned artifact writes)

- Timestamp: 2026-09-21T15:59:04+05:00 (Asia/Almaty)
- Actor: `/root/clock_independent_review`
- Bound target/object: `/home/OWNER/orca/projects/bc250/docs/research/2026-09-21-clock-independent-review.md`, SHA-256 `a4401efe792349a802d01c92d697e1709a0a7f64a10e95cfbb99c0d4241bec4b`; exact firmware provenance target remains `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- GOAL: produce an owned correction-review copy for the newest memory-clock/APOB-ABL reports. Accept exact static edges; disallow a whole menu -> ABL/APOB chain unless a byte-backed dataflow join exists. Independently verify `AmdMemAm4Pei`'s service-pointer immediate, distinguishing `0x09E3B14C` from the root's truncated `0x09E3B14`.
- Checked sources: objective `docs/research/2026-09-21-clv-offline-target-decision.md` (SHA-256 `b3cf42a06c5292ac13ef96eccdb3ad219a9002861091bad8a49e1bb3c4b205e2`); memory `memory/oc-recheck.md`; exact reports `docs/research/2026-09-21-memory-clock-units-next.md` and `docs/research/2026-09-21-apob-abl-handoff-next.md`; machine result, verifier, input hashes, and evidence manifest under the corresponding `evidence/firmware-audit/20260921-*` directories.
- Single writer rule: own only the new `docs/research/2026-09-21-clock-independent-review-v2.md`, its diff/verification/rollback roles, evidence baseline copy, and this action log. Do not edit either worker report, `memory/`, the user guide, any firmware/evidence source, or the original prior review.
- Evidence transaction roles: `MODIFIED_FILE` is a corrected copy of the existing independent-review report with a new bounded correction section; `DIFF_FILE` reconstructs it; `VERIFICATION.txt` records baseline/modified/rollback checks and the decisive pointer-byte test; executable `ROLLBACK.sh` accepts a separate target copy and restores pristine bytes from the sibling baseline report.
- Planned matching behavior check: a read-only Python predicate prints whether a report contains the exact validated pointer statement `service-pointer-immediate=0x09E3B14C`; run on the baseline report, modified copy, and a separate rollback-restored copy, recording literal output/stderr/status and hashes.
- Scope/safety: offline, read-only source/evidence review only. No guide edit, network, board, NVRAM, ROM, candidate, register/MMIO/SMU, voltage, or hardware action.
- Expected finding: exact static `+0x316 -> $INV 0x11ED`, separate ABL1 APCB/CBS token-7 `0x24 -> 0x708`, separate APOB/PPI GUID/InstallPeiMemory chain; no byte-backed bridge between them. The pointer immediate is expected to decode as `0x09E3B14C`.
- Rollback: run the owned `ROLLBACK.sh` on a disposable modified report copy to restore the sibling baseline; do not change the original report or any worker artifact.

## Baseline behavior observed before modified-copy write

- Baseline file: `/home/OWNER/orca/projects/bc250/docs/research/2026-09-21-clock-independent-review.md` (SHA-256 `a4401efe792349a802d01c92d697e1709a0a7f64a10e95cfbb99c0d4241bec4b`).
- Command (read-only): `python3 -B -c 'import pathlib,sys; s=pathlib.Path(sys.argv[1]).read_text(); ok="service-pointer-immediate=0x09E3B14C" in s; print("service-pointer-immediate="+("0x09E3B14C" if ok else "NOT_PRESENT")); sys.exit(0 if ok else 1)' docs/research/2026-09-21-clock-independent-review.md`.
- Literal stdout: `service-pointer-immediate=NOT_PRESENT`; stderr empty; process exit `1` (expected baseline predicate: the previous memo did not yet include this newly verified pointer).
- Expected modified result: the same predicate must print `service-pointer-immediate=0x09E3B14C` and exit `0`.

## Observed result (after owned role writes)

- Timestamp: 2026-09-21T16:05:00+05:00 (Asia/Almaty)
- Independent direct source check passed: exact `AmdMemAm4Pei` module hash `1ef4e7b944672a9a48b6fcb16c4d35cb6d23bb8306429dc3eb10ee1d0c7bb5f8`; section-mapped RVA `0x08A0` -> raw `0x0708`; bytes `68 4C B1 E3 09` decode as `push imm32 0x09E3B14C`. The root spelling `0x9E3B14` omits the trailing `C`.
- The first broad `objdump` display attempt started before the instruction boundary (`RVA 0x0890`), so its apparent instruction decoding was not used. A corrected aligned disassembly at `RVA 0x08A0` and the direct byte/immediate check agree; no claim depends on the misaligned window.
- Reviewer conclusion: the three source paths are distinct. `$INV 0x11ED` from `AmdSetup+0x316`, ABL1 token-7 enum-to-policy mapping `0x24 -> 0x708`, and the APOB service/PPI/InstallPeiMemory chain are static findings, but no byte-backed join links them. Root's “whole chain menu -> ABL/APOB” conclusion is disallowed pending that missing dataflow.
- BASELINE behavior: predicate on original report prints `service-pointer-immediate=NOT_PRESENT`; exit `1`, stderr empty.
- MODIFIED_FILE behavior: same predicate prints `service-pointer-immediate=0x09E3B14C`; exit `0`, stderr empty.
- ROLLBACK.sh behavior: ran on separate `rollback-test.md`, exit `0`; restored hash equals baseline; same predicate prints `service-pointer-immediate=NOT_PRESENT`, exit `1`.
- Reapply behavior: restored the final v2 modified copy from the preserved modified bytes; predicate prints `reapplied_modified_file=GOAL_PRESENT`, exit `0`.
- Diff reconstruction: `diff` returned `1` (expected differences); `patch -p0` exited `0`; reconstructed copy is byte-identical to `MODIFIED_FILE` (`cmp` exit `0`).
- No guide, worker report/result, memory file, ROM, candidate, NVRAM, register, board, or network input was modified. Runtime PPI/APOB/ABL1/SMU execution, physical clocks, training, hardware acceptance, and rollback remain unrun.

## Correction to verification-record editing attempt

At 2026-09-21T16:12+05:00, an edit of `VERIFICATION.txt` used a Python here-document delimiter that collided with the embedded example delimiter. The tool output contained `SyntaxError: unterminated triple-quoted string literal` and a shell unmatched-quote error. A stray malformed shell continuation recorded exit `127` in `pointer-check.exit` and overwrote `pointer-check.stdout`/`.stderr` (stdout became empty; stderr captured `/usr/bin/bash: line 10: $'\nnew=python3': command not found`). This did not touch source reports or firmware. Preserve these failed outputs before replacing them; rerun the same source-byte check using a standalone, hash-pinned verifier script to avoid nested-heredoc parsing.

## New bounded static check intent — ABL1 stack/allocator helper correction

- Timestamp: 2026-09-21T16:31:54+05:00 (Asia/Almaty)
- Actor: `/root/clock_independent_review`
- Exact input: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`, 94,624 bytes, SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`; tied to donor ROM `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Literal sites to test from the new review request: ABL1 `0x463C`, `0x4664/0x4666`, `0x1FB4`, `0x4800`, `0x49CC`, `0x4B54`, helper `0x6238`, adjacent loops `0x6B68..0x6B82`. Derive stack delta, forwarded argument at `entrySP+4`, whether it is zero on the selected branch, helper register-level prototype limits, and fill-vs-copy behavior.
- Reuse: exact retained full Thumb listing `evidence/firmware-audit/20260921-memory-clock-units-next/abl1-full-thumb-llvm.txt` (`b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`); independently regenerate only narrow disassembly windows with existing local LLVM tools into unique evidence path `evidence/firmware-audit/20260921-apob-abl-stack-independent-review/` and verify raw bytes from the pinned payload. No new dependency/analyzer class.
- Acceptance: exact address-to-byte/disassembly correspondence; show calculation `0x34 + 0x6C = 0xA0`, `[SP+0xA4] = entrySP+4`, and caller provenance of the zero; show `0x6B78` body is a byte-store fill loop and distinguish `0x6B6A` load/store copy loop. Do not infer a ratio, memcpy for `0x6B78`, field source from another context, or hardware behavior.
- Safety: static, offline, read-only with respect to donor/ABL1; no board, network, firmware, ROM, NVRAM, register, candidate, or guide changes.

## G3 route check for the stack/helper subcheck

The existing `memory_clock_units_next_verify.py` verifies the enum table and stops at ABL item `0x17`/service `0x0C60`; it does not assert the caller stack arguments feeding `0x1FB4`, the `0x4800 -> 0x49CC` forwarding chain, or the `0x6238/0x6B78` helper body. Reusing its output alone would not adjudicate the new correction. Reuse its pinned exact ABL1 payload and local LLVM 22.1.8 tools, regenerate only the listed narrow windows in the unique evidence directory, and assert the handful of direct branch/store/load bytes. This does not repeat or broaden any UEFI token scan and is not a hardware test.

## Additional bounded comparison intent — call at ABL1 `0x0862`

Parent noted an earlier “outer `0x864` heap-chain” interpretation. Before deciding that claim, inspect the exact call-site at ABL1 `0x0834..0x0866` in this same pinned payload and compare its argument construction with the distinct `0x4B5C -> 0x6238` call. Acceptance is a caller-local distinction (actual R0/R1 values and local descriptor bytes), not a global negative or semantic heap naming. Output goes only to the same unique evidence directory.

## Verifier attempt 1 correction (before rerun)

- Command: `python3 -B evidence/firmware-audit/20260921-apob-abl-stack-independent-review/verify_stack_path.py > evidence/firmware-audit/20260921-apob-abl-stack-independent-review/verifier.stdout 2> evidence/firmware-audit/20260921-apob-abl-stack-independent-review/verifier.stderr`.
- Observed exit: `1`; stdout empty; stderr named only `reader helper call to 0x4800`: the raw Thumb bytes are `02 f0 0e fc`, not the mistyped `02 f2 0e fc`. This is verifier byte-endianness/transcription only; the disassembly at `0x1FE0` is `bl 0x4800` and the input is unchanged.
- Preserve attempt-1 stdout/stderr/exit under unique `verifier-attempt1.*` paths, correct expected raw bytes, and rerun the same pinned input. A separate manual review also caught a second unrun expected string in this verifier: the `0x0862 -> 0x6238` BL raw bytes from the retained exact listing are `05 f0 e9 fc`, not `05 f5 e9 fc`; correct both before retry. No other scope is added.

## Verifier attempt 2 correction (before rerun)

- Command: `python3 -B evidence/firmware-audit/20260921-apob-abl-stack-independent-review/verify_stack_path.py > .../verifier.stdout 2> .../verifier.stderr`.
- Observed exit: `1`; checks reached the final fill-loop branch and stopped at `0x6B80`: raw bytes were observed as `FB D2`, not the mistyped `F9 D2`. The fresh listing shows Thumb word `D2FB` (back branch to `0x6B7A`); this is another manual raw-byte transcription error. Preserve attempt-2 outputs. Two failures are from the same manual-anchor class; if another recurs, switch to address/mnemonic parsing rather than continue editing expected hex.

## Follow-up intent — verify conditional ABL1 stack/helper path

- Timestamp: 2026-09-21T16:32:00+05:00 (Asia/Almaty)
- Current MODIFIED_FILE baseline: `docs/research/2026-09-21-clock-independent-review-v2.md`, SHA-256 `aa5d694468f684e8c608fdfe506fc0608a6b9e300f10295eababc54ab1d6e839`. The original base review and this v2 copy are distinct artifacts; do not overwrite the earlier report.
- New GOAL: review the exact ABL1 branch/call chain `0x463C/0x4664/0x4666 -> 0x1FB4 -> 0x4800 -> 0x49CC -> 0x4B54 -> 0x6238`, with the separate `0x0862 -> 0x6238` call-site comparison and `0x6B6A` copy loop vs `0x6B78` fill loop. Keep it conditional/static and do not label it FCLK or a clock-ratio/application result without a namespace/domain join.
- Fresh static output: `evidence/firmware-audit/20260921-apob-abl-stack-independent-review/` on exact ABL1 SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`; `verify_stack_path.py` reports `43/43 PASS` after retaining two byte-transcription correction attempts.
- Planned copy transaction: save current v2 as a sibling pristine baseline, append one scoped correction section to v2, regenerate the same DIFF_FILE, update VERIFICATION.txt, and point the executable ROLLBACK.sh at the new sibling baseline. Test baseline/modified/rollback using the same stack-correction predicate on the report file. Run rollback only on a separate copy, then reapply the goal to MODIFIED_FILE.
- No guide, memory, worker-owned report/result, firmware, ROM, NVRAM, register, candidate, board, or network write.

### Follow-up BASELINE behavior before v2 modification

- Command: `python3 -B -c 'import pathlib,sys; s=pathlib.Path(sys.argv[1]).read_text(); ok="selected-0x0F-path-entrySPplus4-zero" in s; print("ABL1_stack_correction="+("PRESENT" if ok else "NOT_PRESENT")); sys.exit(0 if ok else 1)' docs/research/2026-09-21-clock-independent-review-v2.md`.
- Literal stdout: `ABL1_stack_correction=NOT_PRESENT`; stderr empty; exit `1` (expected baseline lacks new ABL1 stack check).

## Follow-up intent — independent SVC #6 ABI boundary review

- Timestamp: 2026-09-21T17:46:15+05:00 (Asia/Almaty)
- Actor: `/root/clock_independent_review`
- Target report reopened: `/home/OWNER/orca/projects/bc250/docs/research/2026-09-21-abl-item17-svc6-consumer.md`; exact ABL1 input/wrapper remains `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl-item17-consumer/ABL1-clv-full-thumb.elf.o` plus its exact decompressed payload.
- GOAL: independently check the SVC #6 wrapper ABI around `0x12AC..0x12C8`, its callers (`0x10FA/0x1104`, `0x11E6/0x11E8`), and the local `0x6D10==1` gate, then classify whether any visible ABL write reaches a known clock register. The SVC handler is outside the extracted ABL1; do not infer its semantics.
- Route: re-read exact source bytes and create fresh narrow LLVM windows and a deterministic local check in the unique evidence directory `evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/`. Reuse the exact ABL1 bytes/hash and prior state result; do not repeat the 136-check item17 table verifier, any full scan, or any other owner's SVC implementation work.
- Expected effect: byte-backed wrapper register/stack arguments, literal/SVC bytes, visible-memory-write limits, and exact scope of the local `0x6D10` branch; no physical PLL/clock claim.
- Safeguards: offline/read-only; no guide, worker report, memory file, ROM, firmware, NVRAM, register, candidate, board, network, or hardware changes.
- Rollback: delete only this unique evidence directory and the appended correction text in the owned v2 review copy if invalidated; retain the pristine baseline and append-only action log.

## Follow-up intent — item17 SVC6 reachability adjudication

- Timestamp: 2026-09-21T18:01:50+05:00 (Asia/Almaty)
- Actor: `/root/clock_independent_review`
- Inputs reopened: `docs/research/2026-09-21-abl-item17-svc6-consumer.md` and `docs/research/2026-09-21-item17-reachability-review.md`; their machine results are retained under the corresponding `evidence/firmware-audit/20260921-*` directories. Exact ABL1 raw payload SHA-256 remains `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- GOAL: independently verify the **local** conditional path `0x6D10 -> 0x6C20 output+4 -> 0x95FC [SP+0x164] -> 0x9646 -> 0x9744 -> 0x984E`; establish whether it can reach the item17 SVC6 alternatives (`0x9780`, `0x97E4`, `0x9800`) or any directly visible clock-register write. Do not recheck table row/base arithmetic, repeat the 136/121-count item17 verifiers, or follow the external SVC handler.
- Existing route: use exact ABL1 payload and newly produced local SVC/dispatch windows; regenerate only fresh narrow disassembly and a small raw-byte verifier in the unique `evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/reachability/` directory. New verifier covers the guard/branch/call-site range only, not the callback-table map.
- Expected classification: conditional static reachability only; no PLL/clock application claim. If the selected branch skips SVC6, name the next visible ABL1 continuation/return; if any branch reaches it, stop at the SVC handler boundary.
- Safeguards: no guide/worker-file edits, network, board, firmware/NVRAM/register/candidate write, or hardware action. Output supplements only this owned review/log and unique evidence.

## Reachability subcheck intent — do not infer SVC from its opaque ABI

- Timestamp: 2026-09-21T18:04:14+05:00 (Asia/Almaty)
- Actor: `/root/clock_independent_review`
- Newly reopened item17 reachability report: `docs/research/2026-09-21-item17-reachability-review.md`; result `evidence/firmware-audit/20260921-item17-reachability-review/item17-reachability-result.json` currently reports `121/121 PASS` (the human report's reproduction paragraph says `56/56`, so treat that count mismatch as a report bookkeeping discrepancy, not new semantic evidence).
- GOAL: independently test only the local helper/gate/callsite path from `0x6D10` through `0x6C20`/`0x95FC` to `0x984E`, and decide whether `0x0DD4`, `0x118C`, `0x10C0`, or SVC #6 can execute on that path. Do not rescan/revalidate the item-17 callback table or candidate base. Reopen the already exact CLV ABL1 payload and the SVC report's local bytes.
- Fresh windows/raw check belong only under `evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/reachability/`. Acceptance: static byte-backed branch condition and return path; external SVC handler remains opaque; no clock register write or applied ratio inference.
- Safety: read-only; no guide edits, hardware, board, network, ROM, NVRAM, register, firmware, or candidate write.

## Next reachable-edge intent — ABL1 single-state call at 0x984E

After the direct conditional-branch check, SVC #6 is not reached on the selected item17 path. The fresh window shows that the bypass target `0x984E` contains a direct `BL 0x130C`; this is the next local ABL edge worth classifying, not a repeat of SVC ABI work. Before adding the targeted disassembly, record intent: inspect only `0x984E..0x98B0` and the exact helper entry `0x130C..0x1360` from the pinned ABL1; determine register/stack arguments, return/data stores, and any direct register-write evidence. Stop at opaque indirect/provider calls; do not connect it to `$INV 0x11ED`, physical 1800, ratio, or training without a byte-backed join. Output stays in the same unique evidence directory; no broader census.

## G6 method-class change for reachability subcheck

The first raw-byte verifier attempt in `evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/reachability/verify_reachable_config.py` exited `1` on the first check: bytes at `0x6D1E..0x6D22` are `01 20 10 BD` (`MOVS R0,#1; POP {R4,PC}`), while the manually entered expected string was `01 20 BD 10`. This is a raw-byte window/Thumb halfword transcription error, not a source or runtime result. Earlier two checks in `verify_stack_path.py` also failed on manually transcribed Thumb bytes. This is the third same-kind failure, so G6 now changes method class: the final reachability verifier will parse exact-address/mnemonic/operand records from the fresh byte-disassembler windows, compute the stack-frame arithmetic from decoded push/sub operands, and stop using manually typed instruction-byte expectations for this path. The failed attempt's `verifier.stderr` and `.exit` remain preserved; no source changed.
