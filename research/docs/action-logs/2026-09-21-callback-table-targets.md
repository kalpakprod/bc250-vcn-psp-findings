# Callback-table target trace — 2026-09-21

## Intent and scope

- Target: the separate data-dependent callback table reached by the byte-backed `0x1354 -> 0x1332 BLX R0` edge in `docs/research/2026-09-21-clock-independent-review-v2.md`.
- Scope: offline static trace of its initializer/provider and populated targets in the exact CLV ABL1 object. Do not redo item-17 dispatch/alias work; do not inspect `memory_clock_units`'s `0x7FC2 -> 0x8428` edge or downstream `0x10958`; do not touch `/root/apob_abl_handoff` or PMFW tracks. No hardware, ROM, register, NVRAM, network, or installation operations.
- Intended commands: read only the named checkpoint and its verification metadata; use the explicitly pinned ABL1 raw payload and ABL1 ELF object; invoke local LLVM objdump only for reported initializer/provider/table-target windows; save command/output/status and hashes under a new, separate evidence directory; verify evidence manifest and reopen the report, log, and evidence files.
- Expected effect: a bounded static answer on populated callback targets, or an explicit stop at the first external/indirect boundary. No firmware or source bytes are to be modified.
- Rollback: no firmware/source modification. If new evidence/report records are wrong, preserve them and append a correction; do not overwrite originals.

## Observed dispatcher correction before task trace

- Timestamp/timezone: recorded by the command environment on 2026-09-21 (Asia/Almaty).
- A first inline dispatcher incorrectly selected the donor ROM `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, because its fallback regex accepted a `.bin` referenced elsewhere in the checkpoint rather than binding the explicit ABL1 ELF. It attempted several report-address windows; output was not saved as evidence.
- One visible command was `llvm-objdump -d --start-address=0x1334 --stop-address=0x13b4 /home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`; literal stderr: `llvm-objdump: error: '/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin': can't find target: unable to get target for 'unknown--', see --version and --triple.`; exit status `1`.
- This is a dispatch/input-binding error, not evidence about the ABL1 callback table. No artifact/firmware write occurred. Correction: use only the explicitly pinned `ABL1-exact.o` from the verification metadata for disassembly; no suffix-based candidate fallback. The failed invocation remains in the conversation tool evidence; exact ABL1 checks follow separately.

## Result

- Pending.

## G7 correction — disassembler mode did not honor the intended byte window

- Timestamp/timezone: 2026-09-21T19:12:22+05:00 (host timezone Asia/Almaty).
- The corrected-input attempt used the pinned , but treated the entire non-executable section as disassemblable and emitted a broad full-section listing; the attempted literal dump likewise ignored the intended range. The command returned , but the result is unsuitable and is not semantic evidence. The output and command/status records are preserved as and ; output was visibly truncated by the tool presentation and included instructions/data beyond (as far as in the displayed tail).
- No firmware bytes were changed. Change method: stop using / with range flags on this non-X wrapped object. Next, create a temporary, narrowly sliced executable section from the exact ABL1 payload and force Thumb decoding, or use a local disassembler that supports the required bounded range; retain the full original object/payload hashes and only save the small requested range. Do not repeat a whole-image or whole-section pass.
  evidence sizes and hashes at 2026-09-21T19:12:22+05:00
  evidence/firmware-audit/20260921-abl-callback-targets/code.command size=178 bytes
  0b6d37568d4bc4220572090d9dfd70e5120a887e06cdbea1d64f8b613bf98833 evidence/firmware-audit/20260921-abl-callback-targets/code.command
  evidence/firmware-audit/20260921-abl-callback-targets/code.stdout size=3580 bytes
  65bada95d6fc6c58e7f21e03c6afafb364299db11be13cfddefc8be62a841eab evidence/firmware-audit/20260921-abl-callback-targets/code.stdout
  evidence/firmware-audit/20260921-abl-callback-targets/code.stderr size=0 bytes
  e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 evidence/firmware-audit/20260921-abl-callback-targets/code.stderr
  evidence/firmware-audit/20260921-abl-callback-targets/code.exit size=2 bytes
  9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa evidence/firmware-audit/20260921-abl-callback-targets/code.exit
  evidence/firmware-audit/20260921-abl-callback-targets/literals.command size=178 bytes
  e5b2a9203ae764a6aff7eb1c3b2f4fb309143f502d6fbd3f4b36092db75f13ec evidence/firmware-audit/20260921-abl-callback-targets/literals.command
  evidence/firmware-audit/20260921-abl-callback-targets/literals.stdout size=358314 bytes
  1bf84fe73c777d932b4d2ba3d5a3ea1185a7948632b485524eb835aa710fcc95 evidence/firmware-audit/20260921-abl-callback-targets/literals.stdout
  evidence/firmware-audit/20260921-abl-callback-targets/literals.stderr size=0 bytes
  e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 evidence/firmware-audit/20260921-abl-callback-targets/literals.stderr
  evidence/firmware-audit/20260921-abl-callback-targets/literals.exit size=2 bytes
  9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa evidence/firmware-audit/20260921-abl-callback-targets/literals.exit

## G7 correction — unquoted shell here-document expanded Markdown code spans

- Timestamp: 2026-09-21T19:13:39.263696+05:00. A follow-on logging command used an unquoted `<<EOF` while the text contained backticks. Bash executed code-span contents as command substitutions (observed `command not found`, failed `llvm-objdump` paths, and `Permission denied` when it tried to execute the recorded command-file path). This damaged the newly appended prose but did not modify firmware/source bytes; no successful external operation occurred. The shell command's diagnostic was: `/usr/bin/bash: line 6: ABL1-exact.o: command not found` (followed by command-substitution errors).
- Corrective method: append literal text through a single-quoted Python here-document (`<<'PY'`) and reopen the log and memory incident before relying on them. Preserve this failed attempt; do not rewrite the append-only records.

## Evidence-ledger correction — the two objdump modes behaved differently

- Timestamp: 2026-09-21T19:15:32.669606+05:00. Reopening the preserved output established: `code.stdout` is 3,580 bytes / 70 lines, `code.stderr` empty, `code.exit` `0`; `llvm-objdump -D --start-address=0x1320 --stop-address=0x1420` did honor the address interval, but decoded Thumb code in ARM mode and is invalid for instruction semantics. The earlier statement that this `-D` output covered the full section was incorrect and is superseded by this entry.
- `literals.stdout` is 358,314 bytes / 5,943 lines, `literals.stderr` empty, `literals.exit` `0`; `llvm-objdump -s --start-address=0x1418 --stop-address=0x1420` emitted the entire `.data` section, so this was the broad output. Preserve it only as a failed range attempt; do not use its bytes as the selected literal window.
- Corrective method remains: obtain exact bounded bytes through a section-aware extract and force Thumb decoding; record a dedicated result and stop before unrelated regions.

## G7 correction — LLVM option spelling unsupported

- Timestamp: 2026-09-21T19:21:51.902536+05:00. The focused retry `llvm-objdump -D -M force-thumb --start-address=0x1320 --stop-address=0x1420 <pinned ABL1-exact.o>` started on the correct object but LLVM 22.1.8 rejected `force-thumb` with literal stderr `llvm-objdump: error: '/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/ABL1-exact.o': Unrecognized disassembler option: force-thumb`. The shell used `set -e`, so the `.exit` file was not written; exact process status was not captured and is therefore not asserted. No disassembly semantics are claimed from this attempt.
- The command and stdout/stderr are preserved as `evidence/firmware-audit/20260921-abl-callback-targets/provider-thumb-1320-1420.*`. Corrective method: use LLVM's explicit `--triple=thumbv7m-none-eabi` on this same bounded range; capture status with `set +e` and record it before testing output.

## G7 correction — literal-pool extractor assumed one word per range

- Timestamp: 2026-09-21T19:28:50.076493+05:00. The first direct literal-pool extraction read the caller range `[0x1418,0x1420)` (8 bytes) but used `struct.unpack('<I', x)` as if it were one dword. It printed the range line then raised `struct.error: unpack requires a buffer of 4 bytes`, exit `1`; stdout/stderr/exit are preserved in `evidence/firmware-audit/20260921-abl-callback-targets/provider-literals.*`. This is a host-side extraction harness error, not an ABL1 finding.
- Correction: decode each four-byte word in the bounded range independently; also include the exact callback-record pointer/target literals at offsets `0x50d4..0x50e8` and target callback literal at `0x16b8`.

## G7 correction — JSON result serializer received a bytes value

- Timestamp: 2026-09-21T19:38:13.624972+05:00. `check_callback_targets.py` passed its byte/pointer and output-window assertions but failed while serializing its result because one `checks_detail[].observed` field was raw `bytes` (`TypeError: Object of type bytes is not JSON serializable`, `check_callback_targets.py:79`). The traceback is preserved at `evidence/firmware-audit/20260921-abl-callback-targets/check_callback_targets.stderr`; stdout is empty; with `set -e` the shell stopped before writing an exit sidecar, so exact process exit is not claimed. No result JSON was produced.
- Correction: report the stderr check as a boolean (`not read_bytes()`) rather than a bytes object; rerun the exact pinned-input verifier with status capture using `set +e` and preserve the prior failure.

## Intent — minimal verifier serialization fix and rerun

- Timestamp: 2026-09-21T19:39:23.623219+05:00. Preserve the failed JSON serialization output as `check_callback_targets-failure1.*`, change only the local verifier's stderr predicate from bytes to boolean, then rerun the exact verifier on the same hash-pinned ABL1 inputs with a captured exit sidecar. Expected effect: machine-readable result for the bounded pointer chain; rollback: keep failure1 intact and restore the original verifier copy if the change invalidates checks.

## Observed result — bounded ABL1 callback-table trace

- Timestamp: 2026-09-21T19:41:29.130752+05:00. Bound inputs rechecked: raw ABL1 `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`, 94,624 bytes, SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`; exact ELF `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/ABL1-exact.o`, SHA-256 `adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6`; LLVM 22.1.8.
- Fresh bounded Thumb LLVM windows all exit `0`, stderr empty: `0x1320..0x1420`, `0x54FC..0x557C`, `0x50C0..0x5120`, and `0x16B0..0x16B6`. Commands/stdout/stderr/status are under `evidence/firmware-audit/20260921-abl-callback-targets/`.
- Observed pointer chain: caller literal at ABL1 RVA `0x141C` = `0x6E27C`; caller calls list provider `0x54FC` at `0x1370`, then enumerator `0x1332` at `0x1376`. `0x54FC` calls record initializer `0x50C0`, writes descriptor pointer `0x6E284` to list[0] and null to list[1]. `0x50C0` fills descriptor words with `0x587B1`, `0x58659`, `0x5865D`, `0x58661`. The selected `0x1332` loop loads descriptor[0] at `0x133C` and executes `BLX R0` at `0x133E`; the one populated list item therefore yields direct target `0x587B1` (Thumb pointer). Under the prior conditional base `0x57100` only, it maps to ABL1 RVA `0x16B0`; the target code loads one byte through literal `0x6E131` and returns. Base/runtime execution remains unproven. Sibling descriptor fields were not followed.
- Direct check `/usr/bin/python3 -B evidence/firmware-audit/20260921-abl-callback-targets/check_callback_targets.py`: literal stdout `{"status":"PASS","checks":33,"passed":33,"failed":0,"table_base":"0x6e27c","record":"0x6e284","BLX_R0_site":"0x133e","direct_target":"0x587b1","conditional_RVA":"0x16b0","runtime_base":"UNPROVEN"}`; stderr empty; exit `0`.
- Checkpoint/source metadata and prior item-17 conditional branch were reused; no item-17 mapping/alias review was repeated. No `memory_clock_units` `0x7FC2 -> 0x8428` or `0x10958` edge was examined. No hardware, ROM, NVRAM, register, network, or installation operation occurred. Remaining uncertainty: loader base/runtime dispatch, semantic identity of the byte at `0x6E131`, and any behavior of sibling callback fields.
- Intended deliverables: `docs/research/2026-09-21-abl-callback-targets.md`, this action log, and the evidence directory above. Pending final manifest/hash/readback.

## Intent — finalize evidence checksum manifest

- Timestamp: 2026-09-21T19:45:31.855051+05:00. Hash every regular file in `evidence/firmware-audit/20260921-abl-callback-targets/` except the manifest itself; save the initial `sha256sum -c` literal output/status sidecars, regenerate the manifest to cover those sidecars, and perform a final read-only manifest check. Report the final manifest hash. No source or firmware bytes are to be changed.

## G7 correction — final QA used a misspelled incident path

- Timestamp: 2026-09-21T19:50:39.500503+05:00. The first readback preflight addressed `memory/incidents/2026-09-21-abl-callback-table-dispatch-input-correction.md`; the actual file is `memory/incidents/2026-09-21-callback-table-dispatch-input-correction.md`. Python raised `AssertionError` on the missing path before reading report content or running the evidence manifest/hash checks. No files were changed by the failed QA; its exact exit status was not captured.
- Correction: use the actual incident path above; rerun the bounded readback/manifest check without touching the ABL1 trace or regenerating its output.

## G7 correction — final readback predicate was case-sensitive

- Timestamp: 2026-09-21T19:51:52.734462+05:00. After correcting the incident path, final QA reached the memory-content predicate and raised `AssertionError` because it searched uppercase `0x587B1`, while the incident records the same literal as lowercase `0x587b1`. No files were changed; manifest/hash checks did not run in that QA command and its exit status was not captured.
- Correction: compare lowercased memory text (`casefold`) for hexadecimal address tokens; then rerun the same readback and manifest check. This is a QA-string predicate mismatch, not an evidence discrepancy.

## G7 correction — readback expected a prose marker absent from the action log

- Timestamp: 2026-09-21T19:54:25.258608+05:00. The address-case correction exposed the next brittle QA predicate: it searched the action log for literal `33/33`, but the log records `33 checks`, `33 passed`, `0 failed`; machine result JSON is the structured source. Readback of the incident showed both target tokens were present. No files were changed by this assertion; manifest/hash checks did not run in the failed attempt and its exact exit status was not captured.
- Corrective method after repeated QA predicate mismatches: stop checking freeform prose for derived markers. Reopen the roles by path, validate the machine JSON fields and pinned input hashes, verify the evidence manifest, and print report/log/memory hashes without content-phrase assertions.

## Deliverable closure and hash ledger

- Timestamp: 2026-09-21T19:55:43.727699+05:00. Separate report: `/home/OWNER/orca/projects/bc250/docs/research/2026-09-21-abl-callback-targets.md`, SHA-256 `4e88b6f5631e6c4002189fbaeb310ec91fd53ed5d3bff2c009ddf6d53436f87b` (at this read). Evidence directory: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl-callback-targets/`; 51 files total including the manifest, 50 hashed entries. `evidence-manifest.sha256` SHA-256 `266a8593fc23053f36c79834e89aaed7fe6161e62a24e26e1eb66923583d8cc5`. Result JSON SHA-256 `f877ab0edf28a19bd564ac27eed02bd23a9e25d9b5fcea66231fd0c2d678a4db`; result `PASS`, 33/33 checks.
- Final input read hashes remain raw ABL1 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a` and exact ELF `adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6`. Evidence manifest check was observed exit `0` on all 50 entries. Final readback of report/log/memory/evidence is the next check; no input writes are intended.

## Final QA result

- Timestamp: 2026-09-21T19:57:08.291146+05:00. Structured readback reopened the report, action log, memory incident, evidence `VERIFICATION.txt`, manifest, and JSON result. The JSON result is `PASS` with 33 passed, 0 failed. `sha256sum -c evidence-manifest.sha256` exited `0`; all 50 entries were verified (captured wrapper stdout ended `target-entry-16b0-16b6.stdout: OK`). Raw ABL1 and ELF hashes remain the pinned values above. No changes to firmware inputs or hardware were made.
- Verified paths: report `/home/OWNER/orca/projects/bc250/docs/research/2026-09-21-abl-callback-targets.md`; action log `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-21-callback-table-targets.md`; evidence `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl-callback-targets/`; memory correction/result `/home/OWNER/orca/projects/bc250/memory/incidents/2026-09-21-callback-table-dispatch-input-correction.md`.
