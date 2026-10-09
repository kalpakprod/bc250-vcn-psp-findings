# PIO trigger/proxy phase audit

## Intent

Date: 2026-09-28. Refine the earlier static note that `miso_proxy.pio`'s
post-header selector check makes same-transaction selection structurally
possible. Compare the trigger's post-address instructions with the proxy's
selector-check point. Static source review only; no PIO build, simulator,
firmware upload, board connection, signalling, reset, or flash operation.

Sources:

- `candidates/toctou-rig-v001/pio/spi_trigger.pio`,
  SHA-256 `5a0394f1b90ac626d13e8684769ea216ee2b4e7865ffeff7696537d8d3f30bc3`
- `candidates/toctou-rig-v001/pio/miso_proxy.pio`,
  SHA-256 `a78df951e1a297c9dd2b809c329a2ab5299d292ed3aabb330d4d0a3f7f18d9db`
- `candidates/toctou-rig-v001/src/spihack.c`,
  SHA-256 `cc460cb74854c259f101f3311991c8186b2ddd1a87db60e96de878cfd2cecf36`

## Finding

After capturing the last address bit, `spi_trigger` still executes the loop
decrement, copies OSR and ISR, compares the address, pulls the desired state,
and writes GPIO21. The separate `miso_proxy` skips 32 bits and then checks its
selector on its next PIO instruction. The source establishes no scheduling
The post-header instruction tails differ. After the trigger detects the last
address falling edge, it executes the final `jmp x--`, `mov x, osr`,
`mov y, isr`, address comparison, `pull`, and `mov pins, osr` before its
selector update: at least six PIO instructions when its filter FIFO is ready.
After the proxy detects that same edge, it executes the final `jmp x--` and
then its `jmp pin` selector check: two instructions. In a hypothetical
lockstep schedule with both programs at divider 1, that gives the proxy a
four-instruction lead. But the source does not establish common clock phase,
input-synchronizer phase, start timing, or `pull` readiness, so this count is
not proof of actual relative event order. The checked-in C setup loads
`spi_inject`, not `miso_proxy`.

The header loops also differ: for each command/address bit the trigger executes
`jmp pin`, `wait high`, `in`, `wait low`, `jmp x--` (five instructions), while
the proxy skip loop executes `wait high`, `wait low`, `jmp x--` (three).
These are instruction counts, not measured elapsed cycles; the `wait`
instructions stall on external edges. The trigger additionally runs five
instructions between finishing the command byte and starting address capture.
This makes its capture timing more constrained, but does not resolve how its
GPIO21 write lines up with the proxy's read.

Even a later selector update cannot change the proxy's first decision. If it
already took `passthrough_loop`, that loop does not check the selector again
until after it has waited for a data clock rising edge, sampled flash DO,
driven the PSP-facing pin, and reached the falling edge. That is too late to
establish the first response bit for the current transaction.
Therefore the previous statement that the proxy's check placement makes
same-transaction selection structurally possible is too strong. Static source
alone does not establish it. The first-bit path has an independent issue:
`miso_proxy` waits for CLK rising before `out pins`, so it does not establish
data before a mode-0 rising-edge sample.

## Decision and evidence boundary

Treat same-transaction selector timing in the separate proxy as unresolved,
not established. A cycle-accurate model with the exact state-machine start and
input-synchronizer phases would be needed to settle the relative phase; no
local simulator was found. Actual input-only timing capture would also need
separate approval. The legacy `spi_inject` decision remains delayed until a
later transaction because it samples the selector at CS assertion.

This is static source analysis only. No firmware or BIOS image was changed.

## Local simulator availability

The bounded search of project tools, candidates, tests, and docs found no PIO
simulator or PIO-specific testbench. Python module lookup also found no
`rp2040`, `rp2350`, `pioemu`, `pyqemu`, or `unicorn` module. This is not a
system-wide inventory, but there is no discovered local cycle-accurate
simulator to run this check against. PIO assembly is not execution or
simulation.

## Checks

The candidate host suite passed 21 tests, `make test` passed 7 checks, and
scoped Procoder reported 8 changed paths clean, 0 unformatted, 0 unchecked,
0 out of scope, 473 repository-wide hygiene findings, and 0 blocking findings;
exit code 0. No PIO simulator or hardware test was run.
