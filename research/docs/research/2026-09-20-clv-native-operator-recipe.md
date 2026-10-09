# BC-250 CLV native BIOS operator recipe (1:1:1 attempt)

Status: **manual diagnostic recipe, not a claim of physical acceptance**.

Historical multi-field hypothesis, not the current first-test sequence or authorization for a board change. The later [one-variable native-menu guide](2026-09-20-clv-native-menu-1to1-guide.md) starts from a recorded baseline and changes one logical field per diagnostic test. The profile below has not been run or shown to produce physical `1:1:1`.

This is the shortest native BIOS sequence exposed by the pinned CLV HII/IFR map. It does not modify the ROM. Use it only after recording the current values and preserving the board recovery path.

## Baseline

ROM reference: `evidence/donor/retroweb-20260916/BC250_5.00_clv.bin`  
SHA-256: `ea5781049160ab3343fd8839bf0b745e9948e80dff9db96dca5438c268ca4cb8`

The ROM-stored values are not proof of the live board's NVRAM state.

## Menu sequence

### A. Memory request and UCLK selector

```text
Advanced
  -> AMD CBS
    -> UMC Debug Options
      -> GDDR6 Debug Options
        -> GDDR6 DRAM Timing Configuration
```

Set:

```text
UclkDiv1M0 = Enabled       (QID 0x229, AmdSetup +0x330, value 0x01)
Memory P-state = Disabled  (QID 0x25E, AmdSetup +0x36D, value 0x00)
```

`UclkDiv1M0` is an enum named “UclkDiv1 option, relative to FCLK”. The label alone does not decode the ratio.

### B. Memory clock request

```text
Advanced
  -> AMD CBS
    -> UMC Common Options
      -> GDDR6 Common Options
        -> DRAM Timing Configuration
          -> I Accept
```

Set `Memory Clock Speed` (QID `0x20F`, `AmdSetup +0x316`) to the selected test point. This historical multi-field draft used **1330 MHz** (`0x1A`) or **1750 MHz** (`0x23`) as comparison points only. These are not safety recommendations or current first-test instructions.

### C. FCLK/DF controls

```text
Advanced
  -> AMD CBS
    -> SMU Debug Options
      -> SMU Features
```

Set:

```text
FCLK_DPM = Disabled       (QID 0x7045, AmdSetup +0x6A3, value 0x00)
```

Then:

```text
Advanced
  -> AMD CBS
    -> SMU Debug Options
      -> SMU Debug
```

Set:

```text
DF Clock Override Control = Manual  (QID 0x37D, AmdSetup +0x703, value 0x01)
DF Clock Override         = same test number used for the comparison (QID 0x37E, +0x704)
```

The numeric field accepts `0..2000` and is a little-endian `u16`.

## Save/reset order

1. Change only the fields above; leave voltage, DRAM timings, CPU/GPU clocks and unrelated CBS options unchanged.
2. Save Setup and perform a full reset/cold boot.
3. Re-enter Setup and confirm all six values persisted.
4. If a value does not persist, classify the test as a Setup/NVRAM failure and restore the recorded baseline.
5. If POST, display or training fails, stop repeated boots and restore the baseline; do not flash this recipe.

## Important native warning

The native help text for both DF override fields says:

```text
When you try to override FCLK, please make sure FCLK > UCLK and Memory P-state is disabled.
```

Therefore this recipe is the closest **native attempt** at the requested mode, not a guarantee that the firmware's manual DF path permits exact equality. Do not infer `MCLK=UCLK=FCLK` from equal menu numbers.

## Rollback

Restore the six values recorded at baseline, save, cold boot, and verify readback. If Setup becomes inaccessible, use the board's documented CMOS/NVRAM recovery path. Do not flash a modified ROM for this test.

## Acceptance

A saved value and successful POST are only a stored-request PASS. A physical `1:1:1` result additionally requires independent live measurements of MCLK, UCLK and FCLK on the identified `1002:13fe` board. Current host metrics alias these domains and are insufficient.

## Historical first-test hypothesis (single profile, not current sequence)

The draft chose **1330 MHz**, not 1750 MHz, for its first manual attempt. This is a lower historical comparison point; no safety/stress inference. It is not a validated safe frequency.

```text
Memory Clock Speed         = 1330 MHz (QID 0x20F, +0x316 = 0x1A)
UclkDiv1M0                 = Enabled (QID 0x229, +0x330 = 0x01)
Memory P-state             = Disabled (QID 0x25E, +0x36D = 0x00)
FCLK_DPM                   = Disabled (QID 0x7045, +0x6A3 = 0x00)
DF Clock Override Control  = Manual (QID 0x37D, +0x703 = 0x01)
DF Clock Override          = 1330 decimal (QID 0x37E, +0x704 = 0x0532 LE)
Voltage offsets            = unchanged / Auto
```

This single profile is the **first native test**, not a guarantee of `MCLK=UCLK=FCLK`. If the firmware's own `FCLK > UCLK` warning is enforced, the profile may be rejected, altered by training, or result in a non-equal clock relationship. Record the post-reset values before any performance comparison.
