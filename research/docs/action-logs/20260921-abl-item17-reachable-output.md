# CLV ABL1 item-0x17 reachable output and post-callback consumer trace — intent

Timestamp: 2026-09-21T17:55:00+05:00 (Asia/Almaty)
Actor: `/root/memory_clock_units`; offline static trace only.

## Bound target and state

- TARGET: exact CLV ABL1 Thumb-2 ELF wrapper `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-abl-item17-consumer/ABL1-clv-full-thumb.elf.o`, SHA-256 `adf12203668ce58ee67ae7cd739e373ac8fcf32901483703a6b67f5b000df2f6`.
- Baseline ROM: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Prior result: `evidence/firmware-audit/20260921-abl-item17-consumer/item17-consumer-result.json`, status PASS, 136 checks. Preserve base `0x57100` as conditional. The exact local helper `0x6D10` returns `1`; the selected handler path is `0x95FC -> 0x9646 -> 0x9744 -> 0x984E`.
- GOAL: trace the value written at context +`0x2BC` along this exact local path, then follow the caller after item `0x17` returns to its next local reader/transformer and the nearest evidenced memory-training/apply boundary. Do not repeat callback table mapping, rerun the 136-check verifier, follow alternate SVC paths, or infer a clock unit or hardware effect.

## Existing route and procedure

Reuse the exact local Thumb ELF wrapper and `/usr/bin/llvm-objdump` LLVM 22.1.8. Capture only these fresh bounded windows: callback caller `0x7E30..0x7EA0`; exact aggregate-producing path `0x984E..0x98B0`; aggregate lookup helper `0x751C..0x75A0`; follow-up helper `0x61A0..0x6260`; and caller continuation `0x7E6E..0x7F40`. Preserve separate stdout, stderr, and exit ledgers for each command. Extend only to a concrete direct caller/consumer if these windows establish the next edge.

## Safeguards and owned paths

No image edit, firmware/NVRAM/register write, hardware action, network, install, or board contact. Existing ROM, ABL1 payload, wrapper, prior result and other workers' files remain immutable. New outputs belong only to `evidence/firmware-audit/20260921-abl-item17-reachable-output/`, `docs/research/2026-09-21-abl-item17-reachable-output.md`, and this log. Rollback: delete the report and unique evidence directory; preserve this append-only log and all pre-existing evidence.

## Direct consumer extension — aggregate handler target 0x5E68 (intent before fresh listing)

Timestamp: 2026-09-21T18:03:00+05:00 (Asia/Almaty)

The first fresh caller window directly established `0x7E74 -> 0x5E68` with `r2=r6` (the aggregate loaded from context `+0x2BC`). Before further evidence writes, extend the same unique evidence directory with the exact bounded `0x5E68..0x602C` Thumb slice. This determines whether the aggregate is consumed locally as a value, written into a training/apply record, or only marshalled to another opaque service. Preserve all SVC semantics as unknown; do not repeat the item-0x17 mapping or run hardware. Expected outputs are one listing with separate exit/stderr ledgers and a byte-level sample of any directly addressed local aggregate-input table if the fresh instructions need it. Rollback unchanged.

## Direct downstream-field extension (intent before fresh listing)

Timestamp: 2026-09-21T18:10:10+05:00 (Asia/Almaty)

The fresh `0x5E68` listing proves the exact item-0x17 caller passes the aggregate as `r2`; the bounded handler writes a derived halfword at its context `+0x78`. A prior independent local report observes a load from context `+0x78` at `0x107E4`, but did not bind it to this item-0x17 route. Freshly capture only the continuous outer caller continuation `0x7E3E..0x8450` and the local downstream handler `0x10200..0x10850`. This tests conditional reachability from the same caller and whether the next field consumer performs a direct memory/training/clock write or merely selects a further opaque call. Do not assume a physical unit or hardware effect; no SVC handler is analyzed here. No image or firmware write. Rollback unchanged.

## G7 correction — 0x6D10 gate is conditional after 0x6B78 fill (before report write)

Timestamp: 2026-09-21T18:29:47+05:00 (Asia/Almaty)

The independent report docs/research/2026-09-21-item17-reachability-review.md and machine result evidence/firmware-audit/20260921-item17-reachability-review/item17-reachability-result.json were reopened. Reviewer result is PASS, 128/128, SHA-256 5d5599f220425829401bc86fcf1ff0d20eb96907e4d1fa96b8dd010f428cca26. It directly observes the later call at 0x963A to fill helper 0x6B78 with destination R4+0x278, fill byte 0xFF, length 0x40. The preceding 0x6C20 output has [SP+0x164] = 1; however, no observed address relation proves the dynamic R4+0x278..+0x2B7 range is disjoint from SP+0x160..+0x178. Therefore branch 0x9646 -> 0x9744 -> 0x984E is conditional on non-alias/no clobber, not guaranteed by 0x6D10=1 alone. DD4 reachability remains conditional/unresolved. SVC #6 remains rejected only on the known direct item-17 edges; no global handler/absence claim.

This corrects the earlier wording in this log that called the 0x95FC branch path exact. Before continuing, append a qualification to the owned item-17 reports and keep the new +0x2BC -> +0x78 caller edge conditional on entering the 0x984E path. Do not modify the reviewer-owned files, the earlier verifier JSON, or other workers' artifacts.

## Bounded pointer-provenance continuation intent

Next fresh check is restricted to the already captured outer caller interval around 0x7F4C, 0x7FC2, 0x8418..0x843E, plus direct callee register-preservation windows needed to state which R4 value reaches the conditional 0x8428 call. Determine the exact call argument expression and the 0x8424 [R4+0x0C] -> [channel+0x28] gate. Do not repeat table mapping, rerun broad verifier/corpus scans, assign frequency names, or continue past the nearest unresolved indirect callback at 0x10958.

## G7 memory incident intent

Timestamp: 2026-09-21T18:35:00+05:00 (Asia/Almaty)

Persist the newly independently measured stack/table alias qualification as a new file under memory/incidents/ rather than editing the shared memory/firmware-audit.md while its single-writer ownership is not established. The note will cite the reviewer report/result and exact measurement; it will not alter any other agent's memory artifact. Expected effect: durable correction of the earlier unconditional `0x6D10==1` branch assumption. Rollback: remove only the new incident note; preserve action logs and evidence.

## Observed bounded result and report readback

Timestamp: 2026-09-21T18:54:33+05:00 (Asia/Almaty)

- Fresh output edge: on the conditional path through 0x984E, 0x989A writes a runtime table U16 to context+0x2BC; after the service returns, 0x7E40 reads root+0x2BC and 0x7E74 passes the value in r2 to 0x5E68, which writes a derived halfword to [context+0x78] at 0x5FBA. Immediately afterward the caller reads [channel+0x20] at 0x7E7E and compares raw 0x6D6.
- G7: the path through 0x984E is conditional because 0x6B78 fills 0x40 bytes from dynamic R4+0x278 with 0xFF after 0x6D10 writes 1 at SP+0x164; non-alias with SP+0x160..0x178 is unproven. Independent review and its 128/128 result were reused; reviewer-owned files were not modified. A new dated note records the correction at memory/incidents/2026-09-21-item17-fill-alias-correction.md.
- Pointer task: caller listing shows R4 += 0x2C0 at 0x7F4C and R4 -= 0x2C0 at 0x7FC2. At 0x8420..0x8424 it loads [R4+0x0C] then [channel+0x28]; if nonzero, 0x8426 passes current R4 as R0 to 0x10200. Arithmetic cancels, but object identity with the 0x7E74 context is not proven through the intervening indirect callback at 0x83B0/0x10958; its active [object+0x660] target is unresolved. No frequency name, unit, or applied-effect claim is made.
- The local 0x10200 slice reaches 0x107E4, reads [R4+0x78], compares raw 0x3E8/0x4B0, chooses raw codes 0/0x260/0x264/0x464, then calls 0x10958 at 0x10820. That is a conditional local field-reader edge, not proof the field is the same object written at 0x5FBA or that a hardware apply occurs.
- All eight fresh LLVM Thumb windows in the unique directory exited 0 with empty stderr. The final SHA256SUMS.final passed every listed evidence file and the report. Machine result: reachable-output-result.json SHA-256 814215209b0a13a54b32786d5012f9ae41350d28f39ad862b21877697f178beb. Manifest SHA-256 1ed16615a5dbb683a383606a9c848d2fa44a9ba4d5260271d30cc1af77f8c64e. Report SHA-256 6c3c528cc2b8669d48a7a98067b3241c0adb9daf983b9dca539f80f06d597122. Memory incident SHA-256 4f4da997f27c2af88d32b9f392218f8b98e05d1438d1f4c944a455ee2ab6b66a.
- Scope stop: no hardware/firmware/NVRAM/register/network write. Preserve all pre-existing inputs and independent reviewer artifacts. Independent review of this new report was not requested or performed; no physical training/apply behavior is established.

## Final bounded result and readback

Timestamp: 2026-09-21T18:54:33+05:00 (Asia/Almaty)

- The exact local edge, when the conditional 0x984E gate is satisfied, is: table U16 -> context+0x2BC at 0x989A -> outer load at 0x7E40 -> R2 at 0x7E74 -> 0x5E68 -> derived halfword store [context+0x78] at 0x5FBA. Immediately after 0x5E68 returns, the same caller reads [channel+0x20] at 0x7E7E and compares to raw 0x6D6. This is local static dataflow only.
- The independent 128/128 review establishes that 0x6D10=1 is not enough to guarantee the 0x984E branch: 0x6B78 subsequently fills dynamic R4+0x278..+0x2B7 with 0xFF; relation to SP+0x160..0x178 is unresolved. Corrections were appended to our two earlier reports and the new G7 incident note.
- New pointer-provenance result: 0x7F4C adds 0x2C0 to R4, 0x7FC2 subtracts 0x2C0, so the raw arithmetic cancels. At 0x8420..0x8424 the current R4+0x0C channel pointer is tested at +0x28; if nonzero, current R4 is passed to 0x10200. Same-object identity with the 0x7E74 context is not proven across the intervening 0x83B0 -> 0x10958 indirect callback through current object+0x660; its active target/value is unresolved.
- Bounded 0x10200 code loads [R4+0x78] at 0x107E4, compares raw 0x3E8/0x4B0, selects raw code 0/0x260/0x264/0x464, and calls 0x10958 at 0x10820. The field identity and callback effect remain unresolved; no frequency names, units, hardware or training effect are claimed.
- All eight fresh command ledgers in the unique evidence directory are exit 0 with empty stderr; the final manifest passes every entry including the report. Machine result SHA-256 814215209b0a13a54b32786d5012f9ae41350d28f39ad862b21877697f178beb; manifest SHA-256 1ed16615a5dbb683a383606a9c848d2fa44a9ba4d5260271d30cc1af77f8c64e; report SHA-256 6c3c528cc2b8669d48a7a98067b3241c0adb9daf983b9dca539f80f06d597122; fill-alias incident note SHA-256 4f4da997f27c2af88d32b9f392218f8b98e05d1438d1f4c944a455ee2ab6b66a.
- No source ROM, firmware, NVRAM, register, board, network, candidate, install, or hardware write. Rollback remains deletion of only this new report and unique evidence directory; keep append-only logs and the G7 incident correction.
