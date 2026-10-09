# BC-250 plain CLV 5.00 — evidence-based 1:1:1 setup guide (DRAFT)

**Status: draft only; not a final profile, not a safety approval, and not hardware-verified.**

This guide binds offline development to the plain CLV 5.00 image:

- **TARGET:** `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
- **Size:** 16 MiB
- **SHA-256:** `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- **Provenance:** RetroWeb community redistribution, uploader unknown; donor/reference only.

The user may flash a later BIOS selected by the project, but this document authorizes no flash, NVRAM/register write, voltage application, or board modification.

## 1. What is established and what is not

### Established statically in the exact CLV image

The exact HII/IFR package exposes these native controls and the saved bytes below. The paths are package-local static paths; they do **not** prove that the current board displays, saves, trains, or applies them.

| Control | Static Setup path | QID | `AmdSetup` field | CLV stored request | Exact evidence |
|---|---|---:|---:|---:|---|
| Memory Clock Speed | `UMC Common Options → GDDR6 Common Options → DRAM Timing Configuration → I Accept` (`0x7007 → 0x7028 → 0x702A → 0x702C`) | `0x20F` | `+0x316` / ROM `0x7E5` | `0x24` = `36`, HII label `1800MHz` | `docs/research/2026-09-20-clv-native-menu-1to1-guide.md`; `docs/research/2026-09-21-baseline-nvram-ledger.md` |
| UclkDiv1M0 | `AMD CBS → UMC Debug Options → GDDR6 Debug Options → GDDR6 DRAM Timing Configuration` (`0x7000 → 0x7008 → 0x702E → 0x702F`) | `0x229` | `+0x330` / ROM `0x7FF` | `0x01` = `Enabled` | Same reports; no ratio arithmetic in serializer |
| Memory P-state | `AMD CBS → UMC Debug Options → GDDR6 Debug Options → GDDR6 DRAM Controller Configuration → DRAM Power Options` (`0x7000 → 0x7008 → 0x702E → 0x7030 → 0x7032`) | `0x25E` | `+0x36D` / ROM `0x83C` | `0xFF` = `Auto` | `docs/research/2026-09-20-clv-sync-stage2-memory-pstate.md` |
| FCLK_DPM | `SMU Debug Options → SMU Features` (`0x7009 → 0x703E`) | `0x7045` | `+0x6A3` / ROM `0xB72` | `0x0F` = `Auto` | Exact CLV menu map and serializer evidence |
| DF Clock Override control | `SMU Debug Options → SMU Debug` (`0x7009 → 0x703F`) | `0x37D` | `+0x703` / ROM `0xBD2` | `0x01` = `Manual` | Exact CLV menu map |
| DF Clock Override value | Same `SMU Debug` path | `0x37E` | `+0x704` / ROM `0xBD3..0xBD4`, little-endian u16 | `0x058C` = `1420` | Numeric bounds `[0,2000]`; no direct IFR default opcode |

The static serializer ownership map is currently:

`+0x316 → $INV 0x11ED`, `+0x330 → 0x1204`, `+0x368 → 0x1237`, `+0x36D → 0x123C`, `+0x6A3 → 0x1331`, `+0x703 → 0x1373`, `+0x704 → 0x1374`.

### Not established

- `1800MHz` is a stored/menu request, not a measured physical MCLK.
- `UclkDiv1M0=Enabled` is not a decoded `/1` ratio and does not prove UCLK=MCLK.
- `DF=1420` is not proven MHz and is not proven FCLK.
- Equal menu values, equal Linux metrics, POST success, or lower latency do not prove physical `MCLK:UCLK:FCLK=1:1:1`.
- No current board readback establishes that the present board contains plain CLV or the latest W11 snapshot.
- Memory training, applied clocks, synchronous crossing, voltage, stability, and performance improvement are all unrun.

The exact CLV UI even warns that FCLK should be greater than UCLK and Memory P-state disabled. That is UI guidance, not an executed training rule and not a 1:1:1 recommendation.

## 2. Operator baseline: B1800, not “1800 MHz measured”

The useful control condition is **B1800**: the identified board already running the unchanged, read-back-confirmed baseline with the native `Memory Clock Speed=0x24` request. The donor byte alone cannot establish B1800 on the user board.

Before any later setting test, capture and preserve, read-only:

1. Board identity and target PCI ID `1002:13fe`; reject a workstation/non-target GPU.
2. Current full-chip/recovery image path and SHA-256, if a current read is authorized.
3. BIOS version/date, kernel, amdgpu/firmware identifiers, and power/cooling conditions.
4. Read-only NVRAM/Setup values for all six clock fields above and all voltage controls.
5. POST/display/boot/training observations and error counters.
6. Two idle runtime snapshots at least 10 seconds apart using the existing filtered route in `docs/runbooks/2026-09-20-oc-stock-capture.md`.

If the current board is not already in the requested baseline state, do not change it merely to manufacture a baseline. Mark B1800 `NOT_ESTABLISHED` until the operator-authorized capture exists.

The latest saved board snapshot in the project is W11 (`3c50bc9a…`), not plain CLV; it is historical and not current-state proof. Plain CLV is the offline development TARGET, not a claim about installed firmware.

## 3. Native-menu diagnostic order (not a final profile)

If a later operator-approved live test is performed, start each test from a recorded B1800 state, change **one logical field**, save/reset, read back the field, and restore B1800 before the next test. This order is diagnostic only:

| Test | One field | Allowed interpretation |
|---|---|---|
| T1 | Memory Clock Speed `+0x316` | Request persistence/boot outcome only; not physical MCLK |
| T2 | UclkDiv1M0 `+0x330` | Persistence and boot outcome only; `Enabled` is not `/1` proof |
| T3 | FCLK_DPM `+0x6A3` | Persistence/callback/boot outcome only; not measured FCLK |
| T4 | Memory P-state `+0x36D` | Diagnostic persistence/boot outcome only; no training-safety recommendation |
| T5 | DF control `+0x703` | Control persistence only; leave `+0x704` unchanged |
| T6 | DF value `+0x704` | Only after its control state is already recorded; value is a request, not a unit/frequency proof |

Do not combine a control and value change and call it one-variable. Do not copy historical files named `SYNC_Full_1to1to1_*` as recipes; their names are not hardware results and some contain unsupported native enum values.

### NOT READY profile

There is intentionally **no final value set** for UclkDiv1M0, Memory P-state, FCLK_DPM, DF control/value, or any voltage field. The following profile is not ready to flash or recommend:

- `1800 / 1800 / 1800`: **not defined**; no common unit or physical mapping exists.
- `UclkDiv1M0=Enabled`: **not a synchronization setting** until its consumer/divider meaning is proven.
- Memory P-state `Disabled`: **not recommended**; its training effect is unresolved.
- FCLK_DPM `Disabled/Enabled`: **not recommended**; precedence and application are unresolved.
- DF `1420`, `1800`, or any other numeric value: **not a proven frequency**.
- SoC `1.15 V`: **unset**; no safe or applied electrical path has been proven.

The current first offline technical gap is the caller/input-object construction for exact ABL1 memory-policy function `0x95FC`, especially producers of `[SP+0x164]` and `[SP+0x174]`, and any link from `$INV 0x11ED` to that context. The latest verifier established branch behavior only (`47/47 PASS`).

## 4. Voltage interpretation and stop boundary

### SoC is a separate rail question

The imported GenCAD lead identifies a candidate PUS1 Richtek RT8237E path to `+VDDCR_SOC`, with separate enable and feedback nets. The same CAD is marked `REVISION "NA"`; it is not proof that the operator's physical board has that revision or population. PUA1/ISL69247 evidence concerns core/GFX stages and must not be substituted for SoC.

### Firmware fields are not a voltage recipe

- `AmdSetup +0x6E5/+0x6E6` (`VDDCR_VDD` offset control/value) and the sibling GFX offset fields are unresolved/inert in the current firmware consumer trace; no SoC conversion exists.
- Separate `Setup` fixed-voltage fields are distinct: VCORE `+0x1C9/+0x1CA`, GFX `+0x1CD/+0x1CE`, MEMIO `+0x1D1/+0x1D2`. Static PEIMs stage controller transactions, but PEI dispatch, controller/page semantics, physical rail identity, and applied voltage are unverified.
- UI ranges/options such as VCORE/GFX `700..1250 mV` or MEMIO `1.20..1.45 V` are not electrical limits or recommendations.
- Runtime words `1275/912` are firmware telemetry with unresolved channel-to-rail mapping, not an external SoC measurement.
- The historical “1.2-something” report followed manual VRM feedback modification and is outside the current constraint; it is not a recipe or safety evidence.

**Current voltage decision: no voltage change.** A physical SoC claim requires board revision/markings, revision-matched rail/net mapping, exact controller semantics, PEI dispatch evidence, and independent electrical readback. None is complete.

## 5. Practical baseline and latency/bandwidth protocol (planned; not executed)

The reviewed protocol in `docs/research/2026-09-21-latency-protocol-reviewed.md` is the measurement source. This section is an operator run plan, not a result.

### Preconditions

- Use an identified target board with PCI ID `1002:13fe`; do not use local/workstation GPU data.
- Establish B1800 first, with current image/NVRAM readback and recovery available.
- Keep voltage, timings, CPU/GPU clocks, kernel, driver, PMFW, cooling, CPU affinity, and workload fixed.
- Use a private disposable directory (`umask 077; RUN_DIR=$(mktemp -d /tmp/bc250-latency-XXXXXX)`). Do not collect hostname, command line, credentials, or full journals.
- A future `SYNCCAND` is **not runnable** until it has exact source/output identity, structural review, recovery/readback, boot acceptance, and explicit approval. This draft contains no SYNCCAND.

### Workloads and repetitions

Run three cold boots per condition and five identical trials per boot (15 trials per condition), followed by a separate rollback control. On every boot capture target identity, BIOS/image identity, all six Setup fields, POST/training, temperatures, and errors.

Use the existing harness only after root verifies/integrates it:

```sh
python3 scripts/measure_bc250_perf.py run \
  --label B1800-b1 --method c --cpu N --repeats 5 \
  --out "$RUN_DIR/B1800-b1.json" \
  --notes 'B1800; boot 1; unchanged control'
```

Repeat for `B1800-b2/b3` and, only when accepted, `SYNCCAND-b1/b2/b3`. Compare matched pairs with:

```sh
python3 scripts/measure_bc250_perf.py compare \
  "$RUN_DIR/B1800-b1.json" "$RUN_DIR/SYNCCAND-b1.json" \
  --out "$RUN_DIR/compare-b1.json"
```

W1 is the dependent-load latency proxy; W2 is host-memory `memcpy` bandwidth; W3 is a CPU ALU control. They do not measure GPU VRAM bandwidth. W4 is optional and only uses an already-installed deterministic GPU workload with fixed scene/configuration and read-only target telemetry. If no deterministic workload/telemetry is already available, W4 is `UNRUN`; do not install one as part of this draft.

The current harness records helper **source** identity but deletes its temporary executable. Record compiler path/version and helper/script hashes; mark `same_binary=UNPROVEN` unless a separately approved harness change retains and hashes the executable.

### Analysis and verdicts

Preserve every raw trial. Report per-boot medians, aggregate median, Q1/Q3/IQR, min/max, and raw values. Calculate deltas only after valid data exist:

`delta_percent = 100 × (median_SYNCCAND − median_B1800) / median_B1800`

The reviewed policy uses a 5% latency-improvement threshold plus sample separation and no bandwidth/cache/error/thermal regression; a 2% band can classify no effect. These are decision thresholds, not promises. Missing or invalid controls produce `INCONCLUSIVE`.

Performance and synchronization are separate verdicts. `PHYSICAL_1TO1TO1_PASS` requires independent MCLK/UCLK/FCLK measurements, documented common reference and GDDR6 conversion, and divider/crossing evidence. Equal software metrics, BIOS labels, or a benchmark improvement remain `INCONCLUSIVE` for synchronization.

## 6. Rollback and stop conditions (planned; not executed)

### Settings-only rollback

1. Restore every changed field to the exact B1800 value recorded before that test.
2. Save/reset and re-read all six fields.
3. Cold boot and verify POST/display/OS/error/temperature state.
4. If a field will not restore, stop; use the board's documented CMOS/NVRAM reset procedure and re-read fields. Do not compensate with voltage or another profile.

### Firmware-image rollback

If a later experiment changes SPI firmware, it requires a separate approved transaction: preserve a complete known-good dump, verify candidate/source/output hashes and structure, flash only the approved hash, perform a full independent readback, then cold-boot and verify. The plain CLV source remains untouched. A no-POST or unstable result stops escalation and uses the prevalidated external-programmer recovery path; do not improvise a partial image.

### Stop rules

Stop on missing target PCI identity, missing recovery, training loop, no POST/display/OS, unexpected voltage, corrected/uncorrected errors, thermal alarm, GPU reset, or abnormal harness exit. Preserve the failure and do not retry the same method three times without changing method class.

## 7. Requirement-to-evidence matrix

| User requirement | Current result | Missing evidence before claim |
|---|---|---|
| Preserve base memory speed / 1800 request | **PASS, saved bytes only:** CLV `+0x316=0x24` label `1800MHz`; latest W11 readback also stores `0x24` | Current board NVRAM/readback and physical MCLK |
| Physical MCLK:UCLK:FCLK 1:1:1 | **NOT READY / UNPROVEN** | ABL1 caller/input mapping; consumer/actuator; units/conversion; independent clocks/divider/crossing; training repetitions |
| UclkDiv1M0 semantics | **STATIC UI only:** `Enabled=1`; no ratio arithmetic | Downstream consumer and divider meaning |
| Memory P-state/training | **STATIC UI/serializer only:** `Auto=0xFF` | Consumer, precedence, training and fallback evidence |
| FCLK_DPM / DF override | **STATIC stored requests only:** Auto / Manual+1420 | Actual reader/actuator, units, precedence and training relation |
| SoC 1.15 V | **NOT SET / NOT SAFE CLAIM** | Revision-matched rail mapping, controller semantics, PEI dispatch, independent electrical measurement |
| Core/GFX separation | **STATIC boundary:** PUA1/ISL69247 evidence is separate from PUS1/RT8237E CAD lead | Physical board/revision and net/page mapping |
| Latency/bandwidth improvement | **UNRUN:** historical screenshots are uncontrolled and voltage-confounded | B1800/SYNCCAND controlled 3×5 trials, raw data, environment/error/thermal records |
| Rollback | **Procedure defined, not executed in this draft** | Future exact candidate approval, readback and recovery transaction |

## Additional ABL1 heap-populator evidence — static only (independent verifier)

The selected ABL1 heap-populator verifier was independently executed in a disposable copy; status: `PASS`, check summary: `{"status": "PASS", "checks": {"passed": 34, "failed": 0, "total": 34}}`. Evidence was persisted at `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260921-heap-populator-independent-verify-155804-3347325` (manifest `SHA256SUMS.final`).

The verifier checks the ABL1 heap miss/population flow: selector case key 0xA04E, descriptor miss to 0x6238, node-key write and payload copy via 0x6B78, source pointer outer_object_R1+0x864, and constructor initialization of outer+0x864 to 0x006CD4D0. Those 34 checks cover the static provider-source pointer/heap copy bytes only; they do not establish what the pointed-to data contains, whether the outer object is populated from APOB or $INV 0x11ED, ABL1 runtime execution, an SMU actuator, physical clocks, training, or applied frequency.

Missing join: identify the producer/meaning of the outer ABL1 object R1 entering 0xB84/0xBD2, and prove whether outer+0x864/0x006CD4D0 is sourced from APOB service 0x9E3B14C (message 0x61, argument 0xFF), native $INV 0x11ED, or another runtime source. Do not follow the concurrent apob_abl_handoff, memory-clock item-0x17, or SMU-selector traces here.

This evidence does not change the `NOT READY` profile, assign units, or establish physical MCLK/UCLK/FCLK, training, voltage, or a performance improvement.

## 8. Current status

- **Proven:** plain CLV source identity; static HII paths/QIDs/offsets/options; saved CLV request bytes; static serializer ownership; bounded ABL1 branch behavior.
- **Historical only:** W11 board snapshot, P5.00 screenshots, 131.4 ns/141.7 ns AIDA64 values, manual feedback/“1.2-something” report.
- **Not ready:** any final equal-1800 profile, physical 1:1:1 claim, SoC 1.15 V setting/safety claim, performance improvement, or hardware acceptance.
- **Next offline action:** bind ABL1 `0x95FC` caller/input construction and classify producers of `[SP+0x164]`/`[SP+0x174]`; do not build a candidate until the semantic/migration gates close.

This document is a practical evidence draft, not completion of the user's requested guide and not permission to flash or apply voltage.
