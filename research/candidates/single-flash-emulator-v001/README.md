# Single-flash emulator software prototype

This candidate contains an offline sparse-image packer, a host model for
synthetic `0x03` SPI reads, and a build-only RP2350 PIO header-capture
prototype. It is not a flash emulator and is not hardware-validated.

## Packer

The container stores non-erased 4 KiB pages and an index; absent pages read as
`0xFF`. The CLI accepts only a 16 MiB source and refuses to overwrite an
existing output:

```sh
python3 image_pack.py pack input.bin output.spm
python3 image_pack.py verify input.bin output.spm
```

The source is read-only. Keep generated containers outside the repository.

## Host model

`spi_model.py` handles only the standard `0x03` read command in synthetic
tests. Optional `ReadRule` entries choose a named image for a specific
transaction index and address interval. `toctou_plan.py` pins the exact
stock/candidate SHA-256 values and requires an explicit read order and
non-overlapping windows. It rejects substituted image bytes and never infers
PSP order from filenames. Unsupported opcodes are rejected, not guessed.

The model does not emulate PIO, DMA, electrical timing, chip-select behavior,
or the BC-250.

`pio_selector_model.py` separately traces the legacy TOCTOU PIO filter queue:
the selector sampled at chip-select assertion, matching `0x03` transaction
start addresses, and the later selector update. It is a source-derived
control-flow model only; it does not emulate MISO data, timing, DMA, or hardware.

## First-bit timing estimate

`pio_timing.py` is a host-only mode-0 deadline estimate for the existing
`spi_inject.pio` instruction order. It assumes a half-bit interval after the
last header falling edge, four cycles from that edge until the PIO WAIT
detects it, then three instruction cycles through the first `out pins`
(`jmp x--`, `set x`, `out pins`). The four-cycle allowance includes assumed
synchronizer, phase, and WAIT-detection delay; it is not measured RP2350 timing.
With those inputs, 400 MHz PIO
against 25 MHz SPI leaves an estimated one cycle; against 50 MHz SPI it
misses the estimated deadline by three cycles.

This calculation excludes GPIO pad delay, setup time, clock jitter, and the
exact synchronizer phase. Positive estimated margin is not proof of a timely
MISO bit, and this model says nothing about the separate `miso_proxy.pio`
program, selector timing, or actual BC-250 clocks. It is not hardware
validation.

## RP2350 capture prototype

`CMakeLists.txt` builds an input-only PIO observer using the exact
RP2350B-Plus-W profile from `/home/OWNER/waveshare`. It samples the default
SPI0 pins, samples on clock rising edges (mode-0 assumption), and prints a raw
32-bit transaction prefix over USB stdio. It does not validate the opcode,
parse/serve flash data, drive MISO, or emit a UF2. Build artifacts belong in
the user cache, not in the existing Waveshare workspace. `push noblock` avoids
stalling the PIO if USB output is slow, so captured prefixes may be dropped.

The observer's sample rate and header interpretation have not been measured.
Its GPIO mapping is only the Waveshare board's default SPI0 pin map, not a
verified BC-250/J4004 wiring plan.

## PSP/TOCTOU implementation status

The offline PSP/TOCTOU selection pipeline is implemented: sparse images,
explicit bounded read windows, pinned image hashes, deterministic synthetic
`0x03` transactions, and a generated serve-map are covered by host tests.
`src/sparse_reader.c/.h` now validates the existing container format and
provides bounded read-only access suitable for a later RP2350 responder; its
C test compiles with `-Wall -Wextra -Werror -pedantic` and exercises truncation,
duplicate-map and out-of-range rejection. Exported plans record
`hardware.connected=false`, `hardware.tested=false`, and
`hardware.flash_authorized=false`.

The actual RP2350 flash-response path, stock-flash bus release, reset/DPD
behavior, and first-MISO-bit timing remain unresolved. Do not flash this
candidate or connect it to the BC-250. Passing host tests is not a claim of
PSP acceptance, electrical compatibility, or successful hardware TOCTOU.
