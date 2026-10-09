# CLV ABL1 runtime-heap lookup bridge follow-up — intent

Timestamp: 2026-09-20T10:20:00+05:00 (+05:00)
Actor: luna xhigh bounded worker
Target: exact decompressed CLV ABL1 payload and pinned CLV ROM/APCB; no firmware or hardware writes.

Bounded action: re-open exact existing ABL1 runtime-key boundary and parser outputs, then test the immediate `0x6374` result fields for key `0xA04E` through the provider's caller and adjacent `0x6238` and `0x4e4c` behavior. Inspect only the explicit call chain, table base/sentinels, and exact pinned APCB parser output. Determine whether the returned pointer/length is consumed or copied into a downstream caller/context descriptor, or state the narrow closed-code boundary.

Pinned inputs to reopen:

- ROM `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, expected SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- ABL1 `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`, expected SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Prior runtime-heap verifier/report/result, prior provider result, prior APCB parser output.

Existing route reused: `scripts/apcb_detail.py` and the exact pre-existing ABL1 Thumb disassembly. New unique verifier will directly byte-check small exact windows and read/hash the existing parser output; it will not create an APCB parser or sweep unrelated sources.

Expected effect: unique evidence directory, this report and this append-only log only. No firmware, hardware, settings, project plan, shared memory, installation, global config, MCP/Cutter, candidate, source input, commits, or subagents.

Rollback: remove only this unique evidence directory, report, and action log.

## Correction after first verifier execution

Timestamp: 2026-09-20T10:30:00+05:00 (+05:00)
Observed execution error: verifier exit `1` at the raw assertion for the 0x4B34 descriptor setup. Direct read from the pinned payload yielded bytes `09 a8 29 99 09 96`; the verifier expected the first six bytes in disassembly/display ordering (`a8 09 99 29`). No input was changed.

Correction: change only the expected raw-byte order for this assertion to `09a829990996`, then rerun the bounded verifier. Preserve this failed execution and stderr.

## Correction after second verifier execution

Timestamp: 2026-09-20T10:32:00+05:00 (+05:00)
Observed execution error: verifier exit `1` at the next raw assertion after the descriptor-window correction. Direct read at `0x4B38..0x4B3B` is `09 96 01 f0`, not display-ordered `96 09 f0 01`.

Correction: change only this short raw expectation to `099601f0`; retain both observed errors.

## Method-class change after third repeated raw-window failure

Timestamp: 2026-09-20T10:34:00+05:00 (+05:00)
Observed execution error: verifier exit `1` at another manually transcribed instruction window (`0x6374`). Direct source bytes were `1c 4a f8 b5 ...`, but the verifier again had display-order halfwords. This is the third same-kind byte-order transcription failure in this run.

Circuit-breaker action: stop hand-authoring multi-instruction hex expectations. Keep the direct `llvm-objdump` run as a real independent view, parse its address/byte/mnemonic fields mechanically, compare its emitted bytes against the exact ABL1 source slices, and assert concise instruction semantics at selected anchors. A Capstone availability check returned `ModuleNotFoundError`; no package install was attempted. Retain all failed executions and switch verification method class as required.

## Focused disassembly window correction

Timestamp: 2026-09-20T10:36:00+05:00 (+05:00)
Observed execution error: after changing to mechanically parsed LLVM instruction text, verifier exit `1` because the focused disassembly began at `0x4B1A` but the newly added seed anchors are at `0x4B10/0x4B18`; `KeyError(19216)` (`0x4B10`). No firmware input was read beyond the already pinned payload and no result JSON was written.

Correction: rerun the existing focused disassembly with the narrow start address extended to `0x4B0E`, preserving its same end `0x4C26`; no code or source input changes.

## Disassembly parser normalization correction

Timestamp: 2026-09-20T10:38:00+05:00 (+05:00)
Observed execution error: the mechanical disassembly parser retained LLVM's symbol/comment suffix on `bl 0x6374`, so a mnemonic-anchor check failed (`got ... <symbol> @ imm ...`; exit `1`). The underlying decoded target is visible and the direct window bytes remain input-matched.

Correction: normalize only symbol/comment annotations after parsing each emitted instruction line; preserve the raw output and retain the failed status.

## Focused disassembly window extension

Timestamp: 2026-09-20T10:40:00+05:00 (+05:00)
Observed execution error: verifier exit `1` because the selected bridge window ended at `0x4C26`, while pointer-table destination anchors are at `0x4C5E/0x4C6A`.

Correction: add a second narrow LLVM window `0x4C5C..0x4C70` and parse it with the same source-byte reconciliation; no broad scan or source input change.

## Lookup-window routing correction

Timestamp: 2026-09-20T10:42:00+05:00 (+05:00)
Observed execution error: verifier exit `1` because lookup anchors `0x6374..0x63B6` were incorrectly requested from the heap-init-only window `0x63F8..0x6428`.

Correction: route lookup anchors through the existing full Thumb listing (source-byte reconciled) while retaining the narrow heap-init and call windows.

## Narrow lookup-window generation

Timestamp: 2026-09-20T10:44:00+05:00 (+05:00)
This is the planned bounded method after the raw-byte method-class switch. Generate only payload `0x6374..0x63B8` from the existing exact object so lookup semantics are parsed without reopening/scanning unrelated ABL1 instructions.

## Lookup disassembly comment normalization

Timestamp: 2026-09-20T10:46:00+05:00 (+05:00)
Observed execution error: verifier exit `1` because LLVM's PC-relative annotation at `0x6374` uses `@ 0x63E8`, while the current normalization only removed `@ imm` suffixes.

Correction: discard the full trailing disassembler annotation delimiter `@` after parsing instruction bytes/mnemonic; exact source-byte reconciliation is retained.

## Instruction-anchor address correction

Timestamp: 2026-09-20T10:48:00+05:00 (+05:00)
Observed execution error: verifier exit `1` because the manually selected anchor at `0x6378` was labeled as the push instruction. The fresh narrow listing shows push at `0x6376`, `ldr r7` at `0x6378`; subsequent offsets are adjusted accordingly.

Correction: change only the verifier's lookup instruction addresses/expectations to the exact narrow listing above; keep the LLVM stdout and exact source bytes.

## Result serialization correction

Timestamp: 2026-09-20T10:50:00+05:00 (+05:00)
Observed execution error: all preceding checks reached result serialization, but the verifier exited `1` because a successful byte assertion (`HEAP`) was retained as a Python `bytes` object in the JSON detail ledger (`TypeError: Object of type bytes is not JSON serializable`).

Correction: normalize bytes values to printable `hex:<hex>` in check ledger fields only. No input or finding changed.

## Observed bounded result

Timestamp: 2026-09-20T10:55:00+05:00 (+05:00)
Actor: luna xhigh bounded worker

Reopened pinned ROM/ABL1 hashes and prior reports. Existing APCB parser executed read-only:

```text
python3 -B scripts/apcb_detail.py evidence/donor/retroweb-20260916/BC250_5.00_clv.bin --output evidence/firmware-audit/20260920-clv-abl1-runtime-heap-followup/apcb-detail.json
```

Observed exit `0`; literal stdout in `evidence/firmware-audit/20260920-clv-abl1-runtime-heap-followup/apcb-parser.stdout` is `{"output": "/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-runtime-heap-followup/apcb-detail.json", "images": 1, "failed": false}`; stderr empty. Parser reports exact input SHA-256 `ea578104...ca4cb8`, APCB offset `0xAB1000`, size `2972`, checksum matched, CBSG group `0x1707` present with 2 subgroups.

LLVM 22.1.8 narrow Thumb disassembly commands, each exit `0`, were executed on existing `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-downstream/ABL1-exact.o` and retained under this unique evidence directory:

```text
llvm-objdump -D --triple=thumbv7 --start-address=0x4b1a --stop-address=0x4c26 .../ABL1-exact.o
llvm-objdump -D --triple=thumbv7 --start-address=0x4b0e --stop-address=0x4c26 .../ABL1-exact.o
llvm-objdump -D --triple=thumbv7 --start-address=0x63f8 --stop-address=0x6428 .../ABL1-exact.o
llvm-objdump -D --triple=thumbv7 --start-address=0x6f76 --stop-address=0x6f7c .../ABL1-exact.o
llvm-objdump -D --triple=thumbv7 --start-address=0x4c5c --stop-address=0x4c70 .../ABL1-exact.o
llvm-objdump -D --triple=thumbv7 --start-address=0x6374 --stop-address=0x63b8 .../ABL1-exact.o
```

The first focused range was expanded from `0x4B1A` to `0x4B0E` to include seed-register anchors. Capstone import was tested and returned `ModuleNotFoundError`; no package was installed. Three repeated raw-byte transcription errors triggered the G6 method change recorded above. Subsequent disassembler/parser corrections and their exit-1 errors are also retained in this log.

Final command:

```text
python3 -B evidence/firmware-audit/20260920-clv-abl1-runtime-heap-followup/abl1_runtime_heap_followup_verify.py
```

Observed final exit `0`, stderr empty. Literal stdout begins `{"status": "PASS", "checks": 90, ...}` and is preserved at `.../verifier.stdout`; the parsed result is `.../abl1-runtime-heap-followup-result.json`. The verifier parses only the selected Thumb windows and reconciles their disassembled bytes to the exact decompressed ABL1 bytes.

New output hashes at this readback:

```text
516fd22c80c08375220433c24c821a337cb99f2b26df6884188f9c3d0af2ff7c  evidence/firmware-audit/20260920-clv-abl1-runtime-heap-followup/abl1_runtime_heap_followup_verify.py
47a01ad2a4b07ac0e7f607b1e35a42ce4f2f8bb524d050e4b5f83072493db88c  evidence/firmware-audit/20260920-clv-abl1-runtime-heap-followup/abl1-runtime-heap-followup-result.json
503e4f525f4372903b23ea9320c77f7b0b39250f310d80a1b7565eb98b39f394  evidence/firmware-audit/20260920-clv-abl1-runtime-heap-followup/apcb-detail.json
4c52b4e09be0a584437cc042819870bae8eb12c7a0f7d9bb0b9285c9a4aadec6  evidence/firmware-audit/20260920-clv-abl1-runtime-heap-followup/verifier.stdout
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  evidence/firmware-audit/20260920-clv-abl1-runtime-heap-followup/verifier.stderr
d5b6b92bbad544bc0845edb7337c55ccbf170a270f1fffe3bc032d5b7264ad15  docs/research/20260920-clv-abl1-runtime-heap-followup.md
```

Readback: verifier and parser exit files both contain `0`; fresh parser JSON and machine result reopen/parse; verifier reports 90 passing checks. Finding remains **PARTIAL / STATIC**: ABL1 initializes the runtime HEAP header, consumes key `0xA04E` body data into an indirect output buffer and keyed pointer table, but node population/source and output destination identity remain unresolved. No firmware, board, setup value, settings, plan, shared memory, install, MCP, or source input changed. Rollback: delete only this unique evidence directory, report, and action log.

## Final text/readback reconciliation

Timestamp: 2026-09-20T11:00:00+05:00 (+05:00)
A final wording pass narrowed “caller output” to “frame-indirect destination” because the exact destination identity is not established. The verifier was rerun against that final ledger:

```text
python3 -B evidence/firmware-audit/20260920-clv-abl1-runtime-heap-followup/abl1_runtime_heap_followup_verify.py
```

Observed exit `0`, `PASS`, `90/90`, stderr empty. Reopened the JSON result, verifier stdout/stderr/exit, parser JSON/stdout/stderr/exit, report and this log. The remaining destination-identity and node-population boundaries are stated as unresolved; no external/MHz/1:1 inference was added.

Final artifact hashes after the wording reconciliation:

```text
a2d67d7f015f9992dfcdb8ec2db87c4663a36611f25756234af92b3adebf4780  evidence/firmware-audit/20260920-clv-abl1-runtime-heap-followup/abl1_runtime_heap_followup_verify.py
9c94bf1d3b3a4880b32a36d2e6c95b25e56a7e0292aa495c0ff1400c0492a75f  evidence/firmware-audit/20260920-clv-abl1-runtime-heap-followup/abl1-runtime-heap-followup-result.json
b259abe10ee8ab234b5a81f7562fb4a0099ed5078c2c42ac4034faea6d699d29  evidence/firmware-audit/20260920-clv-abl1-runtime-heap-followup/verifier.stdout
0d2046ec0bb5ac829a68e2e803d142ff0d93ca6f6b0c0df8b4244968d2dd6475  docs/research/20260920-clv-abl1-runtime-heap-followup.md
```
