# Action log: bore-vcn kernel build (kukuruza-pc WSL archlinux)

Date: 2026-09-21. Actor: root. Spec: `specs/2026-09-21-universal-bore-vcn-kernel.md`.

## Intent (before execution)

Build `linux-cachyos-bore-vcn-bc250` 7.2.6: MastaG @ `93f8e69aee9f109b609297833933a2699a9a8ac3`

- `linux-cachyos-bore` + 13-patch BC250 set + local VCN delta + XanMod
  ADAPT survivors, `.config` seeded from running `-vcn-bc250`
  (`/proc/config.gz`, 9754 CONFIGs). Side-by-side pkgbase; no overwrite.
  Build host: WSL2 `archlinux` on .74 (28 threads, 31G RAM), user `builder`.
  Install on board + boot tests are SEPARATE gated steps (not this log yet).

## Phase 1: trial prepare + XanMod dry-run

- Bundle `/tmp/kbore` (16 patches + 10 xanmod + board.config + phase1.sh)
  shipped to `C:\Temp\kbore` (30 items).
- `prepare-pkgbuild.sh` OK (bore variant, custom suffix, nct6687d
  `5f12dd1b`). Board-config seed broke makepkg checksums (expected);
  fixed via `updpkgsums` after first download (custom python surgery
  abandoned — brace-expansion order).
- MastaG 0001-0013 apply clean (one benign +1 offset); local 0014
  (0009 safe-direct-load) applies with offsets.
- Local 0015 (corpus 0010 discovery-default-offset) REJECTED: 7.2.6
  already contains it upstream (same code, own comment; our patch header
  says "gained between v7.2-rc7 and v7.2"). DROPPED from the set — no
  function lost. 0016 (probe-mode) status: untested (build died first).
- Infra lessons: heredoc-created .ps1 mangles newlines (G6: write_file
  only); `$VAR` dies in inline `bash -c` through pwsh (rule: ship .sh
  files, run `bash /mnt/c/Temp/...`; inline only var-free one-liners);
  pc-run.py timeout 900 s; /tmp is tmpfs (builds in ~/).

## Phase 1 rerun (without 0015) — DONE

- 0014 + 0016 (probe-mode, 319 lines) apply clean with offsets/fuzz.
- Package identity: `linux-cachyos-bore-vcn-bc250 7.2.6-1.1`, BORE selected
  (`SCHED_BORE y`). Trial prepare OK, PHASE1_DONE, rc=0.
- XanMod dry-run: KEEP 8 (le9uo, block 0007-0010, vfs 0012, max_map_count
  0013, cpufreq 0015), SKIP 2 (bbrv3 — already in CachyOS scope, vmscan
  0014 — conflict). No hand-porting per spec.

## Phase 2: full build — RUNNING

- Promoted 8 XanMod survivors as 0017-0024. tmux `kbore`, 19:00:55,
  `MAKEFLAGS=-j28`, znver2, ccache armed (`~/.ccache`, 15G).
- First launch HUNG at kconfig RUST prompt: seed 7.2.0 on tree 7.2.6
  raises interactive prompts; tmux pty blocks (phase1 via ssh had EOF
  stdin and passed). Fix: `< /dev/null` on makepkg (= olddefconfig
  defaults). Relaunched; CC/LD/AR flowing (verified 19:02).
- Build log: `~/kbore/build-full.log` (builder, WSL archlinux).
- Next: poll for BUILD_RC, verify packages (nct6687.ko present, BORE in
  config, vcn_mode param), ship .pkg.tar.zst to board, limine entry,
  P0/P1/U1/U2 per spec. Install = separate gate.

## Install on board — INTENT (before execution)

- Verified (artifact-verification): BUILD_RC=0; 0 patch errors; BORE on;
  nct6687.ko + bc250_vcn_mode + 40cu-probe in package; hashes match on all
  3 hops (pkg `f284079c…`, headers `7697a671…`, config `90063125…`);
  independent readers (pacman -Qip + bsdtar, 6490 .ko, vmlinuz present);
  config delta 66/10586 (BORE added, HZ/tick/governor/NCT6687 identical).
  Class: STATICALLY VERIFIED. Boot/hardware acceptance: NOT YET.
- Target: `steammachine@127.0.0.1`, `/tmp/kb/*.pkg.tar.zst`.
- Procedure: sha256 re-check → `pacman -Qip` (3rd reader) →
  `pacman -U` (side-by-side; existing kernels untouched) → verify preset
  - `/boot` images → backup `/boot/limine.conf` → `limine-entry-tool` →
    clone base entry to mode1 (`vcn_mode=1`) + mode2 (mode2 cmdline) →
    syntax review → KEEP `default_entry` (no default change).
- Expected: new entries bootable; default still `-vcn-bc250-mode1`.
- Rollback: `pacman -Rns linux-cachyos-bore-vcn-bc250{-headers,}`;
  restore `limine.conf` from backup; re-run `limine-entry-tool`.
- Boot test (P0/P1/U1/U2) is operator-gated: user selects the entry at
  the menu; agent verifies via SSH after.

## Install on board — RESULT

DONE 2026-09-21 ~20:35 Kyiv (install only; boot test gated):

- Shipped .74 → laptop → board, sha256 match on all 3 hops.
- `pacman -U`: 7727 files, 0 missing; mkinitcpio images OK
  (initramfs 56 MB, vmlinuz 18 MB); snapper root:112.
- `/boot/limine.conf` backed up (`limine.conf.bak-20260921-borevcn`).
  Hook auto-created base entry; added mode0/1/2 via sanctioned
  `limine-entry-tool --add-kernel ... -modeN` + new drop-in
  `/etc/limine-entry-tool.d/91-bore-vcn-probe.conf` (separate file,
  clean rollback). Hashes match base (same images).
- `default_entry` UNCHANGED (`-vcn-bc250-mode1`); fallback unchanged.
- Class: INSTALLED, STATICALLY VERIFIED. Boot/hardware acceptance:
  UNRUN — operator selects `linux-cachyos-bore-vcn-bc250-mode1` at the
  menu; agent verifies (uname, BORE sysctl, VCN probe, game smoke).

## Default + timeout change — INTENT (before execution)

- User order: default → `CachyOS/linux-cachyos-bore-vcn-bc250-mode1`
  (mirrors previous default `...-vcn-bc250-mode1`), `timeout: 15` → `7`.
- Procedure: fresh backup `/boot/limine.conf` →
  `sed -i` the two unique lines → grep-verify → keep fallback entry.
- Expected: next boot auto-selects bore-vcn-mode1 after 7 s; old entries
  intact; fallback `CachyOS/linux-cachyos-bc250` unchanged.
- Rollback: restore backup, or pick any old entry at the menu (7 s window).
- Risk: if bore-vcn fails to boot, box needs physical menu selection.
  Operator is at the board (accepted implicitly by the order).

## Default + timeout change — RESULT

DONE 2026-09-21 ~20:45 Kyiv: `timeout: 7`,
`default_entry: CachyOS/linux-cachyos-bore-vcn-bc250-mode1`,
fallback unchanged. Backup: `limine.conf.bak-20260921-default`.
Next boot auto-selects bore-vcn-mode1 unless the operator picks older.

## Incident: watchdog DOWN during build (2026-09-21 19:13+05)

- hdd-files `pc-watchdog` logged ONE `DOWN (timed out after 90 s)` at
  19:13, recovered `ok` at 19:18. Cause: -j28 kernel build saturating
  host CPU (100%), starving the powershell probe. No crash (uptime
  continuous), no reboot, sshd healthy (2.6 s handshake).
- Mitigation: `vmmemWSL` (pid 11392) PriorityClass → BelowNormal, so host
  sshd/probes preempt the build. Build continues slightly slower.
  `phase=blocked` in the log is pre-existing (since 18:16, before the
  build) and belongs to the photo agent, not this task.
