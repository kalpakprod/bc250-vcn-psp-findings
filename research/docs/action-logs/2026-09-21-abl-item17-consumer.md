# ABL service item `0x17` memory-speed consumer trace — intent

Timestamp: 2026-09-21T16:13:35+05:00 (Asia/Almaty)
Actor: `/root/memory_clock_units`; offline static trace only.

## Bound target and task

- TARGET: exact plain CLV ROM `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, 16,777,216 bytes, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Exact ABL1 payload: 94,624 bytes, SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- GOAL: continue from caller `0x7E3A -> 0x0C60`, resolve the service item `0x17` provider/consumer if supported by exact local bytes, relate it to memory-speed settings/structures, and identify the first unresolved boundary. Do not repeat the previously verified `AmdSetup+0x316 -> $INV 0x11ED` serialization or enum `0x24 -> 1800` report.
- Ownership boundaries: `/root/apob_abl_handoff` owns HEAP `0xA04E` and APOB message `0x61`; `/root/smu_clock_entrypoints` owns PMFW queues. This trace stops at the ABL-side service callback/provider interface and memory-speed policy path; it does not reopen those tracks.

## Existing route and procedure

- Existing evidence: exact Thumb object/listing `evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb.elf.o` and `abl1-full-thumb-llvm.txt`; prior candidate-base audit and downstream producer analysis in the same directory. The newly executed first bounded command was:
  `llvm-objdump -D --section=.data --triple=thumbv7 --start-address=0x7da2 --stop-address=0x7e70 evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb.elf.o`
  It exited `0` and directly confirmed `0x7DAE -> 0x221C`, then `0x7E00 -> 0xAD58`, `0x7E30 -> 0x10CC0`, and `0x7E3A -> 0x0C60` with selector/item `0x17` and context `r4`.
- Next bounded test: reuse the exact extracted ABL1 payload, existing Thumb listing and ELF wrapper; map the `0x0C60` dispatcher's literal callback table through the already-qualified candidate base `0x57100`; check table-key row `0x17`, pointer `0x606FD`, tagged target under that base, and exact target function `0x95FC` bytes/behavior. Re-check all relevant hashes. Follow the target only to its next memory speed policy/service boundary; no physical clock claim.
- The candidate base remains conditional: prior work explicitly did not prove the ABL loader's runtime base. The test must preserve this qualifier even if several table rows map to local function starts.
- Expected result: static provider-table/dataflow finding or a negative result, with a byte-backed exact missing boundary; no synthetic proof of hardware behavior.

## Safeguards and owned outputs

- No hardware, network, ROM/NVRAM/register write, image patch, install, or candidate. Original ROM/payload and existing shared reports remain untouched.
- New owned paths only: `evidence/firmware-audit/20260921-abl-item17-consumer/`, `docs/research/2026-09-21-abl-item17-consumer.md`, and this action log.
- Rollback: remove only this report and unique evidence directory; preserve this append-only action log and all pre-existing work.
- Acceptance event: exact disassembly/byte verifier starts and returns a recorded result; final report names code addresses, command/status, candidate-base qualification, and unresolved consumer boundary.

## Follow-on: table row `0x17` to local memory-speed handler (intent before new evidence writes)

The first disassembly event located a dynamic callback table pointer `0x0006E224` in exact ABL1 code. Under the already-documented conditional candidate base `0x57100`, this points to payload offset `0x17124`. The raw payload at that location appears to contain `{function_pointer, selector}` rows; the `0x17` row appears to hold pointer `0x000606FD`, which under the same candidate base maps to Thumb target `0x95FC`. This could resolve the prior direct-caller negative as an indirect service-table dispatch, but it remains only a lead until a fresh byte-backed test verifies table-row stride, selector match, candidate mapping, and exact Thumb prologue/dataflow.

Next executable action: copy the exact extracted payload, existing ELF wrapper/full Thumb listing, and prior base-review result into this unique evidence directory; run `llvm-objdump` on the bounded service/handler ranges; execute a small deterministic verifier for the table rows and target address/dataflow. Include the mapping under `0x57100` as conditional static coherence only; do not claim the runtime loader base is established. Reuse prior base-check evidence rather than rerunning another broad pointer scan.

Scope stop: map `0x17` to its ABL1 callback and follow the callback's own memory-speed structure writes and immediate ABL data/service calls. Do not trace the APOB message `0x61`/HEAP producer already owned by `/root/apob_abl_handoff`, or PMFW Queue 3/Queue 4 requests owned by `/root/smu_clock_entrypoints`. No firmware write, hardware, network, source patch, or installed tool.

## G7-corrected pointer-table continuation (intent before verifier/report write)

The existing `abl1-producer-base-review-result.json` supplies four exact pointer/code anchors for candidate base `0x57100`, but it predates the item-`0x17` callback table and classifies `0x606FD@0x17134` only as an unvalidated collision. This continuation tests that candidate against the actual table parser structure already used by `0xE50/0xFD8`: literal target `0x6E224`, 8-byte rows `{callback_ptr,key}`, null pair termination, and the key-`0x17` row. It then validates all non-null table pointers against exact local Thumb entry prologues under the same candidate base, and follows the selected function `0x95FC` only through its per-channel memory-speed reducer and immediate ABL data/service calls.

Procedure/output writes (intent): save the bounded disassemblies and a deterministic result under the already-owned `evidence/firmware-audit/20260921-abl-item17-consumer/`; write only the corresponding report under `docs/research/2026-09-21-abl-item17-consumer.md`; append this action log. No pre-existing report, memory file, other worker artifact, ROM, firmware, NVRAM, register, hardware, network, or installed tool will be changed.

Acceptance: exact byte/table row and matching Thumb prologue are observed; base-`0x57100` dependence and lack of loader proof remain explicit; `0x95FC` maps to memory-speed policy but no PLL/physical clock claim; first unresolved consumer is named beyond the callback. Rollback remains deletion of only the owned report/evidence directory; preserve the append-only action log.

## Bounded check expansion: helper-6D10 precedence and ABL SVC ABI (intent before verifier/report write)

The parent requested integration of existing `pstate-precedence-next` evidence and an exact identification of the first outbound ABL service ABI without guessing its clock effect. New focused test will reproduce the local fact chain `ABL1 0x6C20 -> 0x6D10 returns 1 -> output buffer +4 / caller SP+0x164 -> ABL1 0x95FC comparison at 0x9644/0x9646 -> branch 0x9744 -> alternate 0x984E`, preserving that the generic min-reduction branch is skipped on this statically initialized path. It will also follow exact outgoing calls to `0x0DD4`, `0x0FB8`, `0x118C`, `0x10C0`, and `0x12AC/SVC #6`, cross-checking the version-aligned local ABL1 source only as corroboration.

A raw/ELF inspection attempt used the wrong `20260921-clv-abl1-downstream` directory name and returned `llvm-objdump: error: ... No such file or directory`; the wrapper did not retain a shell exit code and no file was changed. The correct source directory is the existing `20260920-clv-abl1-downstream`; all following disassembly commands use that exact copied object under this task's unique evidence directory. This failed lookup is not used as evidence.

Stop at the SVC #6 ABI boundary; do not label the SVC handler, PSP/SMU queue, UMC PLL, or physical clock consumer. The separate handoff and SMU tracks remain untouched.

## Parent-requested precedence/SVC boundary refinement (intent before verifier/report update)

- Reopen the exact pstate-precedence report/result; directly confirm helper `0x6D10` returns `1`, `0x6C20` stores that result at output `+4`, and `0x95FC` reads the same buffer slot at `[SP+0x164]` before its `<=1` branch. This determines the branch used by the exact local helper path and qualifies the generic multi-channel minimum code as a conditional/dormant branch for that path.
- Reopen exact outgoing ABL1 code and version-aligned local `ABL1_decompiled.c` functions only for wrapper `0x0DD4`, inter-die helpers `0x118C`/`0x10C0`, and SVC wrapper `0x12AC`. Record service values `0x0B`/`0x0C`, `SVC #6`, and the exact service literal, but do not name the SVC handler as a clock applier or infer its hardware effect.
- Expected new edge: service item `0x17` -> callback table row -> conditional local `0x95FC` target -> guarded memory speed branch; first external consumer boundary remains the unimplemented SVC #6 handler/recipient beyond ABL1.
- Evidence/output will be appended only to this report, this action log, and the unique evidence directory. Preserve the earlier report's no-serializer claim, all other workers' files, and the exact ROM/payload. No hardware/network/firmware write.

## Verifier capture-shape correction

The new verifier's first run exited `1` before result creation because `callback-anchor-prologues.exit` is a per-address ledger (`0x2e8=0`, `0x8bfc=0`, `0x1bc0=0`), not one integer. This is a checker parsing error; exact disassembly commands all separately recorded exit `0` and had empty stderr. Parse the three ledger values as zero, then rerun the same pinned-input verifier.

## Verifier JSON serialization correction

After correcting the per-address exit ledger, the verifier completed its assertions but exited `1` when `json.dumps` attempted to serialize a byte-valued check detail. This is an output-encoding defect, not an input/result failure. Keep byte comparisons as bytes, but encode `got`/`expected` fields as hexadecimal strings in the JSON ledger; rerun.

## Observed result — verifier and evidence manifest

Timestamp: 2026-09-21T17:11:00+05:00 (Asia/Almaty)
Actor: `/root/memory_clock_units`; offline static trace only.

- Executed: `python3 evidence/firmware-audit/20260921-abl-item17-consumer/item17_consumer_verify.py`.
- Observed command status: exit `0`; stdout status `PASS`, `checks=136`; stderr is empty. Literal stdout is retained at `evidence/firmware-audit/20260921-abl-item17-consumer/item17-verifier.stdout`; exit ledger is `item17-verifier.exit`; stderr ledger is `item17-verifier.stderr`.
- Observed result: item `0x17` has one table row at payload `0x17134`, pointer `0x000606FD`, selector `0x17`; under conditional base `0x57100` it maps to `0x95FC`. Helper `0x6D10` returns `1`; the exact local path takes `0x9646 -> 0x9744 -> 0x984E` and bypasses the multi-channel min/writeback block. The first unresolved boundary is the SVC `#6` handler/recipient at `0x12C0`; no clock-applier or physical-clock claim was made.
- Evidence directory was reopened and all 37 entries passed `sha256sum -c evidence/firmware-audit/20260921-abl-item17-consumer/SHA256SUMS.final`; the final manifest is retained in that directory. No source ROM, payload, prior result, firmware, NVRAM, register, board, network, or installed tool was changed.
- Hashes: report `docs/research/2026-09-21-abl-item17-consumer.md` SHA-256 `271f178d9da1ff8de4ef74641a1b1dc94ec27211860e386ce4d6c2a988077d15`; result JSON SHA-256 `4330bdf964f5ebd3fc7211af953e38d4062a0a1d64276a43cac398b2fc916cd3`; verifier script SHA-256 `c349a0670d6c82481839cd05bf2d19efe4355363b4e09a462b744077b255a535`; final evidence manifest SHA-256 `eb835b9e42300724b0f1b66107bee65a266da66353333654d37898bb368bb52b`.
- Rollback: delete only the task report and unique evidence directory, preserving this append-only log and all pre-existing source/evidence.
- Remaining uncertainty: independent review requested by the parent is incomplete in this execution; loader/runtime base, SVC semantics, physical PLL/MCLK/training consumer and hardware behavior remain unresolved.

## G7 correction — evidence-entry count

Timestamp: 2026-09-21T17:12:00+05:00 (Asia/Almaty)

The preceding observed-result bullet said `37` evidence entries. Reopening the directory showed `40` files excluding `SHA256SUMS.final`, and `40` lines in the manifest; all `40/40` checks pass. The result and hashes are unchanged. The manifest is intentionally not self-listed.

## G4 observed report-path reconciliation

Timestamp: 2026-09-21T17:13:00+05:00 (Asia/Almaty)

The report was reopened after the manifest reconciliation and now names the final manifest path and hash explicitly. Updated report SHA-256: . The evidence manifest, result JSON, verifier stdout/stderr/exit ledgers, and input hashes remain unchanged; no source or firmware bytes changed.

## G7 correction — report hash interpolation

Timestamp: 2026-09-21T17:14:00+05:00 (Asia/Almaty)

The preceding append used shell command-substitution delimiters around the hash placeholder, so the recorded report-hash field was empty; the command emitted a diagnostic but did not modify project inputs. The corrected reopened report hash is e0a6050817295cba354ff4e5fe5997fdaf3e2d4d21393499d91213d2604fe178. This logging defect does not alter the report, verifier result, evidence manifest, or source bytes.

## Final rerun after report-path update

Timestamp: 2026-09-21T17:15:00+05:00 (Asia/Almaty)

- Re-executed `python3 evidence/firmware-audit/20260921-abl-item17-consumer/item17_consumer_verify.py` after the report was reopened. Observed exit `0`, stdout `PASS`, `136` checks, stderr length `0`.
- Reopened `SHA256SUMS.final`: all `40/40` listed files returned `OK`. Manifest SHA-256 remains `eb835b9e42300724b0f1b66107bee65a266da66353333654d37898bb368bb52b`; result JSON remains `4330bdf964f5ebd3fc7211af953e38d4062a0a1d64276a43cac398b2fc916cd3`.
- The final report SHA-256 is `e0a6050817295cba354ff4e5fe5997fdaf3e2d4d21393499d91213d2604fe178`. Exact ROM, decompressed ABL1 payload, and ELF wrapper hashes are unchanged. No firmware or hardware action occurred.

## G7 correction intent — post-6C20 fill alias boundary

Timestamp: 2026-09-21T18:31:00+05:00 (Asia/Almaty)

The independent `item17-reachability-review` result (PASS, 128/128; `item17-reachability-result.json`) shows that `0x95FC` calls `0x6B78` at `0x963A` with dynamic destination `R4+0x278`, fill byte `0xFF`, length `0x40`, after the helper writes `1` at `[SP+0x164]`. No address relation proves disjointness from `SP+0x160..0x178`. Append a G7 correction to this report: the `0x9646 -> 0x9744 -> 0x984E` path and consequent `+0x2BC` output are conditional on no alias/clobber, not guaranteed by `0x6D10=1` alone. Preserve all prior hashes and verifier output; do not modify the reviewer-owned files.
