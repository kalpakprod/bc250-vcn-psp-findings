# V5: SMU second-core window probe — runbook DRAFT (2026-09-23)

Status: DRAFT. Executes only after operator review + explicit «го» per stage.
Method class: runtime-only (booted OS, mode1), no SPI writes, rollback = cold power cycle
(proven repeatedly). Board rules: one variable per step, liveness check after every step,
transient units with auto-stop timers, never `enable`, never compile on the board.

## Question

Does the SMU second-core routing window (`0x0005AFFF..0x0005B7FF`, `FUN_000235c8` ->
`func_0x1b514`) serve VCN state that the main window does not? The op-0x1005/Q3 `0x5C` path
resolves to `0x5C0FC` — OUTSIDE this window — so no sanctioned message reaches it. The
combination "proven Q2 0x23 unlock + direct pokes into the second-core window" was never
tried.

## Proven transports (reuse, do not reinvent)

- Q2 `0x23` ring unlock: PROVEN, repeatable (`memory/firmware-audit.md`, S2-A campaign).
- Q3 `0x98` (ZD-2): unguarded fixed-`0xFF` dword write, caller-supplied low-20-bit-masked
  offset, internal readback, status always 1. Value is NOT verifiable from the host; only
  side effects are observable.
- Q0 `0x02/0x03` queries: the liveness oracle (SMU version + feature query, proven safe).
- PROHIBITED: DF-space reads, full-dump amdgpu_regs reads, 0x090/0x069 clamp-family reads
  (measured wedge classes, MISTAKES.md 2026-09-23).

## Stages

- Stage 0 (preflight, read-only): board reachable, `pgrep -f "[s]teamapps/common"` empty,
  SMU alive via Q0, governor/gpu-fixed units stopped via flock path, baseline telemetry dump.
- Stage 1: Q2 `0x23` unlock (proven). Liveness: Q0.
- Stage 2a: ONE Q3 `0x98` write of `0xFF` to `0x0005B7FC` (top of the second-core window;
  least likely to gate a live domain). Liveness: Q0 immediately, then 60 s watch. Wedge ->
  cold cycle, record, STOP.
- Stage 2b (only after 2a clean): descend the window, one address per power cycle is NOT
  required — one per Q0-liveness check, lowest address last (`0x5B000`). Any wedge -> stop.
- Stage 3: after the window is mapped (which addresses take the write without wedging),
  test the dom6/VCN observable: `--manual-powerup` + fire `0x61` (proven bring-up), then the
  single-register arbiter read (`stage4_arbiter.py`, proven transport). If the arbiter leaves
  all-ones, the second core does NOT hold the missing transition -> V5 joins C3 as closed.
- Stage 4 (only if a state change is observed): freeze the winning sequence, archive
  telemetry, and only then discuss persistence.

## Boundaries

No SPI write, no kernel modules loaded (the dfprobe insmod wedge class), no governor
restarts (SMU-writer transition rule), no readings outside the proven single-register class.
Honest limit: if `0x98`'s 20-bit mask cannot express `0x5Bxxx` (mask check at stage 2a fails
silently — the write lands elsewhere), Stage 2a/2b are uninformative; detecting that requires
the ZD-1 code-exec escalation, which is a separate runbook.
