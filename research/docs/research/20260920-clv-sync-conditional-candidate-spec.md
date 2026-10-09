# Conditional minimal native-sync candidate specification — no ROM built

## Decision

Keep `scripts/build_clv_oc_candidate.py` unchanged and **do not add a `sync` profile yet**. The current builder is intentionally a single-field `DfClockOvrd` stored-request experiment; its tests reject unsupported `sync` and voltage profiles. Existing “sync” files are historical NVRAM byte sets, not semantic or physical proof.

If the offline consumer/semantic gate closes, extend the same builder (not a second framework) with a separately named conditional profile. The future profile must select the authoritative default/request source first, then change only the smallest proven native field set. It must remain explicitly experimental until the hardware gates pass.

This changes implementation choice in one bounded way: **future work is a guarded extension of the existing hash-pinned builder, not reuse of historical `sync` images and not a new generic patcher.** No ROM or candidate was built in this task.

## Exact baseline and native fields

Pinned source:

- `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
- 16,777,216 bytes
- SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`

`AmdSetup` body base is `0x4CF`; absolute offsets are body plus field offset:

| Field                    | Body offset |       Absolute | Current clv bytes/value      | Candidate treatment                                                                                                                               |
| ------------------------ | ----------: | -------------: | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `MemoryClockSpeed`       |    `+0x316` |        `0x7E5` | `0x24` / IFR label `1800MHz` | Change only to an exact proven IFR enum code; do not write decimal MHz as a code.                                                                 |
| `UclkDiv1M0`             |    `+0x330` |        `0x7FF` | `0x01` / `Enabled`           | Change only after divider/synchronous-crossing semantics are proven. `Enabled` is not currently a decoded ratio.                                  |
| `MemoryPstate`           |    `+0x36D` |        `0x83C` | `0xFF` / `Auto`              | Hold unchanged in the minimal profile unless the training gate proves a required value.                                                           |
| `FclkDpm`                |    `+0x6A3` |        `0xB72` | `0x0F` / `Auto`              | Assert unchanged by default; change only if its consumer proves explicit enable/mode is required.                                                 |
| `DfClockOverrideControl` |    `+0x703` |        `0xBD2` | `0x01` / `Manual`            | Treat as coupled with `DfClockOvrd`; current value already enables the pair, so assert rather than rewrite unless semantics require another mode. |
| `DfClockOvrd`            |    `+0x704` | `0xBD3..0xBD4` | `0x058C` / `1420`            | Change only after unit/domain/training meaning is proven.                                                                                         |

## Smallest conditional transformation

If and only if the offline gate proves that the native controls jointly select the desired actuator and crossing mode, the minimal stored-field transformation template is:

1. Keep all bytes at baseline.
2. Set `AmdSetup+0x316` to the selected valid enum code.
3. Set `AmdSetup+0x330` to the proven UCLK/crossing selector.
4. Set `AmdSetup+0x704` to the proven value, while requiring `AmdSetup+0x703` to be the matching control state.
5. Keep `+0x6A3`, `+0x36D`, voltage, timings, PPT/current limits, CPU and unrelated NVRAM unchanged unless a separate semantic/training result proves a required dependency.

With the present baseline (`+0x703=1`), the conditional allowlist contains four byte positions at `0x7E5`, `0x7FF`, `0xBD3`, and `0xBD4`. The actual number of differing bytes depends on the selected values and must be measured against the baseline. That four-position set is a **conditional template, not a justified candidate today**. If semantic evidence proves `FclkDpm` must leave `Auto`, add only byte `0xB72`; if training proves `MemoryPstate` must change, add only `0x83C`. Neither addition is currently justified.

The future builder must reject any profile lacking an explicit semantic manifest containing:

- target enum/code and decoded unit mapping;
- target DF/FCLK value and rate conversion;
- UclkDiv1M0 ratio/crossing meaning;
- authoritative source (`AmdSetup` stored request, default initializer, IFR default, or migration path);
- existing-NVRAM precedence/migration behavior;
- one-variable rationale and allowed changed offsets.

## Why historical `sync` images are not the template

`candidates/BC250_5.00_clv_OC_sync_v002.bin` is an observed historical artifact, not a model for the future route:

- SHA-256 `544b3c24d4b969c3b9b5ab7bbcb873b552f2757808a5855806b5324239749b27`;
- source hash is the pinned CLV donor;
- changes NVRAM bytes at `0x7E5`, `0x7FC`, `0xB72`, and `0xBD3`;
- it changes `BankGroupSwap` (`0x7FC`) without a proven sync role;
- it leaves `UclkDiv1M0` unchanged, despite the filename claiming sync;
- build metadata says `hardware_written=false`.

The profile therefore mixes an unexplained timing/control byte with clock requests and does not satisfy the current one-variable or semantic-actuator requirements.

## Remaining semantic gates

The conditional transform stays blocked until all are resolved offline:

1. `$INV 0x1204` requester/consumer beyond the immediate CbsBasePei adapter, including indirect registration/HOB/DMA/runtime paths.
2. Actual divider/clock/training actuator for each of `0x11ED`, `0x1204`, `0x1331`, `0x1373`, and `0x1374`.
3. MCLK/FCLK/UCLK unit and GDDR6 rate conversion.
4. UclkDiv1M0 ratio and synchronous-crossing selection, rather than an enum label alone.
5. Memory-P-state and `FCLK > UCLK` guidance relation to training.
6. Existing-variable/default/fallback/migration precedence; a stored request must not be called an applied default.

The current native trace ends at an INV adapter and the ABL1 HEAP branch remains static/indirect; no actuator, physical clock, or synchronization result is established.

## Future transaction and acceptance requirements

Once the semantic gate closes, the builder extension must create a new output only and produce the required four roles:

- `MODIFIED_FILE` — conditional minimal profile;
- `DIFF_FILE` — reconstructs it from pinned CLV;
- `VERIFICATION.txt` — exact source/output hashes, changed offsets, parser checks and baseline/request/rollback results;
- executable `ROLLBACK.sh` — restores pristine bytes from a sibling/embedded baseline.

Offline checks: NVAR/FV/APCB/PSP structural validation, exact changed-range check, malformed-input rejection, independent review, and rollback hash equality. Hardware acceptance remains separate: current-board full dump/recovery, programmed readback, cold/warm/Load-Defaults repetitions, independent physical clock/divider/crossing observation, performance A/B, and error-free screening.

## Status

- **Decision artifact:** conditional minimal native-field template recorded; no ROM/candidate written.
- **Direct current builder test:** existing regression suite already recorded `7/7 PASS`, including refusal of unsupported `sync` and voltage profiles.
- **Offline semantic gate:** OPEN.
- **Hardware acceptance:** UNRUN.
- **1:1:1 claim:** not permitted.
