# 2026-09-23: probe3 built (auto file-save + auto reboot); USB boot payload staged

Intent: the operator approved the Probe2 run (UEFI context read) and asked
for a fully automated loop: minimal operator actions (reboot + one-time USB
boot pick), the probe writes its data itself, the board returns to Linux
itself, and the agent times the return and reads the file over SSH.

Investigation first:

- Bc250VcnProbe2.c reviewed: Print()-based output, read-only SMN reads via
  PCI 0xB8/0xBC, no file write, no reset — the automation had to be added.
- Shell search (read-a.bin stock: 188 files; community donor 606a7a7f:
  193 files; no nested FVs): NO UEFI Shell module exists in either image.
  A Shell+startup.nsh+redirect route is impossible on this firmware; the
  self-contained BOOT app is the only clean route.
- Bc250VcnProbeApp (v4, /tmp/edk2ws scratch) donated its proven
  SimpleFileSystem handle-walk pattern; /tmp/edk2ws workspace still alive
  with Linux-built BaseTools in the import capture
  (BaseTools/Source/C/bin, GenFw ELF x86-64).

Built (probe3, supersedes probe2 for the operator loop):

- Source of record: candidates/vcn-unlock-driver-v000-DRAFT/Bc250VcnProbe3.c
  - .inf (new FILE_GUID e14a3821-...-b62507802b0d). Reads the exact probe2
    register set (read-only, no mailbox); writes \probe2-out.txt only to the
    volume carrying the \PROBE2.TXT marker; then EfiResetCold. Fallbacks:
    no marker volume -> console-only report; ResetSystem returning -> normal
    exit so the boot manager continues to Linux.
- Build recipe (no import writes): WORKSPACE=/tmp/edk2ws,
  EDK_TOOLS_PATH=<capture>/BaseTools, CONF_PATH=<capture>/Conf,
  PACKAGES_PATH=/tmp/edk2ws:<capture>, GCC_BIN=/usr/bin/, toolchain GCC,
  build.py direct + PATH+=<capture>/BaseTools/BinWrappers/PosixLike
  (Trim lives there; that was the first failure). First build failed on a
  real compile error in my source (PCI_SEGMENT_LIB_ADDRESS given 4 args
  instead of 5) — fixed, rebuild green.
- Artifact: Bc250VcnProbe3.efi, 32768 bytes,
  PE32+ EFI application x86-64 (2 sections), RELEASE, -Werror clean,
  sha256 `c281d5d8a70656ba26422229f0bf8fed4147fc3aa585db4cd44313e01140dc48`.
  Copied to candidates/vcn-unlock-driver-v000-DRAFT/bin/ (hash identical)
  and verified: UTF-16 strings PROBE2.TXT / probe2-out.txt and the banner
  present in the image.

Staged (no flash — a BOOT stick):

- firmware-flash-pkg/20260923-probe2-usb/:
  EFI/BOOT/BOOTX64.EFI (= probe3, hash above), PROBE2.TXT marker,
  README.md (prep + loop + honest hang-risk note), SHA256SUMS.
- scripts/probe2.sh: `push` (write payload to the stick over SSH, one-time)
  and `fetch` (timer: wait for the board to leave, wait for fresh return,
  mount the stick read-only, pull probe2-out.txt into evidence/runtime/,
  print the descriptor verdict). bash -n OK; live run not yet performed
  (needs the stick on the board + the operator's reboot).

Risk boundary: probe3 does zero register writes, zero mailbox messages;
its only write anywhere is probe2-out.txt on the marked stick. First-contact
SMN reads at the late-boot phase keep the measured 2026-09-12 wedge class
risk: if the board hangs, recovery is a cold power cycle (board boots its
current P3.00; nothing persisted). The operator must pick the USB ONE-TIME
in the boot menu, never change boot order (a probe -> reset -> USB loop
would otherwise cycle).

Gates: pytest tests/ 83 passed (30.8 s); make test 7/7 OK.
Nothing flashed, no firmware image or candidate ROM modified, board
untouched (read-only SSH checks only).

Session follow-up (same evening, read-only checks, no writes):

- scripts/probe2.sh: find_stick_dev now requires RM=1 (removable) so the
  NVMe ESP (also vfat, /boot nvme0n1p2) can never be picked as the "stick";
  TIMEOUT_DOWN raised to 600 s for operator slack.
- First-run blocker: the operator's 32 GB stick did not enumerate anywhere.
  The board sees only the Ugreen dual-bay (sda/sdb, btrfs) and the
  keyboard-hub dongle; USB buses 1-5 (EHCI/OHCI) carry zero devices; dmesg
  USB history is flooded away by the 1 Hz BC250-METRICS logger. The agent
  host shows no stick either (only an empty Genesys microSD reader and an
  unrelated MAFP gadget, vendor-specific, no storage driver). Verdict sent
  to the operator: dead port or dead stick; re-plug into a known working
  port; any stick >=512 MB will do (agent formats and pushes it).
- Plan (psp-breach.md Re-ranking sequence) updated with the probe3 route
  note: no Shell in either image, probe3 supersedes the Shell-launched
  probe2 for the operator loop, live run pending on the stick.

## Run 1 (2026-09-23 ~21:05-21:38): wedge at first SMN read — empirical negative

Operator loop executed for the first time (stick present this evening). Facts,
in order:

- Payload pushed to the stick (sdc2 vfat 23M, auto-mounted ARCHISO_EFI) after
  fixing find_stick_dev (lsblk PATH -> NAME; /dev//dev/sdc2 mount failure).
  The stick is an archiso install stick; its EFI/BOOT/BOOTX64.EFI was replaced
  by the probe payload; ISO data (sdc1) untouched.
- Operator rebooted, picked the USB stick ONCE in the boot menu (item 2 —
  one-time pick, boot order unchanged; correct).
- Screen showed exactly the probe banner
  `BC250 VCN probe3 (auto: file save + reboot; registers read-only)`
  and nothing else, indefinitely. Source order proves the wedge point: the
  banner is printed, then the second line's arguments call the FIRST
  SmnRead32 (SMN 0x0115D000, clock plan A) via PCI 00:00.0 B8/BC — the line
  never printed, the app has no key input, the board never self-rebooted.
  Verdict: first-contact raw B8/BC read of SMU clock-plan space at the
  USB-boot-app phase WEDGES the board (the README's declared 2026-09-12
  wedge-class risk, now hardware-observed for this address family).
- Recovery: operator cold power cycle. Board returned 2026-09-23 21:37:29,
  kernel 7.2.6-1.206-cachyos-bc250, captured by the fetch watcher
  (restarted after its own TIMEOUT_BACK arg bug was fixed: a top-level
  ${1:-420} read the mode word "fetch"; crashed on $((fetch/5)) — see
  MISTAKES.md 2026-09-23 entry).
- Stick check after return: probe2-out.txt missing/empty — consistent with
  the wedge BEFORE the save step (save runs after all reads). The probe's
  no-marker fallback (console-only) also never printed: the wedge precedes
  any further output.

Consequence for the plan: the raw B8/BC boot-app read route is CLOSED for
the clock-plan/SMU register set. Next probe (probe4) must use a proven
transport: the SMU mailbox chain (Q2 unlock 0x23 -> Q3 secure read 0x2A,
hardware-proven at early-DXE in the d10 experiment: read SMN 0x0005A870,
status 0x01, value 0x77, SMU alive after) instead of raw SMN window reads.
Build environment intact (/tmp/edk2ws + import-captured BaseTools, per this
log's build recipe). No firmware or board state was modified by the run;
nothing was written anywhere except the payload push (already logged above).

## Probe4 built and staged (2026-09-23 ~21:50): mailbox transport replaces raw SMN

Design (response to the run-1 wedge): same target register set as probe3,
different transport —

1. SMU debug unlock: the hardware-proven D9R/D10/d19 PerformSmuUnlockDxe
   sequence (Q2 0x23 ring writes x2 stages + Q2 0x0A DMA-table messages +
   Q3 0x28/0x29 SRAM fixup), copied verbatim from
   candidates/d19-gasket-c830-only/source/.../Bc250VcnUnlockDxe.c. Already
   unlocked -> skipped and reported. Mailbox fully silent -> early abort.
2. All reads via the SMU's own Q3 0x2A secure-read service (d10-proven:
   SMN 0x0005A870, status 0x01, SMU alive after). The raw PCI 0xB8/0xBC
   window touches ONLY the Q2/Q3 mailbox registers (0x03B1xxxx) — the
   measured-safe address class. NO raw reads of SMU/DF/VCN space.
3. A line printed per phase and per read: if anything wedges, the last
   screen line names the step and address (run 1's banner-only screen
   proved the need).
4. Survey aborts after 3 consecutive mailbox TIMEOUTs (dead SMU), saves
   the partial report, reboots. Honest change: probe4 is NOT read-only —
   the unlock writes SMU SRAM (proven sequence; non-persistent; recovery
   unchanged: cold power cycle).

Built with the probe3 recipe (WORKSPACE=/tmp/edk2ws, upstream/edk2 capture
BaseTools, GCC RELEASE X64): Bc250VcnProbe4.efi, 36,864 bytes, PE32+
EFI application x86-64, 2 sections, -Werror clean,
sha256 706c9ddb818365ec7699ecc1a19f8c3f2717e43b7f490699fd30f3caa5df909a.
Verified: banner, phase lines, all read tags (planA/planB/bitmap/status/
reqbits/descA/descB/ctl), UTF-16 PROBE2.TXT/probe2-out.txt, timeout-abort
line present in the image. FILE_GUID dce26c2e-da12-4bb4-8115-a4d974530df0.

Source of record: candidates/vcn-unlock-driver-v000-DRAFT/Bc250VcnProbe4.c
+.inf; build copy in /tmp/edk2ws/Bc250VcnUnlockPkg/Bc250VcnProbe4/ (DSC
entry appended). Staged: firmware-flash-pkg/20260923-probe4-usb/
(BOOTX64.EFI hash above + PROBE2.TXT + README + SHA256SUMS);
scripts/probe2.sh PKG repointed (overridable via PROBE2_PKG). Payload
pushed to the stick (sdc2, auto-mounted). Gates: pytest 83, make test 7/7.
Run 2 pending: operator reboot + one-time USB pick.

## probe4l run 1 (2026-09-23 22:14, Linux over SSH — no reboot): first hard data + a new wedge class

After run 2 closed the USB-boot-app route entirely (the SMN window wedges at
ANY transaction at that phase, transport-independent), the read moved to the
proven Linux mailbox chain (~/vcn_unlock/bc250-smu-unlock: unlock.py +
sec_smn_read32 = Q3 0x2A). scripts/probe4_linux.py pushed and run as root.

Measured facts (probe4l_221448.json):

- **The SMU debug gate is ALREADY OPEN on a v001 boot** (secure_access_enabled
  = true, no unlock needed): 0x2A of 0x0005A870 returned status 0x01, value
  **0x000000FF** — the 8-core mask is live (MeiMeiDXEv3 active).
- **Domain bitmap 0x0000CCB8 = 0x00000000** — hardware-observed: the VCN
  domain bit (6) is CLEAR on this boot; the permission map is all zeros.
- **NEW WEDGE CLASS: 0x2A of a hard power-island register kills the SMU.**
  The 0x2A read of 0x01D80218 (power status, the power-gated island) timed
  out and the SMU went dead (alive_after=false) — while the HOST SURVIVED
  (script completed, JSON saved, SSH fine). So 0x2A reads of SMU-local SRAM
  (0x0005A870, 0x0000CCB8) are safe; a 0x2A that makes the SMU touch
  unpowered/gated hardware wedges the SMU itself. Recovery: cold power cycle
  (the project's proven path for a dead SMU).

Consequences:

- The VCN "domain not permitted" state is now hardware-observed (bitmap 0),
  corroborating the static gasket analysis.
- The clock-plan words (0x0115D000/D004) were NOT reached (the reader died on
  the status register before them). Next run order: sanity 0x5A870 ->
  0x0115D000/D004 (the prize) -> descriptor window -> STOP; never re-issue
  0x2A against 0x01D8xxxx (measured wedge) and treat 0x0115Fxxx as
  suspect-until-proven.
- The Linux route itself WORKS: no reboot, no USB pick, seconds per run,
  partial data saved even on wedge. This is the operator loop from now on.

## probe4l run 2 + probe4l2 battery (2026-09-23 23:44-23:47, Linux route, board fresh-booted 22:19): COMPLETE, units closed at the query surface

After the operator's cold cycle (board up 22:19:32), probe4_linux.py (v2 read
order: SRAM sanity -> clock-plan words -> descriptor window; no 0x01D8xxxx,
no 0x0115Fxxx) ran to completion with the SMU alive throughout:

- Gate already open again (v001 boot), core mask 0x0005A870 = 0x000000FF.
- Domain bitmap 0x0000CCB8 = 0x00000000 again (VCN bit 6 clear — reproducible).
- **Clock-plan words A = B = 0x0000000E** (both shadows agree).
- **VCN descriptor window 0x0115D560..0x0115D5AC: all 20 words zero — the VCN
  clock descriptor is EMPTY on the running board** (donor fill required per the
  vcn-mailbox runbook step 0b before any 0x1B power-up attempt).
- JSON: evidence/runtime/20260923-234415-probe4l-clockplan.json.

Then scripts/probe4l2_clocks.py (public driver-class query messages only) ran
twice: run 1 stopped early at c38_sel_04 because SmuRejected(0xFF) was
misclassified as death (SMU stayed alive — script bug, fixed: record rejection,
continue; only timeout/alive-false stops). Run 2 (fixed) completed the whole
battery, SMU alive before and after:

- CPU pstate ladder (q3 0x3B, pstate 0..7): 3200/2550/2325/1960/1820/1600/1271/800
  — real MHz (3200 = the top of the board's own pstate ladder; silicon = 4700S-family 8-core Zen 2 with GDDR6 per the donor lineage).
- Live core freq (q3 0x43): 2629/1400x5/1337/2386 MHz. GFX (q0 0x0F = 0x37): 2200
  MHz (the board's known max). SoC DPM (q3 0x42 = q0 0x11): 1254/500/762/762.
  Voltages (q3 0x36/0x37): CPU 724 mV, GPU 1018 mV. Current DF pstate (q0 0x13): 3.
- **Selector family (q3 0x38/0x39/0x3A): answers only for sel 0..3 (clean 0xFF
  rejections for 4..20). 0x39 = (225, 225, 425, 875) = static DF rows
  450/450/850/1750 divided by 2 — four-for-four exact; 0x3A = (112, 112, 106, 109) matching the static +0x14 k-derived fields (row3 static 109.375 -> 109);
  duplicate rows 0/1 answer identically. 0x38 = (250, 250, 750, 1200) — runtime
  values, not the static +0x18 constants (pointer array is runtime-initialized);
  top step 1200 = the FCLK default, identity not fully pinned.**

Consequence (R3 falsifier (c)): the SMU's clock answers are real MHz/mV across
every family, and the DF pstate table + /2 + k-derivation pattern are confirmed
by the SMU's own answers — units closed at the query surface. Remaining gap:
live FCLK/UCLK/MEMCLK values and the PLL coefficient slots [0x1729c]/[0x1792c]/
[0x17930] (0x2A-readable SRAM class, next run candidate).

Writes this pass: scripts/probe4l2_clocks.py (new, then rejection-logic fix;
board copy at ~/vcn_unlock/), scripts/probe4_linux.py (read-order v2; board
copy), evidence/runtime/20260923-234415-probe4l-clockplan.json,
evidence/runtime/20260923-234526-probe4l2-clocks.json (partial, kept for the
record), evidence/runtime/20260923-234734-probe4l2-clocks-full.json,
docs/research/2026-09-23-r3-clock-actuator-map.md (status, §5 rewritten with
the hardware table, §6(c) closed, §7.2 narrowed, Evidence section),
evidence/firmware-audit/20260923-r3-producer-chains/verify_r3b.py (+25 runtime
assertions). Gates: verify_r3b.py PASS, verify_r3.py PASS.

## probe4l3 + probe4l4 (2026-09-24 00:13-00:15, Linux route): 0x2A aperture measured — not a general SMN peek

After the operator's Zen 2 correction (silicon = 4700S-family, PS5-derived —
doc §5 and this log reworded, MISTAKES.md entry added), two probe runs closed
the "read the live PLL values" question:

- probe4l3 (slots): read the static doc's slot addresses through 0x2A —
  [0x1729c]/[0x1792c]/[0x17930] (PLL coefficients), [0x1745c]/[0x17488]/
  [0x17450], the DF pointer array 0x0CEFC and DF rows 0x0CF0C+0x28*p (+0x10/
  +0x14/+0x18), clock-slot base 0x0F568. ALL read back 0x00000000 with status
  0x1 (success) — except the known-good sanity reads (0x0005A870 = 0xFF) and
  one word 0x0000F56C = 0x0000077F. The phase-2 descriptor walk was skipped
  (pointer read as 0). JSON: evidence/runtime/20260924-001348-probe4l3-slots.json.
- probe4l4 (PLL windows): read the R3 §1 SMN program/poll windows of the live
  clock domains — FCLK 0x0115C0FC/0x0115C120, UCLK 0x0115C8FC/0x0115C920,
  derived 0x0115C924/0x0115C948, mirror 0x0116C0FC/0x0116C120/0x0116C124/
  0x0116C148, selector 0x0116D150/0x0116D174. ALL 0x00000000, status 0x1,
  SMU alive throughout. JSON: evidence/runtime/20260924-001510-probe4l4-pll.json
  (to be pulled with the next evidence sync).

Verdict (measured, both runs): **the Q3 0x2A secure read is an aperture over a
fixed register set, not a general SMN read.** It serves what it serves
(0x0005A870, 0x0000CCB8, the 0x0115Dxxx plan block — all returned real data)
and silently answers 0x00000000 with status 0x1 elsewhere (image-offset SRAM
slots, PLL windows). Consequences:

- Live PLL coefficients / DF rows / domain current codes are NOT readable
  through 0x2A. The remaining units/live-value route is static: decode the
  plan's low bits (FUN_0001cd80 consumer census outside the VCN window), or
  accept the public-message answers as the SMU's own truth.
- The FCLK override question (donor 1420 vs the c38 answer 1200) is answered
  empirically by the v003b flash itself: patch APCB 0160 -> 1800, flash, then
  re-run the public battery + c38. If the top step moves, the override applies.

## +VDDCR_SOC measurement points (from the pinned GenCAD netlist, for the operator's multimeter)

- **PLS1 pin 2** (the SoC buck inductor output pad) = +VDDCR_SOC — the direct
  rail point. PLS1 pin 1 = SOC_PHASE (PUS1.8 switch node; do not use as GND).
- **PRS18** (resistor, pin 1 = +VDDCR_SOC, pin 2 = GND) — alternative small pad.
- **TP18** = SOC_VSS_SENSE2 — the ground-sense point for the black probe.
- Cross-check: PUS1 pin 4 (SOC_FB) = the buck's feedback reference (RT8237E
  class ~0.6-0.8 V; NOT the rail). TP4 = the remote-sense FB_H line (also not
  the rail).
- Volt-mod constraint discovered: **OR63 feeds VDDC_SOC_SIO directly from
  +VDDCR_SOC** — the Super-IO chip rides the SoC rail, so any future physical
  SoC volt mod is capped by the SIO's max rating, not just the APU's.

## probe4l5 (2026-09-24 00:28): FULL clock-plan block read — the plan is populated, VCN window empty, donor-template found

Whole-block 0x2A read of 0x0115D000..0x0115D5AC (364 words, alive throughout;
JSON evidence/runtime/20260924-002838-probe4l5-fullplan.json). 37 nonzero words:

- Low region 0x0115D008..0x0115D0F4 (plan bits ~0x40..0x7A0): populated —
  field values incl. 0x01570049, 0x01830007, 0x0000e00e, 0x00830000, single
  bytes 0x84/0x68/0x55/0x68 (byte 0x50-0x5C, PLL-code class), 0x0a/0x0f,
  0x80000002 x2, 0x80000041/0x80000042 x2/0x00000041, 0x00010000,
  0x01ff00ff x4, 0x11/0x10.
- Descriptor-class region 0x0115D300..0x0115D334 (plan bits 0x1800..0x19A0):
  0xc0000000, 0x000186a0 (=100000), 1, 1, 0x00006003, 0x10, 0x17, 1, 0x3f.
  A populated descriptor of the same bit-packed format the VCN window uses —
  the live template for the 0b donor fill.
- VCN window 0x0115D560+ : still all zero (re-confirmed).
- No IEEE754 floats of 450/850/1750 anywhere (checked mentally against the
  nonzero words — the plan is bit-packed codes, not floats).

Consequences for the v003b build (the queue: bake -> rebuild -> re-inject):

- The 0b donor VALUES are still not derived anywhere in the repo (checked:
  runbook names the step, no value table; the community patches.hex = core
  unlock code patches, BIOS 3, no plan values; the FD donor = image only;
  v2000a delivers VCN config via its SIGNED carrier (HwIpCfg+gasket bank),
  its local dumps are PSP-area-only with no APCB — no shortcut).
- Derivation path (defined, next work chunk): (1) census the FUN_0001cd80
  consumers to map the low/middle plan bits to their controller registers
  (the same method that produced the VCN window map); (2) identify the
  0x300-region descriptor's domain; (3) transpose its filled-field structure
  into the VCN window with VCN-appropriate divider/code values
  (cross-checkable against the emulation: FUN_00024594 with the fill must
  program sane 0x0115F6xx words and pass the tail poll in emu, not just
  hardware).
- v003b build is BLOCKED on this derivation; the driver-side sequence
  (0a bit 6 -> 0b fill -> 0x1B) is unchanged and already emu-validated as a
  body with the acks converging on live SMU.

Script fix: probe4l5_final print used a missing key on the no-wedge path —
corrected to .get() after the run (data was saved before the print; no re-run
needed).
