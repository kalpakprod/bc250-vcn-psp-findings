# SMU dynamic domain ID `0x18`: physical clock identity remains unresolved

Date: 2026-09-21 (Asia/Almaty, UTC+05:00)  
Scope: bounded offline static follow-up to the exact-CLV Queue-3 selector result. This is not a repeated queue-table dump and not a hardware probe.

## Conclusion

**The physical identity is not proven.** Exact Robin-5 bytes establish that Queue ID `3`, message `0x1D`, selector index `11` selects dynamic domain ID `0x18`, whose descriptor assigns internal Group `6` and whose program/poll targets are `0x0116D150` / `0x0116D174`. `CLK_GROUP_6` / “Group 6 Clock” are internal firmware classifications; they do not establish MCLK, UCLK, FCLK, VCLK, DCLK, VCN, or any other physical clock tree.

A focused Ghidra slice on the exact CLV-matching Robin-5 body found only generic record-walk, register-applier, float-conversion, and metrics-export code around the relevant boundaries. The metrics exporter reads internal source floats at `0xF904`, `0xFA00`, and `0xFA1C` for exported metric fields `+0x48`, `+0x4C`, and `+0x4A`; the bounded listing does not link those fields to the target SMN address `0x0116D150` / `0x0116D174`. Prior public-interface/source evidence labels adjacent `SmuMetrics_t` fields as SoC/VCLK/DCLK, but that sibling-field label cannot be transferred to domain ID `0x18`.

This is a bounded negative: **no physical clock-name edge is present in the checked current local evidence**. It does not prove that no undocumented register dictionary or indirect implementation exists.

## Bound object and exact path

- Exact plain CLV ROM: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`, 16,777,216 bytes, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.
- Robin-5 SMU body: `/home/OWNER/orca/projects/bc250/archives/imported/vendor-upstream/legacy-tmp-bc250-upstream/amd_smu_reverse_engineering/smu_fw/smu_fw_robin_5`, 262,400 bytes, SHA-256 `cae8617c572613b610d24845cdb791fc66e8604e3ab1195d0ac3268b39e59f37`, byte-identical to ROM offset `0x8FEF00`.
- Preserved request: `AmdSetup+0x316`, ROM `0x7E5`, value `0x24` (IFR text `1800MHz`). It remains stored request metadata, not physical frequency evidence.

The previously completed exact-CLV selector trace establishes:

```text
Queue 3 / msg 0x1D
  -> selector 11
  -> dynamic domain ID 0x18
  -> descriptor 0xFA48, internal Group 6
  -> program pointer cell 0xFA5C = 0x0006D150
  -> SMN program 0x0116D150; poll 0x0116D174
```

The new raw-byte readback confirms the descriptor window bytes at `0xFA48` begin `06 02 00 00`, and the little-endian dword at `0xFA5C` is `50 D1 06 00` (`0x0006D150`). These bytes substantiate the internal group/pointer boundary only; no vendor field name is encoded in them.

## New focused current-Robin-5 slice

Ghidra 12.1.3 was run in a newly copied disposable `OCConsumer` project. Its script reported that all 262,400 loaded bytes equal the exact Robin-5 input body. The request targeted `0x2387C`, `0x2375C`, `0x23CB4`, and `0x29E34`; a second copied-project run queried `0x23CA8` and aligned helper entry `0x23CB8` after the first run reported no function exactly at `0x23CB4`.

Observed code boundaries:

- `FUN_0002387C` walks records with stride `0x1C`, tests an internal metadata byte, and conditionally calls `FUN_00023F18`. It does not name a physical clock.
- `FUN_0002375C` updates generic state fields and calls `FUN_000235C8` through three loaded addresses. Its exact decompilation/instruction bytes do not identify those fields as MCLK/UCLK/FCLK/VCN.
- `FUN_00023CB8` performs float multiplication and integer/division arithmetic, then returns a value. No physical domain name or frequency-counter read is visible in this bounded helper.
- `FUN_00029E34` (metrics exporter) uses exact body addresses `0xF904`, `0xFA00`, and `0xFA1C`, converting its source floats into fields `+0x48`, `+0x4C`, and `+0x4A`. It does not read `0x0116D150` or `0x0116D174` in the preserved function window. The result therefore does not join dynamic domain ID `0x18` to VCLK/DCLK, even though separate interface-v8 evidence names sibling metric fields.
- `0x23CB4` itself was not an existing function at that exact address in the copied Ghidra project. It is recorded as a boundary, not treated as a semantic negative.

The exact function slices and process captures are in `evidence/firmware-audit/20260921-smu-domain18-identity/`. The original Ghidra project manifest under the prior selector evidence rechecked successfully (18/18 entries); the new runs operated on copied projects only.

## Local name search and namespace cautions

A scoped search over the local SMU/recon text and project reports found internal Group-6/slot labels and historical outputs, but no address-backed source definition assigning `0x0116D150` or `0x0116D174` to a physical clock. The separate five-header address test already records `NO_DIRECT_HEADER_MATCH` (4/4 test assertions; zero literal matches for full/base-stripped address spellings). It was reused by readback, not rerun.

The old `slot-domain-map.json` is built from a **different Robin-3** body. It records slot index `24`, domain index `6`, raw offset `0x6D150`, and `semantic_name: null`; it is cross-version context, not exact Robin-5 physical-name authority. Historical strings such as `slot 0x18 dom=6 gate@0x6d150` are ordinal/internal labels. They must not be confused with the Queue-3 dynamic domain-ID namespace or treated as a physical name. A local hit `slot 24: feature_stapm_tick_0` is from the distinct SMU tick-handler slot table and is unrelated.

## Missing decisive source

The next useful local or authorized primary-source input is an exact Robin-5 / BC-250-applicable AMD/AGESA/SMN register or clock-domain dictionary that names `0x0116D150` and `0x0116D174`, defines their register/field semantics, and ties this Group-6 descriptor to a physical clock tree. An independently decoded exact-board caller/consumer providing that mapping is an equivalent path. Until then, do not relabel the result as MCLK, UCLK, FCLK, VCLK, DCLK, or VCN based on group or neighboring addresses.

A separate physical-frequency claim would additionally need the source unit/conversion and an independent readback/counter with calibrated reference, divider/status semantics, and a safe hardware procedure. None was run here.

## Verification status

- Exact ROM/body hashes and preserved setup byte: **PASS**.
- Focused Ghidra loaded-memory equality: **PASS**, exit `0`; three function entries and one aligned helper decoded. `0x23CB4` exact entry: **INCONCLUSIVE/UNRUN** in Ghidra because no function boundary existed at that address.
- Local text search: **PASS** as a bounded search, exit `0`; internal/historical labels found, no physical clock-name edge recovered.
- Existing register-header test: **PASS** as reported and readback-manifest-verified; `NO_DIRECT_HEADER_MATCH` is only a bounded no-match.
- Hardware identity/frequency/clock behavior: **UNRUN**.

No hardware, board, register, mailbox, network, NVRAM, ROM, firmware, or candidate action occurred. No source firmware or original analysis project was modified.

## Artifacts

- Report: `/home/OWNER/orca/projects/bc250/docs/research/2026-09-21-smu-domain18-identity.md`
- Action log: `/home/OWNER/orca/projects/bc250/docs/action-logs/2026-09-21-smu-domain18-identity.md`
- Evidence: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-smu-domain18-identity/`
  - `domain18-identity-result.json`
  - `focused-clock-slice.txt`, `focused-writer-slice.txt`
  - Ghidra command stdout/stderr/exit captures
  - `raw-table-readback.stdout`, `source-semantic-search.stdout`
  - `VERIFICATION.txt`, `SHA256SUMS.final`
