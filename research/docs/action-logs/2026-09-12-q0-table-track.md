# Q0 driver-table track (2026-09-12/13, Asia/Almaty)

## Intent (G4 before-record; operator approved the Q0 track with `идём`)

- Actor: root, on live board (D10R, mode1, SMU alive this boot).
- Background: Q0 = standard PPSMC queue (cmd `0x03B10A08`, rsp
  `0x03B10A68`, arg `0x03B10A48`); protocol from board-local
  `bc250-smu-unlock/bc250_smu/api_q0.py` (already on board, read-only
  use). Prior S2-L5 proposed the full driver-table transfer
  (0x04/0x05+0x07, then 0x5C) but only ever fired the surgical 0x5C.
- Probe Q0-1 (this run, read-only by design): Q0 msg `0x02` (SMU version)
  and `0x03` (driver-IF version), `check_status=False`, 5 s timeout.
  Precondition: Q3 `0x01` alive before AND after. No DMA address is
  passed; no table transfer is issued; no MMIO/gasket/DF write.
- Expected: version values (SMU 0.58.6.0); proves the Q0 queue answers at
  all (never touched before on this board).
- Stop conditions: any send timeout/exception, or alive_after=False ->
  abort track, cold-cycle only if board unresponsive (no auto-reboot;
  operator power-cycles). Rollback: none needed (no state change).
- Explicitly NOT approved in this run: 0x04/0x05/0x06/0x07 (need DMA
  staging design first), 0x5C, any DF/gasket write.
- Result: appended below after execution.

## Result Q0-1 (2026-09-13T00:24:53+05:00, observed — PASS)

- `alive_before=true`, `alive_after=true` (Q3 `0x01` test messages).
- Q0 `0x02` -> status `1`, ret `0x580600` = SMU version **0.58.6.0**
  (digit-packed, matches the known Robin3-identical firmware exactly).
- Q0 `0x03` -> status `1`, ret `0x8` (driver-IF version 8).
- First-ever Q0 contact on this board: queue answers, no wedge, no state
  change. Exact command preserved in this log (inline `python3 -c`,
  `PYTHONPATH=~/vcn_unlock/bc250-smu-unlock`, `sudo -n`, 5 s timeout).
- Next (NOT run, needs DMA-staging design + separate approval): Q0-2
  table READ (`0x04/0x05` location + `0x06` SMU->DRAM into a cushioned
  physically-contiguous buffer located via pagemap); only then Q0-3
  staged-table write (`0x07`) + `0x5C`. DF-space reads stay prohibited.

## Q0-2 design (ready, awaiting per-run approval — no board contact yet)

- Target: dump the SMU driver table (SMU->DRAM) to learn format/size
  and check for VCN clock entries. Baseline: Q0-1 versions stable
  (`0x580600`/`0x8`), SMU alive, mode1 boot, no prior table transfer
  this boot.
- Recon (done, read-only): NO `amdgpu_smu*` debugfs exists, so the
  driver's table location is NOT recoverable from the OS. Consequence:
  after `0x04/0x05` the SMU location pointer cannot be restored to its
  prior value; mitigation = holder process (below), final reset = reboot.
- Mechanics (single sudo python, board `/tmp`, nothing committed):
  1. `mmap` 16 MiB anonymous + `mlock` + touch every page (fill
     `0xAA`); read `/proc/self/pagemap` per page; require one
     physically-contiguous run >= 64 KiB (table class is KBs); target =
     run start; cushion = rest of mapping. Up to 3 fresh mappings, else
     ABORT with report (no SMU contact beyond alive checks).
  2. `alive_before` via Q3 `0x01`.
  3. Q0 `0x04` (phys high32), `0x05` (phys low32), `check_status=True`,
     5 s each. Any non-OK/exception -> ABORT before `0x06`.
  4. Q0 `0x06`, `check_status=False`, record status; sleep 2 s.
  5. Diff buffer vs `0xAA` fill -> changed prefix = table bytes; write
     artifact to board `/tmp/q0_table_<ts>.bin` + sha256 into the log;
     parse for clock-like structures (report only).
  6. Holder: process stays alive `mlock`'d, re-verifies canary pages +
     SMU alive every 60 s, until operator reboot or explicit kill.
     Rule: kill ONLY to reboot immediately after (location still points
     at freed pages otherwise).
- Expected: statuses OK, coherent changed prefix (KBs), alive true
  throughout, table parseable.
- Stop: any timeout/exception/non-OK on 0x04/0x05 (abort pre-0x06);
  alive_after=false after 0x06 (report, operator cold-cycle standby, no
  auto action); no contiguous run (abort, report).
- Rollback: holder keeps DMA target valid; full reset = reboot
  (operator). No flash touched. DF-space reads NOT part of this probe.
- Approval gate: explicit operator `да` for Q0-2 as designed above.

## Approved batch intent (G4 before-record; operator `разрешаю запуск` 2026-09-13)

Actor: root. Board BC250-01, D10R, mode1, same boot (uptime checked pre-run).
Scope (approved): Q4/Q1 first-contact read-only queries + Q0-2 DMA table READ
as designed above. NOT approved: Q0-3 (0x07+0x5C), 0x5afff DF probe, any
DF/gasket/MMIO write, flash.

### G7 premise correction (static, api_q3.py read this session)
- Battery premise "(i) Q4-alias read-only queries (same risk class as Q0-1)"
  is OVER-BROAD: Q4 msg numbers alias Q3 handlers, and Q3 0x10 is
  `q3_0x10_unforce_cpu_gpu_vid` — a VID WRITE. Q4 0x10 is EXCLUDED.
- Q3 twins of Q4 0x05/0x06/0x07/0x08/0x09 are unwrapped (unknown); 0x04/0x0A/
  0x0B/0x0D/0x11 unwrapped-unknown; 0x27 unwrapped (mixin uses
  check_status=False). Q1 (0x08/0x10/0x68) is an independent queue, no Q3
  alias — all unexamined. All unknowns fire no-arg, check_status=False,
  one at a time, alive check after EACH message.

### Phase A — Q4/Q1 first contact
- Order: Q4 0x04,05,06,07,08,09,0A(mixin,[0]),0B,0D,11,27 then Q1
  0x08,10,68. `Bc250Smu(timeout=5.0)`; alive_before once; per message:
  send (5 s), record (st,ret), alive check. Abort on any exception/
  timeout/alive-false; report, no auto action.
- Expected: statuses + return values (data, incl. NACKs). No state change
  expected (no-arg sends to query/unknown handlers; the one known write
  excluded).
- Rollback: none needed (no state change by design).

### Phase B — Q0-2 (only if Phase A ends alive=true)
- Exactly the design above: 16 MiB mmap/mlock/0xAA, pagemap contiguous
  run >=64 KiB (3 tries else ABORT), 0x04/0x05 check_status=True,
  0x06 check_status=False, 2 s settle, diff, artifact
  /tmp/q0_table_<ts>.bin + sha256, holder loop (canary+alive/60 s).
- Residual risk noted: SMU table-location pointer keeps pointing at our
  buffer until reboot; a driver 0x07 (not expected outside GPU
  reset/resume — none planned) would source our buffer, which by then
  holds the SMU's own dumped table (near-identical content). Holder keeps
  the mapping valid; kill ONLY to reboot immediately after.
- Rollback: holder + operator reboot. No flash touched. DF reads excluded.

## Result Phase A (2026-09-13 ~00:42+05:00, observed — BOARD WEDGE, run aborted)

- Preconditions PASS: same boot (up 29 min, boot_id
  `fb6f7a07-63b5-4ada-99b7-ec7103d25429`), script hashes match transfer,
  SMU `alive True` immediately before launch.
- Launch: `sudo -n env PYTHONPATH=... timeout 220 python3
  /tmp/q4q1_probe.py` (~00:41). SSH returned `Timeout, server not
  responding`; two follow-up SSH attempts `Connection timed out`; ping
  100% loss with ARP INCOMPLETE while gateway pings fine; re-check after
  +90 s still dead (`No route to host`). No panic-reboot recovery.
- Verdict: kernel wedge temporally correlated with the Q4 first-contact
  batch (one of Q4 0x04..0x0B/0x0D/0x11/0x27 or transport interaction;
  the culprit message is UNKNOWN — the script printed results only at
  the end, a design flaw, see incident record). No board output captured.
- Phase B (Q0-2) NOT run. No further board contact attempted. Next step
  needs the operator: cold power-cycle, confirm boot + SSH, report any
  display/serial output. Re-run, if any, must be one-message-at-a-time
  with per-message flushed output and console watch — separate approval.

## Recovery (2026-09-13 ~00:48+05:00, observed — PASS)
- Operator cold power-cycle done. First SSH still `No route to host`
  (board mid-boot); after +60 s ping 0% loss, SSH OK, up 1 min, NEW
  boot_id `35dead9d-181a-454d-b0df-4e069964262a`.
- Fresh boot verified healthy: cmdline `amdgpu.bc250_vcn_mode=1`,
  param = 1, SMU `alive True`, `vcn_v2_0_probe` + `Found VCN firmware`
  lines present (2). Pre-batch state restored; /tmp probe scripts died
  with the old kernel (host copies in /tmp retained).
- No further probes launched. Re-probe options await separate approval.

## Re-probe design (G4 before-record; operator chose `B` 2026-09-13)
- One SSH invocation per message = attribution unit (a wedge kills the
  NIC, so only completed calls count as evidence; per-message prints
  inside one call would be lost with the board).
- Per call: alive_before (Q3 0x01, proven-safe) -> single no-arg send
  (check_status=False, 5 s) -> alive_after; `timeout 60` board-side
  guard; `python3 -u` flushed JSON lines.
- Order: Q4 0x04,05,06,07,08,09,0A([0]),0B,0D,11,27. Q4 0x10 stays
  EXCLUDED (VID write). Q1 deferred until Q4 completes.
- Stop: any SSH failure/wedge (report, await operator cycle — no auto
  action), any alive_after=false (report, stop), any exception (report,
  stop). Expected: (st,ret) + alive true per message.

## Result re-probe Q4 0x04 (2026-09-13 ~01:13+05:00, observed — WEDGE, culprit found)
- Call completed `alive_before=true`, then SSH died (`Timeout, server
  not responding`); ping 100% loss, `No route to host`. Board wedged by
  the Q4 0x04 no-arg send itself (fresh boot 35dead9d, up 25 min).
- Attribution CLOSED for the Phase-A wedge: Q4 msg 0x04 is sufficient
  to hang the kernel. Q4 0x05+ and Q1 remain untested; further Q4 sends
  need per-message power-cycle standby. Q0-2 still unrun (Q0 transport
  proven safe by Q0-1/B3 series).
- Awaiting operator cold power-cycle. Recommendation: cycle, then Q0-2
  first; Q4 remainder only if needed, one message per cycle standby.

## Recovery-2 (2026-09-13 ~14:18+05:00, observed — PASS)
- Operator reported board powered on; root verified over SSH
  (steammachine@127.0.0.1): ping 0% loss, up 1 min, NEW boot_id
  `2b77d998-a616-468c-9525-135e95d0ea2f` (prior wedged boot was
  `35dead9d-...`), kernel `7.2.0-1.92-cachyos-vcn-bc250`, cmdline
  `amdgpu.bc250_vcn_mode=1`, param = 1.
- SMU check PASS: `assess_S1.py` (cwd `~/vcn_unlock`,
  `PYTHONPATH=~/vcn_unlock/bc250-smu-unlock`, `sudo -n`) ->
  `alive=True`, `open_before=True`. D10R early unlock live on this boot.
- VCN probe lines present (2): `vcn_v2_0_probe` + `Found VCN firmware`.
- Pre-probe state restored; /tmp probe scripts from the wedged boot are
  gone with the old kernel (host copies in /tmp retained).
- No further probes launched. Next step awaits explicit operator
  decision: Q0-2 first (recommended), offline-only, or Q0-2 + Q4
  remainder one-per-cycle.

## Q0-2 launch (G4 before-record; operator chose `Q0-2 first` 2026-09-13)
- Approval: structured choice `Q0-2 first (Recommended)` = Q0-2 ONLY as
  designed above; Q4 remainder deferred; Q0-3/0x5C/DF/gasket/flash NOT
  approved. Board boot `2b77d998-...` (mode1, SMU alive, probe lines 2).
- API reconciliation (read this session, before writing the script):
  board `~/vcn_unlock/bc250-smu-unlock/bc250_smu/api.py` =
  `send_message(queue, msg, args=(), check_status=True) -> (st, ret)`,
  raises `SmuRejected` on non-OK when checked; `SMU_RETURN_OK = 0x01`;
  `Bc250Smu(timeout=5.0)` default. NOTE: corpus
  `import/.../bc250_smu/api.py` has a DIFFERENT signature
  (`arg/pack/decode`) — the board deployment is the binding one; the
  script uses only the board form. Mixins `_set_driver_table_*` default
  to check_status=True (matches design for 0x04/0x05); 0x06 is sent via
  raw `send_message(0, 0x06, check_status=False)` per design (NOT the
  mixin, whose default checks).
- Transport: script `/tmp/q0_table_read.py` (host copy, sha recorded at
  transfer), `scp` to board `/tmp`, hash verified, launched detached
  (`setsid`, output to board `/tmp/q0_table_run_<ts>.log`), polled via
  separate SSH reads. JSON-lines, flushed per step (Q4 lesson).
- G3 REUSE (changed before launch): prior-session draft
  `/tmp/q0_2_table_read.py` (00:40, never run) reused instead of a new
  script; minimal run patch applied (per-step flushed log lines for
  alive_before/0x04/0x05/0x06, guarded alive_before, half-pointer note).
  Run-file sha256 `0ee4ae616581ba513a2ce3047650b531e8523f18bfa00ff5f78c5a0e68cab086`,
  verified identical on board. Duplicate new draft removed.
- Preconditions re-verified on boot `2b77d998` immediately before launch:
  up 4 min, NO amdgpu_smu debugfs, `alive=True`, Q0 `0x02->(0x1,0x580600)`,
  `0x03->(0x1,0x8)`, `alive_after=True`. Board shell is fish — all remote
  compound commands must run via `bash -c`.
- Result: appended below after execution.

## Result Q0-2 attempt 1 (2026-09-13 ~14:22+05:00, observed — ABORT, no SMU contact)
- Launch `LAUNCH_EXIT=0` (detached `setsid`, `sudo -n`, `python3 -u`,
  `--out /tmp/q0_2_result.json --log /tmp/q0_2_hold.log`).
- Buffer step failed per design: try 1 best run 8 pages (32 KiB), try 2 =
  1 page, try 3 = 4 pages. `aborted: no contiguous run >= 64 KiB in
  3 tries`, `ok=false`. Best observed contiguous = 32 KiB; host RAM is
  too fragmented 4+ min after boot for a 64 KiB run in a 16 MiB anon mapping.
- Zero SMU contact on this path (script exits before constructing
  `Bc250Smu`; no 0x04/0x05/0x06 issued). Post-abort health PASS: up 7 min,
  NO_HOLDER process, `alive=True`, `open_before=True`. No artifact, no
  state change, no wedge.
- Next options (each needs fresh approval, none run): (a) re-run
  immediately after a fresh reboot (fragmentation lowest early in boot);
  (b) THP-backed allocator variant (`madvise HUGEPAGE`, board THP mode =
  `[always]` — 2 MB pages would give 512-page runs; same risk class, no
  SMU contact until a buffer is proven); (c) park Q0-2, continue
  offline P1.5. NOT proposed: shrinking below 64 KiB (SMU overshoot
  would corrupt unrelated physical pages) or blind same-script retry
  (fragmentation only worsens with uptime).

## Q0-2 attempt 2: THP variant (G4 before-record; operator chose `THP variant`)
- Approval: structured choice `THP variant` 2026-09-13. Scope change is
  confined to step 1 (buffer allocation); all downstream steps, messages
  (0x04/0x05 checked, 0x06 unchecked), abort rules, holder rule, and
  exclusions (no 0x07/0x5C/DF/gasket/flash) are unchanged.
- Step-1 replacement: `mmap` 16 MiB + `madvise(MADV_HUGEPAGE)` + fault/fill
  0xAA, then settle rounds t+0/2/4/8 s per attempt (khugepaged collapse,
  board THP mode `[always]`) checking for a >=64 KiB contiguous run; up to
  3 fresh mappings as before. `mlock` ONLY after a qualifying run is found
  (pin preserves layout), followed by a post-pin run re-verify; any failure
  aborts pre-SMU exactly as in attempt 1. No compaction sysctl, no hugetlbfs
  pool, no persistent host change.
- Rationale: with mode=always a single collapsed 2 MB page yields a
  512-page run (32x margin over the 16-page requirement); attempt 1
  proved plain-anon mappings top out at 8 pages on this uptime.
- Run-file sha256 `4c61c702fb87f84bfcb7c06508444f2b97d97f8e4cf708169ed87e552d28927c`,
  verified identical on board; same boot `2b77d998`.
- Result: appended below after execution.

## Result Q0-2 attempt 2 (2026-09-13 14:26-14:27+05:00, observed — SMU WEDGE)
- Buffer step PASS (THP works): try 1 t+0s best run = 512 pages (2 MB) at
  phys `0x176000000`; `mlock OK`, post-pin re-verify PASS.
- `alive_before=True`; `0x04 OK` (high=0x1), `0x05 OK` (low=0x76000000):
  table location staged at our buffer.
- `0x06 done st=255 ret=0x0`: SMU actively REFUSED the SMU->DRAM transfer
  (status 0xFF bail class, same code as the S2-L5 0x5C gate bail).
  `changed_len=0` — no DMA bytes landed.
- `alive_after=false`: Q3 0x01 fails. Re-check +90 s: still `alive=False`,
  secure Q3 `0x2A` = "timed out - SMU wedged, cold cycle". The mailbox did
  NOT recover — this is a firmware wedge, not a transient busy.
- Collateral (read-only dmesg): amdgpu itself degrading — repeating `SMU:
  No response msg_reg: 6 resp_reg: 0`, `Failed to export SMU metrics
  table!`, one `ring gfx_0.0.0 timeout`; loadavg climbing (5.43). Host SSH
  survives; GPU stack does not.
- Holder (PID 38730) is HOLDING the mapping per design; NOT killed (rule:
  kill only to reboot immediately after — the power cycle will reap it).
- Inference (not proven): the 0x04/0x05 stole the table-location pointer
  that the driver's periodic metrics-table export flow was actively using;
  0x06's 255-bail plus the pointer theft desynced SMU/driver and hung the
  firmware. The design's residual-risk note covered only a future driver
  0x07 — the live metrics flow was the actual collision. Q0-2's 0x06 is
  therefore NOT a safe read on this firmware; the table-location pointer
  is live-shared state.
- Procedural note: pre-launch `rm` of old result/log files failed (sticky
  /tmp + root-owned files from attempt 1); hold.log is appended across
  attempts (attribution by timestamp holds). Use `sudo rm` next time.
- Next step needs the operator: COLD power-cycle (warm reboot may not reset
  the always-on SMU), confirm boot + SSH, report display/serial. No auto
  action taken. Q0-3 (0x07+0x5C) is NOT proposed on this evidence; the Q0
  table track needs a redesign (driver quiesce? metrics-flow-aware staging?)
  or closure — separate decision after recovery.

## Recovery-3 (2026-09-13 ~14:30+05:00, observed — PASS)
- Operator cold power-cycle done ("готово"). Root verified over SSH: ping
  0% loss, up 0 min, NEW boot_id `730a5b8a-1755-45a3-9fbd-d284b9e1594a`
  (wedged boot was `2b77d998-...`), kernel
  `7.2.0-1.92-cachyos-vcn-bc250`, cmdline `amdgpu.bc250_vcn_mode=1`, param = 1.
- SMU check PASS: `assess_S1.py` -> `alive=True`, `open_before=True`.
  The 0x06 firmware wedge is fully cleared by the cold cycle — no
  persistent damage; D10R early unlock live again.
- VCN probe lines present (2); NO_HOLDER process (attempt-2 holder reaped
  by the power cycle as designed; no manual kill was needed).
- Board is back to the healthy pre-probe baseline. No further probes
  launched. Q0 table-track future awaits operator decision (quiesced
  redesign vs closure vs offline P1.5).

## Attempt 3: quiesced redesign (G4 before-record; PROPOSED, not approved)
- Operator chose `Quiesced redesign` 2026-09-13. Full spec (7-section form):
  `specs/2026-09-13-q0-quiesced-redesign.md`.
- One-line summary: byte-identical THP script (`4c61c702...`) on a
  mode2+blacklist boot (limine line 275, verified present); E1 = wedge was
  driver-collision (0x06 safe quiesced), E2 = 0x06 inherently unsafe (CLOSE
  the track), E3 = staging gated without driver.
- Needs before execution: (1) explicit operator approval of this exact
  scope; (2) operator selects the mode2 entry at the local limine console
  and reports "board up" (root cannot switch entries via SSH).
- Approval GRANTED 2026-09-13 (structured choice `Approve + boot mode2`):
  exact scope of `specs/2026-09-13-q0-quiesced-redesign.md`, byte-identical
  script `4c61c702...`, quiesced mode2 boot only. Standing exclusions hold
  (no 0x07/0x5C/DF/gasket/flash).
- CORRECTION (root error, owned): the "root cannot switch entries via SSH"
  gate was false — D20 already proved default-entry switch + `sudo reboot` +
  SSH poll over SSH. Operator explicitly ordered root to do it. Procedure
  (G4 before-record): backup `/boot/limine.conf` to
  `.bak-q0attempt3-mode2`, change exactly the `default_entry:` line to the
  mode2 entry, diff-verify, `sudo reboot`, poll SSH (up to ~5 min), verify
  NEW boot_id + quiesce + SMU alive per spec checklist. Rollback: revert
  the file from backup (via SSH once up) or operator picks mode1 at the
  console; mode2 entry itself is the proven v3 boot.
- Boot switch executed by ROOT (operator explicit order): backup
  `/boot/limine.conf.bak-q0attempt3-mode2`, exactly-one-line diff
  (`default_entry: ...-mode1` -> `...-mode2`), `sudo reboot`, SSH back on
  first poll (new boot `ab1cf8de-...`, up 0 min).
- Quiesce preconditions PASS on `ab1cf8de`: cmdline mode2+blacklist,
  `lsmod|grep amdgpu` = 0, `/sys/module/amdgpu` ABSENT, `alive=True`, Q0
  `0x02->(0x1,0x580600)`, `0x03->(0x1,0x8)`, `alive_after=True`.
- Script re-transferred post-reboot (/tmp is tmpfs): hash `4c61c702...`
  verified identical on board, same boot.

## Result Q0-2 attempt 3 (2026-09-13 14:41+05:00, observed — E1, wedge attributed)
- Buffer: try 1 t+0s best run = 4096 pages (whole 16 MiB mapping
  contiguous — fresh boot + THP) at phys `0x139600000`; mlock + post-pin
  re-verify PASS.
- `alive_before=True`; `0x04 OK` (high=0x1), `0x05 OK` (low=0x39600000);
  `0x06 done st=255 ret=0x0` (same 255-bail as attempt 2 — no table posted,
  as predicted for a driverless boot); `changed_len=0`.
- **`alive_after=true`** (re-verified +60 s: `alive=True`): the 0x06 bail is
  CLEAN without a driver. VERDICT E1: the attempt-2 firmware wedge is
  attributed to the driver metrics-flow collision, NOT to the 0x06 handler
  itself. `0x06` is safe quiesced. The Q0 table track stays OPEN; UC2 (own
  0x07 post + 0x06 readback + 0x5C) is now designable — NOT approved, needs
  a separate design + approval.
- ANOMALY (open, non-blocking for E1): the holder (PID 2464) died silently
  <60 s after printing HOLDING — no beat line, no traceback, no OOM/coredump
  journal trace, `/proc/2464` absent. Attempt-2's holder likely died the same
  way (never verified alive). Consequence: the "holder keeps DMA target
  valid" safety net never actually held in EITHER run; on this quiesced boot
  the dangling pointer (`0x139600000`) is benign ONLY because nothing fires
  0x06/0x07. Rule: any future table op on this boot MUST re-stage 0x04/0x05
  first (or reboot).
- ANOMALY RESOLVED (2026-09-13 ~14:43+05:00, hardware-verified): detached
  `setsid -f sleep 120` also died within ~25 s of SSH disconnect
  (SLEEPER_GONE) — the killer is environmental, not script-specific.
  Mechanism: `setsid` escapes the POSIX session but NOT the systemd
  session-scope cgroup; when the SSH connection closes, scope cleanup
  reaps every process started from it, detached or not. Both holders died
  this way. Future holder designs MUST NOT use bare `setsid -f` from SSH:
  use `systemd-run --scope` (new scope outside the session) or avoid
  cross-SSH persistence entirely (single-shot + re-stage per run).
- Side observations (read-only journal): a boot-time `python[995]` service
  ("Applying 4000 MHz @ Scale -28") talks SMU via PCI 0xB8 even on blacklist
  boots — another SMU actor exists; `gamescope` crash-loops SIGABRT without
  amdgpu (expected, benign for SMU work).

## UC2-step-1: quiesced 0x07 transport validation (G4 before-record; GO per user mandate)
- Mandate: operator ordered autonomous drive toward VCN unlock without
  per-step questions (2026-09-13). Standing exclusions hold (no 0x5C in THIS
  run, no DF/gasket/MMIO writes, no flash). One new variable vs attempt 3:
  firing Q0 `0x07` (never fired on this board).
- Static grounding (this session, our exact fw `f546f118...`): Q3 table
  pattern-verified at image `0x736c` (SRAM `0x746c`, delta +0x100); Q0 table
  identified at image `0x6f74` (populated 0x01-0x07 + distinct 0x02/0x03
  version stubs; Q1/Q2/Q5 candidates lack live-proven slots) →
  Q0 `0x07` handler = `0x1bafc`. pypcode-Xtensa validated only partially
  (0x1b9b4/0x1ba5c/0x1bafc decode cleanly; 0x1b998 crashes, campaign
  func_23b14 matches NEITHER our image nor robin_5 — it came from a live
  SRAM dump; static decode parked per G6 in favor of this empirical probe).
- Upstream reference (torvalds/linux v6.8, comparison only): Renoir uses
  DIFFERENT numbering (0x1A/0x1B addrs, 0x1C/0x1D transfers, 0x34 =
  SetSoftMaxVcn, 0xC = PowerUpVcn) — our fw is a custom PPSMC dialect;
  response codes shared (OK=1, Failed=0xFF, UnknownCmd=0xFE) → our 0x06
  `st=255` = Failed-from-handler, not missing-handler.
- Procedure (script `/tmp/q0_uc2_step1.py`, THP buffer + marker fill
  `0x51000000+i`, quiesce interlock aborts if amdgpu present): gate-byte
  baseline (`smu_read_bytes(0xcec0,64)`, proven read class) → `alive_before`
  → `0x04/0x05` checked (abort pre-0x07 on failure) → `0x07` fire
  (unchecked, record st/ret) → `0x06` readback (unchecked) → diff run vs
  marker + artifact → gate AFTER → `alive_after` → result JSON, plain exit
  (NO holder: G7 scope-reaping makes holders illusory; quiesced boot fires
  nothing afterwards; dangling-pointer rule reiterated).
- Expected outcomes: T1 (0x07 OK + marker round-trips + gate moved = loop
  proven) / T2 (0x07 OK + 0x06 255 + gate moved = post consumed, readback
  needs more) / T3 (0x07 255 = post rejected) / T4 (wedge → report +
  cold-cycle standby, no auto action).
- Script sha256 `f3f42a4bd802c799a212b6641682ebcc4ce507e6336357fd34d0dffff68e9b01`,
  verified identical on board; boot `ab1cf8de` (quiesced).
- Result: appended below after execution.

## Result UC2-step-1 (2026-09-13 14:54+05:00, observed — T3, post refused, no wedge)
- Quiesce interlock PASS; buffer 1024 pages @phys `0x1de400000` (marker fill
  `0x51000000+i`); `alive_before=True`; `0x04 OK`, `0x05 OK`.
- **FIRST-EVER `0x07`: `st=255 ret=0x0`** — fw actively REFUSED the marker
  post (Failed, not UnknownCmd → handler exists, content/staging rejected).
  `0x06` also 255; diff 262144/262144 marker-match (zero DMA either way);
  canary clean; 64B SRAM window `0xCEC0..0xCEFF` byte-identical before/after;
  **`alive_after=True`** — 0x07 is SAFE (no wedge), just refused. T3.
- Artifact (pristine marker dump, forensics): board
  `/tmp/q0_uc2_table_20260913_145451.bin`, sha256
  `f1c8820506d9313720fafbcc928c459872a0cbeffe4a8c0d88968b0a1cbddcac`.
- G7 OFFSET CORRECTION (root error, owned): the gate window was read at
  `0xCEC0`+64B but labeled as `0xCEC8`-relative — the TRUE gate byte
  (`0xCEC8+0xF6` = `0xCFBE`) and freq limits (`+0x100`) were NEVER observed;
  the logged `f6=00 f7=03` are actually bytes at `0xCEF6/0xCEF7`, and `f100`
  printed empty (out-of-range slice). Raw hex remains valid for
  `0xCEC0..0xCEFF`. True-window read follows as step-1b (pure read).
- Next (autonomous campaign, no new questions): (1b) read TRUE gate window
  `0xCEC8`+320B on this boot (post-refusal state); (2) boot mode1, capture
  the DRIVER-posted table from fw SRAM via `smu_read_bytes` (reads are
  safe — the attempt-2 wedge came from pointer/0x06 writes, never reads);
  (3) reboot quiesced, replay EXACT driver bytes via 0x07 (expect st=1),
  0x06 readback, and only then design the 0x5C fire with a proper gate.

## Result UC2-step-1b (2026-09-13 ~14:56+05:00, observed — TRUE gate baseline)
- First-ever CORRECT observation of `0xCEC8`+320B (quiesced `ab1cf8de`,
  post-0x07-refusal): **`+0xF6 (0xCFBE) = 0xFF`** — the S2-L5 gate premise
  is now LIVE-CONFIRMED (nothing posted; refused 0x07 moved nothing).
  `+0xF7 = 0x04` (count limit?), `+0x0D = 0x00` (walk 0),
  `+0x11/12/13 = FF/5A/01` (feat-5 defaults),
  `+0x100` freq limits = 8 zero bytes (nothing posted).
- Struct head: `9a99993f` (float 1.2 coeff?) then pointers
  `0x00CF6C/0x00CF44/0x00CF1C/0x00CEF4` at +0x20..+0x2F (descending by 0x28 =
  40B — candidate per-feature blocks, uninterpreted).
- Window sha256 `55527692177d0ee7d1d9ea2468e80e8ee8eb24b41bd343b11aba6a16f148cbb2`;
  SMU alive before+after (pure reads). Executing step 2 (mode1 capture).

## Result UC2-step-2 mode1 capture (2026-09-13 ~14:59+05:00, observed — IDENTICAL)
- Boot `590a640d` (mode1, driver fully up, SMU alive). `smu_read_bytes(0xCEC8,1024)`:
  **byte-identical window to quiesced** — `f6=0xFF`, `f7=0x04`, `d=00`,
  `11/12/13=FF/5A/01`, `f100/f104` zeros, same head64 (float 1.2 + same 4
  pointers). The healthy mode1 driver NEVER posts to `0xCEC8`.
- Artifact: `evidence/runtime/20260913-mode1-sram-0xcec8-1k.bin`, sha256
  `d5b385e831f983097e12ffe8e4c96ddde4dc1014e3607ba500c07020bf599f88`.
- Consequence: the capture-then-replay plan is VOID (no driver bytes exist to
  replay). The driver's live table flow is metrics-only (`0x06` into ITS
  buffer); `0x07`'s destination/validation must be cracked directly.
- Driver binary findings (amdgpu-1.92.ko, 37MB, NOT stripped, sha256
  `7d6606ba80be79e49bb703f29b79a22fcc4b96d8c51b7799bf694f4d417d1ebf`):
  `smu_v12_0_set_driver_table_location` sends internal enums `0x10/0x11`;
  `cyan_skillfish_message_map` located (3336B) but wire-id decode needs the
  exact 7.2 enum order (v6.8 order does not fit; PARKED per G6).
  Upstream dialect mismatch CONFIRMED as comparison-only evidence
  (torvalds/linux v6.8, fetched 2026-09-13): v11 transfers `0x12/0x13`,
  `PowerUpVcn=0x2B`; v12 addrs `0x1A/0x1B`, transfers `0x1C/0x1D`,
  `0x34=SetSoftMaxVcn` — vs our fw `0x04-0x07` + `0x34=SetDriverTableVMID`.
  Upstream response codes shared (OK=1/Failed=0xFF/UnknownCmd=0xFE).
- VMID HYPOTHESIS (inference, now the lead): Q0 `0x34` (SetDriverTableVMID)
  was NEVER fired on this board. The SMU DMA path may need a VMID/translation
  context: quiesced (no driver ever set VMID) → both `0x06` AND `0x07` refuse
  with 255 (CONSISTENT: channel disabled, not content); mode1 driver works
  because IT set VMID+location at boot; attempt-2 wedged on foreign-location
  + driver-VMID mismatch. Testable in one quiesced run (below).

## UC2-step-3: quiesced 0x34(0)+0x07+0x06 (G4 before-record; GO per user mandate)
- Exclusions hold (no 0x5C, no DF/gasket/MMIO, no flash). New variables, each
  independently attributed by per-step logs: `0x34` (first-ever) then `0x07`.
- Procedure (script `/tmp/q0_uc2_step3.py`, = step-1 script + 0x34 step):
  quiesce interlock → THP marker buffer → gate baseline → alive → `0x04/0x05`
  checked → **`0x34 arg 0`** (unchecked, record; abort-before-0x07 on wedge/
  exception) → `0x07` (unchecked) → `0x06` (unchecked) → diff+artifact →
  gate-after → alive-after → result JSON, plain exit (no holder).
- Expected: V1 (`0x34` OK + `0x07` OK = VMID was the key) / V2 (`0x34` OK +
  `0x07` 255 = content validation stands; next: pristine-post variant) /
  V3 (`0x34` 255/exception = VMID path closed or needs other arg) / V4
  (wedge at any step → report + cold-cycle standby).
- Script sha256 `d170e7302bc4934efe0f104074b9b4fba659b8ab52d6e459bfb3e8cde41eb018`,
  verified on board; boot `e12b66ea` (quiesced, default switched mode1→mode2).
- Result: appended below after execution.

## Result UC2-step-3 (2026-09-13 15:02+05:00, observed — V2, VMID not the key)
- Buffer 512 pages @phys `0x14be00000` (marker); `alive_before=True`;
  `0x04 OK`, `0x05 OK`.
- **FIRST-EVER `0x34` (VMID=0): `st=1 ret=0`** — accepted cleanly.
- **`0x07` STILL `st=255`** with VMID staged → VMID hypothesis DISPROVED as
  the acceptance key. `0x06` also 255; diff 262144/262144 pristine; canary
  clean; 64B window unmoved; **`alive_after=True`**. V2. No wedge anywhere.
- (Same known gate-label bug in this script generation: labels are
  `0xCEC0`-relative; raw hex valid; TRUE gate `f6=FF` stands from step-1b.)
- Artifact: board `/tmp/q0_uc2_table_20260913_150257.bin`, sha256
  `35f6950aa3518db98560035d815723e827f3ea5dec1b0237a740d826b0b181e8`.
- NEW LEAD (table-select): upstream passes a TABLE_* id as the transfer
  argument; our mixin sends NO arg (= id 0 = BIOS_IF, plausibly BIOS-only →
  refused!). The fw may accept `0x07`/`0x06` for ids 1/4/6/7. Directly
  testable quiesced (both msgs proven safe-refusing). Next below.

## UC2-step-4: quiesced table-id sweep (G4 before-record; GO per user mandate)
- Exclusions hold (no 0x5C, no DF/gasket/MMIO, no flash). Variation vs
  step-3: transfer args (proven-safe msgs, new args only).
- Procedure (script `/tmp/q0_uc2_step4.py`): quiesce interlock → THP marker
  buffer → TRUE gate baseline (`0xCEC8`+320B, labels FIXED) → alive →
  `0x04/0x05` checked → `0x34(0)` (unchecked) → for each id in [0,1,4,6,7]:
  `0x07(id)` (unchecked, record) → `0x06(id)` (unchecked, record) → alive
  check (abort-before-next-id on false/exception) → diff+artifact →
  gate-after → alive-after → result JSON, plain exit (no holder).
- Expected: S1 (some id returns st=1 = channel opens; readback bytes reveal
  accepted table + size) / S2 (all 255 = no table-select or all refused;
  next: pristine-post variant) / S3 (wedge at any id → that id is hazardous;
  report + cold-cycle standby).
- Script sha256 `67e681dd99dbbcf65315ede6182b421ecf64232a8e63a001a457d53c7d884814`,
  verified on board; boot `e12b66ea` (quiesced).
- Result: appended below after execution.

## Result UC2-step-4 (2026-09-13 15:06+05:00, observed — S1, metrics channel open)
- Sweep (all with `alive=True` throughout, no wedge): every `0x07` id
  [0,1,4,6,7] → 255 (post refused regardless of id); `0x06` ids 0/1/4/7 →
  255; **`0x06 id=6 → st=1`** with **244 changed bytes** (words 0..60).
  `ret` echoes the arg id on every call (carries no info).
- 244 bytes = EXACT `sizeof(cyan_skillfish SmuMetrics_t)` upstream
  (2×116B Current/Average + 12B trailer) → table 6 IS the metrics table on
  our fw; the upstream struct is CONFIRMED for this dialect.
- Artifact: `evidence/runtime/20260913-quiesced-metrics-table6-244B.bin`,
  sha256 `b29f56ebb6680c8389b1e3d5d62e882a6b025ae7324afa1d4a224bb5a4c4bdcb`.
  Full struct parse PLAUSIBLE: cores 1391-4000MHz/~50mW (core5 boosted
  4000MHz/4730mW/C0 100%), GFX 1500MHz/52C, SOC 1254MHz, **VCLK 0MHz**,
  **DCLK 1111MHz**, MEM 450MHz (= mode1 pp_dpm_mclk, corroborated),
  ~48-53C, Throttler 0, Accnt 0 (Average block all zeros — averaging never
  started without driver).
- KEY READINGS: VCN video clock is OFF quiesced (VCLK=0, the thing to
  change); DCLK runs at 1111 with no driver (selective power — consistent
  with born-diverse dom states). Gate struct untouched by the read.
- DELIVERABLE: live metrics oracle proven quiesced (no driver needed) —
  any future power attempt can now observe VCLK/DCLK/temps directly.
  (Quiesced-only for us: mode1 0x06 with foreign location = attempt-2 wedge.)
- 0x07 status: refused for every id with marker content. Pristine-post and
  invented-table variants NOT run (see pivot below).

## G6 PIVOT (2026-09-13): runtime-SMU class exhausted → PEI-time road primary
- Tally of the runtime-SMU method class: S2-A (gasket latches, bridge
  closed), S2-L5b (0x5C-after-gate-clear hard wedge, QUIESCED),
  S2-L8/L10 (dom14 never ACKs, fw path AND direct path), D12-D19 (DXE-time
  gasket wedges SMU), Q0-2 attempt-2 (0x06 + live driver = fw wedge),
  UC2 (0x07 refused × all ids; driver never posts to 0xCEC8; no template).
  Far past three same-class failures.
- UNIFYING INFERENCE (static + hardware, needs the PEI test): bus-level
  isolation (PSP-applied at boot, hardware-locked) is the SINGLE root cause;
  dom14's never-ACK, the all-ones arbiter, and the DXE/ready-to-boot wedges
  are all consequences of running AFTER the lock. Nothing runtime can grant
  what only boot-time context applies.
- PREDICTION (recorded WITHOUT firing): `0x5C`-with-proper-table would wedge
  identically to S2-L5b, because S2-L6's unacked-poll mechanism is
  table-independent (isolation, not config). 0x5C NOT fired; costs an
  operator cold cycle for an experiment whose mechanism already predicts the
  outcome. Revisit only if isolation is first lifted by other means.
- NEXT (autonomous, offline, zero board risk): PEI-phase `$VNI`/IDS consumer
  hunt + t28 five-domain program analysis → PEI-time gasket candidate on the
  proven unsigned-FV flash surface (D8/D9R/D10R boot PASS). Flash itself
  stays gated on exact-image approval with a complete artifact in hand.
- Board: restoring healthy mode1 default (proven pattern) after the
  quiesced campaign; runtime track parked, not closed.
