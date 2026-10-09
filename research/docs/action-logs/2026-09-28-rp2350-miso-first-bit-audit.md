# RP2350 MISO first-bit timing audit

## Intent

Date: 2026-09-28. Continue the approved software-only SPI emulator work by
checking the first-response instruction order in the existing PIO sources and
correcting the earlier static audit where needed. Do not modify source images,
firmware sources, or the Waveshare workspace. Do not upload firmware, connect
to the BC-250, or perform GPIO/hardware activity.

Inputs:

- `candidates/toctou-rig-v001/pio/spi_inject.pio`
  SHA-256 `02bf02eaaefb43d675bff294a6c74d80c067c1d63196760d24a1df8bff37733a`
- `candidates/toctou-rig-v001/pio/miso_proxy.pio`
  SHA-256 `a78df951e1a297c9dd2b809c329a2ab5299d292ed3aabb330d4d0a3f7f18d9db`
- `candidates/toctou-rig-v001/pio/spi_trigger.pio`
  SHA-256 `5a0394f1b90ac626d13e8684769ea216ee2b4e7865ffeff7696537d8d3f30bc3`
- `candidates/toctou-rig-v001/src/spihack.c`
  SHA-256 `cc460cb74854c259f101f3311991c8186b2ddd1a87db60e96de878cfd2cecf36`
- `candidates/toctou-rig-v001/src/main.c`
  SHA-256 `a9294279cb018ff622fd8558af0f173917e1905ef8ef0913c9762fd58f370876`

## Static result

The prior audit's description of the `miso_proxy` injection branch as outputting
before the next rising edge was incorrect. `pioasm` 2.3.1 assembled the four
existing PIO programs without errors. Its generated `miso_proxy` instruction
list places `wait 1 pin 0` immediately before `out pins, 1`; the passthrough
path likewise waits for the rising edge before sampling flash DO and moving
that value to MISO. Under the source's unverified mode-0 assumption, neither
path establishes that the first bit is ready before the master's sample edge.

`spi_inject` has a different instruction order: its data loop executes
`out pins, 1` before waiting for the next rising edge. The program first
skips 32 clock cycles and executes `set x, 31`, so this is only a source-level
indication that its output instruction precedes the following clock wait. It
is not proof that the data is ready before the actual sample point.

There is an additional unresolved source-level interaction. `spi_trigger`
reads the command and 24-bit address before setting the selector output.
`spi_inject` checks that selector at chip-select assertion, before those
header bits have been read. The source therefore does not establish that the
injection mode can be selected for the same transaction based on its address.
No timing or GPIO waveform was measured.

The local RP2350 SDK describes a two-flip-flop synchronizer on each GPIO input.
The old rig does not configure PIO input synchronizer bypass. Actual
synchronizer latency, SPI mode and frequency, selector timing, pin mapping,
electrical contention, and first-MISO-bit setup remain unverified.

## Evidence boundary and decision

This is reproducible static instruction-order evidence only. PIO syntax
assembly is not a firmware build, a timing simulation, or hardware acceptance.
The old rig's own build notes prohibit connection; its historical wiring also
requires a MISO break that is outside the approved constraints.

Do not flash or connect this rig. Keep the input-only observer and host model
separate from any claim of MISO emulation. A software-only follow-up may model
instruction and synchronizer delays under explicitly stated SPI assumptions,
but it cannot close the hardware timing question.
