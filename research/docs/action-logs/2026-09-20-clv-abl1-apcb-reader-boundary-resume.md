# CLV ABL1 UCLK/FCLK common-reader boundary — intent

Timestamp: 2026-09-20T08:30:00+05:00 (+05:00)
Actor: luna-xhigh bounded executor
Target: exact BIOS 5.00 clv ABL1 decompressed payload and the completed exact-branch result from `20260920-clv-abl1-fclk-uclk-branch-xhigh`.

Bounded continuation: follow the first unresolved edge only, payload `0x1FB4`, using exact raw Thumb bytes. Prove the descriptor-pair lookup, typed output stores, and the first downstream helper boundary. Do not repeat the completed UclkDiv1/Fclk branch match, do not treat the generic reader as a divider/PLL actuator, and do not perform hardware/runtime action.

Pinned inputs:

- ROM SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Exact ABL1 decompressed SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Existing completed branch result SHA-256 `d6d053b5e4a74a5b4fe0526e4d4659d22a500601074baad751977ab21e2ecdfa`.
- Exact ABL1 Thumb disassembly SHA-256 `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`.

Next executable action: run the uniquely owned verifier `evidence/firmware-audit/20260920-clv-abl1-apcb-reader-boundary-resume/abl1_apcb_reader_boundary_verify.py`.

Expected effect: new evidence/report/action-log artifacts only. No firmware, hardware, settings, shared plan, memory, install, global configuration, MCP/Cutter, candidate, or source input changes.

Rollback: remove only this uniquely named evidence directory, report, and action log; preserve the completed branch artifacts.

## Correction after verifier execution

Timestamp: 2026-09-20T08:35:00+05:00 (+05:00)
Observed execution error: verifier exited `1` at the first reader-byte check because the actual 0x1FC8 conditional is four bytes (`18 bb 35 48`), while the expected slice was two bytes. This is a verifier slice-width error, not an artifact mismatch.

Correction: compare only the instruction-width bytes for the conditional and retain the failure output. No input artifact changed.

## Correction after second verifier execution

Timestamp: 2026-09-20T08:36:00+05:00 (+05:00)
Observed execution error: descriptor verification incorrectly treated stack descriptor bytes as contiguous input data at branch starts. The exact code constructs the initial `0x20`/`0x21` pair at `0x2CF0..0x2CF8`; later M1..M3 branches overwrite only the key halfword (`0x22..0x24`) while retaining the zero terminator. This is another verifier anchoring error, not a binary mismatch.

Correction: check the exact construction instructions and branch-local key stores rather than a nonexistent contiguous raw descriptor blob. No pinned input changed.

## Correction after third verifier execution

Timestamp: 2026-09-20T08:37:00+05:00 (+05:00)
Observed execution error: M0 starts with its initial `strh [sp+0x44]`, so its key immediate is at `0x2CF4`, while M1..M3 start at their key immediates. The verifier used one offset rule for both forms.

Correction: use the M0-specific key offset and retain the observed error. No input changed.

## Correction after fourth verifier execution

Timestamp: 2026-09-20T08:38:00+05:00 (+05:00)
Observed execution error: type-1 output branch expected the wrong raw conditional halfword (`39 d0` instead of exact `1b d0`). The actual byte store sequence matched through `strb r0,[r6]`.

Correction: replace only the expected raw branch bytes with the observed exact bytes. No input changed.

## Correction after fifth verifier execution

Timestamp: 2026-09-20T08:39:00+05:00 (+05:00)
Observed execution error: the corrected type-1 expected byte sequence retained one duplicate `1b` before the `strb` instruction. Exact payload has `...1b d0 30 70`.

Correction: remove only the duplicate expected byte. No input changed.

## Correction after sixth verifier execution

Timestamp: 2026-09-20T08:40:00+05:00 (+05:00)
Observed execution error: type-2 output branch had the same raw conditional-width transcription mistake. Exact payload is `...39 43 14 d0 30 80`.

Correction: replace only the type-2 expected bytes. No input changed.

## Correction after seventh verifier execution

Timestamp: 2026-09-20T08:41:00+05:00 (+05:00)
Observed execution error: type-4 output check expected twelve bytes while its selected slice contains ten bytes. The exact word-store sequence through `str r0,[r6]` is ten bytes.

Correction: align expected length to the selected exact instruction span. No input changed.

## Correction after eighth verifier execution

Timestamp: 2026-09-20T08:42:00+05:00 (+05:00)
Observed execution error: source lead text for the exact ABL1 string omitted the word `parameter`; disassembly data contains `APCB parameter disabled: Token...`. The exact report had relied on disassembly phrase matching.

Correction: use the literal exact retained text from exact ABL1 bytes (`APCB parameter disabled: Token`) rather than the incomplete paraphrase. No input changed.

## Correction after ninth verifier execution

Timestamp: 2026-09-20T08:43:00+05:00 (+05:00)
Observed execution error: exact string checks were applied to the disassembly listing, which renders string bytes as Thumb halfwords rather than contiguous text. The exact ABL1 payload contains the strings contiguously; the disassembly text does not.

Correction: move those string checks to the exact payload bytes and retain the observed error. No input changed.

## Observed result

Timestamp: 2026-09-20T08:45:00+05:00 (+05:00)
Actor: luna-xhigh bounded executor

Command:

```text
python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-apcb-reader-boundary-resume/abl1_apcb_reader_boundary_verify.py
```

Observed exit status: `0`; stderr empty; verifier status `PASS`; checks `42`.

Literal stdout and hashes are preserved in:

- `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-apcb-reader-boundary-resume/verifier.stdout`
- `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-apcb-reader-boundary-resume/verifier.stderr`

Final artifact hashes:

```text
be29fe6827d6ad700b0ab46dc54935a118eba72e5384b7c562b23df8f762136e  evidence/firmware-audit/20260920-clv-abl1-apcb-reader-boundary-resume/abl1_apcb_reader_boundary_verify.py
537f987266057865bd7f278939304f2f40dcc5db4e57c6048ca0905ce2dac128  evidence/firmware-audit/20260920-clv-abl1-apcb-reader-boundary-resume/abl1-apcb-reader-boundary-result.json
3204d336cfc1b3de142e43ae3af03a1010aaa6ab8607b35eb16eca663b7f3e33  evidence/firmware-audit/20260920-clv-abl1-apcb-reader-boundary-resume/verifier.stdout
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  evidence/firmware-audit/20260920-clv-abl1-apcb-reader-boundary-resume/verifier.stderr
a4bf8e811d0e7c88f367bbe14f95d7a3b8a5afc2ec45592f75442569bb1a626a  docs/research/20260920-clv-abl1-apcb-reader-boundary-resume.md
```

Observed finding: `0x1FB4` is a generic descriptor-driven typed parameter/APCB lookup; the first unresolved edge is helper `0x4800`. No divider/PLL, MCLK=UCLK=FCLK, physical-clock, runtime, or hardware claim follows.

Readback: reopened the verifier, machine result, stdout/stderr, report, and action log. All are readable and hashes above match the final evidence ledger. Rollback is deletion of only this unique evidence directory/report/action log.
