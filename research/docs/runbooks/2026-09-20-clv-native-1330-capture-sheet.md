# BC-250 CLV native 1330 capture sheet

Use this sheet while manually testing the native BIOS profile. It is not permission to flash a ROM.

## Identity and recovery

- Board identity: __________________________
- BIOS version: ____________________________
- Recovery dump path/hash: _________________
- Date/time: _______________________________

## Baseline B0 (before changing anything)

| Field                     | BIOS value | NVRAM/readback value | Notes |
| ------------------------- | ---------- | -------------------- | ----- |
| Memory Clock Speed        |            |                      |       |
| UclkDiv1M0                |            |                      |       |
| Memory P-state            |            |                      |       |
| FCLK_DPM                  |            |                      |       |
| DF Clock Override Control |            |                      |       |
| DF Clock Override         |            |                      |       |
| Voltage offsets           |            |                      |       |

- POST/display: ____________________________
- OS boot: __________________________________
- Baseline latency/workload: _______________

## T1330 requested values

```text
Memory Clock Speed        = 1330 MHz
UclkDiv1M0                = Enabled
Memory P-state            = Disabled
FCLK_DPM                  = Disabled
DF Clock Override Control = Manual
DF Clock Override         = 1330
Voltage offsets            = unchanged / Auto
```

Record after Save + cold boot:

- All six values persisted: YES / NO
- POST/display: ____________________________
- Training/boot message: ___________________
- OS boot: YES / NO
- Any fallback or corrected-error indication: ___________________
- Latency/workload, run 1: _________________
- Latency/workload, run 2: _________________
- Latency/workload, run 3: _________________
- Independent MCLK measurement: ____________
- Independent UCLK measurement: ____________
- Independent FCLK measurement: ____________

## Rollback

Restore every B0 value, save, cold boot, and record:

- All B0 values restored: YES / NO
- POST/display: ____________________________
- OS boot: YES / NO
- Latency/workload: ________________________

## Classification

- `STORED_REQUEST_PASS`: values persist and POST/OS boot completes.
- `BOOT/TRAINING_FAIL`: value loss, POST failure, training failure, or recovery required.
- `PHYSICAL_1TO1TO1_PASS`: only if MCLK, UCLK and FCLK are independently measured with a documented reference/conversion and remain equal across repeated cold boots.
- `INCONCLUSIVE`: settings persist and system boots, but independent domain measurements are absent.

The current driver metrics are aliased and do not by themselves fill the three independent measurement fields.
