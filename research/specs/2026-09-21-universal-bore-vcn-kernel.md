# Spec: universal BORE+VCN kernel for BC250-01

Date: 2026-09-21. Status: planned (build host undecided). Skill: spec-planning.

## 1. Title and scope

Build `linux-cachyos-bore-vcn-bc250` (7.2-stable based): keeps the proven
boot path of running `7.2.0-1.92-cachyos-vcn-bc250`, adds the BORE CPU
scheduler (absent now), retains the local VCN probe-mode delta
(`amdgpu.bc250_vcn_mode` 0/1/2). Side-by-side install; known-good entries
stay untouched. Out of scope: 7.3-rc rebase, firmware changes, VCN unlock
itself (unchanged research state).

## 2. Planning anchor

- Running: `7.2.0-1.92-cachyos-vcn-bc250`, boots mode1, NO BORE
  (`/proc/config.gz`: 9754 CONFIGs, `NO_HZ_FULL`, no `SCHED_BORE`).
- Builder: `MastaG/linux-cachyos-bc250` @ `93f8e69` (Sep 21 2026),
  `prepare-pkgbuild.sh` + `CACHYOS_SOURCE_VARIANT=linux-cachyos-bore`,
  patch set `patches/linux-cachyos/` (0001-0013: telemetry, nct6687d,
  gfx1013 x2, kfd, ttm-guard, sclk-range, 40cu-unlock, DCN/PCON x5).
- VCN delta (local only): corpus `import/.../archives/imported/recon-evidence/legacy-tmp-bc250-recon/`
  `0010-bc250-amdgpu-discovery-default-offset.patch` (25 lines),
  `0011-bc250-vcn-probe-mode.patch` (319 lines),
  `0009-bc250-vcn-safe-direct-load.patch` (68 lines, maybe absorbed).
- BORE source: CachyOS bore PKGBUILD variant (preferred) or
  `CachyOS/kernel-patches/7.2/sched/0001-bore-cachy.patch` (fallback).
- XanMod: REJECT as base — `docs/research/2026-09-21-xanmod-kernel-evaluation.md`.

## 3. Connected groups / existing logic

- Board `~/linux-cachyos-bc250` = MastaG checkout @ `a1ede09` (Aug 14,
  stale, old `patches/kernel-7.2/` layout) + `build/linux-cachyos-rc/`
  recipe (PKGBUILD, `bc250-build.env`) — reusable template, refresh first.
- Installed siblings `linux-cachyos-bc250` (Aug 21) and
  `linux-cachyos-rc-bc250` (Aug 26) came from MastaG CI; `-vcn-bc250`
  (Aug 26, Unknown Packager) is the undocumented local build — its exact
  recipe was never recorded (gap; reconstruct from MastaG-7.2 + delta).
- `.config` seed: `/proc/config.gz` of the running kernel (proven boot).
- Limine: new entry, keep mode1/mode2/diagnostic entries as fallback.

## 4. Use cases

- U1 gaming daily: BORE latencies + stable amdgpu + MangoHud-verified FPS.
- U2 VCN research: `bc250_vcn_mode=1` probe boot + `=2` controlled probe
  behave exactly as on `-vcn-bc250` (no regression).
- U3 fallback: any failure boots back into `-vcn-bc250` entries unchanged.

## 5. Implementation checklist

- [ ] Pin MastaG revision + record `source-fingerprint.sh` output.
- [ ] Fetch `linux-cachyos-bore` PKGBUILD at matching 7.2 tag.
- [ ] Apply MastaG `linux-cachyos` set; apply local 0010/0011 (+0009 iff
      absent upstream — check `disabled/` first); resolve rejects.
- [ ] Seed `.config` from running `/proc/config.gz`; enable
      `SCHED_BORE`, default new symbols; `PROCESSOR_OPT=generic_v3`,
      `CPU_TUNE=znver2` (MastaG defaults).
- [ ] pkgbase `linux-cachyos-bore-vcn-bc250`, pkgrel 1; build on decided
      host (laptop ready; .74 needs WSL+Arch+reboot; board too slow).
- [ ] Install `-bin` + `-headers` side-by-side on board; add limine entry.
- [ ] P0 boot (video+LAN+SSH), P1 mode1 userspace, BORE sysctl/dmesg proof,
      U2 mode1/mode2 probe parity, U1 10-min game smoke + VRAM check.
- [ ] Record hashes, config diff, dmesg delta in action log + memory.

## 6. Open questions

- BLOCKING Q1: build host? (a) laptop now (16T/61G/66G free/toolchain OK,
  ~30-60 min, user works on it); (b) .74 after operator installs WSL2 +
  Arch + reboot (20C/28T, fastest, but reboot + Kernel-Power-41 history);
  (c) board (too slow, last resort).
- Q2 (non-blocking): is 0009 absorbed in current MastaG set or `disabled/`?
- Q3 (non-blocking): local 0008 vs upstream `0008-bc250-40cu-unlock`
  (`bc250-40cu-enable` vs `ps5-40cu-enable` print) — keep local wording?
- Q4 (non-blocking): 7.3-rc-bore instead of 7.2-stable? (MastaG rc set is
  HDMI/PCON-heavy; 7.2 matches proven board state — default stays 7.2.)

## 7. Decision log

- D1 (2026-09-21, root): base = MastaG + CachyOS-bore, NOT XanMod.
  G7 addendum: XanMod IS current (GitLab 7.2.6, not the stale GitHub
  6.11 mirror) — but stays non-base: Debian config family, zero BC250
  content, and its fair.c latency patch structurally conflicts with BORE.
  XanMod state = ADAPT: cherry-pick block/vfs/mm-le9uo/cpufreq/BBRv3
  tunables that dry-run cleanly; skip on first reject, no hand-porting.
  See `docs/research/2026-09-21-xanmod-kernel-evaluation.md`.
- D2 (2026-09-21, root): new pkgbase side-by-side; no overwrite of
  working `-vcn-bc250` (minimal reversible change).
- D3 (pending operator): Q1 build host. No build starts before D3.

## 8. pkgrel 2: SCLK_MAX 2230 -> 3000 (2026-09-22)

- Anchor: 1.1 (7.2.6-1.1) boots mode1, BORE on, OD_RANGE 350-2230
  (MastaG 0007 active), OD writes locked (ppfeaturemask lacks
  0x4000; mask fix staged in cmdline for next boot).
- Change (one variable): local 0025 raises CYAN_SKILLFISH_SCLK_MAX
  to 3000 (context = post-0007). Same PIN 93f8e69, same 0014/0016
  VCN + 8 xanmod survivors, same flags (generic_v3, znver2).
  BC250_PKGREL=2 -> 7.2.6-1.2, side-by-side install.
- Checklist: sync 0025 + phase2-pkgrel2.sh to bridge; phase1
  re-run; nohup full build (ccache warm); collect 2 pkgs + sha256;
  install; reboot (operator window, combines mask + BF move);
  verify OD_RANGE 350-3000 + boot PASS same as 1.1.
- Open: SMU-side ceiling unknown (empirical after OD unlock);
  3000 is clamp-only, never auto-targeted; OC staging per
  docs/action-logs/2026-09-22-gpu-oc-2100-2200.md.
