# TOCTOU selector queue trace

## Intent

Date: 2026-09-28. Trace the host-configured filter queue against the legacy
PIO state machine to check whether the stated “original on first read, flash
on second” behavior follows from source. Static analysis only. No firmware
build, upload, board connection, signalling, reset, or flash operation.

Inputs and SHA-256:

- `candidates/toctou-rig-v001/src/main.c`
  `a9294279cb018ff622fd8558af0f173917e1905ef8ef0913c9762fd58f370876`
- `candidates/toctou-rig-v001/src/spihack.c`
  `cc460cb74854c259f101f3311991c8186b2ddd1a87db60e96de878cfd2cecf36`
- `candidates/toctou-rig-v001/pio/spi_trigger.pio`
  `5a0394f1b90ac626d13e8684769ea216ee2b4e7865ffeff7696537d8d3f30bc3`
- `candidates/toctou-rig-v001/pio/spi_inject.pio`
  `02bf02eaaefb43d675bff294a6c74d80c067c1d63196760d24a1df8bff37733a`
- `candidates/toctou-rig-v001/include/anchor_original.h`
  `5aadc6440998c00f28c3e9d356e6ae01331c68a1911061b18cb5ad97f0535b9b`

## Queue and transaction trace

Let `S = 0x9DB560` and `E = 0x9DB6A0`.

The firmware source queues these address/state pairs, in order:

1. `S -> true` directly in `main.c`.
2. `S -> true` and `E -> false` from `spihack_inject_payload()`.

`spi_trigger.pio` pulls one address before monitoring transactions. When it
matches that address, it pulls the associated state, writes it to GPIO21, and
does not load the next address until CS goes high. Thus the selector transitions
are driven by matching transaction-start addresses, not by the read pointer
crossing an address during response data.

`spi_inject.pio` samples GPIO21 immediately after CS goes low and before the
command/address header. For a transaction beginning at `S`, it therefore
chooses its path using the selector state from before `spi_trigger` finishes
parsing that transaction. On a first `S` match, the trigger changes the state
to true only after the injector has already selected the pass-through path.

The duplicate `S -> true` entry means the trigger then waits for another
transaction beginning at `S` before it arms the `E -> false` entry. If no
second `S` transaction occurs, the end entry is never reached. Even after it
is loaded, `E -> false` requires a separate SPI transaction whose starting
address is exactly `E`; reading continuously from `S` through `E` does not
match it.

The injector's emulation loop initializes `X` to 31 and outputs one bit per
iteration, for 32 bits total. The configured anchor payload is 320 bytes.
This PIO loop therefore describes four payload bytes per injection transaction,
not the full configured payload in one transaction. DMA/FIFO behavior beyond
these source facts is not established here.

## Source-derived sequence table

Assuming transactions start at `S`, and ignoring electrical/timing behavior:

| Transaction                         | Selector at CS-low | Trigger match and resulting selector                         | Injector path chosen |
| ----------------------------------- | ------------------ | ------------------------------------------------------------ | -------------------- |
| First `S`                           | Low                | First `S -> true`, then waits for another `S`                | Pass-through         |
| Second `S`                          | High               | Second `S -> true`, then loads `E -> false`                  | Emulation            |
| A later transaction starting at `E` | High               | `E -> false` after its header, then waits for another filter | Emulation            |
| Following transaction               | Low                | No filter queued                                             | Pass-through         |

This is a control-flow trace, not a proof that the hardware can execute these
transactions or meet SPI timing. It assumes the trigger recognizes command
`0x03`, the address bytes as encoded in the PIO, and the stated transaction
sequence. It does not establish actual PSP read order or lengths.

## Decision and evidence boundary

The source does not implement the stated “full original anchor on first read,
flash on second read” behavior. In this trace, the first matching read selects
pass-through, the next matching read selects injection, only 32 bits are
explicitly output, and selector reset depends on a separate transaction
starting at `E`. Actual BC-250 transaction sequence and MISO behavior remain
unknown.

This is static source reasoning only. No firmware was built or uploaded. No
board was connected, signalled, reset, or flashed. Do not treat the 400 MHz
configuration embedded in this legacy source as a recommendation or measured
clock.
