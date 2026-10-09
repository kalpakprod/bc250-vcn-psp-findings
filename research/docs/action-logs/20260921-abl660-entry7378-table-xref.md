# ABL1 entry 0x7378 table-reader cross-reference — intent

Timestamp: 2026-09-21T20:00:00+05:00 (Asia/Almaty)
Actor: /root/memory_clock_units; offline static only.

ACTIVE_OBJECT: /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl660-object-identity/ABL1-clv-full-thumb.elf.o
LAST_CONFIRMED_RESULT: PASS_BOUNDED_STATIC_WITH_CALLER_IDENTITY_UNRESOLVED; initializer root object is entry R0; active consumer base identity unresolved.
NEXT_EXECUTABLE_ACTION: targeted disassembly selected from the objective attachment/reused Sept-20 table report; expected pointer 0x5E479 is conditional under base 0x57100.
INPUT_PATHS: /home/OWNER/.codex/attachments/9d7bcc99-0793-46b7-a070-9d0a73377101/pasted-text-1.txt, /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl660-object-identity/ABL1-clv-full-thumb.elf.o, /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl660-object-identity/field660-identity-result.json, /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt
ACCEPTANCE_EVENT: actual bounded llvm-objdump process exits with evidence showing stride-24 table reader fields and any 0x5E479 row; distinguish loaded fields from data.
Attachment SHA-256: ef12cf0e32e81bbb8ee7da775437358d9da5be5b08d10687d97ff62e7ded292b
Selected range: 0x1fa8..0x20f8 (reader/function anchor named in attachment or cited Sept-20 report).

No hardware/network/ROM/NVRAM/register/candidate write. Reuse the existing 97-check field660 report and candidate-target body; do not repeat those checks or scan arbitrary arrays. Rollback: delete only this report and unique evidence directory; retain this append-only log.

## G7 command-selection correction — 0x1FB4 is the wrong reader

Timestamp: 2026-09-21T20:08:00+05:00 (Asia/Almaty)

The first continuation dispatcher selected `0x1FB4..0x20F8` by matching the word reader in the existing descriptor-provider report. Its observed command was `/usr/bin/llvm-objdump -D --section=.data --triple=thumbv7 --start-address=0x1fa8 --stop-address=0x20f8 .../ABL1-clv-full-thumb.elf.o`, exit `0`, stderr empty, stdout 9,771 bytes. This is the unrelated token-candidate array reader `0x1FB4 -> 0x4800`; it is NOT the requested stride-24 code-pointer table and provides no evidence whether `0x5E479` appears in that table. Preserve the captured slice/command record but exclude it from acceptance.

The actual objective attachment is the broad board-tuning brief; it does not identify the stride-24 table or reader. Focused Sept-20 ABL reports read for this task identify the `0x7378` initializer and `+0x660` callback boundary, the separate `0x1FB4` token array, and other descriptor arrays, but no stride-24 callback reader/path. No generic array scan was run. The direct BL-to-0x7378 query is not used as an absence conclusion. Waiting for the exact local report/table-reader identity or pstate_precedence's shared ownership pointer is necessary to issue the correct targeted disassembly.

## Intent — correct and verify the prior 0x1B24 reader-stride interpretation

- Timestamp: 2026-09-21T21:30:00+05:00 (Asia/Almaty). Actor: continuation executor.
- Target: previously captured bounded Thumb listing evidence/firmware-audit/20260921-abl7378-indirect-entry/run-20260921T200924+0500/xref-1b24-1b90.stdout and exact pinned ABL1 raw/object inputs only.
- Procedure: first record the G7 correction to the existing claim stride 0x24, then run a one-purpose host verifier on the pinned raw bytes and captured reader instructions. Verify the loop's affine address calculation, literal table/count pointers, the candidate word at row0+4, the field actually loaded by the loop, count, and row1's correctly addressed +8 value. Do not repeat the candidate target body, do not scan tables, and do not claim this is the requested stride-24 reader.
- Reason: the decoded instruction sequence is RSB r0,r4,r4,LSL #3 followed by ADD r0,r6,r0,LSL #2; its semantics must be reconciled with the previously reported 0x24 stride before continuing.
- Expected effect: either validate a correction to that earlier report or preserve a concrete verifier failure. No firmware/source payload is modified.
- Rollback: preserve the prior report/log and append a later correction if needed; remove only the uniquely named evidence/firmware-audit/20260921-abl7378-reader-stride-correction/ if the verifier itself is invalid.

## G7 correction — first reader-stride verifier failed on listing-column assumption

- Timestamp: 2026-09-21T21:34:00+05:00 (Asia/Almaty).
- Observed process: /usr/bin/python3 -B evidence/firmware-audit/20260921-abl7378-reader-stride-correction/verify_reader_stride.py exited 1; stdout status FAIL, 13/18 checks; stderr empty. Hash, literal, computed-address, and raw table-value checks passed. Five instruction-text checks failed because the verifier split rows on tab although the saved listing renders its columns with spaces.
- This is a host verifier format error, not a disassembly or ABL1 error. Preserve verifier.py/stdout/stderr/exit as attempt 1.
- Method change: because similar disassembly-column assumptions have failed in prior ABL verifiers, switch away from tab-column parsing; use an independently available native disassembler or a raw-byte decoder for the two address-arithmetic instructions before rerun.

## Intent — method change to bounded code plus raw-byte readback

- Timestamp: 2026-09-21T21:37:00+05:00 (Asia/Almaty).
- Procedure: after preserving the failed text-parser attempt, rerun only the exact reader loop window with local llvm-objdump and independently read the two literal pointers, count byte, row0 +4/+8, and true row1 +8 from the pinned raw ABL1 using Python standard-library little-endian unpacking. Do not parse formatted disassembly columns or inspect callback bodies.
- Reason: /usr/bin/rizin, rz-asm, and Python capstone are unavailable; the text-column approach failed. Method changes to a direct fresh bounded native disassembly plus independent raw-byte extraction, not a second string parser.
- Expected effect: settle the 0x1B24 address formula and consumed row members with exact stdout/stderr/status; this candidate reader is not presumed to be the requested stride-24 reader.
- Outputs: evidence/firmware-audit/20260921-abl7378-reader-stride-correction/run-20260921T213700+0500.
- Rollback: delete only this new run directory if its outputs are invalid; inputs remain read-only.

## Intent — publish the verified stride correction without replacing prior evidence

- Timestamp: 2026-09-21T21:40:00+05:00 (Asia/Almaty).
- Target writes: append a superseding correction to docs/research/2026-09-21-abl7378-indirect-entry.md, append its evidence result to docs/action-logs/2026-09-21-abl7378-indirect-entry.md and this task log, and append the successful recheck to the G7 memory incident. Preserve all earlier claims as historical text; do not rewrite existing JSON/manifests.
- Evidence: fresh bounded listing in evidence/firmware-audit/20260921-abl7378-reader-stride-correction/run-20260921T213700+0500/reader.stdout (exit 0, empty stderr) and standard-library raw-byte result (exit 0, empty stderr).
- Expected effect: make the previously reported 0x24 stride and 0x170F4 row1+8 address explicitly superseded; conclude only that this 0x1B24 reader advances 0x1C bytes and reads +8, while candidate 0x5E479 at +4 is not consumed by it. This does not identify the separate requested stride-24 reader.
- Rollback: append a later correction if needed. Do not delete or mutate pinned ABL1/ROM inputs; the new evidence folder is unique and disposable.

## Observed result — prior candidate reader is stride 0x1C, not target

- Timestamp: 2026-09-21T21:40:00+05:00 (Asia/Almaty). Fresh bounded /usr/bin/llvm-objdump -D --triple=thumbv7m-none-eabi --start-address=0x1b40 --stop-address=0x1b62 /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/ABL1-exact.o exited 0, stderr empty. Literal instruction rows show 1b48 rsb r0, r4, r4, lsl #3; 1b4c add.w r0, r6, r0, lsl #2; 1b50 ldr r1, [r0, #0x8]; and count read 1b5c ldrb r0, [r7].
- /usr/bin/python3 -B evidence/firmware-audit/20260921-abl7378-reader-stride-correction/run-20260921T213700+0500/raw_fields.py exited 0, stderr empty; literal stdout: {"count_byte_at_rva_0x17100":"0x2","literal_count_pointer_at_0x1bb0":"0x6e200","literal_table_base_at_0x1bac":"0x6e1c8","raw_sha256":"af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a","raw_size":94624,"row0_plus4_at_rva_0x170cc":"0x5e479","row0_plus8_at_rva_0x170d0":"0x62059","row1_plus8_at_rva_0x170ec":"0x0"}.
- The RSB/ADD semantics yield stride ((8*i)-i)*4 = 28*i = 0x1C*i. The only loop record-member load is +0x8; row0+4 0x5E479 is not loaded. Row1+8 is at 0x170EC, not old offset 0x170F4.
- Failed first text-column verifier (verify_reader_stride.py exit 1, 13/18, stderr empty) remains preserved as a host parser error; direct bounded decode and byte read are the accepted correction evidence. Rizin/rz-asm/Python capstone were unavailable; no new dependency was installed.
- Result is not the requested stride-24 reader. Target table/reader identity still needs the exact local report/range or owner-provided pointer. No global negative, hardware, ROM, or firmware mutation.

## Intent — final evidence-path and manifest readback

- Timestamp: 2026-09-21T21:43:00+05:00 (Asia/Almaty).
- Procedure: append exact new evidence paths and immutable input/evidence hashes to the correction report, then append the final manifest/check/readback result to this action log. Reopen report, memory correction, saved stdout/stderr/exit, and all manifest entries; run whitespace check. Do not alter the evidence outputs or pinned inputs.
- Expected effect: auditable closure of the correction while preserving the separate stride-24 reader as unresolved.
- Rollback: append a later correction; do not rewrite or delete prior evidence.

## Final evidence ledger

- Manifest verification rerun: sha256sum -c evidence/firmware-audit/20260921-abl7378-reader-stride-correction/evidence-manifest.sha256 exited 0; all 14 listed entries reported OK. Manifest SHA-256: 3e660f7647551a5eade8a23f3a7fdef8723f725978701e7dd44f38275ebb3980.
- Final pinned inputs: raw ABL1 94,624 bytes / af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a; exact ELF adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6. Reader stdout SHA-256 5b3973c094d05fc438158273ea99792fad247d2bdf40498b6100a1c3619cb5fd; raw-fields stdout SHA-256 adb62d1acfa446c5bab38ac52d3970b9b09de9d6bd4fe00855b2ac6c0c26128c.
- Correction report reopened at docs/research/2026-09-21-abl7378-indirect-entry.md; its final hash is recorded by the final QA command. G7 memory note reopened at memory/incidents/2026-09-21-abl7378-reader-stride-correction.md. git diff --check exited 0.
- The task's requested stride-24 reader is still not identified. No global negative, board behavior, hardware claim, or firmware mutation.

## Intent — correct final manifest entry count

- Timestamp: 2026-09-21T21:45:00+05:00 (Asia/Almaty).
- Procedure: re-open the evidence manifest and file inventory, then append a count correction wherever the newly appended ledger said 14.
- Expected effect: align text with the observed manifest line count and file count; hash checks/results unchanged.
- Rollback: append a further correction if needed; preserve prior text.

## G7 correction — manifest count

- Fresh wc -l and find counts both returned 15 for evidence-manifest.sha256 and its manifested files. The earlier final-ledger count of 14 was a transcription error; checksum verification itself returned OK for all 15 entries. No evidence bytes changed.

## Final readback — correction artifacts

- Timestamp: 2026-09-21T21:47:00+05:00 (Asia/Almaty). Reopened correction report SHA-256: af4dd43d5b886371a5e1d39447c4204f40830d9dd64306760f9e215d4a2954be.
- Reopened G7 memory incident SHA-256: ded645bad2d936a11ce78e72072d39468366fcd63f6e67dd1dbec7023e4307e8.
- Evidence manifest SHA-256 remains 3e660f7647551a5eade8a23f3a7fdef8723f725978701e7dd44f38275ebb3980; 15/15 entries verified; git diff --check exited 0.
- Pinned ABL1 raw and ELF hashes match the recorded values. Still unresolved: the distinct requested stride-24 reader/table address; no global negative or hardware claim.

## Intent — bounded +4-reader discovery at the known 0x6E1C8 table

- Timestamp: 2026-09-21T22:00:00+05:00 (Asia/Almaty). Actor: continuation executor.
- Target: exact CLV ABL1 ELF object ABL1-exact.o (hash-pinned by prior evidence), with related raw ABL1 table literal/candidate row locations; no ROM or hardware operation.
- Procedure: disassemble only the local Thumb span 0x1A80..0x1BC0 that contains the two existing literal references to table VA 0x6E1C8 / conditional payload RVA 0x170C8. Inspect each nearby caller/initializer/dispatcher instruction for row+4 loads, pointer transformations, and indirect branch/call sites. Do not search arbitrary tables or make a global absence claim.
- Expected effect: identify a reader/callsite consuming record+4, or establish precise local bounds and the remaining indirect mechanism for this table.
- Output path: evidence/firmware-audit/20260921-abl660-entry7378-plus4-reader-xref/run-20260921T220000+0500/.
- Rollback: remove only this unique evidence run if invalid; preserve all pinned input bytes and prior logs/reports.

## Intent — xref exact pool slots for 0x6E1C8

- Timestamp: 2026-09-21T22:05:00+05:00 (Asia/Almaty).
- Target: exact Thumb listing of the pinned ABL1 from the prior downstream run; query only its PC-relative literal xrefs to pool word addresses 0x1B1C, 0x1BAC, 0x1BB0, 0x1BB4, and 0x1BB8, which are the identified nearby literal slots for table/count/other dispatch values.
- Procedure: record listing hash, perform exact-address comment query for the specified pool words (not values across arbitrary arrays), then choose bounded instruction windows only for actual code xrefs. Existing Cutter/Ghidra MCP current-program probes were read-only but their active programs are /bin/true, not ABL1, so they are not evidence for this target; use the exact pinned Thumb disassembler route pending a target-loaded Ghidra program.
- Expected effect: locate the code sites that load the known table/count/dispatch literals and any callsites associated with them; no global absence claim.
- Output path: evidence/firmware-audit/20260921-abl660-entry7378-plus4-reader-xref/run-20260921T220000+0500/.
- Rollback: delete only this unique run output if invalid; no firmware, source, board, network, or ROM writes.

## Intent — verify the +4 table reader at xref 0x18A8

- Timestamp: 2026-09-21T22:10:00+05:00 (Asia/Almaty).
- Target: exact ABL1 ELF/raw inputs, specific PC-relative table-base xref at 0x18A8 -> pool 0x1B1C -> VA 0x6E1C8, conditional table RVA 0x170C8 under base 0x57100.
- Procedure: freshly disassemble only 0x18A4..0x1920 around the bounded reader/dispatch loop, then directly verify only the table row members that this loop loads (+4 callback and +0xC argument), the row1 +4 sentinel, and count separately only if used. Do not follow callback body, scan other arrays, or infer runtime execution.
- Expected effect: establish whether record +4 feeds the indirect branch and record the remaining return-dependent dispatch edge.
- Output path: evidence/firmware-audit/20260921-abl660-entry7378-plus4-reader-xref/run-20260921T220000+0500/.
- Rollback: delete only this run's new files if invalid; firmware, ROM, hardware, NVRAM, and source inputs remain unchanged.

## Intent — record the verified +4 callback-reader finding

- Timestamp: 2026-09-21T22:15:00+05:00 (Asia/Almaty).
- Writes: create a concise separate static-analysis report, append the +4 reader result to the existing relevant memory incident and action log, and create a small verification ledger under the already unique evidence directory. Do not rewrite historical reports or results.
- Evidence already observed: bounded listing 0x18A4..0x1920 exited 0 / empty stderr; independent raw-field verifier exited 0, 7/7 checks.
- Expected effect: document the first exact record+4 load -> BLX r7 path, its conditional mapping to 0x7378, the table arguments/sentinel, and the remaining callback-return-dependent dynamic call. State that loader base/runtime execution/object identity remain unproven.
- Rollback: append a later correction; if evidence is invalid, remove only this unique task directory and its new report/memory append while preserving all earlier records and pinned inputs.

## Intent — correct ELF hash transcription in the new verification ledger

- Timestamp: 2026-09-21T22:17:00+05:00 (Asia/Almaty).
- Procedure: append a G7 correction to memory and verification ledger for a manually mistyped ELF SHA-256; directly re-hash the pinned object, confirm the correct value, then continue manifest/report QA.
- Expected effect: distinguish the incorrect transcription from the verified input identity. No input bytes change.
- Rollback: append a later correction if the new hash readback disproves the expected value.

## Observed result — record+4 reader identified

- Timestamp: 2026-09-21T22:20:00+05:00 (Asia/Almaty). Exact PC-literal xref query over the pinned downstream Thumb listing exited 0 and found 0x18A8 -> pool word 0x1B1C; a fresh bounded Thumb listing [0x18A4,0x1920) exited 0, stderr empty.
- Reader field/call path: 0x18A6 sets index 0; 0x18B6 branches to 0x18EA before the increment block; the computed address at 0x18EA/0x18EE is table_base+0x1C*i; 0x18F2 loads [record+4] into r7; 0x18C4 executes BLX r7. 0x18BE loads record+0xC into r2 and 0x18C2 passes r0=r6. The raw row0+4 value is 0x5E479, which conditionally maps under base 0x57100 to Thumb pointer RVA 0x7379 / entry RVA 0x7378. Row1+4 at RVA 0x170E8 is zero. The loop's other record field is +0xC; this reader does not load +0x8.
- Raw-field check exited 0 with literal stdout {"checks":{"passed":7,"total":7},"fields":{"raw_sha256":"af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a","raw_size":94624,"table_literal_at_rva_0x1b1c":"0x6e1c8","table_row0_plus0c_at_rva_0x170d4":"0x6e154","table_row0_plus4_at_rva_0x170cc":"0x5e479","table_row0_plus8_not_used_by_this_loop":"0x62059","table_row1_plus4_at_rva_0x170e8":"0x0"},"status":"PASS"}; stderr empty.
- Report: docs/research/2026-09-21-abl660-plus4-reader.md. Machine result: evidence/firmware-audit/20260921-abl660-entry7378-plus4-reader-xref/plus4-reader-result.json. Report contains the remaining return-dependent handler at 0x18D4..0x18DA and limits.
- Remaining: candidate base/runtime execution unproven; callback return behavior and [[R6+0x1C]+0x48] handler untraced; R6 is not joined to active consumer R0+0x660. No ROM/hardware/network mutation.

## Observed G7 correction — ELF hash transcription

- Direct sha256sum readback confirmed exact ABL1 ELF SHA-256 adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6 and raw ABL1 SHA-256 af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a. The earlier typo in the new VERIFICATION.txt remains preserved and is explicitly superseded by its appended correction.
- Evidence manifest d2e5c5b0e007816677ce9dacaaebdcf3b91cfaa310c7f7e18349d4c1c9ba29f5 remains valid; no files inside the manifested evidence directory were changed.

## Intent — bounded R6 source and return-handler join

- Timestamp: 2026-09-21T22:30:00+05:00 (Asia/Almaty). Actor: continuation executor.
- Target: exact ABL1 reader at 0x18A4..0x1920 and its stack-derived R6 input; follow only the stack slot loaded at 0x18A4, its producer within the owning function, exact direct callers to that function entry if exposed, and callback return-dependent handler at 0x18D4..0x18DA.
- Procedure: reuse the prior successful llvm-objdump command template/triple and pinned ELF; find the nearest local function prologue and exact SP+0x88 producer(s), then bounded-disassemble only the function/setup and caller xref windows needed. No code patch, callback-body revisit, array scan, or global absence claim.
- Expected effect: accept or reject only the static same-object join between 0x7378 R0 input and the object later supplied to 0x10958; record the remaining indirect boundary precisely.
- Output path: evidence/firmware-audit/20260921-abl660-plus4-reader-context-join/run-20260921T223000+0500/.
- Rollback: remove only this unique evidence run if invalid; no ROM, firmware, NVRAM, register, network, or hardware changes.

## Intent — complete 0x6238 output-pointer helper for the 0x18A4 lookup

- Timestamp: 2026-09-21T22:40:00+05:00 (Asia/Almaty). Actor: continuation executor.
- Target: the exact 0x6238 helper called at 0x1890 with R0=SP+0x7C; its output field is SP+0x88 and feeds R6 at 0x18A4. Reuse the prior 0x6238 Thumb command template and extend only through the helper return.
- Procedure: bounded Thumb disassembly from 0x62A0..0x6380, then trace only the lookup success/failure stores to [request+0xC] and the exact key/namespace arguments constructed at caller 0x187C..0x1890. Reuse prior heap-node evidence; do not repeat generic heap routines or the +4 pointer mapping/raw checks.
- Expected effect: identify the exact returned object pointer or stop at the allocator/registry boundary, then decide only whether this path proves R6 equals preserved caller R4 / active 0x10958 R0.
- Output path: evidence/firmware-audit/20260921-abl660-plus4-reader-context-join/run-20260921T224000+0500/.
- Rollback: remove only this unique run output if invalid. No ROM, firmware, register, NVRAM, network, or hardware writes.

## G7 correction — command-template path typo

- A prior continuation dispatcher attempted to read the nonexistent helper-6238.command path under run-20260921T224000+0500; the shell printed a no-such-file error and set -e stopped before any writes or disassembly. This incorrect path came from a stale run label; the actual newest successful template is run-20260921T224000+0500/helper-6238-full.command. Do not use the failed path again.

## Intent — persist 0x6238 success evidence, then trace the 7378/7E74 path

- Timestamp: 2026-09-21T22:52:00+05:00 (Asia/Almaty).
- First persist the already observed 0x1890 request fields, 0x6238 output+0xC success formula/status, and caller consumption at 0x18A4 in a machine-readable result under the prior unique context-join run. Then use the same pinned Thumb command template for bounded 0x7378..0x7500 and 0x7E74..0x7F20 code windows plus exact direct-call xref queries to 0x7E74/0x10958. Reuse prior 10958/7378 reports; do not repeat their byte checks or callback-body analysis.
- Expected effect: locate the static R5/root continuity or name the first broken edge; no runtime pointer equality inferred.
- Output: evidence/firmware-audit/20260921-abl660-plus4-reader-context-join/run-20260921T225000+0500/.
- No ROM/firmware/hardware/network changes. Preserve all prior evidence and errors.

## Intent — trace the callback in the exact R8+0x3C field and AF90 R5 preservation

- Timestamp: 2026-09-21T23:00:00+05:00 (Asia/Almaty).
- Target: the raw callback field [R8+0x3C] used by 0x7378 at 0x74E4/0x74EA, where R8 is the 0x6E154 row0+0xC value passed by the 0x18C4 reader; plus bounded AF90 prologue/epilogue only to test saved R5 preservation.
- Procedure: read exactly raw ABL1 RVA 0x17090 (= conditional VA 0x6E190 if base 0x57100) as little-endian u32, disassemble the conditional target window if it lands within the pinned ABL1, and disassemble AF90 through its local return. Reuse the pinned object/Thumb triple. Do not search a generic table, do not follow unrelated callbacks, and do not infer runtime identity.
- Expected effect: map the dynamic callback target to an entry/containing function or leave the exact external/indirect boundary; establish whether AF90 saves/restores R5.
- Output: evidence/firmware-audit/20260921-abl660-plus4-reader-context-join/run-20260921T230000+0500/.
- Rollback: remove only this unique run if invalid; no ROM, firmware, NVRAM, register, network, or hardware changes.

## Intent — resolve the post-7378 object+0x48 callback and success gate

- Timestamp: 2026-09-21T23:10:00+05:00 (Asia/Almaty).
- Target: exact R8 descriptor VA 0x6E154 from 7378's incoming R2, specifically [R8+0x48]; and the bounded 7378 success-return tail plus existing 0x18D4 handler.
- Procedure: read only raw ABL1 RVA 0x1709C (conditional VA 0x6E19C under base 0x57100), map any nonzero target conditionally, disassemble its local containing-code window, and freshly disassemble only 0x74F0..0x7508 to resolve successful 7378 return status. Reuse the pinned Thumb command template/object; do not repeat +3C stub, raw pointer mapping, prior 6238 checks, or 18D4 body.
- Expected effect: identify the object-relative callback target and establish whether the zero/nonzero return selects the handler at 0x18D4.
- Output: evidence/firmware-audit/20260921-abl660-plus4-reader-context-join/run-20260921T231000+0500/.
- Rollback: delete only this unique output if invalid; no ROM, firmware, NVRAM, register, network, or hardware changes.

## Observed result — R8+0x48 handler and success gate

- Exact raw field: R8=0x6E154; +0x48 conditional cell VA 0x6E19C / payload RVA 0x1709C contains u32le 0x5E615. Under unproven base 0x57100, this maps to Thumb pointer 0x7515 / entry 0x7514.
- Fresh bounded target window exit 0, empty stderr; at 0x7514: MOVS R0,#0; BX LR.
- Fresh 7378 tail [0x74F0,0x7508) exit 0, empty stderr. Success path calls 0x109BC at 0x7500 with R0=R5 and R1=0, sets R0=1 at 0x7504, then branches to 0x745C return. Therefore reader 0x18C6 CBZ does not take its zero branch on this success path; it reaches 0x18D4..0x18DA.
- R5 from 7378 entry R0 is the heap root. 7378 stores its R8 descriptor at [R5+0x1C] at 0x74EE; 7378 epilogue restores caller R6. The reader's R6 therefore remains the same root after BLX R7, and the 0x18D4 handler reloads that descriptor, calls the +0x48 target with R0=R6. AF90 push at 0xAF90 and pop at 0xB148 both include R5.
- The R8+0x48 target is 0x7514, not 0x7E74. In the separately inspected 0x7E74 window, the instruction at 0x7E74 is BL 0x5E68; the later 0x109BC call is at 0x7EF0. No direct join from this edge to the active 0x10958 wrapper is shown.
- Exact evidence is under evidence/firmware-audit/20260921-abl660-plus4-reader-context-join/run-20260921T231000+0500/. Conditional base/runtime relocation and hardware execution remain unverified.

## Intent — bounded CFG/prologue validation around 0x7E74

- Timestamp: 2026-09-21T23:20:00+05:00 (Asia/Almaty).
- Target: exact containing-code region around address 0x7E74 in the pinned ABL1 ELF; identify a real entry/prologue and whether 0x7E74 is interior, without treating the interior address as a BL target. Reuse current Thumb command template/object and extend backward to the candidate prologue.
- Procedure: freshly disassemble only [0x7D74,0x7F20), inspect push/sub-SP, branch and saved-register transitions, then use that entry/control-flow to test descriptor 0x6E154 fields only after the true function entry is known. Do not repeat R8+0x3C/+0x48 stub or table scans.
- Expected effect: determine whether 0x7E74 lies in the callback root's actual containing function/CFG and locate the input R0 -> R4 save; output a bounded link or explicit dispatch gap.
- Output: evidence/firmware-audit/20260921-abl660-plus4-reader-context-join/run-20260921T232000+0500/.
- Rollback: remove only this unique run output if invalid; no ROM, firmware, NVRAM, register, network, or hardware writes.

## Intent — find the real containing CFG/entry for 0x7E74

- Timestamp: 2026-09-21T23:30:00+05:00 (Asia/Almaty).
- Reuse the prior Sept-20 0x7378/+0x660 and R6+0x3C4 traces; do not repeat callback or stub analysis. Fresh task: bounded backward CFG/prologue validation around 0x7E74 and exact descriptor 0x6E154 fields only, to find the actual callback/function entry pointer and dispatcher.
- Procedure: fresh Thumb disassembly over only 0x7C74..0x7F20 on the pinned ABL1 ELF; bounded little-endian dump of descriptor R8=0x6E154 through +0x48. Do not search direct BL to interior address 0x7E74 or scan other tables. Continue only if the local entry/field chain is byte-backed.
- Expected effect: identify the containing entry, its incoming R0->R4 mapping, and a matching descriptor field/dispatcher edge, or preserve the first broken indirect boundary.
- Output: evidence/firmware-audit/20260921-abl660-plus4-reader-context-join/run-20260921T233000+0500/.
- No hardware, ROM, firmware, NVRAM, registers, network, or installation action.

## Intent — follow the sole distinct candidate entry in descriptor 0x6E154

- Timestamp: 2026-09-21T23:32:00+05:00 (Asia/Almaty).
- Prior bounded dump of only descriptor 0x6E154 showed a distinct candidate pointer at +0x34 (0x67CBD -> conditional Thumb entry 0x10BBC); other checked words matched the 0x7514 stub. Disassemble only entry 0x10BBC and keep the 0x7E74 prologue window bounded to determine whether this descriptor entry reaches or contains the 0x7E74 block. Do not repeat the already confirmed +0x3C/+0x48 stub.
- Expected effect: either establish a local code/dispatcher edge toward the 7E74 block or preserve the precise entry/control-flow break.
- Output: same unique 23:30 context-join evidence run.
- No hardware/network/ROM writes; preserve candidate base as conditional.

## Intent — locate the real incoming caller/table for function 0x7544

- Timestamp: 2026-09-21T23:40:00+05:00 (Asia/Almaty).
- Target: exact Thumb function entry 0x7544 and its entry-R0+0x4-derived object; trace only the bounded caller/function interval needed to find its incoming direct call or the exact static table pointer 0x5E645 under conditional base 0x57100.
- Procedure: reuse the prior entry-75CC LLVM command template; freshly disassemble 0x7544..0x7590, query exact direct xref comments for entry 0x7544 and exact pointer occurrences in the pinned full listing/raw ABL1. If a local pointer hit appears, record only its nearby words and actual reader xref; do not scan other descriptors or claim global absence.
- Expected effect: bind the wrapper input source and the +4 object construction/assignment, or stop at a precise indirect caller/table boundary.
- Output: evidence/firmware-audit/20260921-abl660-plus4-reader-context-join/run-20260921T234000+0500/.
- No firmware, ROM, hardware, register, NVRAM, network, or installation operation.

## Correction and intent — bind 0x7544 replay to active object

- Timestamp: 2026-09-21T23:56:34+05:00 (Asia/Almaty).
- Correction: the stored template `run-20260921T234000+0500/function-7544.command` names `evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/ABL1-exact.o`, not the bound active object `evidence/firmware-audit/20260921-abl660-object-identity/ABL1-clv-full-thumb.elf.o`. Do not attribute the replayed instructions to the active object until an exact readback comparison proves equivalence. Preserve the old output.
- Observed command error: `/usr/bin/llvm-objdump -d --start-address=0x7544 --stop-address=0x7f20 <active object>` exited 0, stderr empty, but yielded only the ELF header and no instruction lines; active object has one non-executable `.data` section at VMA 0. This is a wrong disassembly mode/address setup, not proof of absent code.
- Intent: append this correction to `memory/firmware-audit.md`, then create a unique corrected evidence run bound to the active object hash `adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6`. Run bounded `llvm-objdump -D --triple=thumbv7m-none-eabi` windows `[0x7544,0x7590)` and `[0x75cc,0x7f20)` with that active object, and only then follow local caller/+4/object-identity edges.
- Expected effect: reproduce entry/caller and wrapper data flow on the bound object, preserving source identity.
- Rollback: remove only the new unique evidence run if invalid; no firmware/ROM/hardware/register/NVRAM/network changes.

## Observed result — active-object 0x7544/0x75CC disassembly and identity correction

- Timestamp: 2026-09-21T23:59:52+05:00 (Asia/Almaty).
- Evidence run: `evidence/firmware-audit/20260921-abl660-plus4-reader-context-join/run-20260921T235801+0500-active-object/`.
- Exact active input: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl660-object-identity/ABL1-clv-full-thumb.elf.o`, 94624 `.data` bytes; full-file SHA-256 `adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6`, `.data` SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`. The stored template input has the same full-file SHA-256 and the same `.data` hash, so the earlier path-only mismatch is resolved: its bytes are identical to the bound active object. The prior replay is content-equivalent; fresh active-object output is retained.
- Fresh `llvm-objdump -D --triple=thumbv7m-none-eabi` windows `[0x7544,0x7590)` and `[0x75cc,0x7f20)` both exited 0; both stderr files are empty. The caller at `0x7586` executes `BL 0x75CC` after `MOV R0,R6`, where `R6` preserved caller entry R0. In the `0x75CC` prologue, `R6=R0`; `R4=[R6+4]` at `0x75E2`; `R0=[R4]` at `0x75EA`. At `0x7E74`, the call is `BL 0x5E68` with `R0=R4`, `R1=R5`, `R2=R6`. The bounded window also confirms `BL 0x109BC` at `0x7EF0` with `R0=R4`,`R1=R5`.
- The exact raw `.data` words at `0x1704C..0x1706C` remain `0x5E645,0,1,0x5E615...`; under the conditional base `0x57100`, the first function pointer maps to `0x7544`. The object comparison and bytes are reopened in `object-identity.json`; source hash before and after matches.
- Evidence class: static-analysis plus observed bytes; base/relocation conditional; table owner and entry `+4` producer remain unresolved. No hardware or firmware write.

## Intent — follow exact table-base literal to its code reader

- Timestamp: 2026-09-22T00:03:21+05:00 (Asia/Almaty).
- Target: active object `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl660-object-identity/ABL1-clv-full-thumb.elf.o` (hash remains the recorded `20260922T000321+0500`-run object); exact `.data` hit at offset `0x1B20` is the little-endian value `0x0006E14C`, which conditionally points to table RVA `0x1704C` under base `0x57100`.
- Procedure: freshly disassemble only `[0x1800,0x1C00)` on the same active object, inspect the immediate code and literal use around `0x1B20`, and preserve the relevant raw word window. No generic table/descriptors scan.
- Expected effect: bind the exact literal load / reader function to the pointer table or stop at a precise indirect boundary.
- Rollback: remove only the unique output run if invalid; no firmware, ROM, register, NVRAM, network, or hardware write.

## Intent — complete caller-to-wrapper-plus-four consumer slice

- Timestamp: 2026-09-22T00:07:26+05:00 (Asia/Almaty).
- Target: the same byte-identical active ABL1 object (`/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl660-object-identity/ABL1-clv-full-thumb.elf.o`; SHA-256 `adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6`).
- Procedure: freshly disassemble only wrapper continuation `[0x75cc,0x9000)`, allocator/request helper `[0x6238,0x6310)`, and consumer interval `[0x10958,0x10b80)`; use the existing table-reader output `[0x1800,0x1c00)` to bind the request output slot, `R6`, the stack context `SP+0x68`, and table callback `0x7544`. Search the wrapper's concrete call target(s) to determine whether this path reaches `0x10958`; stop at an unresolved indirect or external boundary.
- Expected effect: validate function terminator/CFG and either bind or explicitly break the heap-root/object identity at the local consumer.
- Rollback: remove only these uniquely named outputs if invalid; no firmware, ROM, register, NVRAM, network, or hardware write.

## Correction — linear Thumb listing is not reachable CFG

- Timestamp: 2026-09-22T00:11:52+05:00 (Asia/Almaty).
- Evidence: `evidence/firmware-audit/20260921-abl660-plus4-reader-context-join/run-20260922T000321+0500-table-reader/wrapper-to-9000.stdout` is produced by `llvm-objdump -D` over a mixed code/data `.data` section. The interval `0x7C00..0x7CE2` visibly decodes embedded ASCII strings (including `Memory Timing` and log format text) as instructions. A prior mechanical scan of apparent `R4`/`R6` destinations across that linear listing therefore included non-code and is not a CFG/data-flow result.
- Preserve earlier direct facts only at instruction sites independently anchored as code; do not carry `R4=[entry+4]` or `R6=entry` from the `0x75CC` prologue to `0x7E74`/`0x7EF0` without reachable-path proof. The `0x7E3E` sequence appears to load `R6` from `[R0+0x2BC]`, but reachability and provenance still need validation.
- Current corrective action: use a reachable CFG/code-map (or an explicit bounded branch trace) before claiming consumer identity; the 0x18xx caller's stack producer and its local `0x7544` callback link remain separately byte-backed. No firmware/hardware changed.
