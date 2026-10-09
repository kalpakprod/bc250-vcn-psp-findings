# ABL `0x7378` table-xref independent review — intent

- Timestamp: 2026-09-21T21:49:18+05:00 (Asia/Almaty).
- Actor: bounded offline reviewer `/root/clock_claims_adjudication`.
- Active object: latest local entry `0x7378` table-xref result linked by `docs/action-logs/20260921-abl660-entry7378-table-xref.md`.
- Last confirmed result: newest machine status printed by this dispatcher; no current output is modified.
- Next executable action: run the newest table-xref-specific verifier from its disposable evidence copy; if no verifier exists, check only the exact conditional address arithmetic and Thumb pointer windows named in checkpoint metadata.
- Inputs: evidence/firmware-audit/20260921-abl660-object-identity, evidence/firmware-audit/20260921-abl660-object-identity, evidence/firmware-audit/20260920-clv-abl1-downstream.
- Acceptance event: observed exit and literal stdout/stderr of the bounded child command in a unique `/tmp` directory.
- Scope exclusion: no HOB/heap/float tests, no old full verifiers, no live memory-clock task restart, no global alias scan.
- Safeguards: no hardware, network, ROM, firmware, register, NVRAM, candidate, or author-output modification.
- Rollback: remove only this review report/log and its unique `/tmp` run directory.

## Direct fallback execution

- Timestamp: 2026-09-21T21:49:20+05:00 (Asia/Almaty).
- No matching finalized 0x7378 verifier was in the checkpoint; ran only exact code/raw windows in `/tmp/bc250-7378-xref-review-57s_p83a`.
- `/usr/bin/llvm-objdump -D --triple=thumbv7a-none-eabi --start-address=0x7370 --stop-address=0x7390 /tmp/bc250-7378-xref-review-57s_p83a/ABL1-clv-full-thumb.elf.o` exit `0`, stdout SHA-256 `6db178978ae39346e10fcaa490841349572a5723e97abbdb94080477a7c2d459`, stderr bytes `0`.
- `od -An -v -tx1 -j 0x7370 -N 0x20 /tmp/bc250-7378-xref-review-57s_p83a/ABL1-clv-decompressed.bin` exit `0`, stdout SHA-256 `127a8af8fcd99f88afa0c14b49a07ffca9d0d9d5945dbee61ee4e9ebcfec48d3`, stderr bytes `0`.
- Final output report: `docs/research/2026-09-21-abl-7378-table-xref-independent-review.md`; no author output changed.

## Conditional pointer-decoding execution intent

- Timestamp: 2026-09-21T21:52:16+05:00 (Asia/Almaty).
- Latest checkpoint has no completed table-reader output; verify only the recorded conditional pointer `0x5E479` under candidate base `0x57100` and Thumb entry `0x7378`, using the exact object/payload copies.
- Inputs SHA-256: object `adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6`, payload `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`. No table census, global scan, HOB, heap, float, or live memory task.

## Observed conditional pointer verification

- Conditional arithmetic: `0x5e479` has Thumb bit `1`; after clearing bit 0, `0x5e478 - 0x57100 = 0x7378`. This is conditional on base `0x57100`, not proof of runtime base or table invocation.
- Disposable dir: `/tmp/bc250-7378-conditional-pointer-b51137g5`.
- `/usr/bin/llvm-objdump -D --triple=thumbv7a-none-eabi --start-address=0x7378 --stop-address=0x73a0 /tmp/bc250-7378-conditional-pointer-b51137g5/ABL1-clv-full-thumb.elf.o` exit `0`, stdout SHA-256 `213bc76d631f6642dbb2edb37ab5a8534603c71c9f51317771a5381b4f80c741`, stderr bytes `0`.
- `od -An -v -tx1 -j 0x7378 -N 0x28 /tmp/bc250-7378-conditional-pointer-b51137g5/ABL1-clv-decompressed.bin` exit `0`, stdout SHA-256 `fa768cdfc5078ccd45e0517a2fcebe11282d542722a723121c0913df519c2592`, stderr bytes `0`.

## Report closeout

- Report: `docs/research/2026-09-21-abl-7378-table-xref-independent-review.md`.
- The conditional mapping and Thumb output are local static evidence only; the artifact does not establish a `0x7378` caller/object identity.
- No author output or source artifact was modified.

## Related current output adjudication and closeout

- Reopened `docs/research/2026-09-21-abl7378-indirect-entry.md`, SHA-256 `c15b43356e66dcdad621e0cf2f89a61af43dc00d84b32d8a8b15fc1bb79952c8`, and result `evidence/firmware-audit/20260921-abl7378-indirect-entry/run-20260921T200924+0500/af58-body-result.json`, SHA-256 `db6cb72a620818c23aae2abab2e5949dbec12850407971ba958c924a0450dce7`.
- This latest completed table output is a distinct bounded `0x6E1C8`/stride-`0x24` table with callbacks `0x62059` -> `0xAF58` and zero; the exact AF58 body does not call `0x7378` or `0xAF90`. It supplies no `0x7378` caller/object identity.
- Accepted conditional mapping check: candidate `0x5E479` has Thumb bit set; if base `0x57100` is assumed, aligned address `0x5E478 - 0x57100 = 0x7378`, and exact Thumb disassembly at `0x7378` matches raw payload bytes. This verifies arithmetic and the known entry decode only, not table membership, active invocation, loader base, or runtime identity.
- Final readback: report `docs/research/2026-09-21-abl-7378-table-xref-independent-review.md` SHA-256 `2adca7e1adc56d024f06b12930f7ce6f408f5dd6abe993e3df03f3b9ed82c5c5`; source object, raw payload, report, and linked result were reopened and hashes matched the recorded values.
- No author output was modified; no hardware, network, ROM, NVRAM, register, HOB, heap, or live `memory_clock_units` action was performed.

## Corrective method after control-script error

The fresh Thumb `llvm-objdump` child exited `0` and emitted the exact loop: `RSB r0,r4,r4,LSL #3`; `ADD.W r0,r6,r0,LSL #2`; `LDR r1,[r0,#8]`; `CBZ r1`; `BLX r1`; then index increment/count compare. The surrounding Python controller then raised `NameError: name 're' is not defined` before the raw arithmetic assertions; the wrapper returned `1`. No source or payload changed. The changed command below drops that unnecessary regex dependency and performs only the named raw table arithmetic/conditional Thumb decoding, not an old verifier replay.

## Final G7 closeout

- The fresh bounded LLVM listing event at `0x1B48..0x1B60` exited `0`, stderr empty, and decoded the actual instructions (`RSB`, `ADD.W`, `LDR [R0,#8]`, `CBZ`, `BLX`, count increment/compare). It was generated from exact `ABL1-exact.o` copy `/tmp/bc250-7378-reader-correction-review-xzd5ljcu/`.
- The independently counted raw check exited `0`, stderr empty, `13/13 PASS`; literal stdout is `/tmp/bc250-7378-table-raw-check-dt94zvvh/result.stdout` SHA-256 `487618b2850cf732e7463ea6834b8c13910ed299f9d0a478becd09fcb24d9562`; `result.stderr` is empty; `result.exit` is literal `0`.
- Superseded author report snapshot `c15b...` is no longer current. Current author report SHA-256 is `d9b70067eb560bee535087f86167c3f13cdcb631655cc91ac0913afc2b0608cd`; current bounded machine result SHA-256 remains `db6cb72a620818c23aae2abab2e5949dbec12850407971ba958c924a0450dce7`. The G7 stride-correction output is from the author and was not edited here.
- Final review report SHA-256: `397f552a1305f8c9d3fd7409044146cfe44f5a738d0d571cf546736e3a11fbee`.
- Verdict: current `0x1B24` table reader consumes row `+8`, not candidate row0 `+4` pointer `0x5E479`; under conditional base `0x57100`, that unused word decodes to Thumb entry `0x7378`. This does not establish that any table calls the `0x7378` initializer or supplies the same object identity; no global absence claim follows.

## Latest shared checkpoint re-read

- Current author report reopened at `docs/research/2026-09-21-abl7378-indirect-entry.md`, SHA-256 `af4dd43d5b886371a5e1d39447c4204f40830d9dd64306760f9e215d4a2954be`; its latest G7 change only corrects the manifest count to 15/15.
- Current table-xref status log reopened at `docs/action-logs/20260921-abl660-entry7378-table-xref.md`, SHA-256 `ba561f2e9636b3e3e5e634923af630c82a60d4ede02b9bf361c796d381fda5df`; the newest 22:05 literal-slot xref step is intent only at this readback, not a completed result.
- No further table/caller range was scanned; the accepted result remains the completed 0x1B24 read of row+8 and conditional-only decode of row0+4 to 0x7378. No current artifact establishes the caller/object identity.

## Final readback

- Final readback command re-opened and SHA-256-checked the owned report/log, latest ABL7378 report/action log, unchanged machine results, exact object/payload, and disposable command exit/result files. Observed `FINAL_READBACK 13/13 PASS`, process exit `0`.
- Final report SHA-256: `e8c2627f78352601a8fbf17595cda73846cff3c9cab478e59e4005df5ae4040b`.
- Current conclusion: the completed `0x1B24` reader consumes row+8, while `0x5E479` at row0+4 conditionally maps to Thumb RVA `0x7378` but is not consumed; no current artifact establishes the initializer caller/object identity. No global-absence or hardware claim.
