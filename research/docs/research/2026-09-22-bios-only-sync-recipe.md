# BIOS-only recipe: expose and test the native sync controls

Status: operator recipe, static-only. Do not call the result physical `1:1:1` until independent clocks and latency are measured.

## Candidate that adds the menu

`candidates/s3-drivers/BC250_5.00_clv_S3-DRV_v001.bin`

SHA-256:

`26c0634da2fbda7125ebf284241917af58b6c30149d18cca434e55a6ded873ab`

Static contents already verified in `docs/action-logs/2026-09-22-goal-s3.md`:

- six MeiMeiDXEv3 DXE drivers, including `Menu_Driver`;
- 57-byte Setup-unhide transplant from the 3.00 CHIPSETMENU image;
- PSP, BHD, APCB and outer FV structures preserved;
- no hardware write and no proof of Setup dispatch on the target board.

This is why we do not need to invent a second menu driver before testing the native controls. The menu is added by the existing MeiMeiDXE path, while the clock questions are native HII questions.

## BIOS paths and values

### 1. Memory clock

`UMC Common Options -> GDDR6 Common Options -> DRAM Timing Configuration -> I Accept`

- `Memory Clock Speed`
- QID `0x20F`
- `AmdSetup +0x316`
- native labels include `1330 MHz` (`0x1A`), `1650 MHz` (`0x21`), `1750 MHz` (`0x23`), `1800 MHz` (`0x24`)

For the first BIOS-only comparison use `1330 MHz` or the existing board value. Do not infer physical MCLK from the label alone.

### 2. UCLK relative-to-FCLK selector

`AMD CBS -> UMC Debug Options -> GDDR6 Debug Options -> GDDR6 DRAM Timing Configuration`

- `UclkDiv1M0`
- QID `0x229`
- `AmdSetup +0x330`
- `Auto = 0xFF`
- `Enabled = 0x01`

`Enabled` is the native enum. It is not yet decoded as a numeric `/1` ratio.

### 3. Memory P-state

`AMD CBS -> UMC Debug Options -> GDDR6 Debug Options -> GDDR6 DRAM Controller Configuration -> DRAM Power Options`

- `Memory P-state`
- QID `0x25E`
- `AmdSetup +0x36D`
- `Auto = 0xFF`
- `Enabled = 0x01`
- `Disabled = 0x00`

The DF help text asks for Memory P-state disabled when overriding FCLK. This is a menu precondition, not proof that disabling it is required for physical 1:1:1.

### 4. FCLK DPM

`SMU Debug Options -> SMU Features`

- `FCLK_DPM`
- QID `0x7045`
- `AmdSetup +0x6A3`
- `Disabled = 0x00`
- `Enabled = 0x01`
- `Auto = 0x0F`

Start with `Auto`. Do not use this field as an FCLK frequency value.

### 5. DF/FCLK numeric request

`SMU Debug Options -> SMU Debug`

- `DF Clock Override Control`
- QID `0x37D`
- `AmdSetup +0x703`
- `Auto = 0xFF`
- `Manual = 0x01`

Then:

- `DF Clock Override`
- QID `0x37E`
- `AmdSetup +0x704` (`u16` little-endian)
- numeric bounds `0..2000`

The menu help says: `FCLK > UCLK` and `Memory P-state is disabled`. That text conflicts with a literal equal-frequency interpretation, so do not call equal numeric entries `1:1:1` without measurement.

## First BIOS-only test order

Do not combine all controls on the first boot. Use the menu and save/reset after each state:

1. **B0 baseline**: photograph/read back all five fields, change nothing.
2. **B1 UCLK discriminator**: change only `UclkDiv1M0` from the current value to the other exposed enum. Leave MCLK, FCLK_DPM, DF control/value, Memory P-state, timings and voltage unchanged.
3. **B2 native sync hypothesis**: only after B1 is read back, set one MCLK label and the matching DF numeric request, set `UclkDiv1M0=Enabled`, and set `Memory P-state=Disabled` if following the menu help. Record this explicitly as a multi-field hypothesis.
4. **B3 optional lower-clock control**: use the native `1330 MHz` label as a lower stress comparison. The external 1650-MHz CMOS result is not the same BIOS control and must not be substituted silently.

After every state, read back the six fields after reset. If a field reverts, the recipe has failed at persistence and no clock conclusion is allowed.

## SoC voltage rule

Keep SoC at or below `1.15 V`. There is no confirmed BIOS field in the current evidence whose raw value maps to an absolute SoC voltage on this board revision. Do not use:

- `VDDCR_VDD offset` values `80` or `100` as `1.14/1.15 V`;
- `VMEMP Voltage Control` as SoC voltage;
- VCORE/GFX/MEMIO fields as SoC voltage.

If the menu lacks a real SoC field, the correct result is `not available in this BIOS`, not an invented offset encoding.

## What this proves and does not prove

It proves that the BIOS can expose native control questions through the existing MeiMeiDXE + Setup-unhide path. It does not prove that the BIOS applies physical clock domains or that `UclkDiv1M0=Enabled` means `/1`.

A physical `1:1:1` acceptance needs independent MCLK, UCLK and FCLK observations, a documented GDDR6 conversion, successful training, and repeated cold boots. No flash or hardware action is included here.
