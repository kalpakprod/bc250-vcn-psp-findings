# CLV native-menu 1:1:1 diagnostic recipe — H1750 hypothesis

Current: fresh exact HII verifier PASS / native-menu hypothesis only / no ROM or NVRAM change / physical synchronization unproven.

## Selected test point

Use the historical label **`1750MHz`** as a diagnostic point because the retained archive contains `SYNC_Full_1to1to1_1750MHz_StockCPU`. This filename and value are **not safe, supported, applied, or hardware-verified**. The recipe is a multi-field BIOS-menu hypothesis, not a final profile.

### H1750-native-help hypothesis

| Control                   | Native menu path                                                                                                                                      |      QID |   `AmdSetup` offset | Requested value                                                |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | -------: | ------------------: | -------------------------------------------------------------- |
| Memory Clock Speed        | `0x7007 UMC Common Options -> 0x7028 GDDR6 Common Options -> 0x702A DRAM Timing Configuration -> 0x702C I Accept`                                     |  `0x20F` |            `+0x316` | `1750MHz`, enum `0x23`                                         |
| UclkDiv1M0                | `0x7000 AMD CBS -> 0x7008 UMC Debug Options -> 0x702E GDDR6 Debug Options -> 0x702F GDDR6 DRAM Timing Configuration`                                  |  `0x229` |            `+0x330` | `Enabled=0x01`                                                 |
| Memory P-state            | `0x7000 AMD CBS -> 0x7008 UMC Debug Options -> 0x702E GDDR6 Debug Options -> 0x7030 GDDR6 DRAM Controller Configuration -> 0x7032 DRAM Power Options` |  `0x25E` |            `+0x36D` | `Disabled=0x00` for the native DF-help precondition hypothesis |
| FCLK_DPM                  | `0x7009 SMU Debug Options -> 0x703E SMU Features`                                                                                                     | `0x7045` |            `+0x6A3` | `Disabled=0x00`                                                |
| DF Clock Override Control | `0x7009 SMU Debug Options -> 0x703F SMU Debug`                                                                                                        |  `0x37D` |            `+0x703` | `Manual=0x01`                                                  |
| DF Clock Override (Value) | same `0x7009 -> 0x703F` path                                                                                                                          |  `0x37E` | `+0x704` (`u16 LE`) | `1750`, bytes `D6 06`                                          |

Leave voltage controls, timings, CPU/GPU clocks, and unrelated CBS controls unchanged. Do not flash a ROM or write NVRAM automatically from this document.

## Important dependency and contradiction

The exact DF help text says: **“When you try to override FCLK, please make sure FCLK > UCLK and Memory P-state is disabled.”** H1750 sets the Memory P-state to `Disabled` to satisfy the explicit menu precondition as a hypothesis, but the strict `FCLK > UCLK` relation conflicts with an equal-target `1:1:1` interpretation. In addition, `UclkDiv1M0=Enabled` is only an enum byte; no ratio is decoded. Therefore H1750 is internally a diagnostic hypothesis with an unresolved/possibly contradictory FCLK/UCLK requirement, not a coherent proven recipe.

The historical 1750 image reportedly leaves Memory P-state `Auto=0xFF`; setting `Disabled=0x00` here intentionally follows the native help text instead of copying that historical stored request. Static evidence finds no Auto-to-Disabled enforcement or training proof. If reproducing the historical bytes rather than testing the help precondition, record that as a separate `Memory P-state=Auto` hypothesis; do not combine both interpretations in one result.

## Manual procedure

1. Confirm the authorized board and current live BIOS/NVRAM values. Donor bytes are not current-board state.
2. Record a no-change baseline (`B0`): all six fields above, POST/display/boot, and a read-only NVRAM readback if available.
3. Navigate each exact path above. If a parent form is absent, mark `UNREACHABLE`; do not install an editor or force visibility.
4. Set the six requested values for H1750, save/reset, and read every field back after reset. This is a multi-field diagnostic test; it is not the one-variable UclkDiv1M0 discriminator.
5. Run the same controlled boot/training and workload capture for at least three cold boots. Use identical kernel, PMFW, driver, cooling, workload, capture interval, and run order.
6. Restore all six pre-test live values, save/reset, and verify rollback readback. Stop on POST/training failure and use the prevalidated recovery path; do not add voltage or another clock change.

## What each result means

- **Menu persistence PASS:** all six requested values survive reset and match readback. This proves only stored-request persistence.
- **Boot/training PASS:** repeated cold boots complete with no training/POST/error regression. This does not prove clocks.
- **Physical `1:1:1` PASS:** requires independent, domain-mapped MCLK/UCLK/FCLK measurements, documented GDDR6 conversion, a common reference, and a synchronous-crossing/divider status readback. The current driver metrics alias `MemclkFrequency`, and existing SMU queries report software state; they do not satisfy this gate.
- **INCONCLUSIVE:** settings persist/boot but only aliased metrics are available.
- **FAIL:** value loss, training/POST failure, instability, or recovery required.

No voltage value is part of H1750. `1.15 V` is not a validated safe ceiling and must not be inferred or entered from this recipe.

## Fresh verifier evidence

The existing exact native verifier was rerun read-only:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -B evidence/firmware-audit/20260920-df-init-route/menu-verify.py
```

Observed exit `0`, status `PASS`, stderr empty; existing `menu-result.json` pre/post SHA-256 remained `6e2d1978f7dcfdb4e780b220503d1a14401cb34c9d65104ca98840a47e2af14a`. The pinned donor remains `16,777,216` bytes, SHA-256 `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`.

No ROM, BIOS/NVRAM, guest, AMIBCP, voltage, frequency, or hardware change occurred. This artifact is a **static experimental menu hypothesis**, not a candidate ROM or hardware claim.
