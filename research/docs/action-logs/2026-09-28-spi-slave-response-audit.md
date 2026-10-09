# SPI-slave response-path audit

## Intent

Date: 2026-09-28. Scope: read-only source audit to continue the approved
software-only single-flash prototype. Determine whether the checked-in RP2350
PIO sources or local Pico SDK prove a timely first MISO bit, and inventory
existing P3.00 images for a possible offline model pair. No source code,
firmware image, or build output will be changed. No device upload, reset,
GPIO activity, BC-250 connection, or flash operation.

Inputs: the local Pico SDK CYW43 PIO SPI master, `toctou-rig-v001` PIO/C
sources, the approved single-flash plan, P3.00 stock `dump/2.bin`, and existing
candidate manifests/action logs. Hashes will be checked only for the candidate
pair under consideration. Any timing result is a static instruction-level
inference, not a measured clock waveform.

## Result

- Local Pico SDK search found no PIO SPI-slave sample. The only SPI PIO
  implementation found is the CYW43 bus driver and is a controller/master
  transfer loop.
- `toctou-rig-v001/src/spihack.c` loads `spi_inject_program`; it does not load
  `miso_proxy_program`. In `miso_proxy.pio`, the passthrough branch waits for
  the rising clock edge, samples flash DO, then executes `mov pins, isr`.
  Under the program's unverified mode-0 assumption, that changes MISO after
  the master's rising-edge sample point. It is therefore not evidence of a
  timely transparent proxy. The injection branch reads preloaded FIFO data
  and issues `out pins, 1` before waiting for the next rising edge; this is a
  plausible distinct response path, but its first-bit timing and electrical
  behavior are not measured.
- The old rig's C setup configures `spi_trigger`'s `jmp pin` source as
  `pin_mainboard_cs`, and the PIO parser uses that pin to frame transactions.
  This establishes source-level intent only; it does not validate the rig or
  make its wiring compatible with the no-modification constraint.
- Exact P3.00 bytes were hashed: `dump/2.bin` is stock SHA-256
  `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`.
  The local `BC250_P3.00_gasket-spoof-vcn_v001.bin` candidate is
  `6a7feaae555fff67cb15b394e873458fc9153c0984d003b5c5e75f3c7450b07c`;
  its own action log records a failed boot and explicitly says not to flash.
  It is a same-lineage negative fixture, not a selected TOCTOU target.
- An offline invocation of the existing host model was tried with that pair
  and a synthetic one-read stock window. It printed that the first modeled
  response matched stock and the next matched the candidate. The terminal
  timed out before recording an exit status, so this is not counted as a
  passing test. No durable serve-map was created; read ordering remains
  synthetic and is not inferred from PSP behavior.
- A bounded rerun with assertions against the exact source bytes printed both
  model checks as `PASS`, then the terminal timed out before an exit status was
  captured. Treat this as observed model output, not a completed passing test.
  No repository code or image was changed by either model run.

## Decision

The first-MISO uncertainty is narrowed, not closed: preloaded PIO injection
may be viable while the existing clock-edge passthrough is late under mode 0.
The next admissible step is offline only: add a bounded model test for a
hash-pinned same-lineage stock/candidate pair and keep its read order explicitly
synthetic. Do not use the failed gasket-spoof candidate as a real attack target.
Actual first-bit timing, the proper candidate pair, stock-flash isolation, and
any BC-250 connection remain unresolved.
