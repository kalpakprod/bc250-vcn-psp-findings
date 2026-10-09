# Exact CLV native BIOS menu guide for a diagnostic 1:1:1 investigation

Current: exact CLV donor / static HII-IFR menu map / diagnostic procedure only / no field combination is justified as physical `MCLK=UCLK=FCLK`.

## Conclusion

The exact CLV HII package exposes the requested controls and their `AmdSetup` storage locations. If a control is visible on the identified board and recovery is prepared, a user can try it in the native Setup browser, save, reset, and read the value back. This is a **diagnostic menu guide**, not a final `1:1:1` recipe.

No exact field combination is currently justified as a proven physical `1:1:1` configuration. The native gate remains blocked at the consumer/actuator, common-unit/rate-conversion, `UclkDiv1M0` ratio, FCLK-DPM precedence, and memory-training crossings. Equal-looking menu numbers, a saved NVRAM byte, a successful POST, or the historical filename `SYNC_Full_1to1to1_*` is not physical-clock proof.

The exact current donor values below are ROM-stored `AmdSetup` requests. They are not a live board readback and must not be assumed to be the operator's current NVRAM state.

## Pinned evidence and direct check

- Donor: `/home/OWNER/orca/projects/bc250/evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`
- Donor size: `16,777,216` bytes
- Donor SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`
- Extracted HII module: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260919-inv-token-consumers/CbsSetupDxe-7ff717d51c9a.bin`
- Module SHA-256: `7ff717d51c9a447c6954c63b633cf836f1e4396c2b01f4bf590268a60ac1d0d8`
- Existing parser: `/home/OWNER/orca/projects/bc250/archives/imported/historical-bios-repo/legacy-bc250-bios/tools/uefi/e1_ifr_dump.py`
- Existing exact verifier: `/home/OWNER/orca/projects/bc250/evidence/firmware-audit/20260920-df-init-route/menu-verify.py`
- Fresh read-only verifier invocation: `python3 -B <temporary-copy-of-menu-verify.py>` from the project root
- Observed verifier exit: `0`; stdout status: `PASS`; stderr: empty
- Existing `menu-result.json` hash before and after the disposable rerun: `6e2d1978f7dcfdb4e780b220503d1a14401cb34c9d65104ca98840a47e2af14a`

Static evidence classes are `observed-bytes` and `static-analysis`. No BIOS browser, NVRAM save/readback, training, clock counter, voltage, or hardware action was run for this guide.

Native-gate sources used for the conclusion:

- `docs/research/2026-09-20-native-gate-candidate-readiness.md` — readiness verifier `67/67`; fields/serializer static, consumer, units, ratio, precedence, training, and build gates remain blocked.
- `docs/research/2026-09-20-clv-sync-configuration-domain-matrix.md` — final `44/44` exact field/domain matrix; UI numeric overlap is not semantic support.
- `docs/research/2026-09-20-clv-sync-frequency-unit-discrimination.md` — `11/11` host check; FCLK/MCLK/UCLK exports are a software alias, not independent physical clocks.
- `docs/research/2026-09-20-clv-sync-stage2-uclk-semantics.md` — `31/31` bounded serializer check; no ratio arithmetic in the native path.
- `docs/research/2026-09-20-clv-sync-stage2-memclk-consumer.md` — `12/12`; memory-init consumer/training edge remains missing.
- `docs/action-logs/2026-09-20-clv-sync-native-gate-audit.md` — native gate matrix `BLOCKED` (`3 PASS / 1 PARTIAL / 6 BLOCKED / 2 UNRUN`) and no candidate build.

Scope clarification: the earlier UEFITool-boundary report says “five questions” because it predates the supplemental Memory P-state audit. This guide's operator scope is **six controls**: Memory Clock Speed, UclkDiv1M0, Memory P-state, FCLK_DPM, DF Clock Override Control, and DF Clock Override (Value). The package-local paths below are known static HII paths; they are not proof that a live Setup browser displays them. UEFITool remains structural extraction only and is not a menu/NVRAM editor or an operator route.

## Native menu map

All listed controls use VarStore `0x5000` (`AmdSetup`), are marked editable in IFR metadata, and have `RESET_REQUIRED`. Package-local decoded conditional scopes are empty. `0x7007` and `0x7009` have no incoming `REF` in this package, so live Setup-browser visibility remains unrun.

| Control                       | Native package-local path                                                                                                                                     |      QID | `AmdSetup` field                |   Absolute ROM | Donor stored byte/value   | IFR default and options                                                                                                                                                                                                                                                                                   |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------: | ------------------------------- | -------------: | ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Memory Clock Speed**        | `0x7007 UMC Common Options` -> `0x7028 GDDR6 Common Options` -> `0x702A DRAM Timing Configuration` -> `0x702C I Accept`                                       |  `0x20F` | `+0x316` (`u8`)                 |        `0x7E5` | `0x24` / `36` (`1800MHz`) | Default `Auto=0xFF`; `125=0x02`, `225=0x04`, `250=0x05`, `400=0x08`, `450=0x09`, `500=0x0A`, `750=0x0F`, `850=0x11`, `1000=0x14`, `1250=0x19`, `1330=0x1A`, `1375=0x1B`, `1500=0x1E`, `1600=0x20`, `1650=0x21`, `1700=0x22`, `1750=0x23`, `1800=0x24`, `1850=0x25`, `1900=0x26`, `1950=0x27`, `2000=0x28` |
| **UclkDiv1M0**                | `0x7000 AMD CBS` -> `0x7008 UMC Debug Options` -> `0x702E GDDR6 Debug Options` -> `0x702F GDDR6 DRAM Timing Configuration`                                    |  `0x229` | `+0x330` (`u8`)                 |        `0x7FF` | `0x01` / `1` (`Enabled`)  | Default `Auto=0xFF`; `Enabled=0x01`. `Enabled` is an enum label, not a decoded divider ratio.                                                                                                                                                                                                             |
| **Memory P-state**            | `0x7000 AMD CBS` -> `0x7008 UMC Debug Options` -> `0x702E GDDR6 Debug Options` -> `0x7030 GDDR6 DRAM Controller Configuration` -> `0x7032 DRAM Power Options` |  `0x25E` | `+0x36D` (`u8`)                 |        `0x83C` | `0xFF` / `255` (`Auto`)   | Default `Auto=0xFF`; `Enabled=0x01`; `Disabled=0x00`                                                                                                                                                                                                                                                      |
| **FCLK_DPM**                  | `0x7009 SMU Debug Options` -> `0x703E SMU Features`                                                                                                           | `0x7045` | `+0x6A3` (`u8`)                 |        `0xB72` | `0x0F` / `15` (`Auto`)    | Default `Auto=0x0F`; `Disabled=0x00`; `Enabled=0x01`. Flags include `CALLBACK`.                                                                                                                                                                                                                           |
| **DF Clock Override Control** | `0x7009 SMU Debug Options` -> `0x703F SMU Debug`                                                                                                              |  `0x37D` | `+0x703` (`u8`)                 |        `0xBD2` | `0x01` / `1` (`Manual`)   | Default `Auto=0xFF`; `Manual=0x01`                                                                                                                                                                                                                                                                        |
| **DF Clock Override (Value)** | same `0x7009` -> `0x703F` path                                                                                                                                |  `0x37E` | `+0x704` (`u16`, little-endian) | `0xBD3..0xBD4` | `0x058C` LE / `1420`      | Numeric bounds `[0, 2000]`, step `0`; no discrete option list and no direct IFR default opcode. A static callback branch can write `1000` as a side effect, but callback/browser execution and live persistence are unrun.                                                                                |

Canonical static serializer ownership is: `+0x316 -> $INV 0x11ED`, `+0x330 -> 0x1204`, `+0x36D -> 0x123C`, `+0x6A3 -> 0x1331`, `+0x703 -> 0x1373`, and `+0x704 -> 0x1374`. These are typed record handoffs, not proven clock-divider, PLL, training, or physical-domain actuators.

## Procedure (menu setting versus proof)

### 0. Recovery and baseline gate

1. Use only the authorized BC-250 target and confirm the board/BIOS identity. Do not use a donor filename as a live-board identity.
2. Preserve the known-good full SPI dump and recovery path. A BIOS menu save changes NVRAM, not the ROM image, but keep the prevalidated programmer/recovery path available before deliberately testing settings. If a firmware write or flash is contemplated later, two fresh full-chip reads, byte comparison, hashes, and explicit approval are separate mandatory gates. This guide does **not** authorize a flash.
3. Record the current Setup screen values and defaults for all six controls above. Capture the exact value shown, not only the label. The donor values are a reference, not a substitute for this readback.
4. Do not change voltage offsets, DRAM timing controls, CPU/GPU clocks, or unrelated CBS options in this experiment.
5. If a control is absent, do not install AMIBCP/UEFITool or force visibility in this route. Record `UNREACHABLE`; package-local lack of `REF` is not proof that AMITSE cannot expose it.

### 1. Baseline (`T0`, no setting change)

1. Enter Setup and photograph or transcribe all six fields.
2. Exit without changing anything. Record POST/display/boot outcome and the exact boot log available to the operator.
3. If a read-only NVRAM/AmdSetup dump is available, record the six field bytes and hash the dump. This is a saved-request check, not a clock check.

### 2. One-variable diagnostic order

Start every test from the same recorded baseline. Change **one logical field only**, save, reset, and record the result. Restore the baseline before starting the next test. For `DF Clock Override (Value)`, the one logical field is a `u16` and may change two bytes.

| Order | Test               | Only field changed     | Diagnostic input                                                                                                                                                                                                                                                                                                                                                       | Do not infer                                                                               |
| ----: | ------------------ | ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
|  `T1` | Memory request     | `+0x316`, QID `0x20F`  | One enumerated label from the table (for historical comparability, `1750MHz=0x23` may be recorded as a test point; it is not a safe recommendation)                                                                                                                                                                                                                    | The label is a physical MCLK value or accepted training point                              |
|  `T2` | UCLK control       | `+0x330`, QID `0x229`  | Select the option opposite to the recorded baseline (`Auto=0xFF` or `Enabled=0x01`)                                                                                                                                                                                                                                                                                    | `Enabled` means a `/1` ratio or synchronizes UCLK to FCLK                                  |
|  `T3` | FCLK DPM           | `+0x6A3`, QID `0x7045` | If baseline is `Auto`, test `Disabled=0x00`; otherwise test the baseline's other exposed enum                                                                                                                                                                                                                                                                          | Callback metadata or a DPM disable means FCLK is fixed at a measured value                 |
|  `T4` | Memory P-state     | `+0x36D`, QID `0x25E`  | Optional diagnostic flip to `Disabled=0x00` or `Enabled=0x01`, only with recovery ready                                                                                                                                                                                                                                                                                | The DF help phrase is an executed training rule; no Auto-to-Disabled enforcement was found |
|  `T5` | DF control         | `+0x703`, QID `0x37D`  | Test the other exposed control (`Auto=0xFF` or `Manual=0x01`) while leaving `+0x704` unchanged                                                                                                                                                                                                                                                                         | The numeric request is consumed or wins over FCLK_DPM                                      |
|  `T6` | DF numeric request | `+0x704`, QID `0x37E`  | If the recorded baseline `+0x703` is `Manual=0x01`, change only `+0x704` to one value in `[0,2000]` and record the exact `u16` readback. If baseline `+0x703` is `Auto=0xFF`, do **not** change the control in this one-variable order; mark T6 `NOT_RUN` or `persistence-only`. A combined control-plus-value change is a separate multi-variable hypothesis, not T6. | The UI number shares units with the MCLK labels or names FCLK                              |

For each runnable test: enter the exact value; save and reset; confirm the BIOS returns; record the field after reset; boot the controlled OS if available; record training/boot errors, POST/display state, and stability; then cold reboot and repeat the saved-value readback. A value that does not persist is a menu/NVRAM failure, not a clock result. If a test is `NOT_RUN` because its prerequisite control would require a second change, preserve that status rather than silently combining variables.

### 3. Historical stored-request comparisons (optional, not recipes)

The retained archive includes images named `SYNC_Full_1to1to1_1333MHz` and `SYNC_Full_1to1to1_1750MHz`. Their bytes are useful as comparison hypotheses only:

- Historical `1333` request: Memory Clock label/value `1330MHz=0x1A`, UclkDiv1M0 `Enabled=1`, FCLK_DPM `Disabled=0`, Memory P-state `Auto=0xFF`, DF control `Manual=1`, DF value `1333`.
- Historical `1750` request: Memory Clock `1750MHz=0x23`, UclkDiv1M0 `Enabled=1`, FCLK_DPM `Disabled=0`, Memory P-state `Auto=0xFF`, DF control `Manual=1`, DF value `1750`.

These are multi-field stored requests from historical images, not native-menu proof of physical `1:1:1`. The historical `FclkUclk_1to1_Mclk1750` image contains `UclkDiv1M0=0`, which is not one of the exact native menu options (`0xFF`/`0x01`); it is therefore not reproducible as a native menu recipe without an unsupported hidden value. Do not copy any historical profile wholesale, and do not call either filename a hardware result.

## Evidence and acceptance rules

### Per-test PASS / FAIL / INCONCLUSIVE

- **PASS — menu persistence only:** the requested QID/value is visible after save/reset, a read-only NVRAM/AmdSetup dump matches the expected byte(s), and the board completes the recorded POST/boot path. This is still only a stored-request PASS.
- **FAIL — menu/boot:** value is not retained, POST/display fails, training or boot errors occur, or recovery is required. Preserve the exact screen/log and previous configuration hash.
- **INCONCLUSIVE — physical behavior:** the menu value persists and the board boots, but no independent domain-specific clock measurement exists. Driver telemetry is insufficient here: retained host evidence aliases FCLK/MCLK/UCLK to one software `MemclkFrequency` metric.

### Requirements for a physical `1:1:1` PASS

All of the following must be observed on the identified board, with baseline and readback:

1. Saved `AmdSetup` bytes match the intended test and survive reset/cold boot.
2. Memory training completes repeatedly; no hidden fallback, P-state change, or corrected-error signature invalidates the observation.
3. MCLK, UCLK, and FCLK are measured independently with domain-specific counters/probes, a common reference, and a documented GDDR6/rate conversion. The current project has not recovered an exact CLV UMC/DF/UCLK counter route; software aliases do not satisfy this requirement.
4. The measured ratios meet a predeclared tolerance at idle, load, and repeated cold boots. Equal UI numbers alone do not pass.
5. Stability/performance checks complete without recovery, and the exact saved configuration and post-test readback are archived.

If any item is missing, report `INCONCLUSIVE`, not `1:1:1 PASS`.

## Rollback and stop conditions

- Normal rollback: restore each changed field to the baseline value recorded before that test, save/reset, and verify the post-reset readback.
- If Setup is reachable but a value will not restore, use the board's documented CMOS/NVRAM reset procedure, then verify all six fields and the boot path.
- If the board no longer reaches Setup/POST, stop repeated boots; use the prevalidated external programmer and known-good full recovery dump only under the project flash/recovery gate. Do not improvise a partial image or overwrite the sole dump.
- Stop after the first repeatable failure mode until its evidence is preserved. Three failures of the same method require a changed method class.
- No BIOS image or hardware state was changed by this guide; deleting this report/evidence is the only rollback for the documentation action.

## Status

- **PASS:** exact CLV source identity, HII/IFR menu paths, QIDs, VarStore, offsets, options/defaults, donor stored bytes, one-variable ordering, and evidence requirements.
- **PASS (static only):** field-to-`$INV` serializer ownership and the fact that the exact native path does not prove a clock/training actuator.
- **BLOCKED:** final consumer/actuator, common units/rate conversion, UclkDiv1M0 ratio, FCLK-DPM precedence, and training semantics.
- **UNRUN:** live Setup visibility, BIOS save/reset, NVRAM readback, firmware execution, training, physical clocks, voltage, performance, and hardware `1:1:1` acceptance.

This document is therefore a **diagnostic native-menu procedure**, not a final or safe `1:1:1` BIOS profile.
