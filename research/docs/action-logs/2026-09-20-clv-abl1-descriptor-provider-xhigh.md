# CLV ABL1 descriptor/provider edge — intent

Timestamp: 2026-09-20T09:20:00+05:00 (+05:00)
Actor: luna-xhigh independent bounded executor
Target: exact BIOS 5.00 clv ABL1 decompressed payload at reader `0x1FB4`, helper `0x4800`, and the common provider path at `0x49CC`; conditional base `0x57100` is a hypothesis only.

Bounded task: independently decode descriptor formats `0x20..0x24` and `0x015F/0x0160` around the common reader/helper using exact payload bytes. Identify one concrete provider/consumer edge or falsify a frequency interpretation. Do not repeat prior branch/token matrices, reduction/classifier results, or generic counter prototypes. Static bytes and reviewed LLVM Thumb listing are the only evidence; no runtime, hardware, firmware, settings, candidate, install, shared MCP/Cutter, memory, source, or project-plan changes.

Pinned inputs:

- ROM: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Exact ABL1: `evidence/firmware-audit/20260920-clv-abl-memory-review/ABL1-clv-decompressed.bin`, SHA-256 `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Exact reviewed LLVM Thumb listing: `evidence/firmware-audit/20260920-clv-abl1-downstream/abl1-full-thumb-llvm.txt`, SHA-256 `b5b10b95c1777b96ef03ac79f819ece4257c87c58a26e43cffeed3b9019e8b65`.
- Existing reader result: `evidence/firmware-audit/20260920-clv-abl1-apcb-reader-boundary-resume/abl1-apcb-reader-boundary-result.json`, SHA-256 `537f987266057865bd7f278939304f2f40dcc5db4e57c6048ca0905ce2dac128`.

Expected effect: new uniquely named evidence, report, and this action log only. No pinned input changes.

Next executable action: create the independent verifier under `evidence/firmware-audit/20260920-clv-abl1-descriptor-provider-xhigh/`, run it, and reopen all owned outputs.

Rollback: remove only the uniquely named evidence directory, report, and this action log; preserve all pinned inputs and prior reports.

## Observed execution and correction ledger

Timestamp: 2026-09-20T08:21:43+05:00 to 2026-09-20T08:31:34+05:00 (+05:00), actor: luna-xhigh independent bounded executor.

Initial direct verifier executions retained the following errors; all were assertion/serialization corrections in the new verifier, not input-byte mismatches:

1. Exit `1`: Uclk call-site assertion used the wrong instruction byte order at `0x2D0A`. Literal mismatch: got `11 a8 ff f7 52 f9`, expected `a8 11 f7 ff f9 52`. Corrected expected raw bytes.
2. Exit `1`: current-token-load assertion at `0x1FD8` used wrong Thumb byte order. Literal mismatch: got `35 f8 14 00`, expected `35 f8 00 14`. Corrected expected raw bytes.
3. Exit `1`: selector comparison at `0x4B26` had a wrong halfword byte order. Literal mismatch: got `1b 98 10 28`, expected `1b 98 28 10`. Corrected expected raw bytes.
4. Exit `1`: `0x1707` immediate check had halfwords reversed. Literal mismatch: got `41 f6 fe 70 41 f2 07 71`, expected `f6 41 70 fe f2 41 71 07`. Corrected expected raw bytes.
5. Exit `1`: case-0x0f descriptor check began at `0x4B18`, which includes `movs r5,#1`; exact pair starts at `0x4B1A`. Changed only verifier slice start/width.
6. Exit `1`: targeted-listing assertion expected a `0x` prefix before the displayed address label; LLVM prints `49cc:`. Corrected output string check.
7. Exit `1`: final JSON serialization rejected raw `bytes` in the evidence-check ledger. Added deterministic hex normalization; no binary input changed.

Final command:

```text
python3 -B /home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-descriptor-provider-xhigh/abl1_descriptor_provider_verify.py
```

Observed exit `0`; status `PASS`; `71/71` checks; stderr empty. Exact output and regenerated disassemblies are retained in the owned evidence directory. Result: descriptors are ordered token arrays, helper `0x4800` routes valid IDs through selector `0x0F` to provider `0x49CC`, and the numeric semantics of `0x0F` (group/priority/source index) remain unknown. The candidate `0x57100` base remains conditional static mapping only.

## Final hashes and readback

See `evidence/firmware-audit/20260920-clv-abl1-descriptor-provider-xhigh/SHA256SUMS.final`. Every owned path was reopened after the final verifier run; pinned ROM/ABL1/full-listing hashes still match the intent ledger. No source or non-owned project artifact changed.

## Timestamp correction

The initial intent header's `09:20:00+05:00` was a manual timestamp error and is not reliable chronology; the contemporaneous shell clock read `2026-09-20T08:21:43+05:00`, while final file metadata shows the action-log artifact was last written at `08:31:34+05:00`. The exact first-write time was not independently captured. Preserve this correction rather than treating `09:20` as measured time. No evidence input or analysis result changed.
