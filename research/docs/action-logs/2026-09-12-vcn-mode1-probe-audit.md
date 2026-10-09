# VCN mode1 probe boot audit (2026-09-12)

## Context

- Continuation point from 2026-09-11 23:15 entry: mode2 limine entry created, operator to reboot via local console. Board carries APCB-only candidate `6b1fe8ef504142d5d5273a85b6c9febdf0b1fb8fc08ebab2593281c320cb9d70`.
- Observed state: operator rebooted 2026-09-11 23:51 PKT selecting mode1 (`amdgpu.bc250_vcn_mode=1`, probe), kernel `7.2.0-1.92-cachyos-vcn-bc250`.

## Actions (root, no delegation, no hardware writes)

1. Read `memory/INDEX.md`, `memory/project-state.md`, `memory/firmware-audit.md`, `memory/open-questions.md`, action log `2026-09-11-vcn-policy-only-candidate.md`, prior runtime audit `evidence/runtime/20260911-apcb-only-v001-boot-audit.md`.
2. SSH read-only audit (`uname`, `cat /proc/cmdline`, `uptime`, `ls /dev/dri`, `sudo -n journalctl -k`, `sudo -n dmesg`). No sysfs/PCI writes, no bc250_smu helpers, no reboot issued.
3. Saved clean journal extract and audit report under `evidence/runtime/`.

## Result

- PASS: mode1 probe boot on APCB-only candidate. 9 IP blocks including `number 8 <vcn_v2_0_0> (vcn_v2_0_probe)`; VCN firmware found `ENC: 1.24 DEC: 8 VEP: 0 Revision: 9`; `VCN probe: fw_version=0x08118009 fw_size=404544 vcpu_bo_size=1064960` (fw_size equals green_sardine_vcn.bin). Fresh hardware reproduction of the historical 2026-08-28 mode1 PASS.
- UNRUN: mode2 hardware block attach, ring bring-up, codec function. No ring-test lines in this boot journal.
- Non-fatal dal_irq warnings unchanged from prior audit.

## Evidence

- `evidence/runtime/20260912-mode1-probe-boot-audit.md`
- `evidence/runtime/20260912-mode1-probe-boot-journal.txt` SHA-256 `c165345b0ec05f12f4939a88b6f315b8e97fcac7bf183ef0bd6ef85c99e2004a`

## Next step

- Operator reboots from local console, selects `linux-cachyos-vcn-bc250-mode2`; root then repeats the read-only SSH audit. Expected: real `vcn_v2_0` hardware ip_block attach, ring/IRQ init, no firmware-load error. Record any hang/reset as evidence. No firmware reflash implied.

## Mode2 boot attempt: no-boot report and zero journal trace (2026-09-12 02:35+05:00)

- Operator report: mode2 does not boot; board returned to mode1 (current boot since 23:50:52 PKT, `bc250_vcn_mode=1`).
- Read-only journal inspection: NO boot record exists between 23:21:30 and 23:50:52; full-journal grep for `bc250_vcn_mode=2` finds only the 23:14:47 limine-entry append. The mode2 attempt never reached persistent journald.
- Mode1 deep read (read-only): param documented `0=off, 1=probe-only, 2=hardware; mode 2 is experimental`; runtime value 1; green_sardine/renoir VCN firmware present; no VCN/MMSCH lines after the probe lines (probe-only does no VCN hardware interaction).
- Inferred hypothesis (unproven): mode2 hardware init hangs before journald activation, consistent with VCN power-gated/disabled by PSP policy. Hang location INCONCLUSIVE without console capture.
- Evidence: `evidence/runtime/20260912-mode1-deep-read-and-mode2-no-trace.md`.
## Diagnostic mode2 entry: write intent (approved 2026-09-12 02:4x+05:00)

- Operator approved via structured question: make the diagnostic mode2 limine entry (remove `quiet splash`, set `loglevel=7`), reboot, photograph last console line.
- Exact target: mode2 `KERNEL_CMDLINE[linux-cachyos-vcn-bc250-mode2]` line in `/etc/limine-entry-tool.d/90-bc250-vcn-probe.conf` on `steammachine@127.0.0.1`, then regenerate/verify the active limine config through the existing `limine-entry-tool` flow.
- One changed variable: console verbosity of the mode2 entry only. Kernel, modules, firmware, SPI image unchanged. No flash.
- Procedure: 1) inspect current dropin + generated limine config (read-only); 2) timestamped backup of the dropin; 3) edit the mode2 cmdline line only; 4) regenerate config if the tool requires it; 5) verify via `limine-entry-tool --get-cmdline linux-cachyos-vcn-bc250-mode2` and by reading the generated config; 6) operator reboots, selects mode2, reads/photographs last console line.
- Expected effect: on next mode2 attempt the text console shows kernel messages up to the hang point instead of a silent screen. Expected signal: last line naming the stuck subsystem (expected candidates: amdgpu/vcn_v2_0/MMSCH/IRQ).
- Rollback: restore the timestamped dropin backup and regenerate the config; `.bak` from 2026-09-11 also preserved.
- Result appended after verification below.

## Diagnostic mode2 entry: write result (2026-09-12 02:5x+05:00)

- Edits applied over SSH with `install -m 644` after timestamped backups:
  - `/boot/limine.conf` line 275 (active mode2 entry cmdline): `quiet` and `splash` removed, `loglevel=0` -> `loglevel=7`; all other tokens unchanged.
  - `/etc/limine-entry-tool.d/90-bc250-vcn-probe.conf` line 4 (`KERNEL_CMDLINE[linux-cachyos-vcn-bc250-mode2]`): same single-line change.
- Verification PASS: `diff` against each backup shows exactly one changed line per file; mode0/mode1/default entries untouched (29 lines still contain `quiet nowatchdog splash`); no other file modified. Temp copies removed from board.
- Backups (rollback): `/boot/limine.conf.bak-prediag-20260912`, `/etc/limine-entry-tool.d/90-bc250-vcn-probe.conf.bak-prediag-20260912`; earlier `.bak` from 2026-09-11 also present. Local reference copies in `/tmp/bc250-limine-diag/`.
- No kernel, module, firmware, or SPI change. No flash.
## Mode2 verbose boot attempt: board link-down (2026-09-12 03:0x+05:00)

- Operator selected mode2 with the diagnostic (verbose) cmdline. Board state immediately after: ICMP `Destination Host Unreachable` (no ARP neighbor), SSH `No route to host`, port 22 unreachable. Second SSH probe after 25 s: same.
- Evidence class: host-side observed network absence. The board's Ethernet stack never came up — consistent with the prior zero-journal trace: mode2 hangs or loses power before drivers/journald/network.
## Mode2 verbose boot: console transcript captured (2026-09-12 03:1x+05:00)

- Operator transcribed the mode2 console (photo OCR corroborated): initramfs reached `Initrd Default Target`, orderly teardown, `Finished Plymouth switch root service`, then holds at `A stop job is running for Rule-based Manager for Device Events and Files (2s / 1min 30s)`.
- No amdgpu/VCN lines in the transcribed tail. Live counter implies the CPU was still executing at that instant (not a fully dead kernel).
- Refined conclusion (G7): mode2 does NOT hang in the early kernel; it reaches initramfs switch-root and stalls on initramfs udevd exit, with the final wedge (and network death) expected either at the 90 s timeout resolution or at real-root amdgpu/mode2 module load before journal sync.
- Evidence: `evidence/runtime/20260912-mode2-verbose-console-transcript.md`.
- Pending: operator observation of the screen for 3 more minutes (counter behavior, post-timeout text, final freeze point), then power-cycle to mode1 for: mkinitcpio amdgpu-in-initramfs check, journal/pstore inspection, and possible boot_delay addition.

## Mode1 return audit and mode2 cmdline v2 (2026-09-12 03:2x+05:00)

- Operator returned the board to mode1 (up 0 min at audit). Read-only checks:
  - Boot list: NO boot record for the mode2 verbose attempt (gap 02:43:35 -> 03:05:34); whole-journal `bc250_vcn_mode=2` count still 1 (only the 23:14:47 sudo edit line). The wedge happened after switch-root before any journal sync, as inferred.
  - `/sys/fs/pstore/`: empty (no warm-reset panic capture; backend may also be unconfigured).
  - `/etc/mkinitcpio.conf`: `MODULES=( lz4_compress)` — amdgpu NOT explicitly in initramfs (amdgpu firmware files present via kms hook); amdgpu+mode2 probe runs from the real root at udev coldplug, after switch-root. Consistent with the console transcript.
- Mode2 diagnostic cmdline v2 installed (same fetch-edit-diff-install flow): added `plymouth.enable=0 printk.time=1` to the single mode2 line in `/boot/limine.conf` and the dropin. Diff verification: exactly one changed line per file; mode1 entries intact. Backups: `.bak-diagv1-20260912` (v1 diagnostic state) plus the earlier `.bak-prediag-20260912` (original state).
- No boot_delay added: the frozen text console (plymouth off) is directly photographable; fewer variables.
- Next: operator reboots into mode2, films/photographs the frozen console; expected freeze frame contains amdgpu `vcn_v2_0` probe lines with timestamps naming the wedging call (MMSCH/VCPU/MMIO). Then the branch decision: D3-B2 policy retest with fixed display wiring (needs exact flash approval) vs other fix.

## Mode2 v2 result and method change to controlled probe (G6) (2026-09-12 03:3x+05:00)

- Operator report: v2 boot behaved "ровно тоже самое, один в один" — same console sequence, same stall, then black screen. With plymouth disabled, a black screen at the same point means the display output/framebuffer dies with the kernel wedge; the console cannot show the wedging call. Console-capture approach exhausted.
- Method change (G6, third no-evidence console death): stop trying to observe the death on the board screen. Boot mode2 with `modprobe.blacklist=amdgpu` so the kernel cannot wedge during coldplug; system must reach SSH (simpledrm text console, slow but alive). Then trigger `sudo modprobe amdgpu` remotely over SSH while streaming `dmesg -w` to a local file on the operator host — the last line before any wedge is captured locally even if the board dies.
- Mode2-diag cmdline v3 planned: v2 + `modprobe.blacklist=amdgpu`. Rollback chain unchanged.
- Board currently down/hung in mode2; operator to power-cycle back to mode1 first.

## Mode2-diag cmdline v3 installed (2026-09-12 03:4x+05:00)

- Base: operator returned the board to mode1 (verified fresh boot, `bc250_vcn_mode=1`).
- v3 change: added `modprobe.blacklist=amdgpu` to the single mode2 cmdline line (retains v2 `plymouth.enable=0 printk.time=1`, loglevel=7, no quiet/splash) in `/boot/limine.conf` and the dropin. Diff-verified: exactly one changed line per file; mode1 entries intact.
- Backups now: `.bak-diagv2-20260912` (v2 state), `.bak-diagv1-20260912` (v1), `.bak-prediag-20260912` (original). Earlier edit-tooling notes: first v3 attempt failed locally (stale OLD pattern not matching v2 text) before any board write; corrected and verified.
- Expected v3 boot: full boot to SSH without amdgpu (simpledrm text console; no graphical session expected). Then root triggers `modprobe amdgpu` remotely with `dmesg -w` streamed to the local host; the last line before a wedge is captured locally even if the board dies. Board may need a power-cycle after the wedge.

## Controlled amdgpu mode2 probe: kernel wedge captured at first VCN hardware touch (2026-09-12 03:17-03:20 PKT)

- v3 boot reached full userspace (SSH up, simpledrm `card0`, enp4s0 UP; `dp=READ-FAIL` and `bc250-cu-live-manager.service` FAILED expected without amdgpu). `BC250-FORENSICS boot prev_clean_shutdown=0` independently confirms the prior mode2 death was unclean.
- Root started `dmesg -w` stream to local file, then ran `sudo modprobe amdgpu` (one variable vs the coldplug death: manual trigger, instrumented). SSH hung; killed by timeout. Board died completely (no SSH, no ARP) — reproduced the coldplug wedge deterministically.
- Captured timeline (log `evidence/runtime/20260912-mode2-controlled-probe-dmesg.log`, SHA-256 `e9c830f8f231c1e803677d4b67ad7b3154885223a7d95ac86cabddd89169c66d`):
  - `179.045` all 10 IP blocks detected, including `number 8 <vcn_v2_0_0> (vcn_v2_0)` REAL hardware variant (mode1 prints `(vcn_v2_0_probe)`) and `number 9 <jpeg_v2_0_0>`.
  - `179.089` VCN firmware header found (file read). `179.110` PSP TMR reserved. `179.146` SMU 88.6.0 init OK.
  - `179.220` custom `bc250-40cu-enable: mode=3` GC CU-unlock register writes (CC `0xfff80000->0xffe00000`, SPI `0x7->0x1f`, 4 SE/SH pairs) — COMPLETED and printed.
  - `179.2206` `kiq ring mec 2 pipe 1 q 0` (gfx rings).
  - `179.278` `clocksource: Watchdog remote CPU 4 read timed out` — the modprobe task was on CPU 4. Then total silence; no panic, no VCN/MMSCH error lines ever printed.
- Differential proof (G2): mode1 and mode2 init paths are identical up to gfx/sdma; the ONLY functional difference is vcn_v2_0 `hw_init` (real MMIO/VCPU touch) vs `vcn_v2_0_probe` (no hardware access). mode1 boots; mode2 dies at exactly the post-gfx stage where VCN hw_init runs, with a stuck CPU and no error output. Conclusion: the kernel wedges on the first VCN hardware access; the VCN domain is power/clock-gated by PSP/SMU and MMIO reads hang the bus.
- The earlier CU-unlock suspect is cleared: its writes completed before death. Board kernel's printed prefix `bc250-40cu-enable` differs from corpus patch `ps5-40cu-enable` — the installed 1.92 build is a later revision than `recon/linux.patch`; no `bc250_vcn_mode` exists in that patch copy, so the installed kernel source is newer than the corpus snapshot.
- Evidence class: `hardware-verified` (controlled experiment, synchronous capture).
- Next branch (firmware policy): retest reviewed D3-B2 candidate `439e2481...` with fixed display wiring, then repeat the same controlled mode2+blacklist+modprobe probe. Requires operator power-cycle to mode1 and exact flash approval. Alternative no-flash branch: S2 runtime C2P mailbox unlock from the booted OS.

## D3-B2 reflash write intent (approved 2026-09-12 03:2x+05:00)

- Operator approval (structured question): flash D3-B2 candidate for the PSP-policy test with corrected display wiring, then mode1 video/PSP check and controlled mode2 probe.
- Exact target: board `BC250-01`, chip Winbond `W25Q128.V` (16 MiB), backend `ch347_spi:spispeed=1.875M`.
- Tool: `/tmp/bc250-flashrom-resume-tDCb0q/prefix/usr/bin/flashrom` (pinned signed flashrom 1.8.0, SHA-256 `5ee0b2e4ea215a81ec08997dad99c469bd9f2335d5237d623388dee29875573c`) — present and hash-verified just now.
- Write image: `/home/OWNER/orca/projects/bc250/candidates/BC250_VCN_D3B2_combined_v001_from_read-a.bin`, SHA-256 `439e248141ef6a9c1313bc7815696d570be8fed5471262596186f3da8914747d` — re-hashed just now, MATCH.
- Rollback image: `/home/OWNER/orca/projects/bc250/evidence/programmer/reads/20260911/read-a.bin`, SHA-256 `83c4e4205eec3ddaed5c284c62a73658cdd68a834b521820a96ef622288f8ee0` — re-hashed just now, MATCH. Rollback is a separate write requiring its own approval; triggered only on write/readback failure.
- Procedure: 1) operator physical reconfirmation — board fully unpowered, CMOS battery removed, clip attached with orientation check, programmer at 3.3 V; 2) probe `--flash-name` (stop unless Winbond W25Q128.V 16 MiB); 3) fresh pre-write capture to `evidence/programmer/reads/20260912/read-h-prewrite-d3b2-retest.bin` + hash reconciliation vs current chip state; 4) write with log to `write-d3b2-retest.flashrom.log`; 5) independent full readback `postwrite-d3b2-retest.bin` byte-compare + parsers; 6) only then operator power-up tests: mode1 video observation, then controlled mode2 probe.
- Expected effect if PSP accepts the policy: mode1 boots with video (display wiring now correct); controlled mode2 probe passes `vcn_v2_0_hw_init` (MMSCH version line appears) or fails GRACEFULLY with logged errors instead of wedging.
- Failure discriminator if PSP rejects: same wedge on VCN MMIO (no policy change applied) or no-video mode1 boot.
- No write has been executed yet. Result appended after each stage below.

## D3-B2 reflash: probe, pre-write reconciliation (2026-09-12 03:31-03:36 PKT)

- Physical reconfirmation: operator reported "готово" (board unpowered, battery removed, clip orientation checked, programmer 3.3 V). pkexec used for privilege (sudo needs password); operator approved the polkit prompts.
- Probe PASS: Winbond `W25Q128.V`, 16 MiB, CH347 SPI 1.875 MHz.
- Pre-write capture `evidence/programmer/reads/20260912/read-h-prewrite-d3b2-retest.bin`: SHA-256 `aa4c581cb4607faca6892879932a586cedd46eb260d01879445c5673c46eaa79` — did NOT match the expected APCB-only readback `6b1fe8ef...`. STOP rule applied; second read `read-i-recheck.bin` is byte-identical (`aa4c581c...`), so the chip content genuinely changed since 2026-09-11 22:10.
- Root cause analysis: full-image diff vs the APCB-only candidate shows exactly 1,420 changed bytes in 31 ranges, all confined to `0x008908..0x00B0B4` — the UEFI NVRAM/variable store at the head of the flash (boot variables written by the board itself during the post-flash boots and hard wedges). ZERO ranges inside APCB `0xAB1000..0xAB1B6F`; PSP directory, `$PS1`, FV/DXE regions byte-identical to the verified APCB-only state.
- Decision: proceed. The payload regions reconcile exactly with the verified prior state; the NVRAM drift is board-written and will be replaced by the candidate image wholesale, as in all previous candidate writes. Residual uncertainty: the drifted NVRAM content is not archived separately beyond the two full reads above (they ARE the archive).
- Proceeding to write with the exact approved image.

## D3-B2 reflash: write, readback, parsers (2026-09-12 03:36-03:45 PKT)

- Write: flashrom exit 0, full erase/write `0..ffffff`, built-in `VERIFIED`. Log: `evidence/programmer/reads/20260912/write-d3b2-retest.flashrom.log`.
- Independent readback `evidence/programmer/reads/20260912/postwrite-d3b2-retest.bin`: SHA-256 `439e248141ef6a9c1313bc7815696d570be8fed5471262596186f3da8914747d`, byte-identical to the approved candidate (`cmp` clean).
- Root parsers on the physical readback (all PASS):
  - `firmware_audit.py`: PSP Fletcher32 `0x9F717AB8` stored=calculated; BHD `0xECE7B2E6` match; APCB checksum byte `0x32` match. Report `d3b2-retest-inventory.json` SHA-256 `f5e687d68858ca4077b4495e6634615fea5e1aab76683a2019dc359eba6279ed`.
  - `apcb_detail.py`: `failed=false`; DFG words `0x007FFF00` (VCN-enabling value). Report SHA-256 `15c2e88f1f0011ed9cc8d66b72678fa65797f6543177485dc2a1239bc72e2529`.
  - `verify_vcn_d3b2_candidate.py` vs stock source `read-a.bin`: 25/25 PASS. Report SHA-256 `9a112d3eb134ce6226296ecbd1048bf6c8b51c34b21e5b88c5255d8f6f54f563`.
- Evidence class: hardware-verified at SPI write/readback layer only. PSP acceptance, video, VCN runtime: UNRUN.
- Next: operator disconnects programmer, reinstalls CMOS battery, connects display CORRECTLY, powers up, selects mode1; reports video result. Then the controlled mode2 probe (blacklist entry already installed).

## Re-write of the same D3-B2 image on operator request (2026-09-12 03:5x PKT)

- Operator statement: "прошей ещё раз возможно я ошибка" — suspects an operator-side mistake during the boot attempt; explicitly requested a re-flash. No boot result was reported before this request.
- Prior state: readback already proved the chip byte-identical to the approved candidate at 03:45; a re-write of the SAME approved image is idempotent and bounded. Approval for this exact image/target was given earlier this session; re-write requested by the operator.
- Result: write exit 0 (erase/write `0..ffffff` done); independent readback `postwrite-d3b2-retest-2.bin` SHA-256 `439e248141ef6a9c1313bc7815696d570be8fed5471262596186f3da8914747d`, byte-identical to the candidate (`cmp` clean). Chip state proven correct twice on the SPI layer.
- Note for the record: a re-flash cannot change the boot outcome because the chip already contained exactly these bytes. The remaining variables are physical setup (battery, clip, display wiring) and board behavior; the video observation is still pending and remains the decisive next datum.
- Next: operator reinstalls battery, connects display correctly, powers up, selects mode1, reports video result.

## APCB-only base restore intent (approved 2026-09-12 04:1x PKT)

- Boot observation of D3-B2 retest: indicators on, fan spins, no video with confirmed-correct wiring — PSP halts on the modified policy. Operator decision: return to a bootable base and continue VCN unlock via the runtime branch (S2).
- Operator approved flashing `candidates/BC250_APCB_DFG_only_v001_from_read-a.bin`, SHA-256 `6b1fe8ef504142d5d5273a85b6c9febdf0b1fb8fc08ebab2593281c320cb9d70`, to BC250-01.
- Rollback for this write: the chip currently holds verified D3-B2 `439e2481...` (readbacks archived); stock `read-a.bin` `83c4e420...` remains preserved.
- Procedure: operator physical reconfirmation (unpowered, battery removed, clip, 3.3 V) -> probe -> pre-write capture + reconciliation -> write -> independent readback + parsers -> operator boots mode1 to confirm video/Linux.
- Parallel root work while the operator prepares hardware: reread `bc250-bios/docs/10-runtime-unlock-recipe.md`, EXPLOIT-SPEC, vuln-1/vuln-2 and design the S2 controlled runtime C2P/mailbox experiment (no flash; write-capable mailbox experiment on the booted OS, one variable, timeouts, readback, stop conditions).
- Result appended after execution.

## APCB-only base restore result (2026-09-12 04:2x PKT)

- Physical reconfirmation: operator "готово" (unpowered, battery removed, clip, 3.3 V).
- Probe PASS: Winbond `W25Q128.V` 16 MiB. Pre-write capture `read-j-prewrite-apcb-restore.bin` SHA-256 `439e2481...` — byte-identical to the verified D3-B2 state (no NVRAM drift; board never booted after the retest write). Reconciliation PASS.
- Write: flashrom exit 0, `VERIFIED`. Log: `write-apcb-restore-20260912.flashrom.log`.
- Readback `postwrite-apcb-restore-20260912.bin` SHA-256 `6b1fe8ef...` — byte-identical to the APCB-only candidate. `apcb_detail.py` failed=false.
- Board base is now the known-bootable APCB-only image. Next: operator reinstalls battery, disconnects programmer, connects display, boots the mode2+blacklist diagnostic entry (boots fully, amdgpu not loaded), then root runs the S2 C2P preflight and mailbox sequence over SSH.

## S2 stage 1 write intent: C2P command 0x100B (token request) (2026-09-12 04:3x PKT)

- Board state: mode2+blacklist boot alive, amdgpu not loaded, BAR5/resource5 mmap verified working.
- Corpus reconciliation: worker-2 verdict table confirms D3-B2-class static policy edits were historically hardware-rejected by PSP RSA (matches our fresh no-boot result; G7 recorded). The C2P runtime path (0x100B/0x100C/0x1033) is UNRUN historically; the transport encoding (direct C2PMSG_35 command write vs ring path) is the recipe's declared open link.
- Planned action (write to live PSP mailbox): allocate one 4K-aligned page (mmap MAP_LOCKED|POPULATE, physical address via /proc/self/pagemap), write buffer PA to C2PMSG_36/37 @BAR5 0x58190/0x58194, write command `0x100B` to C2PMSG_35 @0x5818C, poll bit31 (5 s timeout), then read buf+0x14 (expected `0x40` written by TOS fn@0x3528) and buf+0x100..0x11F (per-boot token).
- Expected signal: bit31 sets within 2 s; token 0x20 bytes non-zero at +0x100; marker file `/tmp/bc250-s2-markers.txt` records each stage with fsync.
- Failure/abort: bit31 never sets or buffer unchanged -> clean stop, no retries of the same encoding; fallback candidate is the C2P ring path (C2PMSG_67/69/70/71), designed separately. Worst case bounded: PSP ignores/rejects the command; no flash touch; power-cycle not expected.
- One variable: this is the first mailbox write; no other command runs in this stage.

## S2 stage 1 script prepared offline (2026-09-12 ~06:20 PKT, board still down)

- Context resolution for the record: the Sep-11 no-video series was non-discriminating (display wiring, G7 at 22:00); the D3-B2 retest at 03:47-04:14 ran with corrected wiring, so "PSP halts on the modified policy" IS a discriminating hardware-verified negative. Static BIOS policy edits are RSA-closed (fresh result + worker-2 corpus verdict agree).
- Built `stage_s2_c2p_token.py` (local staging `/tmp/bc250-stage2a/`, py_compile PASS): BAR5 mmap via `resource5`, MP0-mailbox class only (C2PMSG_35/36/37/64/81 at BAR5 offsets `0x5818C/0x58190/0x58194/0x58200/0x58244`), 4K-aligned MAP_LOCKED page + PA via `/proc/self/pagemap`, prechecks (TOS ready bit31, SOS alive bit31), issue cmd `0x100B`, poll bit31 (2 s), read `buf+0x14` (static prediction 0x40) and `buf+0x100..0x11F` (token). JSON log + `/tmp/bc250-s2-markers.txt` markers. NO VCN-segment MMIO access in this stage (July wedge class avoided by construction).
- Blob builder ready (imported `tools/psp-policy/c2_blob_builder.py`, groups 0x201 VCN tail + 0x210 binding, token-first body layout + `count-then-entries` probe variant). Stages 2-4 (0x100C load + 0x1033 apply) deliberately NOT scripted yet: the dispatcher-word encoding over C2P is the recipe's declared open link; stage-1 results inform it.
- Deploy target: `/home/OWNER/vcn_unlock/`; run under the mode2+blacklist diagnostic boot (proven to reach full userspace without amdgpu). Runbook: operator boots mode2-diag -> root runs stage 1 -> STOP, review JSON -> decide stages 2-4 encoding.
- Rollback: none needed (read-only wrt hardware state except the mailbox command itself; PSP side is volatile, cold cycle restores).

## S2 full-chain script prepared (2026-09-12, loop run #2, board still down)

- Built `stage_s2_c2p_full.py` (local staging `/tmp/bc250-stage2a/`, py_compile PASS): stages 1-4 in one run — 0x100B token -> inline blob build (both layouts: `entries-direct` / `--layout-count-first` for the supervisor-parser probe) -> x86 buffer {0x9000, 0x7F} + pad 0x8000 + blob, 4K MAP_LOCKED pages with pagemap PA -> 0x100C load (primary transport = direct C2PMSG_35/36/37, `--ring` variant via C2PMSG_67/69/70/71) -> 0x1033 apply -> verdict read BAR5 UVD_VERSION/POWER_STATUS.
- Blob builder self-test PASS offline: round-trip parse of both layouts reproduces the exact group records (0x201 x6 incl. program->commit order, 0x210 x2); `entries-direct` blob = 400 bytes == the historical canonical `c2_runtime_unlock_blob.bin` size (format match with the imported builder).
- Explicit stop conditions in-script: no completion bit on any command -> clean stop (no same-encoding retries); the verdict read is documented as potentially bus-hanging if the apply failed (July wedge class) — cold cycle = rollback. One run = one token lifetime (per-boot token).
- Firmware-audit memory updated (loop run #1): stock 0x45 has no VCN records; $KDB parse (kid 96ea7cfe public in own t50); ABL1 three svc#6 wrappers, 0x12a4 returns 0 unconditionally; the "PSP halts" wording downgraded to inference with the SSH-at-t+90s discriminator for the next flash window.

## C2P transport cross-check (2026-09-12, loop run #3, board still down)

- Reconciled `recon/keshas_amdbc250_psp.c` (the recipe's transport reference): the C2P map (MP0 base 0x58000; C2PMSG_35/36/37/64/67/69/70/71/81 at BAR5 offsets 0x5818C/...) is marked "verified by psp-ring-submit-test against live hardware 2026-08-18" — the stage_s2_c2p_full.py primary transport (direct C2PMSG_35/36/37) uses the hardware-verified offsets/class. The ring path in that source serves GFX fw-load frames (GFX_CMD_ID_LOAD_IP_FW 0x06 from psp_gfx_if.h), a different command space than the TOS dispatcher commands 0x100B/0x100C/0x1033 — supports the direct-mailbox primary and keeping `--ring` as fallback only.
- Noted risk in the S2 chain: the dispatcher frame arg r2 (buffer size, fn@0x3528 requires >= 0x140) is supplied by the on-die supervisor, not by us; a size mismatch would surface as error 0xFFFF300F in the response buffer (buf+0x14 / buf+0x00 region) — the stage-1 dump already captures this, so the experiment self-reports the encoding gap.
- Board still unreachable (ping 100% loss, SSH no route) at ~06:3x. S2 full-chain script + stage5 donor-routes script both staged for deployment on the next up window.

## S2 full chain on mode2-diag + stage5 donor dataplane: DEFINITIVE NEGATIVE (2026-09-12 06:42-06:50 PKT)

- Operator powered the board and booted the mode2+blacklist diagnostic entry (cmdline verified: `modprobe.blacklist=amdgpu amdgpu.bc250_vcn_mode=2`, amdgpu NOT loaded, BAR5 512K free). Key transport fact: the SMU lib uses the PCI config-space 0xB8/0xBC window on 0000:00:00.0 — amdgpu-independent; the whole runbook works on mode2.
- Chain executed in one session: `--verify` (unlock, gate FD->open) -> `--manual-powerup` (ctrl=0x00000000 AT BOOT — the gate did NOT re-hold on this boot, unlike all mode1 boots; deviation noted, hypothesis: mode2/amdgpu-absent boot state) -> native run (fire 0x61: slots LANDED, enables ON) -> `stage2b_writefirst.py` (59/59 accepted, commit readback=1) -> `stage5_full_dataplane.py` (DEPLOYED + RUN: all 15 donor route/window/binding writes ACCEPTED, SMU alive, commit=1).
- NEW SAFE CLASS (hardware-verified): NBIF config reads `0x6A1xx` + `0x33E0` via SMU debug path do NOT wedge; first live capture: `0x6A140=0x8000, 0x6A144=0xffff, 0x6A148=0x00800000, 0x6A14C=0x8, 0x6A150=0x80000000, 0x6A154=0x80000001, 0x6A15C=0x2f0, 0x6A17C=0x2, 0x6A1B4=0xf57f, 0x33E0=0x3820`.
- VERDICT (the decisive experiment): BAR5 arbiter `UVD_VERSION/UVD_POWER_STATUS/UVD_NO_OP/UVD_STATUS` = ALL-ONES with CLEAN reads (no hang). The island remains ISOLATED even with full bring-up + gasket (lock tail removed) + full donor dataplane routes. G7-LEVEL FINDING: the donor route VALUES are not the missing lever; the clamp is deeper (remaining suspects: the island ISO/reset held outside the dom6 sequencer; a missing SMU fw-side message (the real PowerUpVcn equivalent in the unmapped Q3 space); PSP-side isolation beyond the gasket).
- C2P track (parallel): direct-mailbox 0x100B encoding dead-ends (completion bit immediate, buffer untouched; size-in-33/34/38 variants all empty) — G6 applied after 4 same-class attempts; the dispatcher frame encoding lives in the on-die supervisor (not in any image). Ring registers 67/69/70/71 = 0 (no boot-time ring; the ring is an amdgpu-driver construct).
- Evidence: `stage2b_writefirst_20260912_064724.json`, `stage5_full_dataplane_20260912_064729.json`, `s2_c2p_probe_20260912_064406.json`, `s2_c2p_probe2_20260912_064513.json` (all on board ~/vcn_unlock/).
- Board state: mode2-diag session fully brought up, SMU alive, rollback = cold cycle. No flash touched.

## S2-L5: msg 0x5C native domain-power experiment (2026-09-12 ~08:10 PKT)

- Intent: fire the NATIVE PMFW message 0x5C (handler @0x1f038) whose body calls PowerUpDomain(idx) for domains 0xe/0xf/0x11 (14/15/17 — never powered in any prior experiment) as part of its frequency-apply flow. Decoded statically today: msg 0x5C handler -> 0xffc(GetMsgArg) -> 0x2384c/0x23860(0xe) -> float freq math -> 0x1f0e6/0x1f0fb PowerUpDomain(0xe) -> 0x1f193(0xf) -> 0x1f19e(0x11); PowerUpDomain = fn@0x2362c -> 0x23b14(idx, 1) (dom6 power fn, hardware-verified anchor).
- Target: live mode2 session (board brought up: unlock + fire 0x61 + gasket 59/59 + stage5 15/15; arbiter all-ones = baseline).
- Procedure: python3 one-shot on board: Bc250Smu(0000:00:00.0); alive(); send_message(3, 0x5C, [700]); alive(). Arg = 700 (MHz-class value; handler parses arg0 via GetMsgArg and rejects 0 via the 0xff bail path).
- Expected effect: domains 14/15/17 power-up + freq set; SUCCESS signal = BAR5 UVD_VERSION/POWER_STATUS become non-all-ones (arbiter).
- Rollback: cold power cycle (universal; session-reversible class, no flash).
- Stop condition: SMU dead (mailbox silent) -> stop, cold cycle, register.

## S2-L5 amendment: gate removal (2026-09-12 ~08:20 PKT)

- First fire result: status=255, ret=700, SMU alive. Static cause: handler 0x1f038 bails when SRAM byte [0xcec8+0xf6] == 0xff (driver-table not posted; amdgpu absent on mode2). The struct 0xcec8 = the fw's driver-state copy (freq fields +0x100/+0x104, flag bytes +0xf6/+0xf7, counts +0x11/+0x12); no fw writer of +0xf6 -> it arrives only via the driver-table transfer (Q0 0x04/0x05 + 0x07).
- Revised procedure (ONE variable): SRAM dump 0xcec8..0xcee8 baseline -> smu_write_bytes(0xcfbe, b"\x00") (proven gated write class: sec_set_write_ptr 0x28 + write-through 0x29) -> readback -> fire msg 0x5C arg=700 -> status/alive -> re-dump.
- Success signal unchanged: BAR5 arbiter non-all-ones.
- Rollback: cold cycle (SRAM state is volatile; the byte is boot-time 0xff anyway).

## S2-L5b RESULT: HARD WEDGE (2026-09-12 ~08:25 PKT)

- Observed: board fully dropped mid-experiment (ping 100% loss, ssh "No route to host") during/between the SRAM gate write (0xcfbe <- 0x00) and the msg 0x5C fire. No JSON captured (the script writes results only at the end). SMU/session state: dead until cold cycle.
- Rollback: COLD POWER CYCLE required (operator). Universal rollback class, proven twice before.
- Evidence value (static-analysis + wedge signature): (1) the first fire (gate intact) returned status=255 CLEANLY = the handler bailed safely — the gate logic works as decoded; (2) with the gate cleared, the board wedged HARD — the same wedge class as the amdgpu first-touch of the isolated VCN MMIO. Strong indicator the handler RAN past the gate and the domain 14/15/17 power-up path hit the isolation trap. This is the first non-amdgpu wedge of the campaign.
- Remaining uncertainty: which exact step killed the board (the SRM write to the live driver-state struct vs the msg execution). Discriminator for the next run: perform the gate write ALONE first (no fire), observe 30 s; then fire in a separate step.
- Method note (G7): next iteration must also snapshot the driver-state struct 0xcec8 fully (0x138 bytes) BEFORE any write, and should consider transferring a complete proper driver table via Q0 0x04/0x05+0x07 instead of surgically clearing one byte (the handler may read other unposted fields after the gate — e.g. freq limits +0x100/+0x104 = 0 garbage -> div-by-zero/hang class).

## S2-L6 loop run: wedge mechanism fully decoded (2026-09-12, offline)

- Input: SMU_OFFCHIP_FW~0x8_0.58.6.0.body (262144 B, corpus) + pypcode Xtensa decode (/tmp/bc250-venv).
- fn 0x23b14(idx, on) = per-domain SMN power-command driver: domain table @0xf550 (pool 0x17434), SMN base 0x10ffe00 (mask 0xfffff), status regs = base + (entry+0x38 + entry+0x8) + 0x200 load offset, cmd regs via fn 0x233e8. THREE infinite status polls (bit8 @0x23b5c, bit16 @0x23b78, bit0 @0x23b96) — NO timeout. The S2-L5b wedge = the fw polling an unacked domain forever.
- Per-domain (cmd, status): dom6 0x110009C/0x11002EC; dom7 0x1100340/0x1100354; dom14 0x1100085/0x11000A84; dom15 0x11000A34/0x11000E84; dom17 0x11000070/0x11000274 (see the script for the authoritative computation). Boot-default state bytes: dom6=0x0c (the only powered domain at boot), dom14=0x08, dom15=0x04, dom17=0x00.
- Also decoded: fn 0x1f038 tail — the arg (MHz) -> float dep conversion (0x23a54/0x23a14) -> PowerUpDomain(0xe) + 0x23538(2, 0xe); garbage freq limits are NOT read in this path — the wedge = the domain-14 power-up itself.
- Deliverable: /tmp/bc250-stage2a/read_domain_status.py (READ-ONLY status dump, host-side mem64 SMN reads, cannot wedge the fw) — ready to deploy for the next boot. Success = the ACK-bit patterns of domains 14/15/17 vs the dom6 baseline -> answers WHY the ACK never comes (ISO-holder identity).
- Evidence class: static-analysis; the addresses are image-derived and need one live read to confirm the addressing model (the read itself = the confirmation).

## S2-L6 RESULT: mailbox wedge from a cmd-register READ; isolation = bus-level (2026-09-12 07:01-07:03 PKT)

- After the operator cold cycle + unlock: read_domain_status.py ran. dom6 cmd/status (0x110009C/0x11002EC) and dom7 (0x1100140/0x1100354) = CLEAN zeros, SMU alive. The dom14 cmd read (0x10FFE85) TIMED OUT -> the SMU mailbox wedged (alive_after=false). HOST SURVIVED (ping/ssh OK, uptime continued) — this wedge class = mailbox-only, NOT the board-killing S2-L5b class.
- Lesson (G7, hardware-verified): the COMMAND registers are side-effect registers — the fw only WRITES them (via 0x233e8) and never reads; the 0x10FFExx block hangs on read (same class as the DF-space read wedge). Status registers = the responsive 0x1100xxx block. My v1 script violated the "never read side-effect SMN registers" rule.
- ISOLATION FINDING (upgraded): the dom14 cmd block sits at 0x10FFE85 (odd address, dead-on-read block); the statuses of doms 14/15/17 (0x1100084/0x1100284/0x1100074) sit in the readable block. The isolation manifests at the power-controller level; whether the ACK can be observed/forced = testable READ-ONLY (statuses) and then via a DIRECT host-side cmd write (the fw's own value formula: cmd = status | bit0/0x10/0x100 per the 0x23b14 decode) with a HOST-side timeout — no fw involvement = no wedge risk.
- Prepared: /tmp/bc250-stage2a/domain_status2.py (v2: statuses ONLY, read-only, safe) — deploy + run after the cold cycle. Then the direct-write experiment (separate step, one variable).
- Rollback: cold cycle (mailbox wedge is not host-recoverable; the read-wedge class was closed earlier with the same recovery).

## S2-L6b loop run: driver-table structure + revised experiment plan (2026-09-12, offline)

- Feature 5 handler (0x1ded8) decoded: sequencer 0x1b1e4(0x17, pool 0x173b4) + sets byte [0xcec8+0x13]=1; the disable sibling (0x1df08) clears it. NOT the driver-table post.
- Driver-state struct semantics sharpened: [0xcec8+0xf6] = the driver-table ENTRY COUNT (0xff = "no table posted" -> the msg 0x5C gate); +0xf7 = the entry-count LIMIT (the accessor fn @0x1df4f bounds idx < [+0xf7]); +0xd = the current index. The ONLY writer = the Q0 driver-table transfer (msgs 0x04/0x05 SetDriverTableDramAddrHigh/Low + 0x07 TransferTableDram2Smu) — the community module already exposes these (api_q0.py).
- Minimal fake table candidate: a zeroed DRAM page with [+0xf6]=0x00, [+0xf7]=0x00 (all accessor walks then safely skip), posted via Q0 0x04/0x05+0x07; verify by reading [0xcfbe] == 0x00 via smu_read_bytes.
- DECISION (G6-consistent): msg 0x5C will NOT be fired via the fw even with the gate open — the fw's own no-timeout polls on the unacked dom14 repeat the S2-L5b board-wedge. Instead: DIRECT host-side SMN cmd write to the dom14 power command register (the proven sec SMN write class; value formula from the 0x23b14 decode: cmd = status | bit) followed by a status read with OUR timeout. If the transaction wedges the fabric -> the board dies (cold cycle), but the fired transaction itself = evidence; if the ACK bit appears -> THE DOMAIN POWERS and the BAR5 arbiter gives the verdict.
- Next-boot sequence: (1) unlock; (2) domain_status2.py (statuses only, read-only, safe); (3) the driver-table fake post via Q0 (optional, only if the direct write path needs the table); (4) the direct cmd write experiment (SEPARATE step, one variable, host-side timeout, ping check after).

## S2-L6c loop run: write primitive + IPC decode (2026-09-12, offline)

- fn 0x233e8(addr, val) = the fw's SMN write primitive: val -> SMN 0x10ffe00 + (addr & 0xfffff) + 0x200 (memw-surrounded dword store). EXCEPTION: if 0x5afff <= addr <= 0x5b7ff (pools 0x17890/0x17894) the write routes through fn 0x1b514 = save (addr, val) on the stack, then call 0x10d0 with msg id 0xfe and the stack pointer as the arg = an IPC REQUEST TO THE SECOND SMU CORE (the master/slave split). The 0x5AF/0x5B0 region = the slave SMU's address space.
- Consequence: the dom14-class power registers reachable from the master fw are written via SMU-to-SMU IPC; a host-side direct write must reproduce the same target semantics (the mem64 SMN write class covers the direct path; the slave-side registers are a separate question if the direct write is rejected).
- Evidence class: static-analysis. Registered in memory/firmware-audit.md.

## S2-L7/L8 RESULTS: the dom14 power transaction never completes (2026-09-12 07:05-07:07 PKT)

- S2-L7 (statuses v2, read-only, ALL FIVE READ CLEAN, SMU alive): dom6 0x00000000, dom7 0x00000000, dom14 0x00000041 (bit0 = busy), dom15 0x00000000, dom17 0x80000002 (bit31 + bit1). The isolated domains carry DISTINCTIVE boot statuses (busy bit0 on dom14, bit31 on dom17) — born locked.
- v1 addressing bug corrected (G7): the 0x233e8 primitive ADDS +0x200 itself; the true dom14 cmd = 0x1100085 (readable block); the S2-L6 wedge = my double-counted offset hitting the 0x10FFExx region. The cmd/status = one dword pair: the request doorbell = write @0x1100084 (value = status|1), the ack = read @0x1100085 (poll bit8 -> 1, bit16 -> 0).
- S2-L8 (direct host-side write, no fw): req_before 0x41; write 0x41 (the decoded power-on request) ACCEPTED; the ack read TIMED OUT -> the mailbox wedged again (the host survived). alive=false.
- VERDICT (hardware-verified, two independent paths): the domain-14 power-on request fires and the transaction NEVER COMPLETES — the ack never asserts whether the request comes from the fw (S2-L5b board wedge) or from the host directly (S2-L8 mailbox wedge). The isolation lives BELOW the SMU firmware, at the power-controller/fabric level for the domain-14 cluster.
- Consequence: the runtime power-on route (any variant that ends in a dom14 power transaction) is CLOSED as a standalone unlock lever. The remaining levers: (a) WHO asserts the ISO/reset on the dom14 cluster BEFORE the power request — the boot-time policy territory (APCB/gasket/policy records; our 59-record gasket may simply not cover the VCN domain cluster — the donor gasket comparison is the next offline step, apcb-policy-analysis skill); (b) the dom17 bit31 marker decode; (c) the boot-time-only re-sampling model.
- Recovery: cold cycle #3 required (the mailbox is wedged; the host is alive and usable for the offline work).

## S2-L9 prepared: the donor 0x201 VCN config gap hypothesis (2026-09-12, offline, apcb-policy-analysis)

- Evidence (docs/02-gasket-groups.md): the donor gasket 0x201 group carries the VCN instance config values (0x0900C914->0x7FFF, 0x0900C930->0x36, 0x0900CB80->0xFF, 0x0900C234->0 then 1); the stock has NONE of these four addresses. Our runtime gasket (59/59) = the xx234 enable-bit family ONLY — the 0x201 VCN config values were NEVER applied at runtime.
- Hypothesis: the dom14 power transaction hangs because the VCN instance clock-gating/config (the 0x201 values) is never applied; the power sequencer waits on an unconfigured instance.
- Prepared: /tmp/bc250-stage2a/s2_l9_vcn_config_then_power.py — statuses baseline -> the 4 config SMN writes + readbacks -> the two-pass C234 -> the dom14 request doorbell -> one bounded ack read. The fw is never involved. Rollback: cold cycle.
- Prerequisite: cold cycle #3 (the mailbox is wedged from S2-L8).

## S2-L9 RESULT: the VCN config space is ALSO bus-isolated (2026-09-12 07:09-07:11 PKT)

- Fresh boot, unlock OK. The baseline statuses reproduced EXACTLY (dom6 0x0, dom14 0x41, dom17 0x80000002) — the L7 data is stable across boots.
- The FIRST config write (0x0900C914 <- 0x7FFF, the donor 0x201 value) TIMED OUT and wedged the SMU mailbox (msg 0x2C). The subsequent steps never ran. alive_after=false. The host survived.
- Contrast: the gasket's 0x0900C234 write = accepted at runtime (59/59, commit=1, twice), but the C914/C930/CB80 config sub-block = hangs on a direct write.
- VERDICT (third independent bus-level confirmation): the dom14 power transaction (S2-L5b/L8), the dom14 config writes (S2-L9), and the DF-space reads (the earlier closed class) ALL share the same signature — a transaction into the VCN cluster that never completes. The isolation sits below the runtime-reachable register space: the VCN config/power fabric is dead on this SKU at boot, not gated by a runtime register we can set.
- STANDING VERDICT: the RUNTIME unlock (any sequence of runtime SMN/SMU writes with the board booted into the stock policy) is CLOSED by evidence. Remaining paths: (a) the boot-time/flash track — a policy/donor image whose PSP/ABL applies the VCN config BEFORE the islands are brought up (blocked so far by the signature acceptance problem; the D3-B2 carrier with stale signature material does not boot); (b) the D3-B2 SSH-at-t+90s discriminator if a flash window happens — it decides whether even the donor boot reaches a working VCN on this board revision.
- Recovery: cold cycle #4 required.

## S2-L10 (stage R) RESULT: dom14 power denial is total (2026-09-12 07:14-07:17 PKT, mode1)

- Environment: mode1 (kernel 7.2.0-1.92-cachyos-vcn-bc250), fresh boot, unlock OK, the full proven runbook applied: --verify, fire 0x61 (the slots/enables), stage2b 59/59 (commit=1), stage5 15/15.
- Stage R: the FULL VULN-1 aperture replay (56/56 ACCEPTED, zero errors, bank-12 control readback 0x1) — the complete Cezanne bank-12 program latched at runtime via the proven transport. The S2-L9 wedge = fully attributed to the mode2 environment, NOT the region.
- The dom14 request doorbell: fired (0x1100084 <- 0x41). The ack read: TIMED OUT -> the mailbox wedged (alive=false). IDENTICAL to S2-L8.
- The dom14 power transaction has now been denied in EVERY tested configuration: mode2 (fw path, direct path, config path) AND mode1 (the full proven environment + the complete aperture program). The denial is independent of the boot mode, the driver table, the gasket aperture, and the dataplane routes. It lives below every runtime-reachable register.
- VERDICT (hardware-verified, five experiments): the dom14-cluster power-up is hardware-denied at runtime. The remaining unlock route = the boot-time application by the PSP itself: (a) D3-A (the APCB DFG grant patch — unsigned, 3 bytes + the checksum, built and verified 26/26) = the test of the lock-2 grant theory; (b) the D3-B2 carrier path (blocked by the signature acceptance, two no-video results). The D3-A flash requires: the programmer, the full dump backup (verified present, md5 7607a34c), the operator approval of the exact image.
- Thinking-skills application (the user-directed inversion pass): the inversion exposed that the aperture+doorbell combination had never been tested together — S2-L10 tested it and produced the definitive negative. The inverted model ("the PSP powers the VCN itself at boot when its policy says so" — the donor 0x03E810=6 = the VCN segment enable in the PSP mailbox) now ranks the boot-time route above all runtime routes.
- Recovery: cold cycle #5 (the mailbox wedged; the host survived).

## Loop run (2026-09-12 ~07:30 PKT): DFG sub-mapping offline verification attempt — negative

- The D3-A patch's core assumption (the VCN master = DFG sub 0x0C) remains inferred. Offline: the vendor sources (keshas_*, agesa_*) contain no requester/permission data (the consumer is on-die); the corpus has no openSIL DfGroup headers; the web search for the AMD DF firewall requester-ID tables (openSIL/AGESA/security whitepapers) returned nothing decisive — the DF firewall requester assignments are not publicly documented for this class.
- Consequence: the sub=0x0C mapping settles ONLY empirically (the D3-A flash test). The decision brief (docs/action-logs/2026-09-12-d3a-flash-decision-brief.md) stands; no further offline work can de-risk the flash decision. The D3-B2 signature question stays closed pending a flash window.
- The board: reachable, mailbox wedged (post-S2-L10); no runtime actions possible.

## Loop run (2026-09-12 ~07:40 PKT): dom17 bit31 decode attempt — inconclusive

- The board responds to ping (the mode1 session up; the mailbox state unchanged = wedged after S2-L10).
- Decoded the 0x23ba3 region (the power-off path continuation of 0x23b14): a 27-byte state-array clear + a walk of the clock-tree pool 0x178f0 (+0x8c validity bytes, +0x74/+0x76 fields). No bit31 consumer found in the power-function region.
- The dom17 status bit31 interpretation stays open (a low-priority backlog item; it does not gate the D3-A decision).
- The blocker is unchanged: the D3-A flash decision (the operator approval + the programmer).

## Loop run (2026-09-12 ~07:50 PKT): D3-A post-flash one-shot prepared and deployed

- Prepared + deployed to the board: `~/vcn_unlock/d3a_post_flash_test.sh` — chains unlock -> verify -> power-up/fire 0x61 -> gasket 59/59 -> dataplane 15/15 -> S2-L10 (the aperture + the dom14 doorbell + the bounded ack) -> the MMIO arbiter (gated: runs only if the SMU survived the doorbell step). Every step = the established proven class; the JSON logs land in ~/vcn_unlock/.
- Purpose: during the D3-A flash window the whole post-boot test = ONE command, minimizing the manual steps and the decision points at the hardware.
- The board: reachable; the mailbox state unchanged (wedged, post-S2-L10). The blocker is unchanged: the operator's D3-A decision.

## Loop run (2026-09-12 ~09:00 PKT): ABL movw/movt hunt — DFG consumer offline search CLOSED

- Scanned all five ABL bodies (ABL0-4, 21.11.26.0) for Thumb-2 movw/movt pairs constructing the VCN-bank addresses (0x0900C234/0x0900C914/0x0900CB80/0x0900C830): ZERO hits in any body. The earlier raw-constant scan (both endiannesses) = also zero.
- Conclusion: no plaintext PSP-side body (PSP bootloader aside, it is encrypted) constructs or references the VCN firewall bank. The DFG/VCN permission consumer is definitively in the on-die ROM or the encrypted t01. The offline search for the DFG consumer is CLOSED.
- Consequence for the campaign: nothing offline can verify the DFG sub=0x0C assumption; the D3-A flash test is the only way. The decision brief stands.
- The board: reachable (mode1); the mailbox state unchanged. The blocker is unchanged: the operator's D3-A decision.

## Loop run (2026-09-12 ~09:30 PKT): idle-poll state reached

- The board: reachable (mode1). No runtime experiments exist without the flash (the method space is exhausted); no offline de-risking remains.
- Note on the dom17 bit31 backlog: the dom17 status address (0x1100074) carries the same table-decode uncertainty as the other parallel-array fields; the bit31 interpretation is likely unreliable without a live re-check. Deprioritized.
- The loop is now in an idle-poll state: every run re-checks the board and re-reports the same blocker. Recommendation: keep the loop only as the board watchdog, or cancel it until the D3-A decision.
- The blocker is unchanged: the D3-A flash decision (the operator approval + the programmer).

## D3-A FLASHED (2026-09-12, CH347T programmer from the workstation)

- The operator attached the CH347T (1a86:55db) with the SOIC8 clip; the flashrom v2.0.0-devel was built locally (/tmp/flashrom-src, the ch347_spi programmer); the chip = Winbond W25Q128.V 16MB detected.
- Pre-flash dump: /tmp/d3a_flash/board_before_d3a.bin (md5 86440b821eb8fd2e15b2b2228b35d9af — differed from the reference base by ~1.37MB, the UEFI region drift from the morning's experiments; saved as the rollback).
- Wrote: 03_D3-A_CONTROL_APCB-DFG-i-only.bin (md5 bd2605e5869b21ec7426e3084d69aec8). flashrom: "Erase/write done from 0 to ffffff; Verifying flash... VERIFIED".
- Independent readback: /tmp/d3a_flash/readback_after_d3a.bin, md5 = bd2605e5869b21ec7426e3084d69aec8 (byte-exact, 0 diffs vs the image).
- Rollback available: board_before_d3a.bin (the pre-flash state).
- NEXT (the operator): remove the SOIC8 clip from the chip, assemble, cold power-on to mode1. Then the one-shot: bash ~/vcn_unlock/d3a_post_flash_test.sh

## D3-A FLASH TEST RESULT (2026-09-12 13:59-14:01 PKT, mode1)

- The D3-A (the APCB DFG grant patch, the wildcard baseline 0x1f -> 0x7f) BOOTED FINE: the board came up normally on mode1 — the unsigned APCB-region patch is field-confirmed accepted (the VULN-2 surface proven on a real flash).
- The full one-shot chain ran: unlock OK -> fire 0x61 -> gasket 59/59 (commit=1) -> dataplane 15/15 -> aperture 56/56 (bank-12 control 0x1) -> the dom14 request fired.
- THE DOM14 DOORBELL WEDGED IDENTICALLY: the status before = 0x41 (born busy, the SAME as the pre-D3-A boots), the ack read = the timeout, the SMU wedged.
- VERDICT: the DFG baseline grant does NOT release the dom14 power denial. The grant theory (lock 2 = the DFG wildcard baseline) is DISCONFIRMED by the flash test.
- The elimination table after the D3-A: the dom14 denial survives the driver table (mode1), the full gasket xx234 (59/59), the full aperture program (56/56), the donor dataplane (15/15), the DFG baseline grants (flashed). The remaining mechanisms: (a) the PSP boot-time gasket program (the STOCK gasket = no VCN bank = the domain never given power rights at boot; the D3-B2-class flash = the carriers with the VCN program = the ONLY remaining path, signature-blocked by two no-video results); (b) the hardware/fuse class.
- CRITICAL OPPORTUNITY: the CH347T programmer is attached and the flash procedure is PROVEN (the dump/write/verify cycle completed on this hardware). The D3-B2 flash test = now one command away; its open question = did the D3-B2 boot AT ALL (the SSH-at-t+90s discriminator never ran — the two no-video results may be the fail-soft skip + the display wiring, not the halt).
- Recovery state: the SMU wedged (cold cycle needed); the rollback image (board_before_d3a.bin) + the procedure = proven.

## D3-B2 FLASHED (2026-09-12, CH347T, the operator-approved)

- Pre-flash dump: /tmp/d3a_flash/board_before_d3b2.bin (md5 047116f978e617177e52c9d2a4edb823 — the D3-A content + drift, saved as the rollback).
- Wrote: 02_D3-B2_MAIN_APCB-DFG-i_gasket+TOSpolicy_A-B-unsigned.bin. flashrom: "Erase/write done 0..ffffff; VERIFIED".
- Independent readback: /tmp/d3a_flash/readback_after_d3b2.bin, md5 448f5df5dfd44b95cc82f5b170dfa94f = the image md5, byte-exact (0 diffs).
- Rollback available: board_before_d3b2.bin + board_before_d3a.bin.
- NEXT (the operator): remove the clip, assemble, cold power-on. THE FIRST-RUN DISCRIMINATOR: the SSH probe at t+90s answers "did the D3-B2 boot at all" (the two historical no-video results may be the fail-soft skip, not the halt). If the SSH answers -> run the one-shot -> the dom14/VCN verdict.

## LOOP FINDING: PSP BOOT-TIME FIVE-DOMAIN PROGRAM DECODED (t28 body) (2026-09-12)

- Byte-pattern scan (the corrected LE pattern ?? C0 00 09 for the 0x0900Cxxx VCN-bank refs) over all extracted PSP bodies (the BC250_3.00 stock reference) hit:
  - 01_t02 (the PSP boot loader, 82KB): 1 ref = 0x0900C0EB @local 0xfea9.
  - 08_t28 (108KB, ARM Thumb-2, the TOS-class body): 3 literal-pool refs = 0x0900C004 @local 0xd2f8/0xfd78/0xfef8.
- The t28 function @local 0xfec8 (its literal pool = 0xfef8): writes 1 to 0x0001F8A4 (svc #0x7c = the TOS register-write syscall: (addr=r0, val=r1, size=r2)), then iterates a FIVE-entry table of (addr, value) pairs, 8 bytes each, writing 4 bytes per entry:
  - the table @t28 local 0x188d8 (the runtime ptr 0x00e188d8 = the load base 0x0E000000 + local): entries = 0x0001F8C4, 0x0001F8C8, 0x0001F8CC, 0x0001F8D0, 0x0001F8D4, all written 0.
- Interpretation: the PSP TOS zeroes FIVE consecutive per-domain registers at 0x1F8C4..0x1F8D4 at boot — the same count and order class as the five SMU domains observed live (dom6, dom7, dom14, dom15, dom17; the dom14 = the third = 0x1F8CC under this ordering). The master write 0x1F8A4 <- 1 precedes the loop.
- The caller chain: the stage-sequencer function @local 0xff04 calls 0xfe00 with the stage indices 1 (via 0x9020), 9 and 0xA (the two 0x80-byte tables selected by [ctx+4]/[ctx+8]); the 0xfe00 = validate -> svc lock -> parse -> dispatch 0x32c8 -> verify 0x14084 -> commit mask 0xffff (bl 0xfb18) -> svc unlock.
- Significance: this is the boot-time per-domain program class = the remaining mechanism (a) from the D3-A elimination table. The five zero-writes did NOT prevent the dom14 born-busy 0x41 in the stock boots — the next question is the semantics of the 0x1F8C4+i registers and 0x1F8A4 (the MP1/SMU-internal region, the same class as the decoded 0x1d940 apply block).
- The unrun check: the live SMN read of 0x1F8A4..0x1F8D4 at the boot baseline (AFTER the cold cycle, BEFORE any experiment) vs after the wedged dom14 request — the register-content diff would settle the semantics. The G7 note: the svc #0x7c syscall semantics (write-4) is inferred from the call shape, not from the TOS kernel decode.

## D3-B2 BOOT FAILURE + ROLLBACK (2026-09-12, the operator-reported)

- The operator reports the D3-B2 board fails initialization (the third no-video-class result; the flash procedure excluded as the cause: the readback md5 448f5df5... = the image md5, byte-exact).
- VERDICT: the PSP signature check rejects the unsigned $PS1-region carriers — the rejection is FATAL (no boot). The D3-B2 carrier route is CLOSED. The campaign elimination table is complete: every software-reachable route to the dom14/VCN power grant is exhausted (runtime x5, APCB DFG, unsigned carriers). Remaining: the PSP key RE (the loop goal (a)) and the hardware/fuse class.
- ROLLBACK: board_before_d3a.bin flashed via CH347T; "Erase/write done 0..ffffff; VERIFIED"; the independent readback md5 = 86440b821eb8fd2e15b2b2228b35d9af = the original pre-experiment state, byte-exact (0 diffs).
- NEXT: the operator removes the clip + cold boots to confirm the recovery; the loop continues with the PSP key RE + the t28 0x1F8A4..D4 register-semantics check (the live SMN read at the boot baseline).

## ROLLBACK CONFIRMED (2026-09-12 14:28 PKT)

- The operator cold-booted the restored board: mode1 (kernel 7.2.0-1.92-cachyos-vcn-bc250) came up cleanly, uptime 0 min at the check.
- The recovery from the D3-B2 boot failure via the CH347T programmer flash-back (board_before_d3a.bin, the byte-exact readback) is CONFIRMED working end-to-end.
- Campaign state: closed (negative for the unlock; the board restored to the pre-experiment state). The loop continues offline (the PSP key RE, the t28 TOS register-semantics decode).

## G7 RE-EVALUATION: the D3-B2 "signature-fatal" verdict is NOT yet proven (2026-09-12)

- Re-read of docs/research/2026-09-11-worker3-policy-sig-bootfail.md reveals a CONTRADICTION with today's fresh evidence: worker3 reports the APCB-only candidate as no-video/no-boot, but the D3-A (the same class: the APCB DFG patch) BOOTED CLEANLY TWICE TODAY (hardware-verified). Worker3's shared-baseline observations are confounded (their own note (b)).
- Worker3's three no-video candidates = the two $PS1 carriers (the policy-only AND the combined D3-B2). Both are equally consistent with TWO unattributed mechanisms: (a) the PSP signature halt before the x86 release (worker3's static assumption, never decoded in the t02); (b) the boot-time application of the VCN policy/gasket records hitting the SAME incomplete-transaction denial we proved at runtime (the S2-L5b class wedge — the policy targets 0x0900C234/C914/C930/CB80 are the exact runtime-wedge registers).
- There is also a third possibility never tested: the t02 fail-soft verifier SKIPS the rejected carriers (the earlier session decoded t02 as fail-soft) — then the x86 boots with the stock policy and no video (the display path unprogrammed), and the SSH would be ALIVE. The SSH-at-t+90s discriminator has NEVER been run on any carrier candidate.
- CORRECTION of today's earlier verdict: "the signature rejection is fatal" is NOT established. The cheapest decisive test = re-flash D3-B2 (the approval + the image + the byte-exact procedure all stand) + the SSH probe at t+90s, with the 3-minute proven rollback available.

## D3-B2 RETEST + DISCRIMINATOR RESULT (2026-09-12, hardware-verified)

- The D3-B2 re-flashed (the readback md5 448f5df5... = the image md5, byte-exact, 0 diffs; the cycle backup pre_d3b2_retest.bin, md5 5ccde448...).
- The operator cold-booted: "does not initialize, no image" (the same failure signature as the first D3-B2 attempt and the worker3 candidates).
- THE SSH-AT-t+90s DISCRIMINATOR RAN FOR THE FIRST TIME: 12 probes at 15 s intervals (~3 min) = ALL FAILED (no route/no SSH). The x86 NEVER releases from reset with the D3-B2 carriers on the chip.
- VERDICT: the fail-soft-skip hypothesis (the t02 skipping the rejected carriers with the x86 alive) is DISPROVEN. The D3-B2 carriers = a HARD boot failure: either the PSP signature halt (worker3's static hypothesis, the t02 verifier never decoded) or the boot-time application of the VCN policy/gasket records wedging on the same incomplete-transaction denial proven at runtime. Both mechanisms kill the route; their discrimination (the UART capture on J5) is optional and does not change the verdict.
- FINAL CAMPAIGN VERDICT: the $PS1 carrier route is CLOSED DEFINITIVELY (2 attempts today, both byte-exact verified flashes, both hard-failed; the discriminator ran). Combined with the runtime exhaustion (5 experiments) and the D3-A DFG disproof, every software-reachable path to the dom14/VCN power grant is exhausted. Remaining classes: the PSP signing/verification key material RE (the loop goal (a), offline) and the hardware/fuse class.
- ROLLBACK: the operator powers off + re-attaches the clip; the flash-back = pre_d3b2_retest.bin (the proven 3-minute procedure).

## D4 SMU-SIGNATURE PROBE: intent (2026-09-12, pre-write log per G4)

- INTENT: determine empirically whether the PSP on-die ROM verifies the SMU firmware blob (PSP dir type 0x08, $PS1 format, kid 8b8df41e...) or loads it unchecked. The SMU firmware is the dom14 power-denial enforcer; if it is loadable without a signature check, the unlock route = patching the SMU body directly in the BIOS (the operator's "everything is in the BIOS" direction). If the probe halts = the SMU is under the ROM signature check and every BIOS-resident route is closed.
- TARGET: 04_D4-SMUprobe-1byte.bin built from 00_BASE-reference_stock.bin (md5 7607a34caeca1ffb95e1f7c52ca227d5) with ONE byte changed: file offset 0x93c64c (the SMU payload zero padding, the longest zero run 21863 bytes, the payload region 0x8FF200..0x92F0FF, well before the 0x100 signature tail): 0x00 -> 0x01. D4 md5 = 32a22534aad10bae64595e663a7e8e2a.
- PROCEDURE: the proven CH347T cycle (the dump -> write -> flashrom Verify -> the independent readback md5).
- EXPECTED: boot OK = the SMU signature unchecked -> the full SMU patch design opens. Silent halt (the D3-B2 signature) = the SMU verified -> the campaign final.
- ROLLBACK: pre_d3b2_retest.bin (the proven 3-minute programmer cycle).
- The operator approved the flash ("шей").

## D4 SMU-SIGNATURE PROBE RESULT (2026-09-12, hardware-verified)

- The D4 (1 byte changed in the SMU payload zero padding at file 0x93c64c, 00->01; the readback md5 32a22534... = the image md5, byte-exact) cold-booted: "нет инициализации" — the HARD halt, identical to the D3-B2 signature.
- The changed byte sits in a 21863-byte zero pad, behaviorally inert. The halt therefore = the on-die ROM signature check over the SMU blob ($PS1, kid 8b8df41e).
- VERDICT: the SMU firmware is signature-verified by the PSP boot ROM and is NOT patchable in the BIOS. The campaign map is now complete: every BIOS-resident enforcer (the $PS1 carriers AND the SMU body) is signature-gated by the on-die ROM; the only freely modifiable surface (the APCB, checksum-only) is proven not-the-lock (D3-A); the runtime is exhausted (5 experiments); the signing keys are RSA-2048 (math-closed); the verifier lives in the on-die ROM (unreadable/unpatchable from the image).
- FINAL: all software routes to the VCN/dom14 power grant are exhausted and each closure is hardware-verified. Remaining: the hardware/fuse class (out of the software scope) and the optional UART-on-J5 attribution (the diagnostics only).
- ROLLBACK: pre_d3b2_retest.bin (md5 5ccde448... = the state that booted mode1 cleanly) after the operator powers off + re-attaches the clip.
