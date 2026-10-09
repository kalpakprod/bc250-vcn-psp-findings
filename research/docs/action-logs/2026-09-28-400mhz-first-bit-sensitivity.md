# 400 MHz first-bit estimate sensitivity

## Intent

Date: 2026-09-28. Evaluate how the host-only first-bit deadline estimate
changes with the assumed edge-to-WAIT delay at the selected 400 MHz PIO
scenario. This is not a clock change or a hardware test. Do not change source
images or firmware, upload firmware, or interact with the BC-250.

Input model:

- `candidates/single-flash-emulator-v001/pio_timing.py`
  SHA-256 `52ad931bf80d8707026f4253368d5a6eb0a20d0c971c4cdfb3488c39364615da`

## Result

Using the model's explicit formula
`half SPI bit period - assumed edge-to-WAIT delay - 3 instruction cycles`,
the estimated remaining PIO cycles were:

| SPI clock | Assumed edge-to-WAIT | Estimated margin |
| --------: | -------------------: | ---------------: |
|    25 MHz |             0 cycles |        +5 cycles |
|    25 MHz |             2 cycles |        +3 cycles |
|    25 MHz |             4 cycles |         +1 cycle |
|    25 MHz |             6 cycles |         -1 cycle |
|    50 MHz |             0 cycles |         +1 cycle |
|    50 MHz |             2 cycles |         -1 cycle |
|    50 MHz |             4 cycles |        -3 cycles |
|    50 MHz |             6 cycles |        -5 cycles |

## Evidence boundary

This is host arithmetic, not a cycle-accurate RP2350 simulation or measured
GPIO timing. The edge-to-WAIT values are sensitivity inputs, not measured
synchronizer latency. The four-cycle default is not independently established.
PIO FIFO readiness, selector timing, pad delay, setup/hold time, actual SPI
mode/frequency, and first-MISO-bit timing remain unresolved.

No firmware was built or uploaded. No board was connected, signalled, reset,
or flashed.
