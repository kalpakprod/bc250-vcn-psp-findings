# CLV ABL1 downstream after function 0x95FC — intent

Timestamp: 2026-09-20T07:05:00+05:00 (+05:00)
Actor: sync_stage2_consumer executor
Target: exact decompressed ABL1 hash `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`; trace callers/use after function `0x95FC` returns, following selected speed/aggregate `+0x2BC` into the next memory initialization/configuration/divider routine.

Next executable action: run `evidence/firmware-audit/20260920-clv-abl1-downstream/abl1_downstream_verify.py`; reuse reviewed `docs/research/20260920-clv-abl-memory-review.md` and exact function-95FC evidence read-only.

Expected effect: own ABL1 downstream evidence/report/log only. No firmware, ROM, hardware, shared plan/memory, Ghidra/Cutter/MCP, candidate, installation, voltage or settings changes.

Rollback: remove only this unique evidence directory, report and action log.

## Correction before downstream trace

The exact decompressed ABL1 hash occurs in two byte-identical evidence copies (`20260920-clv-sync-stage2-abl-memory` and `20260920-clv-abl-memory-review`). The uniqueness assertion was too strict; both are the same full hash. The reviewed path under `20260920-clv-abl-memory-review` will be selected, and duplicate equality retained.

## Method pivot

Timestamp: 2026-09-20T07:08:00+05:00 (+05:00).

The exact ABL1 function listing ends at `0x984A`; no caller listing was retained in the reviewed snippet. Change method class to a fresh full exact-body Thumb disassembly in this own disposable evidence directory using installed LLVM, then search direct calls to `0x95FC` and inspect post-return uses. No historical flat offset or imported ABL1 source will be used as proof.

## Correction after observed tool error; changed method (before retry)

Timestamp: 2026-09-20T12:35:00+05:00 (+05:00).

The pending verifier's direct `llvm-objdump -D --triple=armv7-none-eabi --mattr=+thumb2 <raw-bin>` invocation exited `1` with: `The file was not recognized as a valid object file`. This is a tool-input error, not a finding about ABL1 control flow. Change only the disassembly transport: wrap the immutable raw payload with `llvm-objcopy -I binary -O elf32-littlearm -B arm` into a new local ELF evidence object, then run `llvm-objdump -D --triple=thumbv7` on that object and retain stdout/stderr/exit status. The target bytes and caller-search scope remain unchanged.

## Observed result

Timestamp: 2026-09-20T07:12:00+05:00 (+05:00).

Method-pivot command executed:

```text
python3 -B evidence/firmware-audit/20260920-clv-abl1-downstream/abl1_downstream_trace.py
```

Exit status: `0`; stderr empty; `6/6` checks passed. `llvm-objcopy` produced the own ELF object; `llvm-objdump` produced the full Thumb disassembly. Direct `BL/BLX` callsites to `0x95FC`: `0`.

This is a bounded blocking result after full-body disassembly, not a claim that indirect/vector/external invocation is absent.

## Manifest and final readback

Timestamp: 2026-09-20T07:13:00+05:00 (+05:00).

`sha256sum -c evidence/firmware-audit/20260920-clv-abl1-downstream/SHA256SUMS` exited `0`; all six own entries returned `OK`. Final direct-call trace rerun: exit `0`, stderr empty, `6/6` checks passed, direct call count to `0x95FC` = `0`.

Full exact-body disassembly and own object are retained for reviewer; no imported historical source was used as proof.

## Pointer/dataflow result

Timestamp: 2026-09-20T07:20:00+05:00 (+05:00).

Method-pivot verifier:

```text
python3 -B evidence/firmware-audit/20260920-clv-abl1-downstream-pointers/abl1_pointer_dataflow_verify.py
```

Exit status: `0`, stderr empty, `13/13` checks passed. Raw pointer words `0x95FC/0x95FD` and Thumb branch targets were retained as zero candidates; exact r4 shared-root, aggregate `+0x2BC`, channel pointer and channel `+0x20` stores were independently checked. Downstream owner remains unresolved through indirect/vector/external dispatch.

## Producer-path extension intent (before write)

Timestamp: 2026-09-20T13:15:00+05:00 (+05:00).

The corrected full exact-body Thumb disassembly completed with exit `0` after wrapping the raw payload as an ELF object. It contains no direct `BL`/`BLX` target `0x95FC`; the raw payload contains no searched 32-bit function-pointer variant for the payload-offset or observed absolute-base candidates. Extend the bounded evidence with one concrete `+0x20` producer chain already visible in the same exact payload: caller `0x7E00 -> 0xAD58` and `0x7E30 -> 0x10CC0`, plus the preceding `0x7544` initializer `0x757C` and `0x75CC` object handoff. Preserve exact raw bytes, disassembly windows, alias equations, pointer-scan result, and the distinction between a proven producer path and the unresolved immediate caller of `0x95FC`. No firmware, hardware, candidate, or settings changes.

## Verifier byte-order correction (after observed error)

The first producer verifier run exited `1` because the expected byte strings for multi-halfword Thumb instructions were written in disassembly display order rather than raw little-endian order (`0x7E00` observed `02f0aaff`, expected display `f002ffaa`). No result JSON was emitted and no input was changed. Correct the verifier's expected raw-byte literals only; retain the error and rerun against the same exact payload/disassembly.

The corrected verifier exposed the same display-order issue for 16-bit Thumb halfwords (`0xAE22` observed `0684`, display `8406`). Correct the remaining halfword literals (`0x10D40=008c`, `0x10E50=0784`) and rerun; this remains an evidence-script correction, not a payload finding.

## G6 method change after repeated verifier-literal failures

Three consecutive producer-verifier failures were all caused by manually transcribed Thumb display-order versus raw little-endian literals. Change method class now: stop asserting hand-written byte strings; independently assert the semantic instruction text at the exact payload offsets from the completed LLVM disassembly, while recording raw bytes as observed fields. The immutable payload, disassembly, callsite addresses, and producer dataflow are unchanged.

## Evidence/report readback intent (before manifest write)

Reopen the producer verifier result, final English report, immutable ABL1 input, successful ELF/LLVM outputs, and verifier source; then create a new `SHA256SUMS.final` without overwriting the older `SHA256SUMS`. Record literal statuses, hashes, and the unresolved direct-caller boundary below.

## Observed result

- Corrected producer verifier exit `0`; stderr empty; `16/16` checks passed.
- Fresh full exact-body LLVM Thumb disassembly exit `0`; stderr empty; direct callsite count to `0x95FC` = `0`.
- Raw target-pointer variant scan at zero base, observed `0x60000` candidate base, `0x08000000`, and `0x006A0000`: all searched variants absent.
- Callback initializer: `0xB1F8` stores the literal at `0xB218`; observed value `0x00067ABD`. Under subtraction by `0x60000`, the candidate offset `0x7ABD` is data/string bytes, so callback implementation remains absolute/runtime-bound.
- Concrete producer chain verified at `0x7544/0x757C -> 0x75CC -> 0x7E00 -> 0xAD58 -> 0xAE22` and `0x7E30 -> 0x10CC0 -> 0x10D40/0x10E50`; this writes/reduces the same channel-field offset `+0x20`.
- `SHA256SUMS.final` check exited `0`; every listed entry returned `OK`.
- Readback hashes:
  - report `b25721a5eb514a231b1d11266bdb64210477be81785451dbfde4db276162f1f2`
  - verifier `ad74bbbf9508d7a6f2fb3e0530a99ccd09920d295c49f9fe309ec1692c8ccd5d`
  - result `a5dd7595ec4d07993120dbcd466be6619d3fcd60aff5a85e010bbd8de8c519a9`
  - final manifest `07c6a46abbc266631c9438fc017a59a49d7b4e5d0940870d9dd056310c9d426a`
- Remaining limits: immediate caller of `0x95FC`, runtime dispatch/relocation, AmdSetup/INV edge, units, training, runtime execution, and hardware behavior remain unresolved/unrun.

## G7 correction and conditional runtime-base mapping audit (before write)

The previous report over-qualified `0x00067ABD` as external because it tested only the `0x60000` subtraction. That claim is withdrawn pending a bounded pointer-anchor audit. Reopen the exact literals at `0xB218/0xB21C/0xB220/0xB224` and test the reviewer-proposed base `0x57100`. Accept the mapping only if at least three independent anchors land on exact local Thumb code and the callback at `+0x52C` is decoded through its `+0x0C` channel-pointer write. Update only the supplemental result/report/manifest; preserve earlier result history and the old claim as corrected evidence.

The base-`0x57100` target-pointer scan found one unrelated raw occurrence of candidate value `0x000606FD` at payload `0x17134`; it is not a validated function-pointer reference. Qualify the scan instead of claiming every candidate is absent: all other target variants remain absent, and this single collision is retained as an ambiguity record.

## Corrected mapping observed result and manifest refresh intent

The corrected mapping verifier now passes `32/32`: four independent absolute pointer anchors support candidate base `0x57100`, resolving callback slot `+0x52C` to local Thumb function `0x109BC`; its exact code computes/stores the selected channel pointer at `context+0x0C` (`0x10A04`). The previous `0x60000`-based external-boundary wording is superseded. Refresh `SHA256SUMS.final` and the report readback; preserve the single `0x000606FD@0x17134` target-scan collision as unvalidated.

## Corrected mapping readback observed result

- Corrected verifier exit `0`; stderr empty; `32/32` checks passed.
- Callback mapping: base candidate `0x57100`, four independent code anchors; callback `+0x52C -> 0x109BC`; callback writes selected channel pointer to `[context+0x0C]` at `0x10A04`.
- Direct `0x95FC` callers remain `0`; target-pointer scan retains only unvalidated collision `0x000606FD@0x17134`.
- Manifest check exited `0`; stderr empty; every entry `OK`.
- Corrected readback hashes:
  - report `68f315f08647ce39bace182e48696158a5bbd954772bf5edcc4f98825b5ae4fa`
  - result `d9b40965d4901df0544e460da7e16ac30b4ccd4cd97b07d2de2ec8b1afddf5f8`
  - verifier `abbff9a82781841cfef5099a06d120cd750a0259bd0c331519c61f5d5bcbba50`
  - final manifest `c05ac17b5901c8c8b4ff877139b695d6ac13c52a84b82c7ee42c7b81832e0d3b`
- Superseded wording: `0x00067ABD` is not currently claimed external; it is conditionally local under base `0x57100`, with loader/base proof still open.

## Producer-input upstream trace intent (before write)

Timestamp: 2026-09-20T14:10:00+05:00 (+05:00).

Next bounded action: inspect exact Thumb dataflow at `0x75CC`, `0x7E00`, `0x7E30`, `0xAD58`, and `0x10CC0` to recover the actual input fields/constants, mode/range branches, and object ownership feeding the `+0x20` writers. Reuse the immutable ABL1 payload, current conditional base `0x57100`, and successful LLVM listing. Specifically classify `[r4+4]+{0x28,0x2C,0x30,0x734,0x790}`, root `[r4]+{0x28,0x770,0x79C}`, context `[r4+0x60]`, and the per-channel `[r4+0x0C]+0x20` dataflow. Check whether any inspected literal/field is directly sourced from AmdSetup/APCB/UMC policy; preserve an explicit unresolved boundary where the value enters through an opaque helper or runtime structure. No hardware, firmware, candidate, settings, voltage, install, shared MCP, or commit changes.

## Producer-input trace observed result and manifest refresh intent

- Exact producer-input verifier exit `0`; stderr empty; `65/65` checks passed.
- New result: direct override branch `[r4+0x331]/[r4+0x516] -> [r4+4]+0x2C`, APCB/CBS path `0x1F2C -> 0x47D0 -> 0x49CC` with token `7`, timepoint `2`, and 20 exact enum-to-value mappings.
- `0xAD58` and `0x10CC0` input branches are preserved; units and Setup/INV identity remain unproven.
- Refresh the owned final manifest to include the new verifier, result, windows, and corrected report; preserve the older `SHA256SUMS`.

## Producer-input trace final readback

- Input verifier exit `0`; stderr empty; `65/65` checks passed; `20` enum mappings checked.
- Exact input source path now proven at static boundary: explicit override `[r4+0x516]` or APCB/CBS getter token `7`, timepoint `2`, through `0x1F2C -> 0x47D0 -> 0x49CC`; numeric policy output is written to `[r4+0x04]+0x2C`, mode `2`.
- `0xAD58` consumes mode/value; `0x10CC0` reduces and clamps channel `+0x20`; no units or physical-clock meaning assigned.
- Final manifest check exit `0`; stderr empty; all entries `OK`.
- Readback hashes:
  - report `edfe8887b99f24d1dda33a8667478476fffc17813b94bb8e188183945ea6e6da`
  - result `8bbab6063cc04012ee5e700bd7b48728893c31fdf8a2339fe058bab75040b2a5`
  - verifier `aafbd2280d278ab102949fc3f0a160d71b23137adaa1b67f16e40c30c3791e1e`
  - windows `10ed25fd94f29a7772e295de475ba8d4a65481baa6f704556193e4e4c3778774`
  - final manifest `5dcd423d263fd0566e6c89b270a5306ef82852485d077c478a483422b9ebbad7`
- Remaining boundaries: map token 7/APCB getter to AmdSetup/INV identity, prove loader base/runtime execution, units, training actuator, 1:1:1 synchronization, and hardware acceptance.

## Getter namespace / IFR cross-bind intent (before write)

Timestamp: 2026-09-20T15:05:00+05:00 (+05:00).

Bounded follow-up: bind exact getter `0x49CC` call arguments (`token=7`, `timepoint=2`) to the exact clv APCB/CBSG raw structure, preserve the two observed CBSG token-7 rows and their values, and compare the ABL enum/value map against the exact IFR `Memory Clock Speed` options from `menu-result.json`. Recheck the existing AmdSetup precedence result: stored AmdSetup `+0x316` wins over missing-variable fallback `0xFF`; do not equate the APCB/CBS getter token with `$INV 0x11ED` without a direct edge. New result/report/manifest extend the current downstream evidence; no firmware, hardware, candidate, settings, voltage, install, MCP or commit changes.

## Independent branch/order review intent (before evidence append)

Timestamp: 2026-09-20T07:19:35+05:00 (+05:00).

Independently reparse the exact ABL1 LLVM Thumb listing and immutable payload, without invoking the producer-input verifier's assertion logic, to check the override/fallback branch order, `0xAD58` default/mode branches, `0x10CC0` mode/clamp path, and all 20 enum output constants. No source, firmware, hardware, candidate, settings, or runtime changes.

## Independent branch/order review observed result

A standalone Python check parsed `abl1-data-thumb-llvm.txt` and the immutable `ABL1-clv-decompressed.bin`; it did not import or call `abl1_producer_input_verify.py`. Exit `0`; `21/21` checks passed:

- Exact payload hash matched `af8cf5626a113afe72bc0687ca6f1a3b44fd6d46ca4f0119df3be2356a74203a`.
- Override order matched: `[r4+0x331]` enable, `[r4+0x516]` load/sentinel compare, writes to `[r4+0x04]+0x2C` then mode `2` at `[r4+0x04]+0x28`.
- Fallback order matched: call `0x1F2C`, wrapper call `0x47D0`, `r0=0xD`, then `0x49CC`.
- `0xAD58` matched mode load, mode-0 branch, mode-2 branch, default `0x0320`, mode-2 `+0x2C` load, mode-0 `+0x770` bound, and special `0x1C2` branch.
- `0x10CC0` matched pair load, mode `0/1` branches, clamp write at `+0x60`, and per-channel `+0x20` write.
- All 20 enum constants matched the exact listing.

This independently corroborates the 65-check producer-input result at the static disassembly/table-order layer. It does not establish token-7 to `AmdSetup+0x316`/`$INV 0x11ED`, units, runtime execution, training, synchronization, or hardware behavior.

Current action-log SHA-256: to be recorded after append-only readback.

- Readback action-log SHA-256: f804365690dbfa2ff16df77a1d4f7d1d0727d9648a9c0107345e267a9f6f73bb
- Note: the digest above is the hash of the action log immediately before the self-reference line was appended; no self-referential final-file hash is asserted.

The first getter/APCB verifier run exited `1` because the absolute CBSG body-row calculation added a group-style `0x10` header instead of the subgroup parser's exact `0x08` header. No result JSON was emitted. Correct the raw locations to `0xAB1464` and `0xAB1710` per `scripts/apcb_detail.py` (`body = subcursor + 8`) and rerun.

The corrected getter verifier exposed a substantive semantic difference rather than a tool error: exact IFR `Memory Clock Speed` has `22` non-Auto options, while the ABL TBB decode has `20` valid enum branches. Codes `0x26` (1900 MHz) and `0x27` (1950 MHz) fall through the invalid/default branch (`0x232A`) and are not mapped by the ABL function. Change the acceptance check from equality to subset plus explicit missing-code assertion; retain this as the new result.

The getter verifier then exposed a transcribed TBB-byte assertion typo (`...1c22...` versus observed `...1c1f...`); no payload finding changes. Correct the expected raw table bytes and rerun.

The getter verifier then used the wrong JSON path for the existing-defaults result (`existing_nvar`/`missing_variable_fallback` are nested under `fields`/`precedence_model`). No result JSON was emitted. Correct the readback path and rerun.

## Getter namespace observed result and manifest refresh intent

- Getter/APCB/IFR verifier first exposed two correctable data-boundary issues (subgroup body header and IFR option cardinality); both corrections are retained above.
- Corrected verifier now passes `27/27`: call args token `7`, timepoint `2`; exact CBSG raw rows at `0xAB1464`/`0xAB1710`; IFR has 22 non-Auto options; ABL maps 20 and falls through codes `0x26/0x27`; stored AmdSetup precedence remains `36` versus fallback `0xFF`.
- Refresh final manifest and re-open all owned current outputs. No claim that token7 is `AmdSetup` or `$INV`.

## Resume observed result after prior 429

The resumed actual action reran the existing getter namespace verifier (no duplicate job launched): exit `0`, stderr empty, `27/27` PASS. It preserved the completed result: token `7`, timepoint `2`, CBSG rows `0xAB1464`/`0xAB1710`, IFR 22 non-Auto options, ABL 20 mapped codes with missing `0x26/0x27`, and no direct token7→AmdSetup/INV edge. Final manifest rerun: exit `0`, stderr empty, all entries `OK`. No 429 recurred.

## Independent ABL enum versus exact IFR comparison intent (before write)

Timestamp: 2026-09-20T07:30:00+05:00 (+05:00).

Bounded static check: independently decode the exact ABL1 TBB dispatch at payload `0x2286` from immutable bytes, recover all recognized numeric policy outputs and invalid branches, then compare them against the exact CLV IFR `Memory Clock Speed` options in `evidence/firmware-audit/20260920-df-init-route/menu-result.json`. Include IFR `Auto`/default and all options, including codes that the ABL table rejects. Preserve the distinction between matching numeric values and a proven shared namespace; no units, runtime, training, synchronization, hardware, firmware, candidate, or settings operation.

Expected effect: one machine-readable comparison result, one English report, and an append-only action-log section. Rollback: remove only the new comparison evidence/report/script and appended sections.

## Independent ABL enum versus exact IFR comparison observed result

- Standalone verifier: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-ifr-enum-compare/abl1_ifr_enum_compare.py`; exit `0`; `21/21 PASS`.
- Exact byte decode recovered all 20 ABL-recognized selectors and their numeric outputs from the TBB at payload `0x228A`; it independently confirmed the range guard and invalid target `0x232A`.
- Exact IFR comparison found numeric agreement for all 20 recognized codes.
- IFR-only options are `0x26=1900MHz`, `0x27=1950MHz`, and `0xFF=Auto` (default); all three take the ABL invalid path (`0x232A`).
- This is a bounded table correlation, not proof of a shared namespace: token `7` to `AmdSetup+0x316`/`$INV 0x11ED` remains unresolved, as do units, runtime execution, training, physical clocks, synchronization, and hardware.
- Result: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-ifr-enum-compare/abl1-ifr-enum-compare-result.json`.
- Report: `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-abl1-ifr-enum-compare.md`.
- Manifest: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-ifr-enum-compare/SHA256SUMS`; `sha256sum -c` exit `0`.
- Readback hashes: report `305e91bd87f9368f3cc08fc8e8432e9d0ab04106fb738df014e60bcdd10f7c1a`; result `95f7e14ec171773de562078878f092b072a7f52cec7a80343a03503ccc503a13`; verifier `be92ae36aa95501b5ce1e4c8f658d24c2cfcce3a727aaf1ebcba2618320d518c`; manifest to be recorded after final append-only readback.

## Qualified shared integration intent (before memory/plan append)

Scope: append the independently verified ABL1-versus-IFR comparison to the durable OC review memory and stage-2 plan. Preserve the distinction between exact 20-code numeric correlation, three IFR-only invalid outcomes, and unresolved token-7/`$INV 0x11ED` namespace identity. No route completion or hardware implication.

Expected effect: retain Phase 2 as `PARTIAL` and make the new comparison discoverable without replacing prior evidence. Rollback: remove only the appended integration sections.

## Qualified shared integration observed result

- The durable OC review memory and stage-2 plan were appended without altering prior claims; Phase 2 remains `PARTIAL`.
- Reopened result status: `21/21 PASS`; exact 20-code numeric agreement, IFR-only `1900MHz`, `1950MHz`, and `Auto` invalid outcomes confirmed.
- Reopened absolute role paths:
  - `/home/OWNER/orca/projects/bc250/docs/research/20260920-clv-abl1-ifr-enum-compare.md`
  - `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-ifr-enum-compare/abl1-ifr-enum-compare-result.json`
  - `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-ifr-enum-compare/abl1_ifr_enum_compare.py`
  - `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-clv-abl1-ifr-enum-compare/SHA256SUMS`
- Reopened integration hashes: plan `9dce6f1dea09196d898cb87fd08dd0249e20d5dc76c5d18460f45ec93eaebba7`; memory `cfe3406ac5e29672f11c1c3e1e361ac40ec990599d1fb69049ee485de57ba2c4`.
- Token `7` remains unproven as a direct alias of `$INV 0x11ED`; no units, synchronization, training, runtime, or hardware conclusion was added.
- Final comparison manifest SHA-256: `2e1eb9dfde4aa2fe080ae1f6bd08127ba75334d6d2f388484868bb585cda7bb3` (manifest contents verified with `sha256sum -c`; action-log digest intentionally not self-referenced).

## Final comparison rerun observed result

- Reran the standalone comparison after integration: exit `0`; status `PASS`; `21/21` checks.
- Reran the comparison manifest: `sha256sum -c` exit `0`; both entries `OK`.
- Reopened machine result: `20/20` numeric agreements; IFR-only entries `(38, 1900MHz, invalid-table-gap)`, `(39, 1950MHz, invalid-table-gap)`, `(255, Auto/default, invalid-range)`.
- No new finding or claim was added; token-7-to-`$INV 0x11ED` remains unresolved.
