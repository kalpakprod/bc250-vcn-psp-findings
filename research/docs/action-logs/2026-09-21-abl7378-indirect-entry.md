# ABL1 0x7378 indirect-entry trace

## Intent — targeted 0x7378 indirect-entry trace (20260921T200924+0500)

- Objective attachment: `/home/OWNER/.codex/attachments/9d7bcc99-0793-46b7-a070-9d0a73377101/pasted-text-1.txt` (read-only). Checkpoint: `/home/OWNER/orca/projects/bc250/docs/research/2026-09-21-abl660-object-identity.md` (read only). Bind only the exact ABL1 input/object and the pending 0x7378 pointer-table query.
- Intent: search the pinned decompressed ABL1 only for aligned 32-bit pointer encodings of RVA `0x7378`, Thumb RVA `0x7379`, and their conditional absolute forms under base `0x57100` (`0x5e478/0x5e479`); record exact hit offsets and hashes in `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl7378-indirect-entry/run-20260921T200924+0500`. If a matching controller argv was present, it would be used as the template; no matching command array was found.
- This is a focused value query, not a ROM census. No hardware/network/ROM/NVRAM/register write. Rollback: no input modification; outputs are unique, disposable evidence.

## Intent — inspect the 0x7378 pointer candidate's local table origin

- Timestamp: 2026-09-21T20:11:18.411969+05:00. The targeted exact-value query found `0x5e479` at ABL1 raw offset `0x170cc` under the prior conditional base `0x57100`. Next, inspect only the nearby `[0x170b0,0x170f0)` data window and search the exact ABL1 payload for references to candidate table/object VAs in that bounded neighborhood. This may establish a pointer-table origin; it cannot prove runtime relocation or execution. Results will be saved under `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl7378-indirect-entry/run-20260921T200924+0500`.
- No hardware, network, ROM, register, NVRAM, or installation action.

## Intent — decode xrefs to the bounded candidate table object

- Timestamp: 2026-09-21T20:12:04.844608+05:00. The exact pointer query found conditional object VA `0x6e1c8` at ABL1 raw offsets `0x1b1c` and `0x1bac`, and `0x6e1c4` at `0x1bb4`. Decode only Thumb instruction windows around those literal sites (`[0x1b00,0x1b40)` and `[0x1b90,0x1bc0)`) from the same pinned ABL1 ELF; purpose is to identify whether/how callers pass the candidate table/object. Preserve conditional base `0x57100`; do not follow sibling memory-clock or 0x10958 flow. Results go to `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl7378-indirect-entry/run-20260921T200924+0500`.

## Intent — decode the code window that may load the table-base literal

- Timestamp: 2026-09-21T20:13:26.072010+05:00. The bounded candidate window shows VA literal `0x6e1c8` at ABL1 RVA `0x1b1c` and `0x6e1c8/0x6e1c4` in the pool at `0x1bac/0x1bb4`. The initial Thumb window shows a nearby function beginning at `0x1b24`, but did not cover its full body. Decode only `[0x1b24,0x1b90)` to test whether that code references the candidate object; no whole-image listing or unrelated table trace.

## Intent — trace the concrete 0x7378-table callback field

- Timestamp: 2026-09-21T20:19:33.542198+05:00. The decoded 0x1B24 function loads table base `0x6E1C8`, computes records in 36-byte strides, and invokes record field `+0x8` through `BLX R1` at `0x1B56`. Under conditional base `0x57100`, table RVA `0x170C8` has record[0] field `+0x8 = 0x62059`; record[1] and later `+0x8` fields in the bounded table are zero. This is distinct from the earlier 0x6E27C/0x133E table and from the memory-clock 0x10958 consumer. Decode only target window `[0xAF40,0xAF80)` around conditional RVA of `0x62059` and save it in the same unique run.

## Intent — complete conditional target 0x62059 / RVA 0xAF58 decode

- Timestamp: 2026-09-21T20:20:59.463035+05:00. Decode only the concrete callback target at conditional RVA `0xAF58` through its local return, using the pinned ABL1 ELF and Thumb triple. Separately validate the table count byte at conditional VA `0x6E200` (RVA `0x17100`) and the first two record `+0x8` fields at RVA `0x170D0` and `0x170F4`, confirming whether the zero second field terminates callback dispatch without interpreting later records. No generic scans and no `0x10958`/`memory_clock_units` work.
- Expected result: exact outgoing calls, return path, and whether AF58 forwards its incoming R0 to `0x7378`; stop if an external/indirect boundary is reached.

## Intent — exact AF58 body only

- Timestamp: 2026-09-21T20:22:32.719101+05:00. Objective attachment was reopened before execution. Run one new, bounded Thumb disassembly of exact AF58 body `[0xAF58,0xAF8C)`, ending after `POP ... PC`; do not repeat table-base search. Record outgoing direct calls, R0/R1 forwarding, memory writes, and return. No hardware/network/ROM changes.

## Intent — machine-check AF58 body and bounded table termination

- Timestamp: 2026-09-21T20:25:03.085642+05:00. Convert the just-observed AF58 body listing plus the already executed exact table-count read into a small JSON verifier. Check only pinned ABL1 hash, AF58 listing instruction/call/write predicates, absence of direct `BL 0x7378`/`BL 0xAF90` in this body, and count/record[0..1] values. Save result and literal stdout/stderr/status in the existing unique run; no additional disassembly or broad scan.

## Observed result — AF58 callback target

- Timestamp: 2026-09-21T20:26:52.066281+05:00. Exact AF58 body `[0xAF58,0xAF8C)` disassembly exited `0` with empty stderr. Machine verifier exited `0`, literal stdout reports `PASS`, `23/23`, target `0x62059 -> conditional RVA 0xAF58`, direct links to `0x7378` and `0xAF90` both `false`, opaque direct callees `0x5CBE` and `0xFE60`.
- AF58 saves incoming `R0` in `R4`. If incoming R0 is zero, it first calls `0x64C8`; otherwise it skips that branch. It then calls `0x5CBE` with `R0=SP` and `R1=the saved incoming R0`; calls `0xFE60` with `R0=SP`; if that returns nonzero, it clears bytes at `[[R4+0x28]+0x739]`, `[[R4+0x28]+0x75F]`, and `[[R4+0x28]+0x760]`; then returns at `0xAF8A`. It does not directly call `0x7378` or `0xAF90`, and does not directly forward incoming R0 as R0 to either.
- Table termination check exited `0`: conditional table base `0x6E1C8 -> RVA 0x170C8`; count pointer `0x6E200 -> RVA 0x17100` has byte `2`; record stride `0x24`; record[0] `+0x8` = `0x62059`; record[1] `+0x8` = `0`. The bounded count permits two iterations, and the second callback field is zero, so later records are not interpreted by this loop.
- This is static observed-bytes/static-analysis evidence only. `0x5CBE` and `0xFE60` are the exact opaque boundaries; their indirect behavior could still reach other code, but no such claim is made here. Context-relative offsets `0x739/0x75F/0x760` are not identified as clock-policy fields; no clock register or policy semantic follows.

## Intent — finalize AF58 evidence manifest and readback

- Timestamp: 2026-09-21T20:28:16.047312+05:00. Hash every regular file in the unique run directory except its manifest; run `sha256sum -c` and preserve literal output/status, then reopen the new report, action log, result JSON, and manifest. No source/input modification.

## Closure

- Timestamp: 2026-09-21T20:29:36.115089+05:00. `af58-body-result.json` reopened: `PASS`, `23/23`; manifest has `46` entries and final `sha256sum -c` exit `0`. Manifest SHA-256: `ec79417e1172483d2abbcb6d528255bc4a5850afece2ee60fe79ad078940fdee`.
- Report path: `/home/OWNER/orca/projects/bc250/docs/research/2026-09-21-abl7378-indirect-entry.md`; report SHA-256: `b37fd1a982010629e1a830e2f8cab14e7bce9ff8b8c596ed8222c3be7a8a1f2b`. Unique run: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl7378-indirect-entry/run-20260921T200924+0500`. Exact AF58 command exit `0`, stderr empty. Pinned raw/object hashes remained unchanged.
- Final conclusion: callback table record 0 reaches `0x62059 -> conditional RVA 0xAF58`; AF58 has no direct call to `0x7378` or `0xAF90`; opaque boundaries are `0x5CBE` and `0xFE60`; table count/zero record 1 prevents later record callback invocation.

## G7 correction — final manifest shell used an unset variable

- Timestamp: 2026-09-21T20:31:02.988656+05:00. The final QA command attempted `cd "$out"` in a fresh shell where `out` was unset, producing literal stderr `bash: line 23: cd: null directory` and no manifest output; no evidence or source file was modified. This is a shell QA binding error, not an evidence failure.
- Correction: use the absolute run directory in the manifest command and capture its status/output.

## G7 correction — manifest reconciliation log text had Python brace interpolation

- Timestamp: 2026-09-21T20:32:58.071038+05:00. The manifest reconciliation wrapper used an f-string containing literal `{stdout,stderr,exit}` and raised `NameError: name 'stdout' is not defined` before appending its intent. The shell continued to the independent manifest regeneration/check, which completed with exit `0` for 49 entries. No input/evidence bytes were altered by the failed append; the exact traceback is retained in the conversation tool result.
- Corrective method: append literal text without f-string interpolation; do not regenerate the manifest again unless a new evidence file is intentionally added.

## Final ledger readback

- Timestamp: 2026-09-21T20:34:12.483750+05:00. Final manifest is 49 entries, SHA-256 `3a2090091bd7b161e57aa81ec68ff3de1727e7092bc15b619fdedd71420484f3`; verification was rerun with output outside the evidence directory and exited `0` (49/49). Result JSON remains `PASS`, 23/23. Report was extended with the final manifest hash.

## Intent — bounded 0x5CBE/0xFE60 call-contract trace

- Timestamp: 2026-09-21T20:36:09.086280+05:00. Objective attachment reopened before execution. Trace only the two direct AF58 callees `0x5CBE` and `0xFE60` with narrow Thumb windows from the exact ABL1 ELF. Record entry arguments, direct memory writes, return values/paths, clock-policy literals/names if present, and stop at any indirect/external boundary. Do not repeat AF58 body/table work; no hardware/network/ROM changes.

## Intent — exact helper-body contracts and string/call predicates

- Timestamp: 2026-09-21T20:38:40.764955+05:00. Objective attachment and minimum checkpoint were reopened. Run narrow Thumb windows for exact helper bodies `0x5CBE..0x5CCA` and `0xFE60..0xFE74`, then run only local string/call predicates against those saved outputs and the caller listing. Determine helper input/output and direct writes; stop at first indirect boundary. No AF58/table repeat, broad scan, or hardware/network/ROM/NVRAM action.

## G7 correction — initial FE60 host model used the wrong source bit

- Timestamp: 2026-09-21T20:40:00.923625+05:00. The first helper verifier passed byte-pattern checks but modeled `LSLS r1,#0x1E` and `LSLS r0,#0x1F` as tests of original bit 15. For the exact `0x5CBE` output `[2,1]`, these shifts test original bit 1 and bit 0 respectively; both are set, so `0xFE60` returns `1`, not `0`. The incorrect verifier result (`PASS 20/20`, `fe60_on_5cbe_output=0`) is retained as `helper-contract-check-failure1.*` and is withdrawn.
- Correction: change only the host model and explanatory result field to `fe60_on_5cbe_output=1`; rerun the same exact helper listing checks, preserving pinned inputs and prior outputs. This correction changes AF58's observed consequence: it proceeds to the three cleanup byte stores.

## G7 correction — verifier source was not saved by the first inline run

- Timestamp: 2026-09-21T20:41:40.541598+05:00. The correction wrapper attempted to open `helper-contract-check.py`, but the initial verifier had been inline and no such source file existed. It exited `2` (`can't open file ... helper-contract-check.py`) after the source-bit correction preparation; this is a harness error, not a new binary result. The prior wrong model output remains in `helper-contract-check.stdout` and `helper-contract-result.json` and is not used.
- Corrective method: write a new standalone `helper-contract-check-corrected.py`, preserve prior wrong outputs under `failure1.*`, and emit corrected outputs under `helper-contract-check-corrected.*`.

## Observed result — 0x5CBE/0xFE60 contracts

- Timestamp: 2026-09-21T20:42:38.605544+05:00. Objective attachment and minimum checkpoint were reopened before the exact narrow runs. `0x5CBE..0x5CCA` and `0xFE60..0xFE74` Thumb objdump commands exited `0`, stderr empty. Corrected helper verifier exited `0`, `22/22` checks; result `helper-contract-result-corrected.json`.
- `0x5CBE` ignores AF58's saved-R0 argument, writes `u16 [R0]=2` and `u16 [R0+2]=1`, returns `R0=1`. `0xFE60` reads those two halfwords and tests original bit 1 of the first and bit 0 of the second by `LSL #30/#31`; on `[2,1]` both pass, so it returns `R0=1`. The initial bit-model result that said `0` was withdrawn and preserved under `failure1-*`; corrected result is authoritative.
- No direct clock-policy literals were observed in these exact helper bodies. `0x5CBE` and `0xFE60` perform only stack-buffer validation/flag production; AF58 then conditionally clears its object-relative bytes. No `0x7378`/`0xAF90` link is introduced. No indirect/external boundary occurs inside the two exact helper bodies; caller-level semantics stop there.

## Intent — reconcile helper-contract evidence manifest

- Timestamp: 2026-09-21T20:43:19.404321+05:00. Include the corrected helper-contract outputs and preserved failure/harness sidecars in the unique run manifest, then verify all entries with output outside the evidence directory. No source/input modification.

## Helper-trace closure

- Timestamp: 2026-09-21T20:44:12.937433+05:00. Corrected helper result reopened: PASS, 22/22; final manifest has 84 entries, SHA-256 `71e32b692ae9b85c54103cd401c4478ef76d3acf85bec3b68f454d0f171a0569`; absolute-path manifest verification exited 0. Report SHA-256 before this log-only closure append: `c15b43356e66dcdad621e0cf2f89a61af43dc00d84b32d8a8b15fc1bb79952c8`.
- Final contract: 0x5CBE produces stack halfwords [2,1] and returns 1; 0xFE60 returns 1 on that exact buffer; no direct clock literals, 0x7378, or 0xAF90 in either helper body.

## G7 correction — table stride and row1 field offset

- Timestamp: 2026-09-21T21:40:00+05:00 (Asia/Almaty). The prior result's record stride 0x24 and record[1] +0x8 @ 0x170F4 are superseded. Fresh bounded /usr/bin/llvm-objdump -D --triple=thumbv7m-none-eabi --start-address=0x1b40 --stop-address=0x1b62 .../ABL1-exact.o exited 0, stderr empty. RSB r0,r4,r4,LSL #3 followed by ADD r0,r6,r0,LSL #2 computes table_base + 28*i (stride 0x1C).
- Fresh standard-library little-endian check at evidence/firmware-audit/20260921-abl7378-reader-stride-correction/run-20260921T213700+0500/raw_fields.py exited 0, stderr empty. It confirms table VA 0x6E1C8, count VA 0x6E200, count 2, row0+4 0x5E479, row0+8 0x62059, and actual row1+8 at RVA 0x170EC = 0. The reader loads record +0x8, not row0 +0x4; the candidate is not consumed by this loop.
- The former read at 0x170F4 is not row1+8 for the actual stride. Preserve prior outputs; the correction report is appended in docs/research/2026-09-21-abl7378-indirect-entry.md.
