# Host-side selector queue model

## Intent

Date: 2026-09-28. Add the smallest offline model that reproduces the legacy
TOCTOU PIO selector/filter ordering already traced in
`2026-09-28-toctou-selector-queue-trace.md`. The model will represent
transaction-start addresses, the ordered address/state filters, selector state
sampled at CS-low, and the later filter update. It will not emulate electrical
timing, MISO bits, DMA, flash release, SPI traffic from the BC-250, or firmware.

Target files:

- New `candidates/single-flash-emulator-v001/pio_selector_model.py`
- New `candidates/single-flash-emulator-v001/tests/test_pio_selector_model.py`
- Small status note in `candidates/single-flash-emulator-v001/README.md`

Required synthetic case: filters `S -> true`, `S -> true`, `E -> false`;
transactions `S`, `S`, another address, `E`, another address; initial selector
low. Expected injector choices are pass-through, inject, inject, inject,
pass-through. This is a host control-flow test, not a hardware claim.

No edits to `candidates/toctou-rig-v001/`, BIOS images, firmware binaries, or
board state. After implementation, run candidate unit tests, `make test`, and
scoped Procoder on only the changed paths.

## Result

Implemented the host-only selector trace and two tests. The synthetic `S`, `S`,
other, `E`, other sequence yields pass-through, inject, inject, inject,
pass-through. A second test confirms that only a matching `0x03` transaction
start consumes the next filter. README states the control-flow-only boundary.

- Candidate suite: 21 tests, exit code 0.
- `make test`: 7 checks, exit code 0.
- Scoped Procoder: 4 changed paths clean, 0 unformatted, 0 unchecked,
  0 out of scope, 473 repository-wide hygiene findings, 0 blocking findings;
  exit code 0.
- `pio_selector_model.py` SHA-256:
  `954b426ee0d1271236b13404e244a5238b0424ccb949c9d5fff59dd5d5f65f13`
- `tests/test_pio_selector_model.py` SHA-256:
  `4888ced5e56ee4e675cfb45f42b2711457975a8666f50abd673754c42b87fe89`
- `README.md` SHA-256:
  `2c42ec003e72da39f335b54f7a86c21dbbdc1803bf59cf33a2c2774a0c6e2b68`

The model does not simulate payload contents, bit timing, DMA/FIFO stalls,
flash isolation, or electrical behavior. It does not establish actual PSP
transaction order or make the legacy firmware suitable for hardware.
