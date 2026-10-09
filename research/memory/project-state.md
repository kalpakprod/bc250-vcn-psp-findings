# Project state

## Waveshare continuation anchor (2026-10-03)

- Latest readback-proven historical installed image5c1d; candidate4986 fixes competing CDC RX (Pico stdio USB now disabled) but no hardware upload/acceptance is recorded. Sony054c:0ce6 can be Waveshare emulation, not necessarily physical DualSense. Current computer USB inventory contains no Waveshare/CDC/BOOTSEL.
- Current metrics accept only five Linux-origin fields and5s heartbeat freshness. Physical-voltage ADC sampling, persistent freeze incidents and enabled self-watchdog were not found in current adapter source. Independent physical power monitoring is still unfinished.
- Owner requested state and continuation plan. Saved `.procoder/plans/20261003-waveshare-watchdog-continuation.md`: close CDC acceptance → independent supply/measurement wiring → integrated recorder → actual incident acceptance. No flash/hardware writes in this planning task. Older full-adapter tasks remain open.

## Current console access and 40CU default (2026-10-03)

- Update14:50:40: after reboot kernel confirmed mode3 and `active_cu_number 40`. Previous boot14:32:05–14:34:38 ended abruptly during Black Flag launch; owner reports full freeze. Cause unresolved, PlaneBC250-66. Existing NMI/hardware watchdog already active. Existing netconsole destination corrected from stale.151 to this host.228; receiver and scoped firewall rule active; real board kernel marker received, end-to-end PASS. See `docs/action-logs/2026-10-03-freeze-investigation.md`.

- Current address is `127.0.0.1`, SSH user `steammachine`, alias `steammachine`. Use this address; `.118` entries below are historical.
- Fresh liveness 2026-10-03 14:29:05 +05:00: ping/SSH UP, host cachyos, kernel `7.2.8-1.2-cachyos-bore-bc250`, booted 2026-10-02 22:11:38, BIOS P3.00 dated 12/09/2021.
- Owner requested persistent kernel 40CU enable. Changed `/boot/limine.conf` active root cmdlines at lines 27 and 370 from `amdgpu.bc250_cc_write_mode=0` to `3`. Default entry remains `CachyOS/linux-cachyos-bore-bc250`. `/etc/default/limine` and `/etc/modprobe.d/bc250-40cu.conf` already set mode 3. Exact change and agreement checked successfully.
- Rollback copy on console: `/boot/limine.conf.before-40cu-default-20261003`. No reboot or live GPU write performed. Current session parameter is still 0; kernel enable applies at next boot. Actual post-boot CU count remains untested.

## Scope

This project reverse-engineers the AMD BC-250 board and its firmware/software stack. The active areas are SPI ROM, PSP and `$PS1`, APCB/DFG, SEC GASKET policy, SMU/TOS, UEFI FV/FFS, DXE, VCN, mailbox/MMIO, and host-driver behavior.

## Historical baseline

The imported `bc250-bios` README records Phase A PSP-policy mapping as complete and a D3-B2 patch as statically built. The imported VCN documents also record unresolved hardware behavior and signature questions. These are historical claims that require fresh reproduction before use.

## Current project phase

The raw corpus has been imported and indexed. The next work is to deduplicate and promote canonical source, evidence, scripts, and specs. No firmware has been flashed as part of project bootstrap. No hardware write is implied by a build or analysis result.

## Source

- `import/IMPORT_SUMMARY.md`
- `import/REFERENCE_LAYOUT.md`
- `archives/imported/historical-bios-repo/legacy-bc250-bios/README.md`

## Current status update (2026-09-11)

- Pinned/signed `flashrom v1.8.0` through `ch347_spi` read the physically isolated SPI chip as Winbond `W25Q128.V`; two full reads match byte-for-byte and equal `dump/2.bin`, SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0`.
- Existing parsers pass on the fresh reads; one fresh extraction reproduces 234 executable module hashes.
- Offline candidates now exist in separate tracks: APCB DFG VCN candidate SHA-256 `6b1fe8ef504142d5d5273a85b6c9febdf0b1fb8fc08ebab2593281c320cb9d70` and one-field MemoryClock candidate SHA-256 `63cd074197ce26bafe7d2f943eeceb69b331cdba94f12662820de710fc193fee`. Both are statically verified and independently reviewed, but not hardware-tested or flash-approved.
- No SoC-voltage candidate exists; units, encoding, consumer, training behavior, and rail response remain unresolved.
- Native CutterMCP read-only evidence covers the CoreUnlock module; bundled Rizin covers the broader extracted module set. Additional GUI/MCP module session was attempted but could not be controlled through the current Wayland/Orca provider.
- No firmware write, register mutation, JTAG target-memory write, or flash has occurred.
- On 2026-09-11, after exact operator approval, the APCB DFG-only candidate was written to board `BC250-01`. A separate full-chip readback is byte-identical to candidate SHA-256 `6b1fe8ef504142d5d5273a85b6c9febdf0b1fb8fc08ebab2593281c320cb9d70`; stock recovery SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0` remains preserved. This supersedes the earlier no-flash status for the APCB candidate only. PSP acceptance, POST stage, VCN rings/codecs, and stability remain unresolved.
- First candidate boot observation: indicators illuminated but no display image appeared. Video-output check FAILED; boot stage and cause remain INCONCLUSIVE. A stock rollback was initially proposed as the next control, then superseded by the operator's explicit decision to continue with a freshly captured, independently reviewed combined VCN candidate while retaining stock only as recovery.
- The project objective was clarified as iterative VCN-unlock testing rather than restoration as an endpoint. After a fresh capture proved the chip still contained the exact APCB-only candidate, the independently reviewed combined D3-B2 candidate was written. Independent readback matches SHA-256 `439e248141ef6a9c1313bc7815696d570be8fed5471262596186f3da8914747d`; boot/PSP/VCN behavior remains unrun.
- First D3-B2 boot again produced the same indicators and no display. Video output FAILED while PSP/POST/VCN state remains inconclusive. The next variant removes the common APCB change while retaining both VCN policy carriers.

## Current status update (2026-09-12)

- Supersedes the 2026-09-11 "Current status update" above; see `docs/action-logs/2026-09-11-vcn-policy-only-candidate.md` for the intermediate firmware-write sequence.
- Root cause of the five no-video boots (APCB-only, D3-B2, policy-only, DXE-only, stock restore) was operator display-connector miswiring, not image content (G7 correction 2026-09-11T22:00+05:00). All those boot results are non-discriminating; stock is bootable.
- Board BC250-01 currently runs the APCB-only DFG candidate `6b1fe8ef504142d5d5273a85b6c9febdf0b1fb8fc08ebab2593281c320cb9d70` and boots Linux to SSH.
- Kernel decision (G3): reuse installed `7.2.0-1.92-cachyos-vcn-bc250` with `amdgpu.bc250_vcn_mode` 0/1/2; no new kernel build. VCN fw is green_sardine_vcn.bin (404,544 B); no cyan_skillfish2_vcn exists or is requested.
- Mode1 probe boot PASS 2026-09-11 23:51 PKT (fresh hardware evidence on current image): 9 IP blocks incl. `vcn_v2_0_probe`, VCN fw `ENC 1.24 DEC 8` found, `fw_size=404544`. Evidence: `evidence/runtime/20260912-mode1-probe-boot-audit.md`.
- Next decisive test: operator selects `linux-cachyos-vcn-bc250-mode2` at the local limine console; root repeats read-only SSH audit for real `vcn_v2_0` hardware attach, ring/IRQ init, and firmware-load errors. VCN encode/decode function remains UNRUN.
- Mode2 attempt result (2026-09-12): does not boot per operator; zero journal trace between 23:21:30 and 23:50:52 (no boot record ever logged a mode2 cmdline). Hang/reset occurred before journald activation; location INCONCLUSIVE. Hypothesis (unproven): `vcn_v2_0` hardware init hard-hangs with VCN power-gated by PSP policy. Evidence: `evidence/runtime/20260912-mode1-deep-read-and-mode2-no-trace.md`.
- Next test (pending operator approval): diagnostic mode2 limine entry without `quiet splash`, `loglevel=7`, one variable; operator reads/photographs the last console line before hang. No flash, no other change.
- Diagnostic entry installed 2026-09-12 (operator approved): mode2 cmdline in `/boot/limine.conf` and the dropin now verbose (`loglevel=7`, no quiet/splash), exactly one line changed per file, verified by diff. Rollback backups: `/boot/limine.conf.bak-prediag-20260912` and `/etc/limine-entry-tool.d/90-bc250-vcn-probe.conf.bak-prediag-20260912`. Awaiting operator mode2 verbose boot and console reading.
- Mode2 v2 verbose boot: identical console sequence (initramfs switch-root, stall on udevd stop job, then black screen even with plymouth off) — display death is the fbdev handover dying with the kernel, not plymouth.
- Controlled probe (2026-09-12 03:17-03:20 PKT, hardware-verified): mode2 booted with `modprobe.blacklist=amdgpu` reached full userspace with SSH; root-triggered `modprobe amdgpu` with local `dmesg -w` capture wedged the kernel deterministically. Timeline: 10 IP blocks incl. real `vcn_v2_0` + `jpeg_v2_0`; SMU 88.6.0 OK; custom `bc250-40cu-enable` GC writes COMPLETED; `kiq ring` set; then `clocksource: Watchdog remote CPU 4 read timed out` and total silence (no panic, no VCN lines). Differential vs mode1 (boots, no VCN MMIO) proves the wedge is the first VCN hardware access in `vcn_v2_0_hw_init`: VCN domain is power/clock-gated by PSP/SMU. Log: `evidence/runtime/20260912-mode2-controlled-probe-dmesg.log` SHA-256 `e9c830f8f231c1e803677d4b67ad7b3154885223a7d95ac86cabddd89169c66d`.
- Installed 1.92 kernel is newer than corpus `recon/linux.patch` (prints `bc250-40cu-enable` vs patch's `ps5-40cu-enable`; no `bc250_vcn_mode` in the patch copy).
- Next branch: firmware policy retest — flash reviewed D3-B2 `439e2481...` with fixed display wiring (needs exact operator approval), boot mode1 for video/PSP-acceptance check, then repeat the controlled mode2+blacklist+modprobe probe. No-flash alternative: S2 runtime C2P mailbox unlock from booted OS. Bootloader diagnostic entries to restore from `.bak-*` after the campaign.
- Open track after mode2: if hardware block attaches, run user-visible codec test; if not, capture the exact failure mode (firmware load, hang, missing block) and return to the PSP policy/signature branch per the ranked sequence S1-S5 in `docs/research/2026-09-11-vcn-unlock-synthesis.md`.

## S2-A runtime pivot (2026-09-12, approved, awaiting execution)

- D3-B2 retest with corrected display wiring: board does not boot (PSP signature/policy rejection is the leading explanation; G7 in `memory/firmware-audit.md`). Unsigned policy-relocation branch closed as implemented. APCB-only `6b1fe8ef...` restored and booting mode2+blacklist reliably.
- S2 C2P preflight on BAR5: `0x100B` token request clean-negative (TOS not answering direct C2P commands); BAR0 mmap EINVAL, `/dev/mem` EPERM, BAR5 mmap OK.
- Operator approved S2-A runtime donor-aperture experiment via SMU secure path: full stages 0-4 and pre-approved Q3 msg 0x61 with `vcn_watch`. Runbook: `docs/action-logs/2026-09-12-s2a-runtime-donor-aperture.md` (revised stage order: stage 2a = `smn_lock_probe.py --phase-b` latch discriminator as the first and only write before any donor-aperture work).
- Campaign corpus fully mined and registered (`memory/firmware-audit.md` section 2026-09-12): PMFW t08 blob in current image is byte-identical to robin3 `SMU_OFFCHIP_FW~0x8_0.58.6.0` (unlock.py offsets valid); historical 1461-write replay wrote Robin KILL values, donor stage-A values never written at runtime; writes to gasket address classes proven non-wedging, DF-space/VCN-MMIO reads are the wedge hazards.
- Next action (blocked on operator): reboot board into mode1 (`amdgpu.bc250_vcn_mode=1`), then Stage 0 read-only baseline, Stage 1 SMU unlock, Stage 2a phase-b discriminator. Rollback for all runtime stages = cold power cycle; stock recovery `read-a.bin` `83c4e420...` preserved.

## S2-A executed: runtime gasket latches, bridge still closed (2026-09-12, hardware-verified)

- The approved S2-A runbook was executed to completion (4 cold-power-cycle wedges total, all recovered; SPI untouched). Full chronology, wedge taxonomy, and verdict: `docs/action-logs/2026-09-12-s2a-runtime-donor-aperture.md` and `memory/firmware-audit.md` section "S2-A runtime donor-aperture experiment".
- **Result: the SMU runtime path programs the VCN gasket (59/59 writes accepted, bank-12 commit=1), and the full domain bring-up verifies (gate released, slots clocked ON, up-ack), but the island remains isolated (arbiter all-ones, clean reads).** The NBIF/Fabric bridge (G5) does not pass from the runtime path.
- Proven repeatable bring-up order: mode1 boot -> unlock Q2 0x23 -> `--manual-powerup` -> fire 0x61 -> 59 gasket writes -> single-register arbiter (`stage4_arbiter.py`). Full-dump `amdgpu_regs` reads and DF-space reads are closed wedge classes; single-register reads and gasket writes are the proven transports.
- Next lever (needs a new runbook + operator approval): S4 NBIO bit-writes `0x13b1005c/0x13b10060/0x13b00084/0x13b0004c` then arbiter re-read; alternative model: bridge re-samples gasket only at cold reset (boot-time-only). Board bootloader diagnostic entries still to restore from `.bak-*` after the campaign.
- S4 executed same day (operator approved): NBIO single-register reads are a SAFE class; the four chain-report candidates hold `0x00008000/0x0000ffff/0x00000108/0x00800000` — no PEIM `0x3` clamped pattern, no write made. The candidates are experimentally unsupported; favored model is now the PSP hardware-locked fabric translation (boot-time-only). Next decisive step is OFFLINE: static `AmdNbioGfxARIPei` disasm analysis (Init Config Struct `0x1e0/0x1e1` serialization -> true NBIF registers). Board left in the fully brought-up session.
- Complete unlock-path inventory with post-campaign statuses: `docs/research/2026-09-12-unlock-paths-map.md` (P1 runtime SMU: transport proven/transition missing; P2 UEFI same-session: Bc250VcnProbeApp.efi exists, same blocker; P3 flash ladder: unsigned/APCB closed, D3-C deprioritized, DEBUG_UNLOCK dead; P4 staged kernel 0012: designed, not built; P5 TEE/TOS: no path, C2P measured negative). Primary path = offline static RE of the SEC_GASKET executor (P1.5a/b); E1 DXE-only no-boot result corrected to non-discriminating (predates wiring fix).

## Board state + flash-ladder audit (2026-09-12, supersedes "runs APCB-only" line above)

- D20 restore DONE 2026-09-12 (SPI + boot + unlock): chip holds D10R `addef288...`; mode1 is now the limine default (one-line change, backup `.bak-d20-mode1`, fallback = stock 1.1); fresh mode1 boot on `7.2.0-1.92-cachyos-vcn-bc250` with `vcn_mode=1`; SMU `alive=True`, `open_before=True` live. Flash moratorium holds. Next: DF pair-enumeration readback (safe transports only).
- Live battery 2026-09-13 (all PASS): Q0 first contact (`0x02->0x580600` = SMU 0.58.6.0, `0x03->8`); Q0 queries (gfxclk 2000 MHz x2 routes, WGP 12, core-pstate 6, DF-pstate 3); dom6/7/15 gated-0, dom14 `0x41`, dom17 bit31 marker; VCN fw ENC 1.24/DEC 8 loaded in probe; GPU KFD node live; display WARN triaged benign; D20 evidence + 4 MCP sessions re-verified. Full record: `docs/action-logs/2026-09-12-live-system-battery.md`; Q0 track: `docs/action-logs/2026-09-12-q0-table-track.md`. Gated next: Q0-2 DMA read, Q0-3+0x5C, slave IPC.
- Audit verdict: D19 single-variable claim independently re-verified (PASS); G7 correction: APCB DFG `0x007FFF00` is boot-safe (D8-D19 prove it) and was present in the whole D-wedge series, so the ReadyToBoot gasket wedge is transport/context, not missing-grant; G6 breach: method class should have changed after D14. Full record: `docs/action-logs/2026-09-12-flash-ladder-audit.md`, correction in `memory/firmware-audit.md`.

## Board UP + gaming session (2026-09-15, supersedes DOWN line below)

- BC250-01 is UP and reachable: `steammachine@127.0.0.1` via local `~/.ssh/id_ed25519` (BatchMode OK). Historical IPs `127.0.0.1` and `127.0.0.1` are stale; current DHCP lease is `.245`. Board hostname `cachyos`, kernel `7.2.0-1.92-cachyos-vcn-bc250`.
- Live gaming observed 2026-09-15 ~10:53+05:00: `ACBlackFlag.exe` (Assassin's Creed Black Flag Resynced, AppID 3751950, `/games/SteamLibrary/...`) under GE-Proton11-3 + gamescope + MangoHud, GPU busy 100%. Stock FidelityFX DLLs present in game dir: upscaler 22,348,552 B, loader 25,864 B, framegen 38,245,640 B. No OptiScaler/Xalia files in game dir; Proton built-in `xalia.exe` process running.
- VCN/SMU probing state unchanged (still parked per D17/D18); this entry records reachability + gaming use only. No writes made to the board.
- CPU exposure (2026-09-15, observed): OS sees 6C/12T (cores 0-5, possible=online=0-11, SMT on); cores 6-7 absent below OS level, no `maxcpus` in cmdline. Leading explanation: factory mining-BIOS downcore (3+3 per CCX); alternative: fused-off binning. Not a gaming bottleneck (threads ~65-70%, game ~4.5 cores).
- Disk map (2026-09-15 18:56 PKT, observed via read-only SSH): NVMe `WDC PC SN530 512G` (`nvme0n1`, 476.9G) holds `/games` (p1 ext4 372.9G, 35% used), `/boot` (p2 vfat 4G), `/` (p3 btrfs 100G, 94% used — nearly full); `zram0` 8G swap. Note: remote login shell is fish — wrap probes in `bash -c`.
- Data disks formatted 2026-09-15 19:07 PKT (operator-approved, old NTFS volumes verified empty beforehand): `sdb` CUSU C200 960GB (`YW2SHJTIWDEB2N5AGNAQ`) -> btrfs label `cusu` UUID `06d38a72-...` mounted at `/cusu` (893G avail); `sda` SSD 953.9G (`AA000000000000002119`, Ugreen USB enclosure) -> btrfs label `somnabulist` UUID `877aea7f-...` mounted at `/somnabulist` (952G avail). Both in fstab by UUID (`defaults,noatime,compress=zstd:1,nofail`), owned by `steammachine`, write-tested. fstab backup: `/etc/fstab.bak-predisks-20260915`. Full record: `docs/action-logs/2026-09-15-bc250-data-disks-format-mount.md`. Boot-time automount UNRUN (proven at next reboot only).
- Steam libraries (2026-09-15 19:37 PKT, hardware-verified): `/cusu` (lib "2", label cusu) + `/somnabulist` (lib "3") registered in `steamapps/libraryfolders.vdf` while DM stopped; after DM restart Steam enriched both entries (contentids + totalsizes) and placed app 1174180 download onto /somnabulist. Old libs "0"/"1" + all 10 app entries intact. VDF backups `*.bak-20260915`. Console stack: plasmalogin DM supervises/restarts Steam (no stable stopped window without DM stop). Full record: `docs/action-logs/2026-09-15-bc250-steam-libraries.md`.

## UC-V0 + board DOWN (2026-09-13, supersedes board-state line above)

- PEI primitive pair decoded bit-exact (`0x3c0b/0x3cf2` + 0021 DXE mirror, pure-MMIO @ E0000000, old CF8 trace retracted); stock PEI = class-0 DIRECT only; 0021 DXE DOES program DF (9 write sites — F6 retracted, second injection path + override risk); seg-3→INDEX conversion proven structurally; V1 target list EMPTY (stock→VCN seg-3 delta = 0; VCN delta = 56 seg-9 writes) → V1 BLOCKED, spec §8. Full record: `docs/action-logs/2026-09-13-pei-vni-hunt.md`; corrections: `memory/firmware-audit.md`.
- BOARD DOWN: read-only dfprobe kmod hard-hung BC250-01 at `insmod` (SSH timeout, ping 100% loss, no self-recovery; dmesg lost). Was: SMU-wedged-awaiting-cycle. OS-side DF/SMN probing parked (D17). Awaiting OPERATOR COLD POWER CYCLE (same action, higher urgency). After cycle: verify boot + SMU alive, then static-only until a UEFI-Shell .efi live-proof road is built (OQ6/OQ7, D18).

## 4700S-base campaign (2026-09-16, supersedes board-state line above)

- Board was UP and gaming on native BIOS 2026-09-15/16 (user-observed).
  M0 cross-flash (C0A-stock bb2cf51d, readback-proven) -> full silence P0
  FAIL; verdict V1 same-family/different-drop (D20). M2-full (C0A + native
  APCB, 72acddad, review PASS) flashed + readback-verified 2026-09-16;
  chip holds M2-full (proven). Awaiting OPERATOR COLD BOOT + P0 report
  (fans/LED/video/LAN + ping/SSH). Rollback images preserved
  (pre-m0 3f836668, post-m0 bb2cf51d). Goal: 4700S-based Frankenstein
  (boot -> OC -> VCN -> TPM); Track B fallback armed. D21/D22.

## 4700S campaign complete; error audit done (2026-09-17, supersedes the stale "awaiting M2-full boot" line above)

- Final ladder (all flashes VERIFIED + independent readback; recovery chain
  intact): M0 `bb2cf51d` silent; M2full `72acddad` silent; M4 `856af24b`
  (native BL graft) silent; T1 `b803cb4c` (native pre-m0 + 1-byte memclk
  pin) BOOTED to Linux — P0/P1 PASS, but firmware reverted the `0x7E5` pin
  `0x23->0xFF` (P2 FAIL; OQ-T1d); M5 `3a80f9a8` (M4 + native PEI/NVRAM)
  silent; M6 `3e75177e` (pre-m0 native + M4 PSP region 0x8E0000-0xAB1000)
  silent — LED static red, no LAN, oracle-confirmed 2026-09-17.
- Verdict: the C0A PSP region is the kill locus on BC250-01; the halt
  mechanism inside ROM->BL->TOS/ABL/SMU is UNRESOLVED (no observation
  channel was ever established). 4700S base exhausted as a bootable base.
- BHD @0xAB0000 byte-identical across C0A-stock / native / M2full; APCB
  size self-describing at APCB+8 (no BHD repoint defect exists).
- Recursive error audit: `docs/research/2026-09-17-campaign-error-audit.md`
  (register L0-L4, causal chain, forward tree). Standing rules promoted:
  instrument-first (J5 UART / TPMS1 POST before any next flash campaign);
  goal-map memo before base selection; anti-G6 standing rule (no rung N+1
  until rung N's failure is localizable or a new channel exists).
- Forward proposal (operator choice pending): R0 restore pre-m0 `3f836668`;
  R1 official P5.00 `0d6f136c` as the new base (vs clv shape); R2 OC via
  T1-down 0x14 discriminator / T1b staged flips / host governor (proven);
  R3 fTPM graft after static PSP-app check; R4 VCN S2 re-probe on P5.00
  SMU (runtime-only). Chip currently holds M6 (silent).
- Baseline anchor verified: thelamer/bc250-vcn (HEAD `e53aa40`, 2026-08-18)
  is byte-identical to the local `upstream/` copy; all five of its open
  VCN threads are closed/partial/blocked-with-cause in this project.
  Delta + adopted leads (v2000a chain, 8c-unlock rung, feature-bit naming):
  `docs/research/2026-09-17-thelamer-baseline-delta.md`; campaign spec
  `specs/2026-09-17-vcn-fclk-mem-campaign.md` (completion condition from
  the operator).

## 2026-09-17 loop runs #1-#2 + inter-run session: C1 chain fully mapped (static)

- C1 chain (all static-analysis, byte-identical native vs P5.00):
  svc #0x7C = SMN write primitive; PSP t28 dispatch 0xE6A8 (load base
  0x00E00000) -> fw_type-13 handler 0xE7BC (writes 0x00185103 -> SMN
  0x1F820) -> release block 0xFCC8 (1 -> 0x0900C004 cold-reset UVD,
  1 -> 0x1F8A4, 5 ops via table 0x188D8, also read via svc #0x7B).
- Rejection status actually returned: 0xFFFF0009 (not 0xFFFF0006).
- msg 0x8/0x9 (PowerDown/UpVcn) = NULL in BOTH SMU 0.58.6.0 and P5.00
  (byte-level, worker B, pypcode Xtensa). G7 correction: run-1 "window
  shifted +24 B" was an addressing-convention artifact (new file = SRAM
  - 0x100).
- fw_type pointer table stored in t28 @0x18AAC-0x18D48 (worker C;
  corrects root's "not stored in flash"); no flash-side staging source;
  SRAM 0x69D38 populated outside t28.
- O4 closed: CBSG schema 0717 identical; dump 68 tok / clv 72 tok / P5.00
  84 B stub. O3 map done (MemoryClockSpeed @0x316, 1000MHz=0x14; FclkDpm
  @0x6A3). T1 static closed: no fTPM app in any BC250 production image.
- O1-prep candidate built (never flashed):
  candidates/BC250_O1prep_T1down_memclk-1000MHz_v001_from_pre-m0.bin,
  sha256 a8a813b9..., 1 byte @0x7E5 0xFF->0x14.
- D25: operator selected clv (ea578104) as working base.
- Worker reports: docs/research/2026-09-17-{t28-open-questions-workerA,
  t8-smu-msgtable-workerB,staged-descriptor-hunt-workerC}.md; verdicts:
  docs/research/2026-09-17-decode-1-6-verdicts.md.
- Residual static: svc #0x7B/0x7C/0x5E/0x5F handlers (PSP director, off
  t28); upstream rejection site (validation/0x11460); r1 bitfield 0x185103.
- Gates with operator: R0 restore (pre-m0 3f836668), V4/O1 flash, base
  build-out on clv.

## FD v2.2 drivers-only port onto clv (2026-09-20, offline, unflashed)

- Whole-FV graft af531026 (Sep-17) failed at P0 (single green blink, no
  LAN/video); not repeated. New method class: surgical injection of the 6
  MeiMeiDXEv3 drivers into clv's OWN inner FV (187 -> 193 files).
- Candidate `candidates/BC250_5.00_clv_MeiMeiDXEv3-drivers-only_v001.bin`,
  sha256 0968a70c..., builder `scripts/build_fd_drivers_clv.py`. Static-only:
  PSP/APCB/BHD identical to clv, all FV/FFS checksums PASS, DEPEX satisfiable
  (1 intra-set GUID). Independent review + operator flash approval still
  required. Chip holds W11 3c50bc9a (8-core boot proven on W10 lineage); board
  unreachable (.118) at last check 2026-09-20.
- FD donor re-verified: 606a7a7f (both preserved copies match Sep-17 record).

## CLV native recipe coherence correction (2026-09-20, offline, static)

- Applied the two reviewer-required corrections from
  `docs/research/2026-09-20-clv-native-operator-recipe-review.md`:
  (1) the H1750 machine record is preserved verbatim as
  `evidence/firmware-audit/20260920-clv-native-1to1-recipe/recipe-result-H1750-historical.json`
  (sha256 `e4a2c423...`) and the canonical `recipe-result.json` was refreshed to
  `test_point=H1330-native-help` with `hardware_run: none`;
  (2) the unsupported "reduce the first experiment's stress" phrase became
  "lower historical comparison point; no safety/stress inference".
- `review_recipe.py` wiring follows the artifact split (historical artifact for H1750
  assertions, canonical artifact for coherence, one added H1330-value assertion).
  Observed: review verifier `FAIL 1/23` before -> `PASS 0/24` after; `ROLLBACK.sh`
  restored pristine bytes hash-identically and the verifier returned to the same
  single failure, then GOAL reapplication restored `PASS 0/24`.
- Evidence: `evidence/firmware-audit/20260920-clv-native-recipe-coherence-correction/`
  (`MODIFIED_FILES.txt`, `changes.patch`, `VERIFICATION.txt`, `ROLLBACK.sh`, literal
  stdout/stderr/exit captures); log
  `docs/action-logs/2026-09-20-clv-native-recipe-coherence-correction.md`.
- Unresolved: H1330 stays a static menu hypothesis (no board run, no persistence/POST,
  no independent MCLK/UCLK/FCLK measurement); independent review of the corrected
  assertion wiring is pending; no ROM/NVRAM/hardware action occurred.

## CLV $INV field-record ownership — producer-only in the UEFI set (2026-09-20, offline static)

- Question resumed from the newest prior log: the consumer of `$INV` record
  `0x1364` (`AmdSetup+0x6E6`, control record `0x1363` / `+0x6E5`) was unresolved.
- Result `PRODUCER_ONLY_IN_MODULE_SET` (644 checks, exit 0): all seven AmdSetup
  field records (`0x11ED`, `0x1204`, `0x1331`, `0x1363`, `0x1364`, `0x1373`,
  `0x1374`) appear as bare immediates in the same seven modules, one site each
  (`AmdFabricAriPei`, `AmdNbioBaseARIPei`, `AmdNbioGfxARIPei`, `AmdNbioPcieARIPei`,
  `AmdNbioSmuV10Pei`, `AmdSocBl5AriPei`, `CbsBasePei`); zero `push <token>` request
  sites and zero `cmp`/`test` immediate sites across all 233 extracted modules.
  Positive control on the same detector: `push 0x1000` `14`, `push 0x1388` `11`,
  `push 0x10FF` `1`, `push 0x1104` `1`.
- Raw census of the pinned image `ea578104…ca4cb8`: the 32-bit encodings of
  `0x1363` and `0x1364` occur exactly seven times each, all at producer stores
  inside the seven modules (attributed `0xE2D4D7`…`0xEC8483`); no other literal
  occurrence and therefore no data table carries these records.
- G7 correction: the prior wording "both exact serializers" understates the
  producer count — seven byte-identical inline serializer copies exist in this
  image. The observations for `CbsBasePei` and `AmdNbioSmuV10Pei` stay valid.
- Boundary: no UEFI consumer exists in this image for the native Setup field path;
  a computed/indirect or 16-bit-encoded consumer is not excluded, and PSP/`$PS1`,
  ABL1 and SMU/TOS were not searched. No voltage, rail, unit, clock,
  synchronization or hardware claim follows.
- Evidence: `docs/research/20260920-clv-inv-token-ownership.md`
  (`4fa011ce…` (report; hash updated after the reconciliation section was appended)), `evidence/firmware-audit/20260920-clv-inv-token-ownership/`
  (verifier `004bd876…`, result/stdout `262c9f3c…`, empty stderr),
  log `docs/action-logs/2026-09-20-clv-inv-token-ownership.md`. Repository suite
  re-run `30 passed`. Board `BC250-01` still unreachable; flash/boot gates unrun.

## CLV `$INV`/NVTB non-UEFI carrier trace — bounded negative (2026-09-20, offline static)

- Question closed for the flash image: no `$INV`/NVTB container exists outside the x86
  UEFI FV region, so PSP/`$PS1`, ABL0-4, SMU, SEC_GASKET and TOS cannot consume the
  voltage-offset records `0x1363`/`0x1364` (`AmdSetup+0x6E5`/`+0x6E6`).
- Markers: `$INV` 8, `NVTB` 1, all nine inside `0xE00000..0x1000000`; zero markers in all
  19 PSP payloads after zlib-decompressing the five compressed ABL `$PS1` bodies. Raw u16
  `0x1363`/`0x1364` = 46/39, min distance from any occurrence to any marker = 39,025 bytes,
  `0` within 64 bytes; `0` id pairs within 8 bytes; `0` ids preceded by `0xFFFF`.
- G7 clarification: `PRODUCER_ONLY_IN_MODULE_SET` is true for the token _ids_ only. The
  `$INV` container _has_ readers — generic tag lookups at `AmdFabricAriPei` RVA `0x1D3C`
  and `AmdCcxVhAriDxe` RVA `0x5AC4` (`cmp dword [..], 0x564E4924`; records from `+0x20`;
  `u16 tag` + `u8 type` + 1/2/4/8-byte payload; `0xFFFF` terminator). Observed direct
  lookup tags: `0x10FF`/`0x1104` (PEI, the tokens already recorded in
  `docs/research/20260920-clv-voltage-offset-consumer-boundary.md`) and `0x1000`/`0x1001`
  (DXE). No call site passes `0x1363`/`0x1364`; the voltage-offset consumer stays a
  computed-tag caller.
- Evidence: `docs/research/20260920-clv-voltage-consumer-trace.md` (`593226d0…`),
  `evidence/firmware-audit/20260920-clv-voltage-consumer-trace/`
  (`SHA256SUMS.final`; scanner `20d4272f…`, boundary verifier `61b84ca4…`), log
  `docs/action-logs/2026-09-20-clv-voltage-consumer-trace.md`. Deterministic re-run
  reproduced the scan JSON; repository suite `30 passed`.
- Boundary: opaque type `0x01`/`0x09`/`0x4F` bodies not decompressed; caller set of the two
  lookup functions not enumerated; no emulation, no board contact, no firmware/NVRAM/
  register/hardware write; no voltage, rail, unit, clock or safety claim follows.

## CLV fixed-voltage Setup consumer trace — PEI VR drivers identified (2026-09-20, offline static)

- Finding: fixed-voltage Setup fields are consumed in PEI by two vendor VR-controller PEIMs:
  1. `834D976F-B91A-4FDF-A45A-4DF1BF9024DA` (`VddPei`, `0xE2FA38..0xE32398` in donor FV)
     consumes `AmdSetup+0x1C6` (GFX Fixed Voltage Enable), `+0x1C7` (GFX Voltage),
     `+0x1CA` (VCORE Fixed Voltage Enable), `+0x1CB` (VCORE Voltage), `+0x1CC` (VCORE Loadline),
     and `+0x1C8` (GFX Loadline).
  2. `37B47C56-D1B0-4A82-BF9B-C51B78B4511D` (`VddMemPei`, `0xE79EC8..0xE7B2F8` in donor FV)
     consumes `AmdSetup+0x1D1` (MEMIO Fix Voltage) and `+0x1D2` (MEMIO Voltage).
- Transport: neither module accesses hardware directly; both stage transactions into a
  mailbox structure dispatched via a shared helper to external PWM controllers (ISL69269
  and ISL95712).
- Boundary: static analysis only. Runtime PEI dispatch, mailbox transport chip identity,
  PMBus-style register semantics, physical rail identity, and applied voltage remain
  unverified on hardware. No ROM, NVRAM, register, candidate, or hardware action occurred.
  No voltage value is recommended.
- Evidence: `docs/research/2026-09-20-clv-fixed-voltage-consumer.md`,
  `evidence/firmware-audit/20260920-clv-fixed-voltage-consumer/`
  (`SHA256SUMS.final`; scanner `e67ded12…`, machine result `54b5e333…`), log
  `docs/action-logs/2026-09-20-clv-fixed-voltage-consumer.md`. Deterministic re-run
  passed 350/350 checks with exit `0`.

## Ultimate kernel opts: BORE/ThinLTO tradeoff found (2026-09-22)

- Workflow deep-research (9 agents, opencli-only) + root recheck:
  7.2.0 seed = clang + ThinLTO, NO BORE; 7.2.6-1.1 = GCC + LTO_NONE
  - BORE. The 1.1 build implicitly traded ThinLTO for BORE (CachyOS
    never ships the combo). Ranked plan: keep base; pkgrel3 =
    BORE+ThinLTO (first combo, low risk, 0-1% expected); no FullLTO;
    AutoFDO deferred (Zen2 cannot collect, foreign reuse unproven).
    Full verdict: docs/research/2026-09-22-ultimate-kernel-opts.md.

## Game SSDs: Ugreen USB3 dual dock, no SATA on BC250 (2026-09-21)

- Both game SSDs live in ONE Ugreen USB3 dual-bay dock (JMicron JMS561U
  `152d:1561`, usb-storage/BOT driver, 5 Gbps single uplink shared by
  both disks). `/cusu` = CUSU C200 960G (sdb1, btrfs, 661G free);
  `/somnabulist` = 954G SSD (sda1, btrfs, 206G free). fstab by UUID,
  `nofail` (system boots clean without the dock).
- G7: the BC250 board has NO usable SATA port (FCH AHCI shows 1 port,
  `ata1: SATA link down`, nothing routed). Root's "check SATA cables"
  advice 2026-09-21 was wrong; the dock had simply not enumerated until
  21:53 (re-plug/re-enumeration during the session). For missing
  /cusu//somnabulist: check USB/dock power first, never SATA.
- Measured sequential (dd 2G, direct): solo 327 MB/s (sda1) / 341 MB/s
  (sdb1); parallel 176+176 MB/s — shared ~350 MB/s uplink budget.
  SATA-SSD-class over USB; internal NVMe is ~6x faster. Game loads
  slower than /games but fully playable; random 4K stays SSD-fast.
- Game map 2026-09-21: dock/cusu = RDR2 119G, Metro EE 79G, RDR1 9G,
  RotTR 25G; dock/somnabulist = 13 titles ~737G (Elden Ring, Days Gone,
  Uncharted 124G, Spider-Man, TLOU1+TLOU2, Ratchet, Horizon FW 124G,
  SotTR, SR3, Plague Inc, Dispatch, KOTAMON); internal /games = AC
  Black Flag 66G + Overcooked2 8G + Stray 6.2G (+ Proton/SLR tools).
  Operator policy: games belong on the dock SSDs; move the /games trio
  there (AC BF only after the game quits — never move running files).

Date: 2026-09-20T18:14:35.670645+00:00

## G7 correction: rejected fixed-voltage reviewer identities

The preceding D37 / fixed-voltage summary attributing this result to AmdSetup, VddPei/VddMemPei and ISL69269 is NOT supported by its cited report. Root reopened that report and fixed-voltage-consumer-result.json: they identify the separate Setup VarStore EC87D643-EBA4-4BB5-A1E5-3F3E36B20DA9, ISL69247 GUID 6E6D2018-28D0-4AD3-BEB3-B48E4981707D and ISL95712 GUID 02544BE0-2CB9-4B75-8111-CD8CDC07B837, fields 0x1C9..0x1D2. The mismatching memory summary is withdrawn; it must not drive patches or voltage recommendations. This reconciliation validates attribution to the source only, NOT that source's complete semantics or physical rail mapping. Independent review of misleading byte-assertion labels remains incomplete.

### Independent re-verification and transport detail (2026-09-20T23:15+05:00, root)

- Independent re-run of the cited scanner reproduces its stdout byte-identically
  (`54b5e333759cb72f41f8e863bcc4c3f683a11951f47d25e903ca60af7213822e`), exit `0`, stderr `0`
  bytes, `status=PASS`, `350/350` checks; `sha256sum -c SHA256SUMS.final` 5/5 `OK`;
  `/home/OWNER/.local/bin/pytest -q tests/` -> `30 passed`. Inputs unchanged.
- Transport detail from the same cited report: the write helper stages `0x65 <- 0xC0`,
  `0x66 <- target register`, `0x70/0x71 <- 2-byte LE value`, `0x63 <- 3`, `0x60 <- 0xC0`,
  then polls status bit `0x40` (max 10 retries) and writes `0x60 <- 8`; the mailbox is reached
  through x86 ports `0x2E`/`0x2F` and `0xA20`/`0xA21`/`0xA22` (Super-I/O/EC configuration +
  data window) after the `0x87,0x87` unlock. Protocol/register semantics remain inferred.
- Rollback: remove this addendum only; the section above and the evidence directory stay
  unchanged.

## BC-250 board voltage sources — firmware-visible inventory (2026-09-20, offline static)

- Question: which pinned CLV 5.00 modules can drive a VR register through the shared
  Super-I/O/EC window, as opposed to merely touching that window?
- Result: exactly two of 233 modules implement the complete transport — `ISL69247`
  (`6E6D2018-28D0-4AD3-BEB3-B48E4981707D`, TE image ROM `0xed2c74`, FFS `0xed2c30`) and
  `ISL95712` (`02544BE0-2CB9-4B75-8111-CD8CDC07B837`, TE image ROM `0xed3d8c`, FFS
  `0xed3d48`), both PEIMs in FV `0xe02000`. Transport bytes: config unlock `0x87,0x87` on
  ports `0x2E`/`0x2F`, EC data window `0xA20`/`0xA21`/`0xA22`, mailbox staging registers
  `0x65` (`0xC0`), `0x66` (target register), `0x70`/`0x71` (2-byte LE value), `0x63`
  (count), `0x60` (trigger), then a `test al,0x40` status poll. This is the same pair that
  the fixed-voltage Setup consumer trace identified as VCORE/GFX/MEMIO field readers
  (cross-check `agree: true`).
- Bounded negative: 28 modules carry at least one strong anchor without the full
  conjunction (16 contain `push 0x2e`/`0x2f`, 9 contain the `0x00000a20` immediate); no
  third module in this corpus can stage a VR register write through that window.
- Independent verification (root): scanner re-run reproduces its result JSON
  byte-identically (`852ffd0d…`, exit `0`, stderr empty); root verifier re-derives the
  match set from the pinned objdump text with its own anchor conjunction, re-locates both
  images in the ROM by whole-image search, recomputes the 14-anchor module census and
  re-reads all 200 recorded anchor offsets — `status PASS`, `604` checks, `0` failed.
  Two anchor offsets are cross-instruction literal false positives (HiiDatabase,
  `A0327FE0-…`), both in the weak bucket.
- Boundary: static analysis only. PEI dispatch, mailbox chip identity, PMBus/register
  semantics, physical rail identity and applied voltage remain unverified; register-valued
  call arguments are recorded as unresolved, not guessed; no voltage value is recommended.
  No ROM, NVRAM, register, candidate, board or network action occurred.
- Evidence: `docs/research/2026-09-20-bc250-board-voltage-sources.md`,
  `evidence/firmware-audit/20260920-bc250-board-voltage-sources/`
  (`scan_vr_mailbox_writers.py` `63ae081c…`, `vr-mailbox-writers-result.json` `852ffd0d…`,
  `verify_board_voltage_sources.py` `3a207fac…`, `VERIFICATION.txt`, `SHA256SUMS.final`
  14/14 `OK`, `ROLLBACK.sh` exercised on two isolated copies), log
  `docs/action-logs/2026-09-20-bc250-board-voltage-sources.md`. Repository suite `30 passed`.

## G7 correction: fixed-voltage byte-assertion labels (2026-09-20, independent instruction-level decode)

- The fixed-voltage consumer finding above stands (two PEI VR-controller PEIMs `ISL69247`/`ISL95712`,
  `Setup` fields `0x1C9`-`0x1D2`, ECU/mailbox transport), but three labels in
  `evidence/firmware-audit/20260920-clv-fixed-voltage-consumer/scan_fixed_voltage_consumer.py` and in
  `docs/research/2026-09-20-clv-fixed-voltage-consumer.md` are contradicted by disassembly:
  (1) the `0x1C9` enable test is `0x30F: cmp BYTE PTR [ebp+0x51],bl` (`bl==0` from `xor ebx,ebx` at
  `0x27C`), not the `push 0x21` at `0x30A` printed in that report's table - the `0x030A` entry carries two
  contradictory labels and only the "register index 0x21" one is true;
  (2) `0x709` decodes as `movzx eax,BYTE PTR [edi]`, not as a u16 read (the second byte is `[edi+0x1]` at
  `0x714`, staged to mailbox register `0x71`);
  (3) the `2e 59` window asserted at `0x0566` starts one byte inside `0x565: push 0x2e` and straddles
  `push 0x2e` (`6a 2e`) + `pop ecx` (`59`); the port `0x2E` claim itself is correct.
  Three further assertions (`0x2AC`, `0x2B3`, ISL95712 `0x270`) are 3-byte prefixes of 4-byte stores, so
  their claimed immediates are correct by decode but are not covered by the asserted pattern.
- Method/evidence: independent FFS-by-GUID extraction of the PEIMs from the immutable donor plus objdump
  2.47 disassembly at the report's RVAs (no census dependency for selection, prior assertion table loaded
  rather than transcribed); `evidence/firmware-audit/20260920-fixed-voltage-independent-decode/`
  (`independent-decode-result.json` `3da15d4a…`, `SHA256SUMS.final` 11/11), report
  `docs/research/2026-09-20-fixed-voltage-independent-decode.md`, log
  `docs/action-logs/2026-09-20-fixed-voltage-independent-decode.md`; `28` decoded semantic checks with
  `2 CONTRADICTED`, exit `0`, repository suite `30 passed`.
- Effect: byte-pattern assertions in this project must be read as presence-of-bytes claims, not as decoded
  semantics; the fixed-voltage substance and every earlier uncertainty statement are unchanged (static
  only - no PEI dispatch, mailbox chip, PMBUS semantics, rail identity or applied voltage).

## G7: board SSH access — user steammachine, key id_ed25519 (2026-09-21, root self-correction)

- Board login is `steammachine@<dhcp-ip>` with local `~/.ssh/id_ed25519` (BatchMode OK, passwordless sudo).
  There is NO `kukuruza` user on the board. Current DHCP address: `127.0.0.1`.
  Historical sightings: `127.0.0.1`, `127.0.0.1`, `127.0.0.1` (other network, dead now).
- Method failure 2026-09-21: root probed `kukuruza@127.0.0.1` with all local keys, hit sshd throttling,
  and swept the whole /24 before reading this file's 2026-09-15 entry that already named `steammachine@.118`.
  Rule: for any board-access problem, read this file's reachability lines FIRST (G1), never re-probe blindly (G6).
  Canonical alias `Host steammachine` added to laptop `~/.ssh/config` 2026-09-21 (update HostName on DHCP move).

## Board shell + terminal state (2026-09-21)

- Login shell is now `/bin/bash` (was `/bin/fish`); fish package + its 4
  fish-only dependents cascade-removed. SSH probes need no fish wrapping.
- `kitty 0.48.2` installed, default via `~/.config/kdeglobals`
  (TerminalApplication/TerminalService); `~/.config/kitty/kitty.conf` is a
  Nord migration of `~/.config/alacritty/alacritty.toml` (31/31 directives
  valid vs shipped defaults). GUI launch unrun.
- VRAM stack live: `dmemcg-booster` system+user active, user app.slice
  `dmem.max` = VRAM-50M via `dmem-app-ceiling.service`. Full per-game
  accounting after game restart.
- `linux-cachyos-bore-vcn-bc250 7.2.6-1.1` INSTALLED side-by-side
  2026-09-21 (built on kukuruza-pc WSL archlinux, 23 patches, BORE on,
  config delta 66/10586). Limine: base + mode0/1/2 entries; default =
  bore-vcn-mode1, timeout 7 s (2026-09-21 user order).
- BOOT TEST PASS 2026-09-21 ~22:00 (first reboot): uname
  `7.2.6-1.1-cachyos-bore-vcn-bc250`, cmdline mode1 + zswap lz4/25%,
  `kernel.sched_bore=1`, VCN fw `0x08118009` loaded + Powered down
  (mode1 probe as expected, card1 debugfs), zswap Y/lz4/25 live,
  zram absent (unit disabled), 32G disk swap active (both files).
  Regression found + fixed same session: dock missed boot mount (USB
  race) → `x-systemd.automount` in fstab, proven live on /cusu.
- Freeze root cause 2026-09-21: RAM/swap, not VRAM (7.5G RAM, zram 8G
  lz4 99.7% full spilling to disk, si/so tens of MB/s, swappiness was
  150). Mitigation: swappiness=20 live+persisted
  (`/etc/sysctl.d/99-bc250-gaming.conf`); zram lz4→zstd staged in
  `bc250-zram.service` for next boot (combine with kernel test).
  Remaining: game diet (1.7G steamwebhelpers), zram-size review.
- G7 freeze correction 2026-09-21: catastrophic freezes ENDED after the
  operator reseated the SSD (flapping link under swap/game I/O). Swap
  pressure is a real AMPLIFIER (zram refills in <30 min) but was not the
  sole cause; the "swap thrash = freezes" verdict was overstated.
  dmesg proof unavailable (cmdline loglevel=0 hides nvme errors).
  Community consensus (toolkit f8fb098 + docs 0524002): zswap lz4/25%
  over fixed zram, 16G+ disk overflow, high swappiness, fixed VRAM
  split. Our split is FIXED 8G (sysfs), not the broken 512M-dynamic
  combo. See `docs/research/2026-09-21-bc250-swap-tuning.md`.

## Operator takeover: empirical OC track on live P3.00 board (2026-09-21 ~23:55+05:00)

- Operator moved the OC/voltage/1:1:1 task from Codex goal thread `01a0bba1…`
  to this session; STAND DOWN queued to Root (`01a0c55d…`). Static ABL/PSP
  tracing parked (G6 pivot); method class is now live empirical.
- Live baseline (hardware-verified, read-only): board UP, bore kernel 7.2.6
  mode1, BIOS P3.00 12/09/2021, GPU `1002:13fe`, NVRAM all-Auto
  (`FF/FF/FF/0F/FF/1000`, body `6f266c3c…d055`), offsets zero, committed
  mclk/sclk/fclk `450*/2000*/450*`. Evidence:
  `evidence/runtime/20260921-takeover-live-baseline/`; log
  `docs/action-logs/2026-09-21-takeover-live-baseline.md`.
- G7: live board is P3.00 + stock-Auto, NOT W11/CLV bytes — CLV-static menu
  paths are leads until verified live. Operator procedure:
  `docs/guides/bc250-p300-111-operator-runbook.md` (clock-only T0–T6 +
  Stage B hypothesis; voltage NO-GO unchanged).

## Operator requirement D-REQ1: unified 5.00-CLV 8-core firmware (2026-09-22)

- Operator demands a 5.00-CLV-based image with in-firmware 8-core unlock
  plus all community patch classes (core unlock, menu unhide, NVRAM shape).
  Fixed in `specs/2026-09-22-clv500-8core-unified.md` (anchors, checklist,
  Q1–Q7). Method: surgical injection (whole-FV rejected); flash:
  programmer-only. Starting point: drivers-only `0968a70c…` (unreviewed).
- State conflict (unresolved join, Q7): operator reports "5.00 CLV
  installed, just flashed community BIOS"; live readback 2026-09-22 02:05
  shows DMI P3.00 12/09/2021, uptime 4:10, NVRAM == baseline `6f266c3c…`
  (no reboot since 21:53, no NVRAM change). Board was NOT reflashed during
  this session. Which file/when needs operator clarification.
- G7 2026-09-22 (Mesa A/B INVALID): the "52.0 -> 60.0 system-Mesa" verdict
  is WITHDRAWN as a Mesa comparison. The game never loads system Mesa:
  `/etc/profile.d/60-bc250-gfx1013.sh` (2026-09-02) globally pins
  VK_DRIVER_FILES/VK_ICD_FILENAMES to
  `/opt/bc250-gfx1013/v3.3.0/.../radeon_icd.x86_64.json` whose library is
  the 2026-08-25 async build = Mesa 26.2.0-rc3 (strings-verified).
  64-bit Vulkan -> /opt driver; 32-bit ICD -> system /usr/lib32. Raw
  numbers (A0 52.0 n=53, A1 60.0-capped n=21) stand as measurements, but
  the delta is NOT attributable to the 26.2.3 system install; A1's 60.0
  cap smells of vsync/limiter, not a 15% gain. Next: paired A/B on one
  scene with taskset -c 8-11 + DXVK_HUD + MangoHud CSV, and decide
  whether to re-point the pin at system Mesa or rebuild /opt from
  26.2.3+9 patches. Credit: handoff from cerulean-albiorix.
- G7 2026-09-22 (2230 NOT arbitrary): AMD stock cyan_skillfish range is
  1000-2000; MastaG 0007 widened to 350-2230 explicitly so userspace
  SMU governors can drive clocks (PATCHES.md). Community 40CU wall is
  ~2200 (2255 fails) — 2230 sits on the real wall. Our 0025 claim
  "arbitrary clamp" was half-wrong; 3000 is above the firmware wall and
  SMU rejects pp_od writes (EINVAL + `Invalid sclk` in dmesg). OC path
  is governors (filippor/cyan-skillfish-governor), not pp_od.
- G7 2026-09-22 (read-a NOT stock): board dump read-a.bin (83c4e420)
  already contains the V2 core-unlock DXE (same PE32 as 8_cores_steam);
  8core-vs-read-a differ only in NVRAM. Live chip runs MeiMeiDXEv3-XL
  (2b69dc32) with full V3 unlock present but Disabled in NVRAM
  (MeiMeiDXEv3CoreVar=zeros, factory mask 0x77=6 cores, verified in
  dump). Enable path: Setup MeiMeiDXEv3 Menu -> SMU Unlock + Core
  Unlock=All Cores. A2 report: /tmp/fin-A2.md.
- G7 2026-09-22 (sg_display default): amdgpu sg_display default is
  AUTO (-1), not 1 as I claimed; 0=disable, 1=undocumented
  force-value. My sg=1 hung boot (gray); community runs auto/-1 or 0.
- G7 2026-09-22 (sg=-1 + UMA512 tested): boots clean — cmdline/sysfs
  sg=-1, VRAM/BAR/GART 512M, pin-fail 0 (sg=0 errors gone), gamescope
  alive. Mechanism fix vs earlier guess: auto allocates framebuffer in
  S/G scatter pages (no contiguous carveout), hence no gray-hang.
  FPS effect vs 8G config still untested — needs paired A/B.
- G7 2026-09-22 (512+auto FAILS under game): AC Black Flag launch ->
  gamescope "drm: flip error: Cannot allocate memory" -> SIGABRT.
  512M visible VRAM starves compositor flip buffers when a real game
  allocates. 512-dynamic experiment CLOSED as failed; revert to
  UMA 8192 proposed. 04:42 reboot was operator-ordered `sudo reboot`
  via SSH from .151, not a crash (board healthy: 62C, no throttle).
- FINDING 2026-09-22 (uma512 15-agent wave): 512 is community default
  but always bundled (ttm raise, big GTT, tuned swap, light/lowered
  loads). Our flip-ENOMEM/SIGABRT: 0 chat matches, EXACT match in
  community docs (CP2077+gamescope+512, pin -12, 6G fix) and upstream
  drm/amd#3704 (Ally X 512M+gamescope+pin-12). 4+ chat A/Bs confirm
  bigger split fixes game crashes. Revised dose: UMA 6144 (6G) per
  docs+chats instead of 8192. Artifacts /tmp/uma512-T01..T15.md;
  synthesis docs/research/2026-09-22-uma512-synthesis.md.
- G7 2026-09-22 (whiteflower-config debunked): whiteflower never
  posted sg_display/ttm params (T3: repo async-compute-only). Prior
  attribution of sg_display=0+ttm4G to him was wrong; drop it.
- G7 2026-09-22 (BIOS UMA menu does not stick): operator set 6G in
  BIOS menu, but post-reboot CMOS readback stayed UMA_SIZE=0512 and
  vram_total stayed 512M. This board's firmware reads memcfg's CMOS
  block only; the menu option writes elsewhere or nowhere. 6G applied
  via `bc250memcfg UMA_SIZE 6144` + reboot: vram_total=6442450944,
  RAM 9.4G, gamescope alive. Always verify split in sysfs, never
  trust the menu.
- G7 2026-09-22 (pkill -f self-match): pattern matches own SSH
  cmdline -> SIGKILLs own session (exit 255). Always bracket-trick:
  pkill -f "AppId=37519[50]". pgrep -f counts include self (+1).
- G7 2026-09-22 (Steam Cloud authoritative): localconfig.vdf file
  edits get reverted from Cloud on Steam start; /tmp backups die
  on reboot. Launch options only via Steam UI; PROTON_LOG via
  GE-Proton tool-dir user_settings.py (NOT compatdata prefix!).
- G7 2026-09-22 (GART vs GTT): dmesg "GART 512M" is the aperture;
  GTT pool is ~14.85G via ttm.pages_limit=3959290 (community max
  recipe, ACTIVE at crash). sg_display=-1 is the driver default —
  not a differentiator vs community; red herring closed.
- FINDING 2026-09-22 (UMA 512 kills gamescope): operator set UMA 512M
  (+8 cores, no MCEs — cores innocent). vram_total=512M, RAM 14G.
  gamescope SIGABRT x2 (03:46:18, 03:47:18) with matching kernel
  `amdgpu pin failed` same seconds: scanout pin needs contiguous VRAM
  (cmdline has amdgpu.sg_display=0!) + ttm.pages_limit=4G while game
  wants 6.4-6.9G = whiteflower mechanics reproduced. Fix: UMA back to
  8192; 512-dynamic would need sg_display=1 + ttm up + retest.

## Discord wave synthesis (2026-09-22, STOP-ordered, zero-API synthesis)

- 6/12 tracks complete (T1,T2,T3,T6,T10,T11) + T7 draft + local 113k-msg export (Sep25-Mar26).
  Full synthesis: `docs/research/2026-09-22-discord-synthesis.md`.
- G7: peer "pp_od dead, zero recipes" is OVERSTATED — `vc`-path recipes (FilippoR, Nov-Dec 2025)
  exist; peer tested `s`-path only. Retest of `vc 0 <clk> <volt>` on 7.2.6-1.2 is open.
- Old Lamer = community YouTuber (SMU-OC step-by-step, BIOS guides); transcript pending.
- Operator Discord footprint: 4 msgs, 2026-06-17 (asked P5.00_clv, warned off by T.Sharp).
- No further Discord API without explicit operator order (STOP 2026-09-22).

## S3 driver-input audit (2026-09-22, offline, static)

- G7 2026-09-22 (injected driver-set names): my shorthand names
  (SMU_ACPI_Dump/APCB_Dump/TOS_Dump) do NOT name the pinned injected set.
  The pinned set per `scripts/build_fd_drivers_clv.py` + v001 build.json
  is: SMU_Unlock (A3F8B2D5…), SMU_Core_Unlock (7A8B9C0D…), Menu_Driver
  (0DDDE9E4…), ACPI_AutoInject (A9981D14…), SMU_Patch (9D4E5E12…),
  ColdBoot (6C98E4F3…). Any *Dump files live elsewhere in the FD tree,
  not in the 6-driver injection.
- S3-A (S3A-verdict.json) accepted by root: input table == v001 build.json
  GUIDs/offsets/sizes; donor 606a7a7f re-verified; S2 vs donor diff is
  exactly the 2 S1 NVRAM bytes (0x7E5 0x24->0x1A, 0xBD3 0x8C->0x32);
  0xAE0000-0xE00000 identical (7cb00768…). REPLAY-GO verified.

## S3 closed (2026-09-22, offline, static-only)

- S3B-verdict UNHIDE-GO accepted by root, 20/20 checks: 57-byte span is
  EXACTLY the full 3.00->CHIPSETMENU delta of 899407D7 (V4b, ndiff=57);
  S2 carries pre-edit bytes (V2/V3); new FormId 0x7005 + FormSetId guid
  both present in S2's own CbsSetupDxe (FORM_SET@0xb388, guid@0xb38a,
  FORM@0xeb78); same-size FFS, attr=0x00 (no content checksum).
- G7 2026-09-22 (root off-by-2): my first V6d read took the FormSetId at
  the FORM_SET opcode offset 0xb388 instead of guid start 0xb38a and
  falsely FAILED. Fixed by parsing REF3 payload + guid-anchored find.
  Cite opcode vs field offsets separately in IFR verdicts.
- S3-DRV_v001 `26c0634d…` (16 MiB): 187->193 (+6 S3A drivers, donor-exact),
  57/57 unhide applied, containment [0xAE0000,0xE00000) ndiff=1341763,
  PSP/BHD/APCB subtrees identical to S2 (root firmware_audit re-run),
  S1 NVRAM bytes intact. C==D byte-identical (root cmp). E gate 7/7,
  F tests 20/20, S1/S2 suite 23/23 — all re-run green by root.
- Static-only closure stands: no claim that Setup shows the menu or that
  drivers dispatch; that is hardware acceptance after an exact-approval
  flash, which has NOT occurred.

## S4 closed (2026-09-22, offline, staged-not-flashed)

- Package `firmware-flash-pkg/20260922-clv500-s123/` (S3 image copy,
  SHA256SUMS OK) + runbook `docs/guides/bc250-clv500-s123-programmer-flash-runbook.md`
  (9-step procedure, exact-approval form, x2 dump, readback, H1-H7
  hardware acceptance, rollback). Boot block + 0xE00000+ == CLV donor.
- GOAL COMPLETE at BUILD layer: S1 c5dc6424 (2 bytes, gate 6/6),
  S2 == S1 (template, 23/23), S3 26c0634d (E 7/7, F 20/20, C==D,
  root 11/11), review briefs recorded (second-family review
  INCOMPLETE), S4 staged. No flash performed. No sync/volt/VCN
  claims. Operator decision: flash or not.
- Note: working tree was already dirty at session start (unrelated
  M entries + one unstaged `D "C:\Users\OWNER"`);
  left untouched — not this goal's scope.

## Game activation failure on 6G/7G (2026-09-22, observed-bytes + inferred)

- G7 2026-09-22: earlier verdict "Ubisoft backend transient, HTTP 204
  refusal" is WITHDRAWN as a mechanism. The 204 follows the game's own exit.
  Game exits right after DRM/launcher DLLs load, before it connects to the
  launcher API (GNM Code 10). Log: docs/action-logs/2026-09-22-uma6g-memcfg.md.
- Launcher RAM value separates outcomes 100% (27 launches): 8G/512M OK,
  6G (9655) and 7G (8647) fail. 6G worked Sep 15-16 (9659 MB).
- Inferred: hardware-bound activation limit after several split changes on
  Sep 22. Unverified; test = cooldown + single launch, no new split sizes.
- G7 2026-09-22 08:45 (game activation): 8G/RAM 7651 MB, which activated
  at 06:23, was refused at 08:43 with identical launch inputs. The
  RAM-fingerprint hypothesis is falsified; refusal is config-independent.
  Board left at UMA 8192. Next: no local launches; operator checks the
  Ubisoft account / support. Log: docs/action-logs/2026-09-22-uma6g-memcfg.md.
- FACT 2026-09-22 09:05 (observed-bytes, laptop): official CachyOS
  `linux-cachyos-bore 7.2.6-1` and `linux-cachyos-lts 6.18.52-1` .config =
  CC_IS_GCC + LTO_NONE. So GCC/no-LTO for BORE is CachyOS's own choice;
  clang+ThinLTO in the 7.2.0 seed came from MastaG's default-EEVDF base.
  The kernel-opts "ranked plan" is a worker-research recommendation, NOT an
  operator decision (operator: "я ничего не решал").
- FACT 2026-09-22 09:05 (board): mesa/lib32-mesa/vulkan-radeon 26.2.3
  (MastaG 9-patch build) installed; /etc/profile.d/60-bc250-gfx1013.sh
  pin is gone; RADV exposes 1 gfx + 4 compute queues, kernel has
  amdgpu_ring_comp_1.* rings. Async-compute queue EXPOSED; in-game use,
  benefit and stability UNVERIFIED.
- G7 2026-09-22 10:20 (Zen2 knob): my claim "CachyOS has _processor_opt=zen2
  (CONFIG_MZEN2)" was from memory and WRONG for linux-cachyos-bore 7.2.6:
  PKGBUILD case = GENERIC_V1-4 / ZEN4 / NATIVE only. Zen2 codegen in pkgrel3
  goes via KCFLAGS -march=znver2 -mtune=znver2 on GENERIC_V3.
- FACT 2026-09-22 (static diff): the async-compute "kernel half" of
  DryhoppedIPA/bc250-gfx1013-fix (patches/kernel/v33: pasid-tlb-invalidation,
  compute-gfxoff-guard) is ALREADY in our kernel as MastaG 0003/0004 (same +/-
  lines; 0004 differs only in hunk line order). helper-wave "bore needs v33
  kernel half" is satisfied. Open: in-game ACE use + stability (bc250-async-compute trace/soak).
- FACT 2026-09-22: latest CachyOS linux-cachyos-bore = 7.2.6-1 (= our base).
  MastaG has 1 commit past pin 93f8e69: 0697a5d "bind BC-250 secure processor (ccp)".
- G7 2026-09-22 11:40 (game activation ROOT CAUSE, community-confirmed): AC Black
  Flag Resynced uses Denuvo: max 5 activations / 24 h; any hardware/compat change
  (UMA split -> RAM value, Proton change) counts as a new PC; every launch during
  lockout extends it. Source: steamcommunity.com/app/3751950/discussions/0/572669207837198177/.
  Withdrawn: "backend 204", "session state", "RAM-value fingerprint only", mod, region.
  Fix: no launches for 24 h from last attempt (11:31 PKT -> after 2026-09-23 11:31),
  keep UMA 8G + pinned Proton fixed, one launch, then back up the prefix.

## Ladder rename + STUB boots (2026-09-24, hardware-verified)

- Plain-name canon in force (`MISTAKES.md` 2026-09-24): ladder files say what
  is inside (`FULL`/`STUB` + what differs + placement); old `vNN` tags are
  `alias` only. Private `candidates/`, `scripts/`, `firmware-flash-pkg/`,
  registry, and `docs/RELEASES.md` (Rule 0 amended by operator) converted.
- Public repo `kalpakprod/amd-bc250-bios-unlock`: PR #1 merged, `v2.0.0`
  released (24 assets, 7/7 images `cmp`-identical to `v1.0.0`); standing rule
  is every change ships as a semver release (`CHANGELOG.md`).
- VERDICT 2026-09-24 ~19:37: STUB early-slot (`6500bea5…`) BOOTS to Linux
  (kernel `7.2.6-1.206-cachyos-bc250`, amdgpu up, SMU 88.6.0). DXE completes
  with our driver in the first TRUE-pool slot → insertion surgery innocent,
  FULL-driver code guilty. Registry: STUB `FLASHED-OK`.
- NEXT: flash FULL-appended (`9d249397…`) on BC250-01 — needs exact operator
  approval. STUB-appended demoted to fallback-only.
- Board software baseline: kernels `7.2.6-1.206-cachyos-bc250` and
  `7.2.6-1.3-cachyos-bore-vcn-bc250` (Limine modes 0/1/2 via
  `amdgpu.bc250_vcn_mode=`); full home + `/boot` + bore modules pull into
  `evidence/board-home-20260924/` in progress; kernels publish as public
  `v2.1.0` next.
- Plane BC250 synced: #7 Done (STUB verdict), #8 Todo (flash FULL-appended),
  #9 In Progress (board pull + kernels). Log:
  `docs/action-logs/2026-09-24-stub-boots-verdict.md`.

## H19 wins + v2.1.0 (2026-09-24, hardware-verified)

- FULL-appended (`9d249397…`) flashed VERIFIED, cold boot: 1 blink, no
  LAN/video (pre-dispatch signature; FV statically valid, 194 files, checksums
  OK). STUB-appended (`0133a34b…`) flashed VERIFIED, BOOTS to Linux.
- H19 WINS: append structure fine, FULL code wedges only against initialized
  SMU. Surgery/position work CLOSED; main line is now write content.
- Driver audit: all polls bounded (125 loops, 5 s mailbox cap) → stuck
  mechanism is SMU-side. Sequence: 0/0a (probe+permission) → R (gate modes →
  enable/trigger → ready poll → tail → power steps → enable block) → V.
  Safe-reads (raw reads deleted) is NEXT (#11, needs approval). Fallback:
  no-replay probe, then replay bisection.
- Board pulled to `evidence/board-home-20260924/` (1.2G+563M+367M).
- Public: PR #2 merged, `v2.1.0` (30 assets: kernels + fresh verdicts),
  help issues #3 (wedging write?) and #4 (Linux VCN + missing recipe).
  Plane: #8/#10 Done, #9 Done, #11 Todo. Missing: bore-vcn 1.3 PKGBUILD +
  `bc250_vcn_mode` patch source (not on the board).

## Software-only SPI emulator continuation (2026-09-28)

- The approved scope remains offline software/model/build only. Do not infer
  current BC-250 state from these tests; no board was connected, signalled,
  reset, or flashed in this work.
- Added `candidates/single-flash-emulator-v001/pio_selector_model.py`, a
  host-only trace of the legacy selector/filter ordering. The queued filters
  are `S -> true`, duplicate `S -> true`, then `E -> false`. For synthetic
  transaction starts `S, S, other, E, other`, injector choices are
  pass-through, inject, inject, inject, pass-through. This is control-flow
  modeling, not PIO execution.
- Exact P3.00 stock `dump/2.bin` (`83c4e420…8f8ee0`) and selected
  SteamOS-BlackOut (`7c636c8f…d77dee6`) are both 16 MiB. Their diff is
  1,440,179 changed bytes in 10,867 contiguous runs, merged with a 64-byte
  gap into 11 ranges. Full-byte synthetic host checks covered every merged
  range at read indices 0 and 1 (2,907,216 byte comparisons, PASS). The
  read order is arbitrary and not inferred from PSP behavior. Map:
  `~/.cache/bc250-single-flash-emulator/p300-steamos-blackout-serve-map.json`.
- The legacy TOCTOU window `0x9DB560..0x9DB6A0` is identical in those exact
  P3.00 images (320/320 bytes, SHA-256
  `db40c2770dda6de90ae7852b76d1181a7fa6429e0efa3aa286dadfffed0498a8`).
  The stored 320-byte payload is labeled in its source comment as stock
  BC250 5.00 CLV and differs in 314 bytes. It is not a discriminating target
  for this P3.00 pair and must not be assumed to be a matching payload.
- Legacy `spi_inject` samples the selector at CS assertion before parsing the
  address, so a matched-address decision is delayed to a later transaction.
  The separate `miso_proxy` checks later, but source instruction counts alone
  do not prove its selector update arrives before its check; no local
  cycle-accurate PIO simulator was found. First-bit timing and actual PSP
  order remain unresolved.
- Evidence and corrections: `docs/action-logs/2026-09-28-host-selector-queue-model.md`,
  `2026-09-28-toctou-selector-queue-trace.md`,
  `2026-09-28-pio-trigger-proxy-phase-audit.md`,
  `2026-09-28-p300-steamos-blackout-offline-map.md`, and
  `2026-09-28-p300-anchor-window-audit.md`. Candidate unit suite: 21 passed;
  `make test`: 7 passed; final scoped Procoder: 11 changed paths clean, 0
  unformatted, 0 unchecked, 0 out of scope, 0 blocking, with 474 broader
  repository hygiene findings left untouched.
