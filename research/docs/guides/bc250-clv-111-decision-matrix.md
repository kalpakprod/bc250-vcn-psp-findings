# BC-250 plain CLV 5.00 — operator decision matrix (DRAFT)

**Status: DRAFT / NOT READY.** This matrix is an evidence-and-decision aid, not a flash authorization, voltage recommendation, or proof of physical `MCLK:UCLK:FCLK=1:1:1`.

## 1. Decision summary

| Decision | Current disposition | Evidence boundary |
|---|---|---|
| Preserve memory request | **YES, request-only:** retain `AmdSetup+0x316=0x24`, the exact IFR-labelled `1800MHz` option | Saved donor/readback bytes and static IFR; no current-board readback or physical MCLK |
| Enable physical `1:1:1` | **NO-GO / UNPROVEN** | UclkDiv1M0 ratio, units/rate conversion, training, crossing/divider state, and independent clocks are unresolved |
| SoC `1.15 V` | **NO-GO / UNMAPPED** | No revision-matched SoC rail/controller path, conversion, safe ceiling, or electrical readback |
| Performance claim | **UNRUN** | No controlled B1800/SYNCCAND board campaign or valid paired measurements |
| Hardware acceptance | **UNRUN / EXPLICIT GATE** | No current board state, physical clock, training, voltage, stability, or rollback acceptance |

The pinned target is a donor/reference image, not proof of installed firmware:

- ROM: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
- Size: `16,777,216` bytes
- SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- Latest saved board snapshot is W11, SHA-256 `3c50bc9a65194b75ca805e6ed31c5778369de1fe8eca4600f44e15fae3b40fc3`; it is not current-state proof.

## 2. Exact native menu map

These are package-local static HII paths in VarStore `0x5000` (`AmdSetup`). They do not prove live Setup visibility, save/reset behavior, training, or application.

| Control | Exact static menu path | QID | Field / saved CLV request | Interpretation |
|---|---|---:|---|---|
| Memory Clock Speed | `UMC Common Options → GDDR6 Common Options → DRAM Timing Configuration → I Accept` (`0x7007 → 0x7028 → 0x702A → 0x702C`) | `0x20F` | `+0x316` / ROM `0x7E5`; `0x24` = enum `36`, label `1800MHz` | Request persistence only; physical MCLK unknown |
| UclkDiv1M0 | `AMD CBS → UMC Debug Options → GDDR6 Debug Options → GDDR6 DRAM Timing Configuration` (`0x7000 → 0x7008 → 0x702E → 0x702F`) | `0x229` | `+0x330` / ROM `0x7FF`; `0x01` = `Enabled` | Enum label, not decoded `/1` ratio |
| Memory P-state | `AMD CBS → UMC Debug Options → GDDR6 Debug Options → GDDR6 DRAM Controller Configuration → DRAM Power Options` (`0x7000 → 0x7008 → 0x702E → 0x7030 → 0x7032`) | `0x25E` | `+0x36D` / ROM `0x83C`; `0xFF` = `Auto` | Training/P-state effect unknown |
| FCLK_DPM | `SMU Debug Options → SMU Features` (`0x7009 → 0x703E`) | `0x7045` | `+0x6A3` / ROM `0xB72`; `0x0F` = `Auto` | Callback/static serializer only; applied FCLK unknown |
| DF Clock Override control | `SMU Debug Options → SMU Debug` (`0x7009 → 0x703F`) | `0x37D` | `+0x703` / ROM `0xBD2`; `0x01` = `Manual` | Does not prove request wins |
| DF Clock Override value | Same `SMU Debug` path | `0x37E` | `+0x704` / ROM `0xBD3..0xBD4`; LE `0x058C` = `1420` | Numeric request `[0,2000]`, not proven MHz/FCLK |

The UI guidance “FCLK > UCLK” and “Memory P-state disabled” is not an executed training rule. Numeric overlap between Memory labels and DF `[0,2000]` is not unit equivalence.

## 3. Candidate-setting decisions

All rows below are **experimental/unknown**, not recommendations. A live test requires an identified board, recovery, readback, one logical field, and explicit approval.

| Test | Single variable | Diagnostic value | Prohibited inference |
|---|---|---|---|
| T1 | Memory `+0x316` / QID `0x20F` | Request persistence and boot outcome | Label is physical MCLK or training acceptance |
| T2 | UclkDiv1M0 `+0x330` / QID `0x229` | Persistence/boot comparison of `Auto=0xFF` vs `Enabled=0x01` | `Enabled` means `/1` or synchronization |
| T3 | FCLK_DPM `+0x6A3` / QID `0x7045` | Persistence/callback/boot comparison | DPM state is measured FCLK |
| T4 | Memory P-state `+0x36D` / QID `0x25E` | Diagnostic persistence/boot only | `Disabled` is training-safe or enforced by help text |
| T5 | DF control `+0x703` / QID `0x37D` | Control persistence with value unchanged | Numeric value is consumed or wins precedence |
| T6 | DF value `+0x704` / QID `0x37E` | One `u16` persistence test only if control is already recorded `Manual` | `1420`, `1800`, or any number is a frequency or FCLK |

Do not combine T5 and T6. Historical files named `SYNC_Full_1to1to1_*` are comparison evidence only, not recipes. No candidate setting is currently recommended.

## 4. ABL1/consumer boundary — what the new static evidence changes

- AF58 table: under conditional candidate base `0x57100`, bounded table VA `0x6E1C8` has count `2`; row 0 callback `0x62059` maps to RVA `0xAF58`, row 1 callback is zero. `0x5CBE` produces `[2,1]` and returns `1`; `0xFE60` returns `1` on that exact buffer. Neither helper contains a direct `0x7378`/`0xAF90` link or clock-register operation. Runtime loader/base and callback execution remain unproven.
- Item `0x17`: `0x7E3A → 0x0C60` selects item `0x17`; conditional table mapping reaches `0x95FC` only under the candidate base. `0x7E40` loads context `+0x2BC`; `0x7E74 → 0x5E68`; the `0x5E68` branch conditionally stores a derived halfword at context `+0x78` (`0x5FBA`). The later object identity and indirect target remain unresolved.
- HEAP source-copy claim is **withdrawn**: `0x6B78` is a zero-fill loop on the inspected path; constructor/provider `[SP+0xA4]` slots are different frames. This does not join APOB/`$INV 0x11ED` to a clock actuator.

These findings are static/observed-bytes evidence, not physical clock or training evidence. No frequency or clock unit is assigned.

## 5. Voltage decision matrix

| Area | What is proven | Decision |
|---|---|---|
| SoC target `1.15 V` | Operator target only; no mapped absolute-voltage BIOS field or revision-matched rail proof | **NO-GO; do not translate into an offset or menu value** |
| `AmdSetup+0x6E5/+0x6E6` VDDCR_VDD offset | Stored offset fields; final consumer/rail identity unresolved | **No change; not a SoC setpoint** |
| VCORE fixed voltage | Separate `Setup+0x1C9/+0x1CA`, QIDs `0x73/0x74`, UI bounds `700..1250`, donor enable `0`, value `900` | Static path only; no numeric value recommended |
| GFX fixed voltage | Separate `Setup+0x1CD/+0x1CE`, QIDs `0x76/0x77`, UI bounds `700..1250`, donor enable `0`, value `900` | Not SoC; no numeric value recommended |
| MEMIO fixed voltage | Separate `Setup+0x1D1/+0x1D2`, QIDs `0x79/0x7A`, enum donor `0x1E` labelled `1.35 V`, enable `0` | Enum/controller/net semantics unresolved; no value recommended |
| CAD PUS1/RT8237E vs PUA1/ISL69247 | Revision-uncertain static board/design leads; no operator-board package/net/readback | Do not map labels to physical rails |

`700..1250 mV`, `1.20..1.45 V`, telemetry words, or historical “1.2-something” reports are not safe limits or recommendations. Current voltage decision: **no voltage change**.

## 6. Required operator readbacks before any approved live test

1. Exact board identity and target PCI ID `1002:13fe`.
2. Current full-chip/recovery image path and SHA-256; distinguish it from donor CLV and historical W11.
3. BIOS version/date, kernel, amdgpu/firmware/PMFW identifiers, cooling and power conditions.
4. Read-only NVRAM/Setup values for all six clock fields and all voltage controls.
5. POST/display/boot/training result and error counters.
6. Two filtered idle runtime snapshots at least 10 seconds apart using the existing capture route.
7. For voltage: board revision, regulator/package markings, revision-matched output-to-net mapping, and independent electrical readback. BIOS bytes alone are insufficient.
8. For synchronization: independent MCLK/UCLK/FCLK measurements, common reference, documented GDDR6 rate conversion, divider/crossing state, and repeated cold boots.

A persisted field plus successful POST is only `PASS — menu persistence`; physical behavior is `INCONCLUSIVE` without independent measurements.

## 7. Final hardware gate: read-only procedure and missing operator inputs

### Required operator-provided inputs

Before any setting change or candidate discussion, the operator must supply or authorize a read-only capture of:

1. Board identity, revision/markings, target PCI ID `1002:13fe`, and whether the board changed after the latest saved W11 readback (`3c50bc9a…`).
2. Current full-chip readback path and SHA-256, plus a separate known-good recovery dump and tested programmer/recovery path.
3. Current BIOS identity/date, kernel, amdgpu/firmware/PMFW versions, cooling/power conditions, and current NVRAM/Setup values for all six clock fields and voltage controls.
4. A read-only target sensor/telemetry route and an independent clock measurement route; the local workstation DRM probe is not a board measurement.
5. For SoC voltage only: board revision, regulator/package markings, revision-matched output-to-net map, instrument identity/calibration, and operator authorization for an electrical readback. No voltage write is part of this gate.

If any input is missing, status is `HARDWARE_BASELINE_NOT_ESTABLISHED`; do not manufacture B1800 from the donor image.

### One concrete read-only measurement that could settle physical `1:1:1`

Run one **synchronized three-counter capture** on the identified board, first at unchanged B1800 and then at a separately approved candidate only if all recovery gates pass:

- sample independent hardware counters for the memory clock domain (MCLK/UMC), UCLK/DF, and FCLK/fabric/PLL, using the same documented reference interval and no writes;
- record counter addresses/fields, reference frequency, sample interval, divider state, edge/data-rate conversion (including GDDR6 conversion), instrument uncertainty, and at least 100 samples at idle and load across three cold boots;
- reject the capture if any “clock” is the same software `MemclkFrequency` export, a committed firmware target, or a duplicated driver metric; those are not independent;
- archive raw counter readbacks and the exact conversion equations. The project currently has **not** recovered an exact CLV UMC/DF/UCLK counter route, so this is a required future measurement, not an available result.

For each sample, compute exact physical-domain estimates from the documented counter equations:

```text
f_MCLK = C_MCLK(count_MCLK, ref_interval, documented_GDDR6_conversion)
f_UCLK = C_UCLK(count_UCLK, ref_interval, documented_divider)
f_FCLK = C_FCLK(count_FCLK, ref_interval, documented_divider)
r_MU = f_MCLK / f_UCLK
r_UF = f_UCLK / f_FCLK
```

Set tolerance `ε` before capture from the stated counter/instrument uncertainty. A physical synchronization PASS requires `|r_MU−1| ≤ ε` and `|r_UF−1| ≤ ε` for every valid idle/load sample and all three boots, plus successful training, no fallback, stable errors/thermal state, and matching pre/post readbacks. Missing conversion, independent domains, or repeated samples means `INCONCLUSIVE`, not `1:1:1`.

### Hardware-gate sequence

1. Read-only identify board/PCI/recovery/current image and capture all six fields.
2. Capture B1800 counters, training/POST, temperatures/errors, and two idle snapshots 10 seconds apart.
3. Do not change voltage. If a candidate is later approved, change one logical field only, save/reset, read back, cold-boot three times, and repeat the same counter capture.
4. Restore B1800, save/reset, read back, cold-boot, and capture a final rollback control.
5. Accept only the separately evidenced layer: persistence, boot/training, physical clocks, voltage, and performance are independent verdicts.

### Offline boundary

Offline static work can establish menu paths, QIDs, stored requests, serializer ownership, bounded code contracts, and conditional callback/table relationships. It cannot establish the operator board's current image/NVRAM, runtime dispatch, applied clocks, physical clock ratios, training, SoC rail voltage, stability, or performance. No candidate is ready until those missing gates are separately evidenced.

## 8. Measurement and acceptance matrix

| Claim | Minimum acceptance | Current status |
|---|---|---|
| Stored request | Exact value survives save/reset and read-only NVRAM readback | Donor/static only; current board unknown |
| Physical `1:1:1` | Independent domain clocks, common reference/conversion, divider/crossing evidence, repeated training and stability | **UNRUN / BLOCKED** |
| Voltage applied | Revision-matched rail mapping, controller semantics, PEI dispatch, independent electrical readback | **UNRUN / NO-GO** |
| Latency/performance | Three cold boots per condition × five trials, matched harness/compiler/environment, rollback block, raw data and error/thermal checks | **UNRUN** |

For future performance work, use B1800 as unchanged control and SYNCCAND only after structural review, recovery, explicit approval, readback and cold-boot acceptance. A 5% improvement threshold and 2% no-effect band are decision thresholds, not promises; no percentage or nanosecond result exists.

## 9. Rollback and stop conditions

### Settings-only rollback

1. Restore every changed field to the recorded B1800 value.
2. Save/reset and verify all field readbacks.
3. Cold boot and verify POST/display/OS/training/errors/temperature.
4. If restoration fails, stop and use the documented CMOS/NVRAM reset; re-read all fields. Do not compensate with voltage or another profile.

### Firmware rollback

Never overwrite the sole original. A later image transaction requires a complete recovery dump, source/output hashes, structural validation, exact approval, flash verification, independent readback, cold-boot acceptance, and a tested recovery path.

### Stop immediately on

Missing target identity/recovery; training loop; no POST/display/OS; changed/unexpected voltage; corrected/uncorrected errors; thermal alarm; GPU reset; abnormal harness exit; or any value that fails to persist. Preserve the failure and change method class after three same-kind failures.

## 10. Evidence ledger

| Source | SHA-256 | Evidence class / use |
|---|---|---|
| `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin` | `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8` | `observed-bytes`; pinned donor |
| `docs/research/2026-09-20-clv-native-menu-1to1-guide.md` | `03a7239adf248a32558ea8fc0bea801325cb010035a41198df888350aa8236e6` | `static-analysis`; paths/QIDs/options |
| `docs/research/2026-09-20-clv-sync-configuration-domain-matrix.md` | `6441b5c1cc7f5e19d478be690a0136a608e83ab4f1ac770fde8a8b5d74973841` | `observed-bytes` + `static-analysis`; request/domain boundary |
| `docs/research/2026-09-21-hardware-baseline-consolidated.md` | `7c9b494697581339beb3f4af3423f7852bf4eee6e50ef1964f959c2e1a11812c` | saved-vs-current identity boundary |
| `docs/research/2026-09-21-baseline-nvram-ledger.md` | `d130ba9663cdfa3cdf67b07ba11f33fcf3b1c483cc33d815f82b7abcaeb4d7d7` | saved request/readback ledger |
| `docs/research/2026-09-21-manual-voltage-safety-matrix.md` | `e43bb1d0108bb58ab8a81bb87bb5768e76ccf42d1b958424540c111a9926cb9d` | static voltage safety boundary |
| `docs/research/2026-09-21-voltage-evidence-integration.md` | `9dda181dc478400d8e06313296674572fdb00bebb50dfedc4d2bee8703b91d36` | voltage/memory/latency integration |
| `docs/research/2026-09-21-latency-protocol-reviewed.md` | `11d15b3a2158c71290e917ee0339bfc000bf2a74655b94fe0e4979f7d75ebcfb` | future A/B protocol; no run |
| `docs/research/2026-09-21-abl7378-indirect-entry.md` | `c15b43356e66dcdad621e0cf2f89a61af43dc00d84b32d8a8b15fc1bb79952c8` | AF58/table/helper static boundary |
| `docs/research/2026-09-21-abl-item17-reachable-output.md` | `6c3c528cc2b8669d48a7a98067b3241c0adb9daf983b9dca539f80f06d597122` | item17/output conditional boundary |
| `docs/research/2026-09-21-apob-abl-outer864-root-verification.md` | `13f9575b8ffcd6cb275cf19e87d714334d81ca749327fe3b4988aafbbb2821d2` | HEAP correction/static boundary |

**Final status:** This matrix is an operator decision aid, not a completed 1:1:1/SoC-voltage guide. No board, ROM, NVRAM, register, network, or hardware action was performed while creating it.
