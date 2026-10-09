# 2026-09-21 callback-table disassembly input-binding correction

## Trigger and incorrect action

During continuation of the bounded callback-table trace, an inline address-extraction dispatcher scanned the whole `clock-independent-review-v2` report and accepted the first existing `.bin` mentioned in its prose as the disassembly input. It therefore selected the donor ROM at `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` rather than the ABL1 ELF explicitly pinned by the verification metadata. The visible `llvm-objdump` attempt at `[0x1334, 0x13b4)` failed with unknown architecture (`unknown--`, exit 1). This failure says nothing about the ABL1 code.

## Correction and measurement

The checkpoint metadata identifies `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl-item17-svc6-independent-review/ABL1-exact.o` as the ABL1 ELF object and SHA-256 `adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6`; its raw input is `ABL1-clv-decompressed.bin` with SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`. Use that explicit path/hash, not file-suffix discovery. Save the next exact invocation, output, stderr, exit status, and hashes under the callback-target evidence directory.

## Scope

Static/offline only. Do not redo the already-completed item-17 reachability/alias reviews and do not cross into the separately owned `memory_clock_units` `0x7FC2 -> 0x8428` or `0x10958` track. No hardware, ROM, register, NVRAM, network, or installation operation occurred.

## Second correction — range flags were ineffective on a non-executable data section

After correcting the input binding, returned but decoded the whole wrapped ELF section, because the section lacks the executable flag; the literal command also emitted beyond the requested interval. The preserved is full-section output and must not be used as callback evidence. This is a tool-mode/range error, not ABL1 semantics. The changed method is to inspect a small bounded extracted slice with an executable Thumb section or a bounded disassembler; do not repeat / on the whole wrapped object.

## Third correction — safe logging method

A correction-log append was attempted with an unquoted Bash here-document containing Markdown backticks. Bash performed command substitutions; observed errors included `ABL1-exact.o: command not found`, failed `llvm-objdump` invocations on missing relative paths, and `Permission denied` for a recorded `.command` file. No successful firmware, source, network, hardware, or installation operation occurred. The append-only records were then corrected by appending literal text via a single-quoted Python here-document. Reopen both records and confirm their exact text before resuming analysis.

## Fourth correction — disassembly output itself was bounded, but decoded in ARM mode

Reopened evidence sizes show `code.stdout` has 70 lines / 3,580 bytes for the requested `0x1320..0x141f` range, stderr empty, exit 0. The previous note that `-D` covered the whole section was wrong: the disassembly range was honored, but the wrapped ELF `.data` lacks executable flags and LLVM defaulted to ARM decoding rather than Thumb; that output is not valid instruction evidence. The broad output was the separate `llvm-objdump -s --start-address=0x1418 --stop-address=0x1420` command, which emitted all 358,314 bytes / 5,943 lines of `.data` (stderr empty, exit 0) despite the intended byte range. The large output is retained as a failed range attempt only.

## Fifth correction — local LLVM ARM backend does not accept `force-thumb`

LLVM 22.1.8 returned the exact diagnostic `Unrecognized disassembler option: force-thumb` for the bounded `[0x1320, 0x1420)` attempt on the pinned ABL1 ELF. The shell's `set -e` stopped before writing the status sidecar; exact process exit is not recorded. No semantics are inferred. Next invocation changes mode-selection method to the explicit `--triple=thumbv7m-none-eabi`, captures status without `set -e`, and keeps the same narrow address bounds.

## Sixth correction — literal extractor must iterate over dwords

The bounded extraction of caller literal pool `[0x1418,0x1420)` failed because the helper tried to unpack all 8 bytes as one 4-byte integer. Observed traceback: `struct.error: unpack requires a buffer of 4 bytes`, exit 1. It is not binary corruption. Preserve the failed result; next extractor unpacks each aligned u32 little-endian word separately and reports raw bytes.

## Seventh correction — machine result requires JSON-safe observed values

The new callback verifier reached JSON serialization after its assertions but failed because it stored `b''` as an observed value; literal error: `TypeError: Object of type bytes is not JSON serializable` at line 79. No result JSON was written and the shell did not capture an exit sidecar. Correct the value to a boolean and rerun with explicit status capture; preserve the error output. This does not disprove any input bytes or disassembly claim.

## Static callback trace result (2026-09-21)

From the exact pinned ABL1 ELF/raw payload and bounded LLVM Thumb windows, the caller at `0x1354` passes table base literal `0x6e27c` to `0x54fc`, then passes it to enumerator `0x1332`. Provider `0x54fc` calls `0x50c0`; the latter writes target fields `[0]=0x587b1`, `[4]=0x58659`, `[8]=0x5865d`, `[12]=0x58661` into record `0x6e284`. Provider writes record pointer `0x6e284` as list[0] and null as list[1]. Enumerator `0x1332` loads `[record]` at `0x133c` and invokes it with `BLX R0` at `0x133e`. Thus one populated list item resolves the exact `BLX R0` target to Thumb pointer `0x587b1`. Its RVA is `0x16b0` only under the prior conditional ABL1 base `0x57100`; bytes at that RVA are `LDR literal; LDRB r0,[r0]; BX lr`, with literal `0x6e131`. The machine byte/window check passed `33/33`. This remains static conditional mapping, not runtime reachability; sibling descriptor callbacks and the separate `0x10958` track were not followed. Report and evidence paths are in the action log after final readback.

## Eighth correction — readback preflight path typo

A final readback assertion used the wrong filename `2026-09-21-abl-callback-table-dispatch-input-correction.md`; the actual incident is `2026-09-21-callback-table-dispatch-input-correction.md`. The assertion failed before report content, hashes, or manifest checks ran; no files were changed. Exact command status was not captured. Correct the QA path only; do not repeat the trace.

## Ninth correction — address-case-sensitive final QA

The corrected readback path reached a predicate that required uppercase `0x587B1`, while this incident uses lowercase `0x587b1`. It stopped before manifest/hash checks and made no writes; exact command status was not captured. Use case-insensitive hexadecimal matching; the observed address values are unchanged.

## Tenth correction — final QA used an unrecorded prose marker

The readback assertion searched the action log for `33/33`; the log's truthful equivalent is `33 checks; 33 passed; 0 failed`. The result JSON carries the structured count. The incident address checks both passed. This is a QA predicate failure with no file modification. After three failed final-QA predicate approaches (path, case, prose marker), change method: use structured JSON and actual `sha256sum -c`, not freeform substring assertions.

## Deliverable paths (2026-09-21)

- Report: `/home/OWNER/orca/projects/bc250/docs/research/2026-09-21-abl-callback-targets.md` (SHA-256 at creation/read: `4e88b6f5631e6c4002189fbaeb310ec91fd53ed5d3bff2c009ddf6d53436f87b`).
- Action log: `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-21-callback-table-targets.md`.
- Evidence directory: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl-callback-targets/`; manifest SHA-256 `266a8593fc23053f36c79834e89aaed7fe6161e62a24e26e1eb66923583d8cc5`; result JSON SHA-256 `f877ab0edf28a19bd564ac27eed02bd23a9e25d9b5fcea66231fd0c2d678a4db`, 33/33 PASS.
- This table is distinct from the `memory_clock_units` B0C4/`0x10958` object track: owned pointer list base `0x6e27c`, descriptor `0x6e284`, direct `BLX R0` site `0x133e`, target `0x587b1`. Runtime base remains unproven.

## Final QA readback (2026-09-21)

Structured JSON re-open: `PASS`, 33/33. `sha256sum -c evidence-manifest.sha256`: exit 0, all 50 entries. The final readback reopened the report, action log, memory incident, evidence verification text, manifest, result JSON, and pinned ABL1 inputs; raw/object hashes remained unchanged. Report, action-log, and evidence paths are recorded in the closure above.
