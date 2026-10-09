# 2026-09-12 — S2-A: runtime donor aperture via SMU secure path (no flash)

## Context

Board BC250-01 runs the APCB-only DFG candidate `6b1fe8ef504142d5d5273a85b6c9febdf0b1fb8fc08ebab2593281c320cb9d70`
(PSP region = stock; gasket and TOS policy untouched). Established today (hardware-verified):

- mode2 wedge is the first VCN MMIO access with the island closed (`evidence/runtime/20260912-mode2-controlled-probe-dmesg.log`).
- C2P direct command path (0x100B) is not the TOS transport (clean negative).
- BAR5 mmap works; BAR0 mmap EINVAL; /dev/mem EPERM (STRICT_DEVMEM).

## Why this experiment (G3)

Two-lock model (`import/.../bc250_firmware/VCN-LOCK-MECHANISM.md` §7.4, §11 A1/A3):

- Lock carriers: SEC_GASKET (type 0x24) and TOS_SECURITY_POLICY (type 0x45), both signed.
  D3-B2 (unsigned edit of both, flashed 2026-09-12) was rejected by PSP — no video. Signature branch closed.
- The VCN-relevant kill records: `0x03E810=0` (VCN_SEG enable, grp 0x210), DF window
  `0x03A2011C=0x87FF` (no bank-12 bit), `0x03A20124=0`. Donor (Cezanne): `0x03E810=6`,
  `0x03A2011C=0x107FF`, `0x03A20124=0x10FFF`, plus 56 bank-12 (HWID 12, `0x0900Cxxx`) aperture records.
- Historical VULN-1 full SMN replay (1461 writes, 2026-08-25/29) wrote **Robin kill values** + bank-12:
  the stage-A donor values were never written at runtime. That is the untested variable.
- All these addresses are SMN addresses. The SMU Q3 0x98 privileged SMN proxy accepts writes to them
  (field-proven: 56 bank-12 writes accepted, `0x0900C234` readback 1). The SMU secure/debug path is opened
  by the Q2 msg 0x23 exploit (`bc250-smu-unlock/unlock.py`), which ran successfully on this board 2026-08-25/26.

## Plan (staged, one variable at a time, rollback = power cycle at every stage)

Stage 0 — baseline (read-only): mode1 boot (`amdgpu.bc250_vcn_mode=1`, probe-only, proven stable),
check `~/vcn_unlock` deployment on the board, verify PMFW blob (t08 `0x8FF000`) in the current image
hash-matches the BIOS-3 basis used to derive unlock offsets, read dom6/gasket baseline via `--verify`.

Stage 1 — SMU unlock (SMU SRAM writes, no flash): `unlock.py`; success = dbg byte `0x7B3C`==0,
secure probe read OK, SMU alive. Known-good on this board (Aug 25/26).

Stage 2 — donor aperture (the new variable): write `0x03E810<=6` (grp 0x210),
`0x03A2011C<=0x107FF` (grp 0x201), `0x03A20124<=0x10FFF` (grp 0x201), then the 56 bank-12 records
in donor order (51 into 0x201, 5 into 0x280: recommit sequence per `smn_vcn_gasket_full.json`).
`0x03E814` (DTR FIFO) and `0x03A20120` stay untouched (donor-equal / safest-leave per §3 DTR note).
IOHC `0x0322xxxx` and NBIO bridge stay untouched (stage C — not in this run).
Verify: SMN readback of `0x0900C234` (expect commit=1), SMU alive after every ~25 writes.

Stage 3 — dom6 power (proven procedures only): `--verify` (read-only) → `--manual-powerup`
(window stores; the Aug-25 run released the ctrl gate `0x06d0f8` 0x02→0x00 and it persisted in-session).
Q3 msg 0x61 clock-sequence fire ONLY if slots show off/gated (documented SMU-wedge risk on headless;
SMU survived the Aug-25 fire; run with the `vcn_watch.sh` watchdog).

Stage 4 — arbiter (safe driver path, only after stage 3): read `/sys/kernel/debug/dri/1/amdgpu_regs`
VCN frame (dword 0x7800): `mmUVD_VERSION` (0x78CA), `mmUVD_POWER_STATUS` (0x78BC), `mmUVD_STATUS`,
`mmUVD_SCRATCH9`, `mmUVD_JPEG_CNTL`. All-ones ⇒ island still closed (remaining suspects: PSP-side ISO,
fw-internal power-up msg — next step would be static msg-table decode 0x3C/0x3D + FUN_00023b14 caller).
Live value ⇒ VCN visible from x86; next session: mode2 boot for real driver attach.

## Safety envelope

- No flash, no SPI writes. Rollback = cold power cycle (PSP re-applies the stock gasket at every boot;
  nothing in this experiment is persistent across boots).
- Failure mode is the known wedge (board link-dead until power cycle); recovery documented and
  operator-experienced (2026-08-29, 2026-09-12).
- Reads of VCN MMIO happen only after the domain work (2026-08-29 lesson: read-before-enable = wedge).
- Secure-path reads of DF space happen only after unlock (2026-09-03 lock-probe wedge lesson).
- Stock recovery image preserved: `read-a.bin` SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`.

## Corpus mining inputs (registered 2026-09-12, pre-execution)

Corpus-mined facts that refine the plan (full analysis in `memory/firmware-audit.md`, section
"S2 campaign corpus mining and PMFW identity validation (2026-09-12)"):

- PMFW identity: the type `0x08` blob in the current on-chip image is byte-identical to
  `recon/robin3_psp_unique/SMU_OFFCHIP_FW~0x8_0.58.6.0` (full `0x40000` body), so the Stage-0
  hash check is already satisfied by an offline observation; the boot-time re-check is a formality.
- Historical 1461-write replay wrote Robin KILL values (`0x03E810=0`, `0x03A2011C=0x87FF`,
  `0x0322011C=0x8000`) + bank-12 only; donor stage-A values were never written at runtime.
  Stage 2 here is genuinely the first donor-aperture runtime write, not a replay.
- Measured wedge taxonomy: VCN MMIO reads before domain enable wedge the bus (2026-08-29);
  DF-space reads may wedge SMU even with the probe script (2026-09-03, secure-state unrecorded);
  writes to all gasket address classes are proven non-wedging (1461-write replay completed).
- Decisive pre-test available: `smn_lock_probe.py --phase-b` (never run) — single additive write
  `0x03A2011C 0x87FF->0x107FF` + readback, verdict LATCHED / DROPPED / WEDGED.

## Revised stage order (supersedes "Plan" staging above)

- Stage 0 — unchanged (mode1 boot, deployment check, baseline `--verify`).
- Stage 1 — unchanged (SMU unlock Q2 msg 0x23 + liveness).
- Stage 2a (NEW, first and only write of this run) — `smn_lock_probe.py --phase-b`:
  LATCHED  => runtime DF-window programming viable, proceed to Stage 2b.
  DROPPED  => DF space is hardware-locked until cold reset; runtime windows are dead;
              pivot to boot-time-only gasket carriers (PSP branch) or NBIO S4; stop this run.
  WEDGED   => cold power cycle; record; do not retry the same address class (G6).
- Stage 2b — donor aperture (0x03E810=6, 0x03A2011C=0x107FF, 0x03A20124=0x10FFF) + 56 bank-12
  records, SMU-liveness check every ~25 writes. Only after a LATCHED verdict.
- Stage 3 — unchanged (dom6 `--verify` -> `--manual-powerup`; msg 0x61 only if slots gated,
  pre-approved with `vcn_watch`).
- Stage 4 — unchanged (amdgpu_regs arbiter read: `mmUVD_VERSION` 0x78CA, `mmUVD_POWER_STATUS`,
  `mmUVD_SCRATCH9`; all-ones => island closed, next = msg-table static decode 0x3C/0x3D and NBIO S4).

## Stage 0 + Stage 1 result (2026-09-12 04:44-05:0x PKT, hardware-verified)

- Operator booted mode1 (`amdgpu.bc250_vcn_mode=1`, kernel `7.2.0-1.92-cachyos-vcn-bc250`). Journal: IP block 8 `vcn_v2_0_probe`, `Found VCN firmware ENC 1.24 DEC 8`, `fw_size=404544`. Board SSH-reachable.
- Deployment intact: `~/vcn_unlock/` with `bc250-smu-unlock/` (unlock.py, smn_lock_probe.py, Sep-3 JSON logs), `daveconde-bc250-vcn-enable/` (enable_vcn.py), `vcn_safe_run.sh`, `vcn_watch.sh`, `unclamp_step1.py`, `smn_vcn_gasket_unclamp.py` + JSONs. Note: `enable_vcn.py` lives in the daveconde subdir, not at `$VB` root where `vcn_safe_run.sh` expects it.
- `enable_vcn.py --verify` (read-only first contact per VCN-START-SAFE.md): SMU alive; gate was 0xFD (closed) -> library unlock (Q2 0x23) ran inside --verify -> secure access OPEN; dbg byte 0x01 -> 0; dom6 state word @0xf714 = 0x00010101 (state byte 0x01); slots 0x16/0x17/0x18 dom=6 enable=0 (off), divider 5, status READY(bit16). This completes Stage 1 (unlock + liveness) as designed.
- amdgpu_regs found at `/sys/kernel/debug/dri/0000:01:00.0/amdgpu_regs` (dri/1 symlink path to be confirmed at Stage 4).

## G7 correction: phase-b precheck read is itself the wedge class; write-first order required

- Sep-3 JSON logs (read 2026-09-12 from board): three attempts, ALL wedged on a DF-space READ with the gate open: `0x0900C234` (12:04), `0x03A2011C` (12:20), and at 12:27 the control read `0x5A870` returned OK `0xFF` immediately before the `0x03A2011C` read wedged — differential proves the wedge is specific to DF-space reads, not to the mailbox or unlock state.
- Corollary A: `smn_lock_probe.py --phase-b` cannot reach its discriminating write on this boot state — its precheck read of `0x03A2011C` wedges first. The probe design assumed DF reads are safe post-unlock; measured evidence says otherwise on a cold boot with amdgpu loaded.
- Corollary B: bank-12/DF reads DID work on 26.08 immediately after the 56-record write run (`0x0900C234` readback = 1). Working model: DF/bank-12 windows read-wedge only in the never-programmed boot state; after runtime programming, reads are safe. (Static side: the boot gasket applies Robin kill values `0x03A2011C=0x87FF` deterministically from the on-chip Robin blobs, so the pre-write value is known without a read.)
- Correction to the runbook: the "reads only after unlock" envelope rule is INSUFFICIENT — the measured rule is "DF-space reads only after the region has been programmed this session; VCN MMIO reads only after domain power work". WRITES remain the proven-safe first touch.
- Revised Stage 2a (supersedes the phase-b invocation): single blind write `0x03A2011C <- 0x107FF` (the exact additive probe value; boot value 0x87FF known statically), then `smu.alive()` liveness, JSON log, NO DF reads before the write. This preserves the one-variable probe while removing the hazardous precheck. SMN readback happens only after Stage 2b programs the region (then it doubles as the LATCHED/DROPPED verdict for the window class).

## Stage 2a result (2026-09-12 04:49 PKT, hardware-verified)

- Executor: `stage2a_writefirst.py` deployed to `~/vcn_unlock/` (SHA-256 `63696284e8712efadc5ceeda010c29d22f71cc7f5dabf4c0361c68b4c644fb1a`): unlock check -> single blind write `0x03A2011C <- 0x107FF` -> alive check -> single readback. No MMIO, no other addresses.
- Sequence observed: SMU alive=True; secure access already open (persisting from the `--verify` unlock in the same SMU session); **write ACCEPTED, SMU alive after write = True** (fourth write-class confirmation: DF-window writes do not wedge); **readback WEDGED**: `queue 3 msg 0x2A timed out` — the DF-window SMN read kills the SMU mailbox even immediately after a successful write to the same address.
- Aftermath: OS alive (telemetry streaming), SMU messaging globally dead including the kernel driver path (`amdgpu ... SMU: No response msg_reg: 6 resp_reg: 0`, `Failed to export SMU metrics table!` repeating) — same global-SMU-wedge signature as 2026-09-03. Cold power cycle required; the stage-2a write is volatile and wiped by the cycle (documented rollback).
- Knowledge:
  - `LATCHED/DROPPED` discrimination via SMN readback of DF windows is a DEAD method class on this boot state (four read wedges: Sep-3 x3, today). The latch question can only be answered indirectly (driver-visible behavior after dom6 power).
  - Working model update: the 26.08 post-write bank-12 readback (`0x0900C234` = 1) remains the single successful post-write read; it used the bank-12 region `0x0900Cxxx`, not the `0x03A2` DF window. Region-dependent read behavior is possible; keep at most ONE verification read of `0x0900C234` at the END of stage 2b, with the stop rule.
- Revised Stage 2b (for the next boot, after cold cycle + mode1): unlock -> donor aperture WRITES (`0x03E810<-6`, `0x03A2011C<-0x107FF`, `0x03A20124<-0x10FFF`) -> 56 bank-12 records (proven sequence) -> alive check after every ~25 writes -> single `0x0900C234` readback (expect commit=1) -> STOP. No `0x03A2/0x0322/0x03D2` reads, no MMIO reads. Then Stage 3 (dom6) and Stage 4 (amdgpu_regs arbiter) unchanged.

## Stage 2b attempt 1 result (2026-09-12 05:09 PKT, hardware-verified) — reorder required

- After cold cycle #2 (operator), mode1 boot verified (fresh boot, SMU metrics streaming, no SMU errors in dmesg).
- Executor `stage2b_writefirst.py` (SHA-256 `bb19e0725a8470a38215dc435c63637351539526b3f0afb67f1579608de252c2`): unlock ran (Q2 0x23, dbg `0x01`->`0`), then writes with alive check after each.
- Writes [01..03] ACCEPTED, SMU alive after each: `0x03E810<-6`, `0x03A2011C<-0x107FF`, `0x03A20124<-0x10FFF` — the full donor aperture, first runtime programming ever executed.
- **Write[04] `0x0900C234 <- 0` (first bank-12 touch) WEDGED**: `queue 3 msg 0x2C timed out`. SMU mailbox dead again (same global signature); OS alive. Cold cycle #2 required.
- Differential with the 26.08 run of the identical 56-record sequence (all accepted, readback=1): on 26.08 the dom6 domain had been manually powered on 25.08 and the release persisted in the SMU session; today the domain is gated (fresh cold boot). The 2a readback wedge is consistent with the same model.
- Working model v2: bank-12 regions and DF-space READS sit behind the VCN island fabric/power state. With the domain power-gated, even SMU-master WRITES to bank-12 hang the mailbox. The domain power state is the discriminating variable.
- REVISED ORDER for the next boot (supersedes stage numbering): (3) dom6 power FIRST — `--verify` -> `--manual-powerup`; 0x61 fire with `vcn_watch` only if slots stay gated; (4a) arbiter baseline via amdgpu_regs with the domain powered (driver reads safe; expect all-ones = bridge closed); (2b) gasket programming — donor aperture + bank-12 writes with alive checks, single `0x0900C234` readback at end; (4b) arbiter re-read — real `mmUVD_VERSION` would mean the bridge opened. Cold power cycle remains the rollback at every step.

## Cycle #2 attempt: manual-powerup LANDED; amdgpu_regs read without clocks wedged the kernel (05:19-05:2x PKT)

- After cold cycle #2 + mode1 boot (fresh, SMU metrics streaming): `--verify` re-established unlock + identical dom6 baseline (slots 0x16/0x17/0x18 enable=off, READY).
- `--manual-powerup` SUCCESS (hardware-verified): ctrl gate `0x06d0f8`-class store LANDED and HELD `0x00000002 -> 0x00000000` — "the first real sequencer state change on this card"; per the tool's verdict, SMU-side power state is maximally complete (clocks programmed + enables ON + gates released + rail taken).
- **Kernel wedge on the NEXT step**: reading `/sys/kernel/debug/dri/0000:01:00.0/amdgpu_regs` (the arbiter baseline) hung the board mid-read (SSH "server not responding", then ping 100% loss / no route). Root cause of the deviation: domain power was released WITHOUT the clock-enable work (slots enable=off). The manual-powerup verdict itself warned: "hang = cold cycle (July, pre-clock-work only)". VCN MMIO reads with power-but-no-clocks hang the island bus; the amdgpu_regs dump touches VCN-frame registers through the driver.
- G7 correction (order): the 0x61 clock-enable fire (pre-approved with `vcn_watch`) is a PREREQUISITE for any VCN MMIO read, including driver-based amgdpu_regs — not only for the direct-load step. The fire's own first POWER_STATUS MMIO read is the designed arbiter baseline (real values = island live; all-ones = isolation, clean abort per 2026-08-20 measurement).
- FINAL reordered sequence for cycle #3: `--verify` -> `--manual-powerup` -> fire msg 0x61 under `vcn_watch` (its MMIO read doubles as the arbiter baseline) -> stage-2b gasket programming (donor aperture + bank-12 writes, single `0x0900C234` readback) -> amdgpu_regs re-read (`mmUVD_VERSION` real = bridge opened). Rollback = cold power cycle at every step.

## Cycle #3: full domain bring-up + FIRST successful runtime gasket programming; arbiter reader class corrected (05:2x PKT)

- After cold cycle #3 + mode1: `--verify` (unlock re-established, identical baseline) -> `--manual-powerup` (ctrl LANDED and HELD `0x02->0x00`) -> fire msg 0x61: SMU survived, slot clocks programmed (0x17 clock `0x00->0x20`), **per-slot clock enables LANDED on all three slots (0x16/0x17/0x18 enable=1 ON)**, dom6 power oracle: status bit8 SET (up-ack) matching the powered dom0-5 baseline, ctrl=0 (no gate holds), handler disarmed + thunk wiped. First time the full domain bring-up was performed and verified within one session.
- **Stage 2b attempt 2 SUCCESS (hardware-verified)**: all **59 writes accepted** (3 donor aperture + 56 bank-12), SMU alive throughout, single verification readback `0x0900C234 = 1` (commit OK). The donor gasket aperture is now fully runtime-programmed for the first time in project history. JSON: `~/vcn_unlock/stage2b_writefirst_20260912_052402.json`. The domain-power hypothesis is confirmed: bank-12 programming requires the powered+clocked domain.
- **Kernel wedge #2 on the arbiter**: full-dump read of `amdgpu_regs` (`cat`) hung the board again, even powered+clocked. Reader-class forensics: `enable_vcn.VcnDirect.rd` uses the SAME amdgpu_regs file but via SINGLE-REGISTER seek+read(4); the 26.08 clean all-ones ladder used exactly that class. The full dump reads every enumerated register range and hangs. G7 correction: amdgpu_regs FULL-DUMP reads are a closed method; single-register reads remain the proven transport (`read_vcn_direct.py` arbiter: `mmUVD_VERSION` dword `0x78CA` / byte `0x1E328`).
- Board state: dead, cold cycle #4 required. All SMU-side state (power/clocks/gasket) is volatile and wiped by the cycle; the full proven sequence must re-run in one boot: verify -> powerup -> fire -> 2b -> single-register arbiter (`stage4_arbiter.py`, SHA-256 recorded at deploy).

## Cycle #4: complete S2-A execution — definitive verdict (2026-09-12 05:2x PKT, hardware-verified)

- Full proven sequence re-run in one boot session, every step verified: `--verify` (unlock, baseline) -> `--manual-powerup` (ctrl `0x02->0x00` LANDED) -> fire msg 0x61 (slots 0x16/0x17/0x18 clock-enable LANDED, SMU alive, thunk disarmed) -> `stage2b_writefirst.py` (59/59 writes accepted, `0x0900C234` readback commit=1, JSON `~/vcn_unlock/stage2b_writefirst_20260912_052757.json`).
- **Arbiter (`stage4_arbiter.py`, SHA-256 `821635e2c0f80a34f03a2a82902d1f3b65c5ec451110ec602c01b1da0d883227`): ALL FIVE PROBES ALL-ONES, reads completed cleanly, no wedge** (`~/vcn_unlock/stage4_arbiter_20260912_052802.txt`): `mmUVD_POWER_STATUS/mmUVD_STATUS/mmUVD_SEMA_ADDR_LOW/mmUVD_SCRATCH9/mmUVD_VERSION` = `0xffffffff`.
- **Definitive S2-A verdict (hardware-verified): the SMU runtime path programs the gasket/aperture (writes latch, bank-12 commit=1), but the VCN island remains isolated — the NBIF/Fabric bridge does not pass with the runtime-programmed gasket.** This confirms the 2026-08-29 chain report's G5 blocker by experiment: the bridge needs more than the gasket values. Candidate explanations for the next runbook: (a) the bridge re-samples the gasket only at boot/cold reset (boot-time-only model — favors the PSP-time ladder, but D3-B2 showed unsigned PSP edits are rejected); (b) the S4 NBIO register moves (`0x13b1005c/0x13b10060/0x13b00084/0x13b0004c`) gate the bridge and were never executed — they are the one remaining runtime lever and were explicitly excluded from THIS run's approved scope ("stage C — not in this run").
- Board left in the fully brought-up state (unlock open, domain powered+clocked, gasket programmed); rollback = cold power cycle whenever desired.
- Session wedge accounting: 3 kernel/SMU wedges today (2a readback; amdgpu_regs full-dump x2), all recovered by cold power cycle; no persistent change (all state volatile; SPI image untouched).

## S4 NBIO un-clamp run (2026-09-12, operator approved "делаем") — G4 intent, appended BEFORE execution

- Source prescription: `recon/VCN-UNLOCK-CORRECT-CHAIN.md` §3.3 Путь A / §6 S4 (the never-executed main move).
- Board state: the cycle-#4 session is still up (unlock open, domain powered+clocked, gasket programmed, bridge closed). S4 runs in this session; rollback = cold power cycle.
- Executor `stage4_s4_nbio.py` (to be deployed, SHA recorded at deploy):
  1. liveness + unlock check (no writes);
  2. SINGLE-REGISTER SMN reads of NBIO candidates `0x13b1005c`, `0x13b10060`, `0x13b00084`, `0x13b0004c` plus gasket-diff context addresses `0x13b103f8`, `0x13b10400`; stop-on-timeout (wedge rule), JSON log;
  3. decision rule from the PEIM disasm (§3.3): value `0x3` (low bits) = Port-Disconnected/Clamped, `0x7` = Full-Enabled; find the FIRST candidate register whose low 3 bits == `0x3`;
  4. ONE reversible bit-write: `value | 0x4` (set bit2: 0x3 -> 0x7, Full-Enabled); restore = clear bit2 (original value recorded in the JSON log);
  5. alive check + single-register readback; NO further writes; arbiter re-read is a separate step.
- Expected signal: after the unclamp write, `mmUVD_POWER_STATUS`/`mmUVD_VERSION` (single-reg arbiter) leave `0xFFFFFFFF` -> bridge passing. No change -> the register candidates are wrong or the bridge is boot-time-only (the runbook's alternative model).
- Wedge risks: NBIO-space SMN reads/writes are an unproven class (Sep-3 survey never reached them); recovery = cold power cycle; the board session state is volatile anyway.

## S4 result (2026-09-12 05:31 PKT, hardware-verified): NBIO reads safe; no clamped candidate; no write

- Executor `stage4_s4_nbio.py` (SHA-256 `ab307782fe286f6472fd4668e709632813df74604ad7ebc31ec1c28374b0f5d9`; first run crashed on a logging-format bug AFTER the verdict — verdict-decision logic unaffected; clean re-run JSON `~/vcn_unlock/stage4_s4_nbio_20260912_053126.json`).
- **NBIO-space single-register SMN reads are SAFE** (six reads, twice, no wedge — the class is proven, unlike DF-space reads).
- Values (reproduced identically twice): `0x13b1005c=0x00008000`, `0x13b10060=0x0000ffff` (low3=0x7), `0x13b00084=0x00000108`, `0x13b0004c=0x00800000`; gasket-diff addresses `0x13b103f8=0`, `0x13b10400=0`.
- **No candidate carries the PEIM's clamped `0x3` port-config pattern** -> per the S4 prescription ("ONE reversible bit-write" only where the clamp is found), NO write was performed. The chain report's own warning ("точные регистры NBIF всё ещё нужно доказать") is now experimentally supported: these four registers, in this boot state, do not hold the clamped config.
- Combined with the S2-A arbiter verdict, the evidence now favors the chain report's model: PSP applies the gasket and hardware-locks the Fabric translation matrices until cold reset; the runtime-programmable data registers do not re-open the bridge.
- Next decisive step (offline, no board risk): static analysis of `robin3_uefi/disasm_*` `AmdNbioGfxARIPei` — trace where Init Config Struct offsets `0x1e0/0x1e1` (the `0x3` writes) serialize in NBIO space; derive the TRUE NBIF registers instead of the disproven candidates.

## P1.5 static RE, session 1 (2026-09-12): AmdNbioGfxARIPei helpers decoded — NEW SMN register class found

Source: `recon/disasm_AmdNbioGfxARIPei.txt` (25,318 lines). Decoded:

- Helper `0x6a3(instance ECX, index EAX, smn_addr, &out)` = SMN READ through the PCI `0xB8` window: base from `[instance+0xe]`, `OR EBX,0xb8`, dword-align, stride `0x83/0x103` per index, result -> `*out`. The address argument is used DIRECTLY as a hardware SMN address (same path as the live-proven `0x13b1005c` reads).
- Helper `0x75b(instance, smn_addr, and_mask, or_mask)` = READ-MODIFY-WRITE: `reg = (reg & and_mask) | or_mask` via `0x6a3` + `0x72d`(write with arg 3).
- Helper `0x72d(&out, smn_addr)` = plain SMN read variant (arg `0x3` to `0x140a`).
- The PEI init therefore performs these REAL SMN RMWs (tokens = live NBIO SMN addresses, NOT IDS table offsets as previously assumed): `0x6a148 <- (reg & ~0x00800000)|v`, `0x6a14c <- (reg & ~0x8)|v`, `0x6a150 <- (reg & ~0x7ffffe)|MSR 0xc001001a`, `0x6a154 <- (reg & ~0x7ffffe)|(MSR 0xc001001d|1)`, `0x6a15c/0x6a17c/0x6a1b4` reads/derivations, `0x33e0 <- (reg & ~0x2)`.
- The four `0x13b1xxxx/0x13b0xxxx` calls are READ-ONLY captures of hardware state into the config struct (explains why they hold no clamped pattern).
- G4 intent for the follow-up read-only capture: single-register SMN reads (proven transport) of `0x6a140, 0x6a144, 0x6a148, 0x6a14c, 0x6a150, 0x6a154, 0x6a15c, 0x6a17c, 0x6a1b4, 0x33e0` on the live board (session still up: unlock open, domain powered). New SMN region — wedge risk unproven; stop-on-timeout, cold cycle recovery. Expected signal: current values vs. the PEIM post-init state -> identify which NBIF config writes are missing/different on BC250.

## P1.5 static RE, session 1 continued: serializer decoded — the 0x3 clamp reaches the APCB token stream (offline)

- The serializer block (`0x6946..0x6a4c+`, and the `0x7322/0x7342` + `0x7354/0x7374` snippets) emits APCB token records: `word token_id` + type/size byte (`AND 0xfc`, `OR 0x2`) + payload copied from Init Config Struct fields (`0x1a2, 0x1a3, 0x1a7, 0x1ab, 0x1ac, ...`), including **token `0x10c2` <- byte [struct+0x1e0] and token `0x10c3` <- byte [struct+0x1e1]** — the fields written to `0x3` (Port-Disconnected/Clamped) at PEI (`0x2404/0x240e`).
- Chain confirmed end-to-end: PEI writes `0x3` into struct `0x1e0/0x1e1` -> serializer emits APCB tokens `0x10c2/0x10c3` (NBIF_VCN_PORT_CONFIG / NBIF_VCN_BRIDGE_ENABLE) -> the APCB token stream (flash `0xAB1000` region) is consumed by NBIO init at boot -> NBIF VCN port/bridge clamped.
- NEW flash-candidate idea (P3.3b, not built): if tokens `0x10c2/0x10c3` EXIST in the board's current APCB token stream with value `0x3`, an in-place `0x3 -> 0x7` byte edit + APCB checksum byte is the smallest possible boot-time clamp release (S5-style, no relocation). If the tokens are ABSENT (Robin omits VCN tokens like it omits the gasket bank), adding them grows the APCB — higher risk. Parse the current APCB token stream offline first (`scripts/firmware_audit.py` inputs at `0xAB1000`, size `0xB70`).
- Live capture of `0x6A1xx/0x33e0` registers: BLOCKED this session — the board went down before the run (`stage4b_nbif_config_capture.py` deployed and compiled, not yet executed; intent logged above). Board state at last contact: the fully brought-up cycle-#4 session; currently unreachable (no route) — requires operator power-on + mode1 boot.

## P1.5 static RE, session 1 finale: APCB token scan — VCN NBIF tokens ABSENT from the flash APCB (offline)

- Scan (`/tmp/bc250-stage2a/scan_apcb_tokens.py` on the current chip image `postwrite-apcb-restore-20260912.bin`, SHA-256 `6b1fe8ef...`): **tokens `0x10c2` and `0x10c3` do NOT occur anywhere in the APCB block (`0xAB1000`, `0xB70` bytes)**. Other flash matches are byte coincidences outside the APCB.
- Conclusion: like the SEC_GASKET VCN bank, Robin's APCB omits the VCN NBIF tokens entirely. The PEIM's runtime serializer (`0x6946+`) builds the merged token list in memory at boot — the `0x3` (clamped) values are injected there, not stored in flash. Fail-closed by absence: no token = clamped port/bridge.
- P3.3b ("in-place 0x3 -> 0x7") is DEAD — there is nothing to flip. An APCB-level release would require ADDING tokens (growth + checksum + the already-demonstrated APCD/APCB boot-unsafety class) — low probability, not recommended.
- State of the unlock-path map after this session: the bridge clamp is produced at boot from the ABSENT-token default plus the PEIM's hardcoded `0x3` struct fields; changing it needs either (a) the runtime trusted transition (P1.5 executor RE — primary), or (b) boot-time token injection (structurally risky flash path). The `0x6A1xx/0x33e0` register capture (script ready on board) remains the cheapest next live experiment. Board left in the fully brought-up session (rollback = power cycle whenever).

## 2026-09-12 ~05:5x UTC — P1.5 offline decode session 2 (SMN primitives + token consumer search), board DOWN

- Operator directive: "изучай биос, плату включу как упрешься" — offline BIOS study until full understanding; board stays powered off (no route since ~05:3x, not rebooted).
- Target: complete the NBIF clamp chain structure in `disasm_AmdNbioGfxARIPei.txt` / `disasm_AmdNbioPcieARIPei.txt`.
- Commands: `grep`/`Read` over `import/.../tmp_bc250/recon/disasm_AmdNbioGfxARIPei.txt` (helpers `0x13d9/0x140a` at lines 1878-1941, `0x143c` dispatcher 1942+, defaults block 2940-3059) and `disasm_AmdNbioPcieARIPei.txt` (serializer 13100-13209).
- Findings (static-analysis):
  - F1: `0x143c` = SMN-window access dispatcher: size codes 1/2/3 (byte/word/dword) dispatch to `0xe0000000`-window primitives; sizes >= 0x81 route to the `0x846` bulk helper. Confirms the PCI `0xB8`-index + window model for ALL NBIO SMN access in these PEIMs.
  - F2: `0x13d9`/`0x140a` = token read/write wrappers over `0x983` (index program) + `0x143c` (window access, with stride `EBX+ESI` next-address computation). Token args are real SMN addresses.
  - F3: The giant defaults initializer (`0x22a3..0x24f8+`) writes the Init Config Struct unconditionally: VCN fields `+0x1e0/+0x1e1` = `0x3` (clamped) at `0x2404/0x240e`; neighbors `+0x1e2/+0x1e4/+0x1e5/+0x1e6/+0x1ea` = `0x7` (Full-Enabled). The clamp is a hardcoded default, not measured hardware state.
  - F4: `AmdNbioPcieARIPei` has its OWN serializer emitting the SAME shared token IDs (`0x0aa72` -> token `0x10c2` <- `struct+0x1e0`, `0x0aaa4` -> `0x10c3` <- `struct+0x1e1`, plus the `0x109x/0x10ax/0x10bx/0x10c0-0x10c1/0x10c4+` run). Token IDs are shared AGESA NV tokens; the consumer engine is NOT in these two PEIMs (no compare-against-token loops found) — likely the common AGESA token engine or the PSP/ABL side.
  - F5: Full clamp chain now has 5 decoded stages (defaults -> serializer -> APCB RAM merge -> token engine -> NBIF SMN RMWs) plus the separate PSP SEC_GASKET firewall/lock stage. Documented in `docs/research/2026-09-12-nbif-clamp-mechanism.md`.
- No hardware touched. No files modified besides the research doc and this log.
- Remaining uncertainty: token ENGINE location and per-token register targets; whether the Fabric translation lock (PSP gasket lock) guards the routing registers (`0x6A1xx/0x1C7xx/0x1F8xx`) or only the firewall targets. The live `0x6A1xx` capture (`stage4b_nbif_config_capture.py`, deployed) discriminates the routing-register writability question in one run.
- Next: ARM-side RE of ABL/PSP blobs (`recon/robin3_psp_bodies/`, `disasm_arm_binary.py`) for the gasket executor and the token engine; live capture when the board returns.

## 2026-09-12 ~06:10 UTC — NEW METHOD: ProbeApp v4 (DXE/UEFI-Shell, zero-flash) built and validated; keys verdict confirmed

- Operator directive: "изучай биос досконально, найди новый способ анлока, например dxe driver, или реверс инженеринг ключи".
- Reused the E1-era EDK2 package (G3): sources `tmp_bc250/dxe/Bc250VcnUnlockPkg/`, tree `tmp_bc250/worktrees/edk2-bc250-capture/` (Linux ELF BaseTools already built). Copied the package to `candidates/bc250-vcn-probeapp-v4/Bc250VcnUnlockPkg/` and rewrote the ProbeApp source.
- ProbeApp v4 changes vs v3 (2026-08-26), each grounded in hardware evidence from this session:
  - F1: added the FULL donor dataplane route list (stage5: NBIF `0x1C760/64/80/84/88/8c <- donor b2a values`, NBIO `0x1F820 <- 0x185103`, `0x1F8A4` ×2, IOHC `0x322` windows ×3, DF mirror `0x3D2` ×2, VCN_SEG binding `0x3E810/0x3E814`). v3's partial DF values (`0x01E0A414` etc.) preserved in comments as provenance — they conflict with the donor b2a capture; donor values win (hardware-verified end-state).
  - F2: added the dom6 gate release write `0x06D0F8 <- 0` BEFORE the 0x61 fire (2026-09-12: LANDED and HELD; boot value 0x02 = gate hold).
  - F3: added BAR5 MMIO arbiter reads (UVD_VERSION `0x20f24`, POWER_STATUS `0x1f810`, NO_OP `0x20efc`): baseline after unlock + verdict after gasket+routes. Transport class proven 2026-08-25 (post-clock BAR5 reads: all-ones + NO hang). Write-first discipline kept: NO DF-space SMN reads, NO Q3 0x2A reads in UEFI.
  - F4: alive checks (Q3 test msg 0x01) after unlock / fire / gasket / routes; stop-and-report on any failure (cold cycle = rollback).
  - F5: chainload Limine same-session kept (zero reboot -> VCN state persists into Linux).
- Build: EDK2 2025 tree (GCC5 toolchain REMOVED upstream — used `-t GCC`); Conf regenerated fresh in `/tmp/bc250-edk2-conf` (the tree's Conf was a WSL artifact pointing to `/mnt/c`); nasm 3.02 extracted locally from the official Arch mirror (no system change). Build OK, 7s. The tree received only additive `Build/Bc250VcnUnlockPkg/` output; no source modified.
- Validation (G9, structural layer only): both artifacts PE32+ x86-64, MZ/PE signatures OK.
  - `candidates/bc250-vcn-probeapp-v4/bin/Bc250VcnProbeApp.efi` — 28,672 B, sha256 `c8a97360474a158388bcf804658adc0a233c28e45ccdd2fdfd35173be08edeae`
  - `candidates/bc250-vcn-probeapp-v4/bin/Bc250VcnUnlockDxe.efi` — 12,288 B, sha256 `ca461899931f58be988806e7e0447c7be796ced2a56269088b96d8a8d978663c` (v3 driver source rebuilt; the DXE variant still needs the v4 sequence ported before BIOS integration)
- NOT verified (explicit): boot behavior, UEFI Shell run, arbiter values — hardware layer untouched. A successful build is not proof of boot or device function (G2/G9).
- Keys verdict (operator question "реверс инженеринг ключи"): per VCN-LOCK-MECHANISM §6 (canonical, 2026-09-03): the $PS1 signature scheme is deterministic and NON-STANDARD (byte-identical nonce+signature across 4 independent gasket samples; offline RSA recovery tried: modulus × 3 signatures × 2 endian × 15 spans × 4 hashes = empty — likely AES-wrapped signature with fused key by key-id). DEBUG_UNLOCK 0x13 = challenge+token against the AMD RSA-2048 key — forgery closed. The ONLY live keys question is the SOFT-FUSE test: whether the PSP gasket loader verifies the signature at all (path A: modified gasket 0x24+0x45 with the VCN bank, repointed PSP dir — ALREADY BUILT and 26/26-verified offline in the September analysis; one flash test answers soft-fuse; recovery = programmer, field-proven).
- Remaining uncertainty: UEFI-era behavior of the Q2/Q3 mailbox under a freshly booted shell (v3 was never hardware-run); donor-route acceptance at DXE time (the same open question as stage5 at Linux runtime — the v4 run discriminates it pre-OS).
- Board prereq for the trial: USB stick with `Bc250VcnProbeApp.efi`, UEFI Shell entry, display+keyboard on DP-1.
