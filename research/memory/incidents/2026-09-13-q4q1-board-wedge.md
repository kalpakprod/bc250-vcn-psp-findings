# Incident: board wedge during Q4/Q1 first-contact batch (2026-09-13 ~00:41+05:00)

## What happened
- Approved batch Phase A (`/tmp/q4q1_probe.py`, sha
  `1489873d...`) launched on BC250-01 (D10R, mode1, SMU alive) via SSH.
- Board went fully unresponsive: SSH timeouts, ping 100% loss, ARP
  INCOMPLETE, no recovery after 90+ s. Gateway fine. No panic-reboot.
- Phase B (Q0-2) never ran. No board-side output captured.

## Cause hypotheses (ranked)
1. One of the Q4 no-arg sends (0x04..0x0B most likely, fired first) hits
   a handler with platform side effects (clock/voltage/power) that hangs
   the kernel. Culprit UNKNOWN — no per-message output was streamed.
2. Q4 0x0A `[0]` ("freq_op1") zeroes a frequency/voltage target.
3. Transport/driver interaction (flock + concurrent amdgpu SMU use).
   Disfavored: same transport class ran fine for all Q0-1/B3 queries.
4. Coincidence (unrelated crash at the same minute). Disfavored by
   timing; testable only by clean boot + controlled re-probe.

## Corrections (G7)
- DISPROVED: "no-arg Q4-alias sends are the same risk class as Q0-1".
  At least one Q4 message (or the batch pattern) wedges this board.
- METHOD FLAW (mine): first-contact probes must flush per-message
  results (JSON lines) so a wedge still identifies the culprit. Never
  print-only-at-end on untried messages again.
- Q1 (0x08/0x10/0x68) was never reached; its risk is still unmeasured.

## Recovery needed (operator)
- Cold power-cycle BC250-01, confirm boot to mode1 + SSH.
- Report any display/serial/panic output observed.
- Rollback state: SPI untouched (D10R), no flash, no persistent change;
  `/tmp` scripts died with the kernel.

## Follow-up (needs fresh design + approval)
- One-message-at-a-time Q4 probe, per-message flushed output, alive
  check between, operator console watch, starting at Q4 0x04.
- Consider serial console to capture panic traces if the wedge repeats.

## Recovery (2026-09-13 ~00:48+05:00)
- Operator cold power-cycle: board back, fresh boot_id
  `35dead9d-...`, mode1, SMU alive, VCN probe lines present. Full
  recovery, no persistent damage. SPI untouched throughout.

## Attribution closed (2026-09-13 ~01:13+05:00, hardware-verified)
- Re-probe fired Q4 0x04 alone (no-arg, check_status=False, 5 s):
  `alive_before=true` printed, then the board wedged identically
  (SSH/ping dead, no route). Q4 0x04 send is SUFFICIENT for the kernel
  wedge. The Phase-A culprit was the first message all along.
- Mechanism unknown: a mailbox-level hang would raise at the 5 s
  timeout and complete the SSH call; total NIC death implies the SMU
  reaction hangs the host (platform-level event) or wedges PCI config
  access kernel-wide. Offline follow-up: Q3 0x04 handler semantics in
  the RE corpus (RECONSTRUCTION.md / 147-handler table).
- Q4 0x04 is now a CLOSED wedge class. Do not send again without serial
  console + per-message cycle standby.
