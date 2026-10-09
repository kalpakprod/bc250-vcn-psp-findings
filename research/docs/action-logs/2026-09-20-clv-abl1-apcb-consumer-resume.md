# CLV ABL1 UCLK/FCLK lookup consumer continuation — intent

Timestamp: 2026-09-20T08:50:00+05:00 (+05:00)
Actor: luna-xhigh bounded executor
Target: exact clv ABL1 payload and already completed 0x1FB4 reader result; continue only into exact helper 0x4800 and its first consumer.

Bounded question: recover the implementation called by 0x4800 (0x49CC in range) and trace the minimum argument/value path far enough to classify the returned UCLK/FCLK value as enum/voltage/frequency/pointer or stop at the first raw provider boundary. No generic searches, no 0x95FC/0x751C deliverable reuse.

Pinned inputs:

- ROM SHA-256 ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8.
- Exact decompressed ABL1 SHA-256 af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a.
- Previous branch result SHA-256 d6d053b5e4a74a5b4fe0526e4d4659d22a500601074baad751977ab21e2ecdfa.
- Previous reader result SHA-256 537f987266057865bd7f278939304f2f40dcc5db4e57c6048ca0905ce2dac128.
- Exact disassembly SHA-256 b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65.

Fresh preliminary direct observation (read-only): 0x4800 range-checks caller key against 0x160 then routes valid keys to 0x49CC with internal selector 0x0F; this is the current branch to qualify, not a final semantic claim.

Next executable action: run the unique verifier evidence/firmware-audit/20260920-clv-abl1-apcb-consumer-resume/abl1_apcb_consumer_verify.py over the pinned payload/disassembly and read back its machine result.

Expected effect: new evidence/report/action-log artifacts only. No firmware, hardware, settings, shared plan/memory, installation, global config, MCP/Cutter, candidates, source, commits, or subagents.

Rollback: remove only this uniquely named evidence directory, report, and action log; preserve prior completed artifacts and pinned inputs.

## Correction after verifier execution

Timestamp: 2026-09-20T08:55:00+05:00 (+05:00)
Observed execution error: provider prologue check selected six bytes from an eight-byte slice (`0x49CC..0x49D3`). Exact bytes are `2d e9 ff 4f fe 48 9b b0`; this is a verifier slice-width mismatch, not an input mismatch.

Correction: align expected prologue bytes to the exact selected span; retain the failure output. No pinned input changed.

## Correction after second verifier execution

Timestamp: 2026-09-20T08:56:00+05:00 (+05:00)
Observed execution error: provider selector bytes were transcribed in instruction display order rather than raw little-endian bytes. The exact raw sequence begins at `0x4A18` with `1b 9a 41 f6 fe 70 ...`.

Correction: update only the raw expected byte order; no input changed.

## Correction after third verifier execution

Timestamp: 2026-09-20T08:57:00+05:00 (+05:00)
Observed execution error: one final halfword in the selector dispatch slice was reversed; actual bytes are `10 2a 72 d2`.

Correction: update that exact expected byte sequence only; retain the error output.

## Correction after fourth verifier execution

Timestamp: 2026-09-20T08:58:00+05:00 (+05:00)
Observed execution error: TBB instruction bytes were in disassembly display order rather than raw order; exact bytes at `0x4A26` are `df e8 02 f0`.

Correction: update the raw TBB signature and retain the failed check output.

## Correction after fifth verifier execution

Timestamp: 2026-09-20T08:59:00+05:00 (+05:00)
Observed execution error: selector-case signature had display-order bytes and an incorrect slice offset; actual 0x0f case starts `0f 22 40 f2 62 1a ...` at payload `0x4B0E`.

Correction: update exact raw signature. No pinned inputs changed.

## Correction after sixth verifier execution

Timestamp: 2026-09-20T09:00:00+05:00 (+05:00)
Observed execution error: exact helper-6374 call window was specified in display byte order and one byte off. Raw bytes at `0x4B34` are `09 a8 29 99 09 96 01 f0 1b fc`.

Correction: update the byte literal only.

## Correction after seventh verifier execution

Timestamp: 2026-09-20T09:01:00+05:00 (+05:00)
Observed execution error: long output-descriptor signature used instruction display order and was shorter than selected exact span. The verifier now records the actual raw byte window directly from `0x4B40..0x4B5D`.

Correction: replace only that expected raw window.

## Correction after eighth verifier execution

Timestamp: 2026-09-20T09:02:00+05:00 (+05:00)
Observed execution error: provider output-count slice at `0x4B62` used display-order and wrong length. Exact bytes are `9d 48 01 f0 b0 fc 08 9e 0c 96 08 36 00 27` in the wider boundary.

Correction: use the exact raw window and preserve failure.

## Correction after ninth verifier execution

Timestamp: 2026-09-20T09:03:00+05:00 (+05:00)
Observed execution error: provider iteration slice at `0x4B6C` likewise had raw instruction byte order reversed. Exact bytes start `08 36 00 27 03 a8 00 90 ...`.

Correction: use the observed raw bytes and retain the error output.

## Observed result

Timestamp: 2026-09-20T09:05:00+05:00 (+05:00)
Actor: luna-xhigh bounded executor

Command:

```text
python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-apcb-consumer-resume/abl1_apcb_consumer_verify.py
```

Observed exit status: `0`, stderr empty, `PASS`, `36/36` checks. Literal stdout is preserved at:
`/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-apcb-consumer-resume/verifier.stdout`.

Final artifact hashes:

```text
0c7dfca63d7227f1d8c1b29ddde756786f895e0b05f68e6459ad98c4492a8ced  evidence/firmware-audit/20260920-clv-abl1-apcb-consumer-resume/abl1_apcb_consumer_verify.py
3950e5136254db2aa9c96c91caba4d48da4a11c369b38a36703c9f54cef45ee9  evidence/firmware-audit/20260920-clv-abl1-apcb-consumer-resume/abl1-apcb-consumer-result.json
5bd2425cd98c86f5040ba059c8a259813eab9192be5e225e4e571b278c90eb0c  evidence/firmware-audit/20260920-clv-abl1-apcb-consumer-resume/verifier.stdout
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  evidence/firmware-audit/20260920-clv-abl1-apcb-consumer-resume/verifier.stderr
f137d5261a5b65aaf61aa9ae85271d10fc666686c8f2091751aa8badf21d8b7d  docs/research/20260920-clv-abl1-apcb-consumer-resume.md
```

Finding: `0x4800` dispatches accepted token IDs to `0x49CC` using selector `0x0F`; bounded `0x49CC` body reaches `0x6374`/`0x6238` table/provider helpers and eventually copies raw typed bytes to the `0x1FB4` caller. Semantic type/value domain remains unresolved. No divider/PLL, clock equality, or hardware result is claimed.

Readback: all new paths were reopened; result JSON parses; stdout/stderr hashes match. No firmware, hardware, settings, shared plan/memory, installation, configuration, candidates or source input changed. Rollback is deletion of this uniquely named report, action log and evidence directory.
