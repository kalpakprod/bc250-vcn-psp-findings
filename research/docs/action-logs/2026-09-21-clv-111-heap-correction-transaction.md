# CLV 1:1:1 draft — ABL1 HEAP-source correction transaction

## Intent (recorded before role writes)

- Timestamp: 2026-09-21T17:01:52+05:00 (Asia/Almaty); actor: root project executor.
- TARGET: exact offline CLV donor `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, 16,777,216 bytes, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Input ABL1 payload: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`, 94,624 bytes, SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`. Exact Thumb object: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o`, SHA-256 `54abef3a390abb0ff745685de2eed4e0e8db5e9ba27bba1a0f245573b47ff135`.
- Existing route reused: exact `.data`/Thumb object and direct aligned LLVM 22.1.8 windows; fresh root windows are retained under `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-apob-abl-outer864-root-review/`. Manual raw bytes are read with GNU `od` after `xxd` was observed unavailable. Do not rerun the old 34-check verifier or the concurrent orchestration verifier.
- Evidence qualification: inspect the bounded `0x463C -> 0x1FB4 -> 0x4800 -> 0x49CC -> 0x4B54 -> 0x6238 -> 0x6B78` path and compare direct raw bytes to fresh disassembly. Preserve old PASS report as superseded provenance; no byte-backed edge connects `outer+0x864` to the provider's second stack argument in this path. Keep constructor's own frame-local `SP+0xA4` distinct.
- The guide change stays a copy; original `/home/OWNER/orca/projects/bc250/docs/guides/bc250-clv-111-evidence-draft.md` is expected to remain SHA-256 `334d6b879156bb2ba773c2d2d766ddc54cbacd37e33e3eab3bab949d2fe8e065`. Behavior check on that original already produced `{"heap_claim_status": "asserted", "path": "/home/OWNER/orca/projects/bc250/docs/guides/bc250-clv-111-evidence-draft.md"}`, stderr empty, exit `0`.
- Required role set: MODIFIED_FILE = `/home/OWNER/orca/projects/bc250/docs/guides/bc250-clv-111-evidence-draft-corrected.md`; DIFF_FILE = `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-apob-abl-outer864-root-review/DIFF_FILE.patch`; VERIFICATION.txt and executable ROLLBACK.sh beside it, with BASELINE.md as rollback source. The report is supplemental at `/home/OWNER/orca/projects/bc250/docs/research/2026-09-21-apob-abl-outer864-root-verification.md`.
- Expected result: change only the guide's active HEAP interpretation to `HEAP claim status: WITHDRAWN`; preserve prior `34/34 PASS` as historical bytes-only evidence; state static zero-fill and stack-argument result with runtime/load-base/clock/training/voltage/hardware boundary. Guide remains DRAFT / NOT READY.
- Rollback: run ROLLBACK.sh on a separate disposable copy of MODIFIED_FILE; it restores sibling BASELINE.md bytes. Verify restored hash equals the original, then reapply GOAL to the final MODIFIED_FILE. No ROM/NVRAM/register/hardware/network write.

## Correction — guide next-action marker typo, no role files written

The first Python transaction draft successfully checked the source-guide hash and section boundaries but aborted with `SystemExit: expected current-status next-action line not found exactly once` because its anchor began `-- **Next offline action:**`; the guide contains one leading hyphen. No baseline, MODIFIED_FILE, or report was written. The following `sha256sum` command then printed “No such file or directory” for those intentionally not-yet-created paths; the shell cell exited `1`. Correct the anchor to the exact single-hyphen line (or match its line prefix) and re-read the guide before writing roles. Original guide hash remains `334d6b879156bb2ba773c2d2d766ddc54cbacd37e33e3eab3bab949d2fe8e065`.

## Correction — baseline predicate classification (before rerun)

The first transaction role checks classified `BASELINE.md` and rollback-restored bytes as `unknown` because the predicate only matched the new report wording (`0x6B78` “as copying”) while the original guide uses `payload copy via 0x6B78`. The baseline and rollback commands therefore exited `1`; the rollback script itself exited `0` and restored the expected source hash. This is a predicate-coverage error, not an artifact mismatch. Extend the predicate to recognize the exact original guide phrase, rerun the same BASELINE/MODIFIED/ROLLBACK/REAPPLY checks, and rewrite only the ledger outputs after readback.

## Correction — DIFF_FILE reconstruction labels (before rerun)

The first ledger recorded `patch -p0` exit `1` because `DIFF_FILE.patch` used absolute source paths while the disposable reconstruction used `guide.md`; the controlled fallback copied MODIFIED_FILE bytes and produced the expected hash, but that was not a patch reconstruction. Recreate DIFF_FILE with explicit sibling labels `BASELINE.md` and `MODIFIED.md`, apply it in a fresh disposable directory to `BASELINE.md`, and require byte equality with MODIFIED_FILE. Preserve the prior failed patch output and status; no source guide or firmware input changes.

## Observed role checks — corrected predicate and patch reconstruction

- The revised predicate returned `BASELINE` asserted/exit `0`, `MODIFIED_FILE` withdrawn/exit `0`, separate rollback-restored copy asserted/exit `0`, and re-applied modified copy withdrawn/exit `0`; stderr was empty for all four.
- `ROLLBACK.sh` exited `0`; the restored copy SHA-256 equals BASELINE/source `334d6b879156bb2ba773c2d2d766ddc54cbacd37e33e3eab3bab949d2fe8e065`; `cmp` returned `0`.
- The first absolute-path patch attempt remains preserved as exit `1`/fallback provenance. A second DIFF_FILE was written with explicit labels and applied to a disposable BASELINE copy; `patch` exited `0`, reconstructed hash equals MODIFIED_FILE `c01fc5b4d9a9cab549119a192e176b113c2d6eac6256946009a235ac7cf93c06`, and `cmp` returned `0`.

## Correction — DIFF_FILE hash drift during shared-workspace reopen

Final role reopen observed `DIFF_FILE.patch` SHA-256 `81c617cee97e53e4cbe2fb6f285f04a40b8ff19db6f0c575f1a1a04062255629`, while the just-written VERIFICATION ledger retained the earlier hash `a7e24f...`. The current patch still applies with exit `0` and reconstructs MODIFIED_FILE byte-identically; this is shared-workspace artifact drift, not a semantic change. Before reporting, reread current DIFF_FILE and all four roles, then rewrite VERIFICATION.txt with the current patch hash and rerun the patch/hash checks. No source guide, ROM, payload, or firmware changed.

## Final role reopen and ledger consistency (observed)

- MODIFIED_FILE reopened: `/home/OWNER/orca/projects/bc250/docs/guides/bc250-clv-111-evidence-draft-corrected.md`, 18,754 bytes, SHA-256 `c01fc5b4d9a9cab549119a192e176b113c2d6eac6256946009a235ac7cf93c06`.
- DIFF_FILE reopened: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-apob-abl-outer864-root-review/DIFF_FILE.patch`, SHA-256 `81c617cee97e53e4cbe2fb6f285f04a40b8ff19db6f0c575f1a1a04062255629`; explicit-label patch applied with exit `0` and `cmp` exit `0`.
- VERIFICATION.txt reopened: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-apob-abl-outer864-root-review/VERIFICATION.txt`, SHA-256 `4feec772d3ef0b5b76fa0615ea52e3e2f63467225e6ecf24fceb44eb30a041b5`.
- ROLLBACK.sh reopened: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-apob-abl-outer864-root-review/ROLLBACK.sh`, executable mode `755`, SHA-256 `9ae05df1cf810d110b9fd57a38b34066863c2aefc654c6ff72f08ca58246b75b`.
- BASELINE/source SHA-256 remains `334d6b879156bb2ba773c2d2d766ddc54cbacd37e33e3eab3bab949d2fe8e065`; original guide reopened with the same hash. BASELINE/MODIFIED/ROLLBACK/REAPPLY predicates all exit `0` with asserted/withdrawn/asserted/withdrawn results; rollback restored `cmp=0`.

## Parent-requested item-17 reachable-output check — intent and source-path correction

- Timestamp: 2026-09-21T18:58:18+05:00 (Asia/Almaty). Re-opened objective attachments: `docs/research/2026-09-21-abl-item17-consumer.md` and `docs/research/2026-09-21-abl-item17-reachable-output.md`.
- Parent-bounded check: directly trace `0x7E40` aggregate load -> `0x7E74` call -> callee `0x5E68` -> output store `0x5FBA` using fresh exact-object disassembly and independent raw bytes in a disposable `/tmp` copy. Preserve the candidate base `0x57100` only as conditional static coherence; no clock units or hardware implication.
- First copy attempt used missing `evidence/firmware-audit/20260921-abl-item17-reachable-output/ABL1-clv-decompressed.bin`; shell reported `cp: cannot stat` and the tool command exited `1` before disassembly. The reachable-output directory contains the wrapper, not a payload copy. Use existing hash-pinned payload `evidence/firmware-audit/20260921-abl-item17-consumer/ABL1-clv-decompressed.bin` for the independent raw-byte window; preserve the missing-path failure and do not alter worker artifacts.
- Reuse prior object wrapper `evidence/firmware-audit/20260921-abl-item17-reachable-output/ABL1-clv-full-thumb.elf.o` SHA-256 `adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6`; expected payload SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`. No prior verifier replay; only direct windows/raw bytes.
- Reopen the same guide transaction roles after the check and repeat the existing behavior predicate on BASELINE/MODIFIED/ROLLBACK; do not modify guide or any worker report.

## Intent — supplement same verification role with item-17 output edge (before ledger update)

- Timestamp: 2026-09-21T19:04:30+05:00 (Asia/Almaty). Parent-requested extension; preserve the exact same MODIFIED_FILE, DIFF_FILE, VERIFICATION.txt and ROLLBACK.sh paths. Do not edit the guide or any worker report.
- New check already executed in disposable `/tmp/bc250-item17-5e68-chain-g0V8cz`: fresh LLVM 22.1.8 windows of `0x7E3E..0x7E7A` and `0x5E68..0x5FC2`, plus GNU `od` raw-byte captures at `0x7E40`, `0x7E6E`, `0x5E68` and `0x5FBA`; all disassembly windows exited `0`, stderr empty. The initial miss-path copy attempt against `reachable-output/ABL1-clv-decompressed.bin` exited `1` because that directory contains no payload copy; corrected input is the hash-pinned item17-consumer payload `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Expected conditional static finding: caller `0x7E40` loads `[R0+0x2BC]` to R6, passes it as R2 at `0x7E74 -> 0x5E68`; callee saves R2 in R4 and R0/context in R5; on the branch where the halfword at `[context+4]+0x790` is not 6, a getter result is stored at `[context+0x78]` by `0x5FBA`. No unit, frequency, hardware, or runtime loader-base inference.
- Append direct command/hash/output evidence to VERIFICATION.txt. Then rerun the identical existing predicate and inputs for BASELINE/ MODIFIED / ROLLBACK, reopen all four absolute role paths, and retain all prior statuses. No old 34/136/128 verifier rerun.

## Observed parent-requested item-17 output check

- Timestamp: 2026-09-21T19:28:08+05:00 (Asia/Almaty), actor: root.
- One initial source-path lookup failed before disassembly: the reachable-output artifact has no `ABL1-clv-decompressed.bin`; `cp` returned “cannot stat” and the tool command exited `1`. The exact payload was then copied from the existing `20260921-abl-item17-consumer` evidence directory; payload hash remained `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`. The wrapper hash remained `adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6` and matches item17-consumer and prior exact wrapper copies byte-for-byte.
- In disposable CWD `/tmp/bc250-item17-5e68-chain-g0V8cz`, fresh LLVM 22.1.8 Thumb windows `0x7E3E..0x7E7A` and `0x5E68..0x5FC2` each exited `0`, stderr `0` bytes. Independent `od` reads at `0x7E40`, `0x7E6E`, `0x5E68`, and `0x5FBA` also exited `0` with empty stderr; exact output copies and SHA-256 ledger are under `evidence/firmware-audit/20260921-apob-abl-outer864-root-review/item17-post-callback-*`, and the separate manifest verifies every listed file.
- Direct finding: `0x7E40` loads `[R0+0x2BC]` into R6; `0x7E6E..0x7E74` passes that value in R2 to `0x5E68`. Callee entry stores R0/context in R5 and R2/input in R4. On the `*[context+4]+0x790 != 6` path, it calls selector-`0x0F` reader `0x463C`, reads the result from `[SP+4]`, then stores R3 as a halfword to `[R5+0x78]` at `0x5FBA`; equality to 6 branches away to `0x6028`. This is a conditional static local field flow, not a clock/unit/training/hardware claim.
- Object identity remains byte-identical across exact wrapper copies, but table-based reachability uses only the conditional candidate base `0x57100`; actual loader/runtime base and later `0x8428` object identity remain unresolved.
- No old 34-, 136-, or 128-check verifier was rerun. The older 7/7 manifest is mentioned only as file-integrity, not as independent semantic confirmation. Four guide-role behavior rechecks remain the final step.

## Final observed parent-requested check and role readback

- Timestamp: 2026-09-21T19:40:51+05:00 (Asia/Almaty).
- The first disposable copy command's stderr was `cp: cannot stat 'evidence/firmware-audit/20260921-abl-item17-reachable-output/ABL1-clv-decompressed.bin': No such file or directory`; shell tool status `1` occurred before disassembly. Corrected payload source `evidence/firmware-audit/20260921-abl-item17-consumer/ABL1-clv-decompressed.bin` was then copied into `/tmp/bc250-item17-5e68-chain-g0V8cz`; exact payload and object hashes matched the project inputs, and `cmp` returned `0` for both copied inputs.
- Fresh direct `llvm-objdump` windows `0x7E3E..0x7E7A` and `0x5E68..0x5FC2` each returned exit `0` with empty stderr. Raw GNU `od` windows for `0x7E40`, `0x7E6E`, `0x5E68`, and `0x5FBA` returned exit `0` with empty stderr. Captures are preserved under `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-apob-abl-outer864-root-review/item17-post-callback-*`; manifest SHA-256 `a80fc5342c3417da64fd82946c250dd9e6daa6406d956fa1334da7464da54657`, `sha256sum -c` passed all listed entries.
- New finding: `[context+0x2BC]` is loaded at `0x7E40` to `R6`; `0x7E6E..0x7E74` passes it in `R2` to `0x5E68`. `0x5E68` preserves its context pointer in `R5` and input R2 in `R4`. On the nested-value-not-6 branch, a selector-`0x0F` call to `0x463C` returns a local halfword read from `[SP+4]` and stores it to `[R5+0x78]` at `0x5FBA`; if the nested halfword is `6`, branch `0x5FA2 -> 0x6028` bypasses that store. Evidence class is static/observed bytes only; it assigns no unit, frequency, clock role, training effect, or hardware behavior. The candidate-base `0x57100` callback binding remains conditional; later object identity (including `0x8428`) remains unresolved.
- The existing item17 136-check and reachability 128-check verifiers were not rerun; no aggregate PASS is claimed by this new check. Earlier 34-check manifest remains file-integrity only.
- Repeated BASELINE/MODIFIED/ROLLBACK/REAPPLY behavior checks: asserted/withdrawn/asserted/withdrawn respectively, all predicate exits `0`, empty stderr. `ROLLBACK.sh` exit `0`; restored hash equals baseline and `cmp` exit `0`. Follow-up capture manifest `followup-20260921/SHA256SUMS.final` SHA-256 `050e2d9024a57841af57bc413053bfd18678f3375bd082f1d9763e68897fccc5` passed.
- Final four-role hashes reopened: MODIFIED_FILE `c01fc5b4d9a9cab549119a192e176b113c2d6eac6256946009a235ac7cf93c06`; DIFF_FILE `81c617cee97e53e4cbe2fb6f285f04a40b8ff19db6f0c575f1a1a04062255629`; VERIFICATION.txt `6f624f92cdc1a9d22ed70b0ad7d620b6bff7c67b1e364a0f8cebbb552a04cfea`; ROLLBACK.sh `9ae05df1cf810d110b9fd57a38b34066863c2aefc654c6ff72f08ca58246b75b`. BASELINE and original-guide hash remain `334d6b879156bb2ba773c2d2d766ddc54cbacd37e33e3eab3bab949d2fe8e065` and `334d6b879156bb2ba773c2d2d766ddc54cbacd37e33e3eab3bab949d2fe8e065` respectively.
- No ROM, firmware, NVRAM, register, hardware, network, candidate, or source-guide write occurred.

## Follow-up end-state re-open — same four roles and behavior inputs

- Timestamp: 2026-09-21T19:43:39+05:00 (Asia/Almaty). The identical predicate/input-role checks were repeated after the supplemental result was appended.
- BASELINE: asserted, exit `0`, stderr empty. MODIFIED_FILE: withdrawn, exit `0`, stderr empty. ROLLBACK: rollback script exit `0`; restored hash `334d6b879156bb2ba773c2d2d766ddc54cbacd37e33e3eab3bab949d2fe8e065`, equals BASELINE; `cmp` exit `0`; predicate asserted/exit `0`. REAPPLY copy: withdrawn/exit `0`. Fresh follow-up manifest `evidence/firmware-audit/20260921-apob-abl-outer864-root-review/followup-final-20260921/SHA256SUMS.final`, SHA-256 `5aa2a494df5d23d00f49eb69ed6f5845caabfbdcba740632d5c9126c80cdd5df`, all listed files re-opened `OK`.
- Same four role paths reopened: MODIFIED_FILE `c01fc5b4d9a9cab549119a192e176b113c2d6eac6256946009a235ac7cf93c06`, DIFF_FILE `81c617cee97e53e4cbe2fb6f285f04a40b8ff19db6f0c575f1a1a04062255629`, VERIFICATION.txt `6f624f92cdc1a9d22ed70b0ad7d620b6bff7c67b1e364a0f8cebbb552a04cfea`, executable ROLLBACK.sh `9ae05df1cf810d110b9fd57a38b34066863c2aefc654c6ff72f08ca58246b75b`. Original guide remains SHA-256 `334d6b879156bb2ba773c2d2d766ddc54cbacd37e33e3eab3bab949d2fe8e065`; ROM remains `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- This completed a direct conditional static dataflow check only; it does not upgrade any physical clock/training/voltage/hardware claim or resolve loader base/object identity outside the exact local caller.

## Final follow-up result and four-role re-open

- Timestamp: 2026-09-21T19:47:37+05:00 (Asia/Almaty). The exact source object/payload copies in the disposable check matched the pinned inputs byte-for-byte; direct commands exited `0`, stderr was empty, and `item17-post-callback-SHA256SUMS.final` rechecked all capture entries `OK`.
- New static edge: `0x7E40` loads context `[R0+0x2BC]` into R6; the call site at `0x7E74` passes R2=R6, R1=R5, R0=R4 into `0x5E68`. That callee saves `R5=R0` and `R4=R2`. On the nested halfword `*[R5+4]+0x790 != 6` branch, it calls `0x463C` with an output local initialized to `0x4B0`, reads the returned halfword into R3, and stores R3 at `[R5+0x78]` at `0x5FBA`; `BEQ 0x6028` on equality to 6 bypasses that store. This is conditional local static flow only, with no frequency unit, physical clock, training or hardware conclusion. The callback base `0x57100` remains conditional; later `0x8428` object identity remains unresolved.
- Same four roles reopened after the check: MODIFIED_FILE `c01fc5b4d9a9cab549119a192e176b113c2d6eac6256946009a235ac7cf93c06`, DIFF_FILE `81c617cee97e53e4cbe2fb6f285f04a40b8ff19db6f0c575f1a1a04062255629`, VERIFICATION.txt `6f624f92cdc1a9d22ed70b0ad7d620b6bff7c67b1e364a0f8cebbb552a04cfea`, executable ROLLBACK.sh `9ae05df1cf810d110b9fd57a38b34066863c2aefc654c6ff72f08ca58246b75b`.
- Same predicate and input roles re-run: BASELINE asserted/exit `0`, MODIFIED withdrawn/exit `0`, ROLLBACK asserted/exit `0` with rollback script exit `0`, restored hash equal to baseline and `cmp=0`; REAPPLY withdrawn/exit `0`. Stderr empty throughout. Final repeat ledger: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-apob-abl-outer864-root-review/followup-final-20260921/SHA256SUMS.final` (all listed files `OK`).
- Original guide remains unchanged at SHA-256 `334d6b879156bb2ba773c2d2d766ddc54cbacd37e33e3eab3bab949d2fe8e065`; ROM remains unchanged at `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`. No firmware, NVRAM, register, board, network, or candidate write occurred.

## Intent — AF58/item17 evidence-table integration continuation (before candidate write)

- Timestamp: 2026-09-21T20:46:04+05:00 (Asia/Almaty); actor: root project executor.
- ACTIVE_OBJECT: `/home/OWNER/orca/projects/bc250/docs/guides/bc250-clv-111-evidence-draft-corrected.md`; original guide remains immutable.
- NEXT_EXECUTABLE_ACTION: update only the corrected guide's evidence table with byte-backed AF58 helper contracts (`[2,1]` arguments and no clock writes), conditional item-17/callback/table boundaries, and an explicit unresolved hardware gate. Preserve the retracted HEAP source-copy claim and all existing NOT READY language.
- Inputs: `docs/research/2026-09-21-abl-item17-reachable-output.md`, `docs/research/2026-09-21-abl-item17-consumer.md`, exact wrapper/payload evidence; no ROM or firmware write.
- Required follow-up: reuse MODIFIED_FILE, DIFF_FILE, VERIFICATION.txt, ROLLBACK.sh under `evidence/firmware-audit/20260921-apob-abl-outer864-root-review/`; rerun matching text/evidence predicates and BASELINE/MODIFIED/ROLLBACK behavior.
- Expected status: static-only update; loader base, SVC semantics, clocks, training, voltage, and hardware acceptance remain unresolved.

## Candidate observed — AF58/item17 evidence-table patch ready for role write

- Timestamp: 2026-09-21T20:47:54+05:00 (Asia/Almaty). Disposable candidate `/tmp/bc250-guide-af58-item17-final-IgrfGw/candidate.md` was created from the current MODIFIED_FILE and patched only in the requirement-to-evidence matrix. Candidate SHA-256: `0aa1b5e5580d8d136c41be2d03c092dcf88aa2c1b1df1cf09141ec88c537847d`; bytes: `19990`.
- Added rows: AF58 helper contract (`0x5CBE` `[2,1]`, `0xFE60` returns 1, no direct `0x7378`/`0xAF90` or clock-register operation); conditional item-`0x17`/`0x95FC` output edge; explicit hardware acceptance gate. Existing HEAP retraction and NOT READY claims are retained.
- Next write: copy this candidate into MODIFIED_FILE only, regenerate DIFF_FILE from immutable BASELINE labels, update VERIFICATION.txt, then rerun the same behavior predicates/rollback. Original guide remains immutable.

## Observed role write — AF58/item17 table integration

- Timestamp: 2026-09-21T20:48:33+05:00 (Asia/Almaty). Disposable candidate copied into MODIFIED_FILE; original guide unchanged. MODIFIED_FILE hash is `0aa1b5e5580d8d136c41be2d03c092dcf88aa2c1b1df1cf09141ec88c537847d`.
- DIFF_FILE regenerated from immutable BASELINE with labels `BASELINE.md`/`MODIFIED.md`; current hash `7bbb043ddb63010e7560a929935c1eb88297d0552286a2c137eb834516819f10`; `diff` expected exit `1` because files differ.
- Matrix now explicitly records AF58 helper `[2,1]`/no-clock-write contract, conditional item-`0x17` callback/output edge, and explicit unresolved hardware acceptance gate.
- Next: update VERIFICATION.txt and run matching text/evidence predicates plus patch reconstruction and rollback.

## Intent — AF58/item17 guide evidence predicate and role verification

- Timestamp: 2026-09-21T20:48:58+05:00 (Asia/Almaty). Write a small read-only text/evidence predicate under `evidence/firmware-audit/20260921-apob-abl-outer864-root-review/table-integration-20260921/`. It will verify exact matrix tokens, the AF58 corrected result (`22/22 PASS`, helper `[2,1]`, no direct `0x7378`/`0xAF90`), item17 conditional/table boundary tokens, explicit hardware-gate wording, and pinned report/hash inputs.
- Then update only VERIFICATION.txt's current role hashes and supplemental ledger, reconstruct DIFF_FILE in disposable space, and repeat the identical BASELINE/MODIFIED/ROLLBACK behavior predicate with empty-stderr/exit records.
- No original guide, ROM, payload, worker report, or firmware artifact will be modified.

## Correction — item17 predicate wording mismatch before rerun

- Timestamp: 2026-09-21T20:50:23+05:00 (Asia/Almaty). The new evidence predicate exited `1` because it required the exact phrase `conditional static`; the reopened item17 report uses conditional wording but not that two-word phrase, while it does contain `No frequency or clock unit is assigned.` and the hardware boundary. No role or input file changed; the result JSON was not emitted.
- Correction: test the report for its observed conditional wording plus the exact no-unit/hardware sentences, then rerun the same predicate and capture status.

## Observed evidence predicate — AF58/item17 table integration

- Timestamp: 2026-09-21T20:51:21+05:00 (Asia/Almaty). Corrected text/evidence predicate ran exit `0`, stdout `PASS`, `17/17`, stderr empty. Initial wording-only predicate failure is retained as a harness correction; no finding/input changed.
- AF58 corrected result JSON: `PASS`, `22/22`; no direct `0x7378`/`0xAF90` or clock-register operation in helper bodies. Item17 report preserves conditional/no-unit/hardware boundaries.
- Predicate evidence directory: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-apob-abl-outer864-root-review/table-integration-20260921`; manifest SHA-256 `ab4829045a322f482988c2e40aaf5a3f350596ea21a14e01f25f4b20bc995ce9`, absolute verification exit `0`.

## Correction — AF58 result path in verification ledger

- Timestamp: 2026-09-21T20:52:24+05:00 (Asia/Almaty). The AF58 result path appended to VERIFICATION.txt omitted `evidence/firmware-audit/`; it was a ledger path transcription defect. The result/report/artifact were not changed. Correct the absolute path to `evidence/firmware-audit/20260921-abl7378-indirect-entry/run-20260921T200924+0500/helper-contract-result-corrected.json`, then rerun role verification.

## Final integration verification and role reopen

- Timestamp: 2026-09-21T20:53:41+05:00 (Asia/Almaty). Text/evidence command `PYTHONDONTWRITEBYTECODE=1 python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-apob-abl-outer864-root-review/table-integration-20260921/guide_evidence_check.py` returned exit `0`, stdout `PASS`, `17/17`, stderr empty. Its evidence manifest `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-apob-abl-outer864-root-review/table-integration-20260921/SHA256SUMS.final` returned exit `0`, all entries `OK`, SHA-256 `ab4829045a322f482988c2e40aaf5a3f350596ea21a14e01f25f4b20bc995ce9`.
- AF58 corrected helper result remains `PASS`, `22/22`; its helper contract is represented in the guide only as static/conditional and no clock-register operation. Item17/callback/table and hardware boundaries remain explicit.
- Final four roles reopened: MODIFIED_FILE `0aa1b5e5580d8d136c41be2d03c092dcf88aa2c1b1df1cf09141ec88c537847d`; DIFF_FILE `7bbb043ddb63010e7560a929935c1eb88297d0552286a2c137eb834516819f10`; VERIFICATION.txt `e507585d53106ab785068c2f4383b93fd30175f0fd796bc8e6cf150124853f31`; executable ROLLBACK.sh `9ae05df1cf810d110b9fd57a38b34066863c2aefc654c6ff72f08ca58246b75b`.
- Repeated behavior: BASELINE asserted/exit `0`; MODIFIED withdrawn/exit `0`; ROLLBACK script exit `0` and predicate asserted/exit `0`, restored hash equals baseline and `cmp=0`; REAPPLY withdrawn/exit `0`; all stderr empty. Patch reconstruction exit `0`, reconstructed hash equals MODIFIED_FILE and `cmp=0`. Follow-up manifest `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-apob-abl-outer864-root-review/followup-integration-final-20260921/SHA256SUMS.final` returned exit `0`, SHA-256 `82d3fbf6f949a6baa8a8d24a4d54960be62a5bdcd2b64e61bcfddf7a4619acce`.
- Original guide remains `334d6b879156bb2ba773c2d2d766ddc54cbacd37e33e3eab3bab949d2fe8e065`; ROM remains `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`. No firmware, ROM, NVRAM, register or hardware write.
