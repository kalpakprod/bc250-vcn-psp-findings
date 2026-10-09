# PIO same-transaction selector audit

## Intent

Date: 2026-09-28. Determine from the legacy source whether the PIO selector can
choose an injected response based on the address of the transaction currently
being handled. Static source review only. Do not modify firmware or BIOS
images, upload firmware, or connect, signal, reset, or flash hardware.

Inputs:

- `candidates/toctou-rig-v001/pio/spi_inject.pio`
  SHA-256 `02bf02eaaefb43d675bff294a6c74d80c067c1d63196760d24a1df8bff37733a`
- `candidates/toctou-rig-v001/pio/spi_trigger.pio`
  SHA-256 `5a0394f1b90ac626d13e8684769ea216ee2b4e7865ffeff7696537d8d3f30bc3`
- `candidates/toctou-rig-v001/src/spihack.c`
  SHA-256 `cc460cb74854c259f101f3311991c8186b2ddd1a87db60e96de878cfd2cecf36`
- `candidates/toctou-rig-v001/pio/miso_proxy.pio`
  SHA-256 `a78df951e1a297c9dd2b809c329a2ab5299d292ed3aabb330d4d0a3f7f18d9db`

## Source-level finding

`spihack.c` wires GPIO21 as both `spi_trigger`'s output and `spi_inject`'s
`jmp pin` selector. `spi_trigger` parses the eight command bits and 24 address
bits, compares the address, and only then writes the requested selector value
to GPIO21.

`spi_inject` checks GPIO21 immediately after it detects CS going low, before
consuming the command or address. It then stays on the selected path: either
select the flash (`orig_flash`) or enter the data-emulation path. Therefore,
an address-dependent decision made by `spi_trigger` cannot select the
emulation path for that same transaction in this program structure. A selector
left high by an earlier transaction could affect a later transaction, but that
is a different sequence and is not validated here.

The separate `miso_proxy` checks its selector after skipping the 32-bit
command/address header, so same-transaction selection is structurally
possible there. However, its injection loop waits for the next CLK rising edge
before `out pins`; this does not establish a timely first bit under the
unverified mode-0 assumption. The two programs therefore do not combine into
a verified response path.

## Decision and evidence boundary

The legacy `spi_inject` address-trigger arrangement is not evidence that it
can inject on the matched read. Do not use it as a same-transaction response
design. The `miso_proxy` selector placement resolves only the ordering issue,
not the first-bit deadline or electrical behavior.

This is static source reasoning, not execution or hardware evidence. No PIO
program was changed or built for this audit. No board was connected,
signalled, reset, or flashed.

## Correction

The statement above that `miso_proxy`'s post-header selector check makes
same-transaction selection structurally possible is superseded. The separate
`spi_trigger` continues parsing and comparing the address after the proxy
reaches its selector check; static instruction order does not establish that
GPIO21 updates in time. The first bit is independently late in the proxy's
injection loop. See
`2026-09-28-pio-trigger-proxy-phase-audit.md`; same-transaction selection
remains unproven.
