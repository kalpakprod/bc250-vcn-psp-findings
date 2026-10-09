# ABL1 HEAP key 0xA04E producer and APOB/INV boundary — targeted trace

## Intent (before owned evidence writes)

- Timestamp: 2026-09-21T15:20:00+05:00 (Asia/Almaty)
- Actor: delegated project executor (`gpt-5.6-luna`; offline read-only).
- Target: exact CLV donor `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`; exact decompressed ABL1 payload SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Objective attachment/current boundary: existing provider trace reaches fixed selector-case HEAP key `0xA04E`; existing APOB handoff trace reaches service `0x9E3B14C/message 0x61/argument 0xFF` but does not join its output to ABL1. Trace one exact HEAP node producer/populator path and name the first unresolved APOB/`$INV 0x11ED` boundary.
- Scope: inspect ABL1 provider `0x49CC`, HEAP lookup `0x6374`, HEAP producer `0x6238`, byte-copy helper `0x6B78`, and the ABL1 runtime-object constructor at `0xC00`/caller `0xB84`; compare only the existing AmdMem APOB service bytes and native `$INV 0x11ED` evidence as boundary context. Do not repeat PPI GUID proof or `$INV 0x1204` work.
- Hypothesis: the missing HEAP node is populated by `0x6238` from a field-backed runtime pointer (`outer+0x864`), while the provider key is `0xA04E`; this will close the writer/field edge but leave the producer of the outer object/APOB-to-field bridge unresolved.
- Existing routes reused: exact ABL1 payload and LLVM Thumb listing under `evidence/firmware-audit/20260920-clv-abl1-downstream/`; prior machine result under `evidence/firmware-audit/20260921-abl1-df-key-join/`; prior exact AmdMem module under `evidence/firmware-audit/20260919-inv-token-consumers/`; existing native `$INV 0x11ED` report only as read-only context.
- Expected effect: unique verifier, JSON result, literal stdout/stderr/exit captures, report, and manifest; no ROM, firmware, NVRAM, register, hardware, network, source, shared memory, or candidate changes.
- Rollback: remove only `evidence/firmware-audit/20260921-apob-abl-heap-populator/`, this report, and this action log.
- Acceptance event: verifier starts, exits, and reports exact key write, source pointer field, copy helper, APOB service boundary, native INV boundary, and first unresolved edge.

## Correction to initial verifier trial (before rerun)

The first run exited `1` on a local slice-width assertion: provider `0x4B34` is a 2-byte `ADD SP` instruction (`09 A8`) followed by the next instruction, but the verifier sliced four bytes while expecting two. No input artifact or finding changed; the corrected check uses the exact two-byte window.

## Correction to second verifier trial (before rerun)

The second run exited `1` on another local Thumb display-order expectation: listing `E9CD 0605` is raw `CD E9 05 06` at `0x4B4E`. The corrected verifier now uses raw little-endian bytes for the descriptor construction and narrows adjacent instruction slices. No input artifact or finding changed.

## Correction to third verifier trial (before rerun)

The third run exited `1` only because the expected ASCII bytes for the raw `HEAP` literal were reversed (`48 45 41 50` is the byte string `HEAP`). The verifier expectation was corrected; no input artifact or finding changed.

## Correction to fourth verifier trial (before rerun)

The fourth run exited `1` on a local slice-width error at constructor `0xC29E`: the expected two-instruction window is 8 bytes, while the verifier sliced 6 bytes. The exact window is `01 F6 64 00 C1 F8 6C 28`; no input artifact or finding changed.

## Correction to fifth verifier trial (before rerun)

The fifth run exited `1` on a local slice-width error at `0xC2A8`: the verifier sliced 4 bytes for a 6-byte two-instruction window. The exact window is `29 90 01 F5 07 60`; no input artifact or finding changed.

## Correction to sixth verifier trial (before rerun)

The sixth run exited `1` on the adjacent constructor window at `0xC2AE`: the verifier sliced 4 bytes for a 6-byte instruction pair. The exact window is `C1 F8 64 28 81 4A`; no input artifact or finding changed.

## G6 method pivot and independent disassembly readback

After repeated local raw-byte assertion-oracle errors, the method class changed to fresh LLVM Thumb disassembly windows. Commands for provider `0x4B1A..0x4B64`, HEAP writer `0x6238..0x6344`, copy helper `0x6B78..0x6B84`, and constructor `0xBD0..0xC2B4` all exited `0` with empty stderr. The retained listings independently show provider key/call, node-key store/copy call, byte-copy loop, and constructor `outer+0x864` field stores. This pivot is the acceptance readback for the manual raw-byte trial corrections; inputs remain unchanged.

## Observed result after write

- Timestamp: 2026-09-21T15:38:00+05:00 (Asia/Almaty)
- Verifier command: `PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260921-apob-abl-heap-populator/heap_populator_verify.py`
- Exit status: `0`; literal stdout: `PASS`, `34/34`; literal stderr empty.
- Positive new edge: fixed HEAP key `0xA04E` -> miss descriptor -> `0x6238`; `0x6238` writes key to the new node and copies payload from R10 through `0x6B78`; provider source pointer is outer object `R1+0x864`; constructor `0xC00` initializes that field to `0x006CD4D0`.
- First missing edge: the producer of the outer ABL1 object passed by callers `0xB84/0xBD2` and any relation of `outer+0x864/0x006CD4D0` to APOB service `0x9E3B14C/message0x61/arg0xFF` or native `$INV 0x11ED`.
- Fresh LLVM Thumb windows `provider 0x4B1A..0x4B64`, `HEAP 0x6238..0x6344`, `copy 0x6B78..0x6B84`, `constructor 0xBD0..0xC2B4` each exited `0`, empty stderr; raw/decoded windows corroborate the byte assertions.
- Manifest `sha256sum -c evidence/firmware-audit/20260921-apob-abl-heap-populator/SHA256SUMS.final`: `12/12 OK`; manifest SHA-256 `03f9413d47e89300ea4bf3811451d6bfbe3d40b14036852e8d0c8642abbfc4b1`.
- No ROM, firmware, NVRAM, register, hardware, network, candidate, shared memory, or source input changed. Hardware/runtime status remains unrun.

Readback hashes:

```text
7995df35b9cf7e19239c4dd3a6f3589daf7cd5cadefeffd298c7c304456ccc01  docs/research/2026-09-21-apob-abl-heap-populator.md
41bdf4e173dc91e840f7d16e35281c878b37207c52d9d039ebb37185803d1f9f  evidence/firmware-audit/20260921-apob-abl-heap-populator/heap_populator_verify.py
acad9717893994744064d2f9573661aec0ad65024fd2816f39296e811d81a617  evidence/firmware-audit/20260921-apob-abl-heap-populator/heap-populator-result.json
85fc6a35b3c5a8427f2601465acff3736869d70412296d22885cc6439c34c920  evidence/firmware-audit/20260921-apob-abl-heap-populator/verifier.stdout
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  evidence/firmware-audit/20260921-apob-abl-heap-populator/verifier.stderr
ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8  evidence/donor/retroweb-20260916/BC250_5.00_clv.bin
```

## G6 process correction and final readback

The first six verifier trials failed on manual byte-oracle issues (section/RVA offset, width, Thumb halfword ordering, and expected string bytes); I should have changed method after the third failure per G6. The later method pivot to fresh `llvm-objdump` windows produced successful instruction-level readback, but it was delayed. No source/input changed; preserve all six failed captures/errors in the existing `verifier.stderr` trail only if the shell capture persisted (the final successful stderr file is intentionally empty). Future work on these bytes must use decoded-window/raw-byte reconciliation first, not additional hand-entered literals.

Final evidence manifest check: `sha256sum -c evidence/firmware-audit/20260921-apob-abl-heap-populator/SHA256SUMS.final` returned `12/12 OK`.

Final owned path hashes (recomputed after report/log appends):

```text
7995df35b9cf7e19239c4dd3a6f3589daf7cd5cadefeffd298c7c304456ccc01  docs/research/2026-09-21-apob-abl-heap-populator.md
03f9413d47e89300ea4bf3811451d6bfbe3d40b14036852e8d0c8642abbfc4b1  evidence/firmware-audit/20260921-apob-abl-heap-populator/SHA256SUMS.final
```

No ROM, firmware, NVRAM, register, hardware, network, candidate, shared plan, shared memory, or source input changed. Rollback is deletion of only this owned report/log/evidence directory.

G6 final-manifest command correction: the first readback invoked `sha256sum -c` from the project root, but `SHA256SUMS.final` contains evidence-directory-relative names; it exited `1` with 12 `No such file or directory` errors. Corrected procedure is to run from the manifest's directory. From `evidence/firmware-audit/20260921-apob-abl-heap-populator/`, `sha256sum -c SHA256SUMS.final` returned `12/12 OK`, exit `0`. No files changed during this failed check.
