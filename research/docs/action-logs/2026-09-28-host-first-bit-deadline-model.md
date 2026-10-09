# Host-only first-bit deadline model

## Intent

Date: 2026-09-28. Add a small offline estimate for the first SPI mode-0 MISO
bit deadline based on the instruction order in the existing `spi_inject.pio`.
Do not change the PIO firmware, board profile, BIOS images, or Waveshare
workspace. Do not connect, signal, reset, or flash hardware.

Input PIO source:

- `candidates/toctou-rig-v001/pio/spi_inject.pio`
  SHA-256 `02bf02eaaefb43d675bff294a6c74d80c067c1d63196760d24a1df8bff37733a`

Added files:

- `candidates/single-flash-emulator-v001/pio_timing.py`
  SHA-256 `52ad931bf80d8707026f4253368d5a6eb0a20d0c971c4cdfb3488c39364615da`
- `candidates/single-flash-emulator-v001/tests/test_pio_timing.py`
  SHA-256 `edbf81f6f7fc141e8586fd68abac8ac3198f9b213008a71f69f35fa7c232e65a`
- `candidates/single-flash-emulator-v001/README.md`
  SHA-256 `17d97532ed2a5df15cf0e7c22afd66ee150f7580a15e0111ab80eeb000b76fe6`

## Model and assumptions

The host-only function computes:

`half SPI bit period in PIO cycles - assumed edge-to-WAIT delay - 3 PIO instruction cycles`

The three instruction cycles represent `jmp x--`, `set x`, and the first
`out pins` in the data loop. The edge-to-WAIT delay defaults to four cycles,
an explicit estimate that includes synchronizer, sampling phase, and WAIT
detection. The RP2350 SDK describes a two-flip-flop GPIO input synchronizer,
but the exact phase and edge-detection latency are not measured here.

With these assumptions, the calculated margin is +1 cycle at 400 MHz PIO /
25 MHz SPI, -3 cycles at 400 MHz / 50 MHz, and -5.5 cycles at 150 MHz /
50 MHz. Positive margin is not treated as a pass threshold.

The function does not simulate PIO execution, FIFO/autopull readiness, selector
timing, chip select, electrical setup/hold, clock jitter, pad delays, or actual
bus mode/frequency. The old `spi_inject` source also checks its selector at
chip-select assertion, while `spi_trigger` only determines an address match
after reading the header. Whether these separate programs can select
injection for the same transaction remains unresolved.

## Validation and boundary

- Candidate unit tests, including five deadline/argument tests: exit 0.
- Project contour test (`make test`): exit 0.
- Scoped Procoder check on the model, tests, README, and this log: exit 0;
  4 target files clean, 0 unformatted, 0 unchecked, 0 out of scope, 473
  repository-wide hygiene findings, and 0 blocking findings.
- No firmware target was built. No board was connected, signalled, or flashed.

This is host-side arithmetic only, not a cycle-accurate RP2350 simulator and
not evidence of first-bit hardware timing. Actual SPI mode, frequency,
selector behavior, and MISO setup remain unverified.
